import os
import pwd
import re
import shutil
import time
import itertools
import sys
import threading
from typing import List, Optional
from config import Config, Colors
from utils import handle_exception

def create_directory(directory: str):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory, mode=Config.DEFAULT_PERMS)
            if os.access(directory, os.W_OK):
                os.chown(directory, os.getuid(), os.getgid())
            else:
                raise PermissionError(f"No permissions to modify {directory}")
        data_dir = os.path.join(os.path.expanduser('~'), '.data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, mode=Config.DEFAULT_PERMS)
            if os.access(data_dir, os.W_OK):
                os.chown(data_dir, os.getuid(), os.getgid())
            else:
                raise PermissionError(f"No permissions to modify {data_dir}")
    except PermissionError as e:
        handle_exception(f"Directory permission error", e, True)

def check_directory_permissions(directory: str):
    if not os.access(directory, os.R_OK):
        raise PermissionError(f"No read permissions for {directory}")
    for root, dirs, files in os.walk(directory):
        for d in dirs:
            if not os.access(os.path.join(root, d), os.R_OK):
                raise PermissionError(f"No read permissions for directory {os.path.join(root, d)}")
        for f in files:
            if not os.access(os.path.join(root, f), os.R_OK):
                raise PermissionError(f"No read permissions for file {os.path.join(root, f)}")

def sanitize_file_path(file_path: str, root_dir: str) -> str:
    abs_path = os.path.abspath(file_path)
    root_abs = os.path.abspath(root_dir)
    if not abs_path.startswith(root_abs + os.sep):
        raise ValueError(f"Invalid path: {file_path}")
    if os.path.islink(file_path):
        raise ValueError(f"Symbolic links not allowed: {file_path}")
    return abs_path

def read_tool_file(file_path: str, max_file_size: int, root_dir: str) -> List[str]:
    try:
        if os.path.getsize(file_path) > max_file_size:
            print(f"{Colors.RED}[-]{Colors.RESET} File {file_path} exceeds maximum allowed size.")
            return []
        abs_path = sanitize_file_path(file_path, root_dir)
        if not os.path.exists(abs_path):
            return []
        with open(abs_path, 'r', encoding='utf-8') as file:
            lines = [line.rstrip('\n') for line in file]
        return lines if lines else []
    except (PermissionError, UnicodeDecodeError, ValueError) as e:
        print(f"{Colors.RED}[-]{Colors.RESET} Error reading file {file_path}: {e}")
        return []

def get_safe_editor() -> Optional[str]:
    allowed_editors = {
        'nano': '/bin/nano',
        'vim': '/usr/bin/vim',
        'vi': '/usr/bin/vi'
    }
    editor = os.environ.get('EDITOR', 'nano')
    editor_name = os.path.basename(editor).split()[0]
    editor_path = allowed_editors.get(editor_name)
    if editor_path and os.path.exists(editor_path):
        return editor_path
    return None

def parse_directory_structure(search_command, interactive=True):
    if not os.path.exists(search_command.root_dir):
        raise FileNotFoundError(f"Directory not found at {search_command.root_dir}")

    search_command.tools_by_category = {}
    search_command.categories = {}
    search_command.tool_to_file = {}
    search_command.tool_to_category = {}
    seen_tools = set()
    duplicate_count = 0

    if interactive:
        title = " LOADING TOOLS "
        term_width = min(shutil.get_terminal_size().columns, 50)
        side_width = (term_width - len(title) - 4) // 2
        total_width = len(title) + 2 * side_width + 4
        spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

        def print_loading_box(spinner_char, clear_lines=0):
            if clear_lines > 0:
                sys.stdout.write(f"\033[{clear_lines}F\033[J")
            sys.stdout.write(f"{Colors.BLUE}{Colors.BOLD}╓{'─' * side_width}╢{Colors.WHITE}{title}{Colors.BLUE}╟{'─' * side_width}╖{Colors.RESET}\n")
            sys.stdout.write(f"  {Colors.GREEN}┃ {spinner_char}{Colors.RESET} Processing...{' ' * (total_width - 20)}{Colors.RESET}\n")
            sys.stdout.write(f"{Colors.BLUE}{Colors.BOLD}╙{'─' * (total_width - 2)}╜{Colors.RESET}")
            sys.stdout.flush()

        start_time = time.time()
        def animate():
            first_frame = True
            for i in itertools.count():
                if time.time() - start_time >= 1:
                    break
                print_loading_box(spinner_chars[i % len(spinner_chars)], clear_lines=3 if not first_frame else 0)
                first_frame = False
                time.sleep(0.1)

        spinner_thread = threading.Thread(target=animate)
        spinner_thread.start()

    try:
        for category in sorted(os.listdir(search_command.root_dir)):
            category_path = os.path.join(search_command.root_dir, category)
            if not os.path.isdir(category_path):
                continue

            tools = []
            for tool_file in sorted(os.listdir(category_path)):
                if tool_file.endswith('.txt'):
                    tool_name = tool_file[:-4]
                    if tool_name in seen_tools:
                        if interactive:
                            sys.stdout.write(f"\r{' ' * total_width}\r{Colors.RED}[-]{Colors.RESET} Duplicate tool: '{tool_name}' in {category}. Ignored.\n")
                            sys.stdout.flush()
                            time.sleep(0.5)
                        continue
                    seen_tools.add(tool_name)
                    tools.append(tool_name)
                    tool_path = os.path.join(category_path, tool_file)
                    search_command.tool_to_file[tool_name] = tool_path
                    search_command.tool_to_category[tool_name] = category

            search_command.categories[category] = tools
            search_command.tools_by_category[category] = tools

    finally:
        if interactive:
            spinner_thread.join()

    if not search_command.categories:
        raise ValueError("No categories with valid tools found in the directory")

    if interactive:
        total_tools = sum(len(tools) for tools in search_command.tools_by_category.values())
        total_categories = len(search_command.categories)

        sys.stdout.write(f"\033[3F\033[J")
        sys.stdout.write(f"{Colors.BLUE}{Colors.BOLD}╓{'─' * side_width}╢{Colors.WHITE}{title}{Colors.BLUE}╟{'─' * side_width}╖{Colors.RESET}\n")
        sys.stdout.write(f"  {Colors.GREEN}┃ 📂{Colors.RESET} Categories: {Colors.CYAN}{total_categories:>3}{Colors.RESET}\n")
        sys.stdout.write(f"  {Colors.GREEN}┃ 🔧{Colors.RESET} Tools: {Colors.CYAN}{total_tools:>3}{Colors.RESET}\n")
        if duplicate_count > 0:
            sys.stdout.write(f"  {Colors.YELLOW}┃ ⚠️{Colors.RESET} Dup: {Colors.YELLOW}{duplicate_count:>3}{Colors.RESET}\n")
        sys.stdout.write(f"{Colors.BLUE}{Colors.BOLD}╙{'─' * (total_width - 2)}╜{Colors.RESET}\n\n")
        sys.stdout.flush()
        time.sleep(1)

def load_tools(search_command, interactive=None):
    if interactive is None:
        interactive = search_command.interactive
    if interactive:
        search_command._clear_screen()
    try:
        parse_directory_structure(search_command, interactive)
    except (FileNotFoundError, ValueError) as e:
        print(f"{Colors.RED}[-] Error: {e}{Colors.RESET}")