from typing import List
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.completion import Completer, Completion
from config import Colors, __version__
from utils import strip_ansi_codes, handle_exception, normalize_text
from completer import EnhancedCompleter
from services import get_safe_editor, sanitize_file_path
import os
import re
import shutil
import time
import itertools
import sys
import subprocess

def init_prompt_session(search_command):
    try:
        prompt_style = Style.from_dict({
            'prompt.parens': '#5EBDAB',
            'prompt.name': ' #fe013a bold' ,
            'prompt.dash': ' #5EBDAB',
            'prompt.brackets': '#5EBDAB',
            'prompt.success': '#5EBDAB',
            'prompt.failure': '#EC0101',
            'prompt.white': '#FFFFFF',
            'prompt.variable': '#FEA44C italic',
            'input': '#F5F5F5',
            'completion-menu': 'bg:#131419 #474747',
            'completion-menu.completion': 'bg:#131419 #F5F5F5',
            'completion-menu.tool-completion.current': 'bg:#347cf1 #FFFFFF bold',
            'completion-menu.tool-completion': 'bg:#131419 #FEA44C',
            'completion-menu.category-completion.current': 'bg:#FEA44C #FFFFFF bold',
            'completion-menu.category-completion': 'bg:#131419 #347cf1',
            'completion-menu.meta.completion': 'bg:#131419 #474747 italic',
            'completion-menu.meta.completion.current': 'bg:#131419 #fcfcd4 italic',
            'completion-menu.multi-column-meta': 'bg:#131419 #f79b3e',
        })
        search_command.prompt_style = prompt_style
    except ValueError as e:
        handle_exception(f"Error setting styles", e, True)

    try:
        completer = EnhancedCompleter(
            categories=list(search_command.categories.keys()),
            tools=[tool for tools in search_command.tools_by_category.values() for tool in tools],
            tools_by_category=search_command.tools_by_category,
            recent_ips=search_command.recent_ips,
            recent_urls=search_command.recent_urls,
            tool_to_category=search_command.tool_to_category,
            tool_to_file=search_command.tool_to_file
        )
        search_command.completer = completer
    except TypeError as e:
        handle_exception(f"Error initializing autocompletion", e, True)

    kb = KeyBindings()
    
    @kb.add(Keys.ControlL)
    def clear_screen(event):
        search_command._clear_screen()
        search_command.print_header()
        event.app.renderer.reset()
        event.app.invalidate()

    @kb.add(Keys.ControlT)
    def list_tools(event):
        search_command._list_tools()
        event.app.renderer.reset()
        event.app.invalidate()

    @kb.add(Keys.ControlK)
    def list_categories(event):
        search_command._list_categories()
        event.app.renderer.reset()
        event.app.invalidate()

    @kb.add(Keys.ControlR)
    def refresh_tools(event):
        try:
            search_command._load_tools()
            search_command._init_prompt_session()
            search_command._clear_screen()
            print(f"{Colors.GREEN}✔ {Colors.RESET}Tools reloaded successfully.\n")
        except (FileNotFoundError, PermissionError, ValueError) as e:
            handle_exception(f"Error reloading tools", e)
        event.app.renderer.reset()
        event.app.invalidate()

    @kb.add(Keys.ControlE)
    def edit_last_tool(event):
        if search_command.last_query and search_command.last_query in search_command.tool_to_file:
            editor_path = get_safe_editor()
            if not editor_path:
                print(f"{Colors.RED}[-]{Colors.RESET} No compatible editor found (nano, vim, vi).")
                return
            try:
                file_path = sanitize_file_path(search_command.tool_to_file[search_command.last_query], search_command.root_dir)
                subprocess.run([editor_path, file_path], check=True)
                
                editor_name = os.path.basename(editor_path)
                
                print(f"{Colors.GREEN}[✔] {Colors.RESET}Opening {Colors.GREEN}{search_command.last_query}{Colors.RESET} with {editor_name}. Use {Colors.BLUE}refresh{Colors.RESET} to reload changes.\n")
            except (subprocess.CalledProcessError, FileNotFoundError, ValueError) as e:
                print(f"{Colors.RED}[-]{Colors.RESET} Error opening editor: {e}")
        else:
            print(f"{Colors.RED}[-]{Colors.RESET} No recent tool to edit. Use 'edit <tool>'.")
        event.app.renderer.reset()
        event.app.invalidate()

    @kb.add(Keys.ControlC)
    def exit_program(event):
        print(f"\n\t\t\t{Colors.RED}{Colors.BOLD}H4PPY H4CK1NG{Colors.RESET}")
        sys.exit(0)

    def get_prompt():
        display_query = search_command.last_query if search_command.last_query else "~"
        if search_command.last_command_success:
            return [
                ('class:prompt.parens', '('),
                ('class:prompt.name', 'searchCommand'),
                ('class:prompt.parens', ')'),
                ('class:prompt.dash', '-'),
                ('class:prompt.brackets', '['),
                ('class:prompt.white', display_query),
                ('class:prompt.brackets', ']'),
                ('class:prompt.dash', '-'),
                ('class:prompt.brackets', '['),
                ('class:prompt.success', '✔'),
                ('class:prompt.brackets', ']'),
                ('class:prompt.white', ' > '),
            ]
        else:
            return [
                ('class:prompt.parens', '('),
                ('class:prompt.name', 'searchCommand'),
                ('class:prompt.parens', ')'),
                ('class:prompt.dash', '-'),
                ('class:prompt.brackets', '['),
                ('class:prompt.white', display_query),
                ('class:prompt.brackets', ']'),
                ('class:prompt.dash', '-'),
                ('class:prompt.brackets', '['),
                ('class:prompt.failure', '✘'),
                ('class:prompt.brackets', ']'),
                ('class:prompt.white', ' > '),
            ]

    history_file = os.path.join(os.path.expanduser('~'), '.searchcommand_history')
    search_command.prompt_session = PromptSession(
        completer=search_command.completer,
        key_bindings=kb,
        style=search_command.prompt_style,
        message=get_prompt,
        validate_while_typing=False,
        multiline=False,
        erase_when_done=True,
        history=FileHistory(history_file)
    )

def create_add_category_prompt(search_command):
    prompt_style = Style.from_dict({
        'prompt.parens': '#5EBDAB',
        'prompt.name': '#fe013a bold',
        'prompt.dash': '#5EBDAB',
        'prompt.brackets': '#5EBDAB',
        'prompt.success': '#5EBDAB',
        'prompt.white': '#FFFFFF',
        'input': '#F5F5F5',
        'completion-menu': 'bg:#131419 #474747',
        'completion-menu.completion': 'bg:#131419 #347cf1',
        'completion-menu.completion.current': 'bg:#FEA44C #FFFFFF bold',
    })

    class ExitCompleter(Completer):
        def get_completions(self, document, complete_event):
            word = document.get_word_before_cursor()
            word_normalized = normalize_text(word).lower() if word and normalize_text(word) else ""
            if 'q'.startswith(word_normalized):
                yield Completion(
                    'q',
                    start_position=-len(word),
                    display=HTML('[q] Exit mode'),
                    style='class:completion-menu.completion'
                )

        async def get_completions_async(self, document, complete_event):
            for completion in self.get_completions(document, complete_event):
                yield completion

    kb = KeyBindings()
    @kb.add(Keys.ControlC)
    def _(event):
        event.app.exit(exception=KeyboardInterrupt)

    def get_prompt():
        return [
            ('class:prompt.parens', '('),
            ('class:prompt.name', 'searchCommand'),
            ('class:prompt.parens', ')'),
            ('class:prompt.dash', '-'),
            ('class:prompt.brackets', '['),
            ('class:prompt.white', 'add categories'),
            ('class:prompt.brackets', ']'),
            ('class:prompt.dash', '-'),
            ('class:prompt.brackets', '['),
            ('class:prompt.success', '✔'),
            ('class:prompt.brackets', ']'),
            ('class:prompt.white', ' > '),
        ]

    return PromptSession(
        completer=ExitCompleter(),
        key_bindings=kb,
        style=prompt_style,
        message=get_prompt,
        validate_while_typing=False,
        multiline=False,
        complete_while_typing=False,
        complete_style='multi_column'
    )

def create_add_tool_prompt(search_command):
    prompt_style = Style.from_dict({
        'prompt.parens': '#5EBDAB',
        'prompt.name': '#fe013a bold',
        'prompt.dash': '#5EBDAB',
        'prompt.brackets': '#5EBDAB',
        'prompt.success': '#5EBDAB',
        'prompt.white': '#FFFFFF',
        'input': '#F5F5F5',
        'completion-menu': 'bg:#131419 #474747',
        'completion-menu.completion': 'bg:#131419 #347cf1',
        'completion-menu.completion.current': 'bg:#FEA44C #FFFFFF bold',
    })

    class CategoryCompleter(Completer):
        def __init__(self, categories):
            self.categories = categories

        def get_completions(self, document, complete_event):
            word = document.get_word_before_cursor()
            word_normalized = normalize_text(word).lower() if word and normalize_text(word) else ""
            if 'q'.startswith(word_normalized):
                yield Completion(
                    'q',
                    start_position=-len(word),
                    display=HTML('[q] Exit mode'),
                    style='class:completion-menu.completion'
                )
            for category in self.categories:
                if normalize_text(category).lower().startswith(word_normalized):
                    yield Completion(
                        category,
                        start_position=-len(word),
                        display=HTML(f'📂 {category}'),
                        style='class:completion-menu.completion'
                    )

        async def get_completions_async(self, document, complete_event):
            for completion in self.get_completions(document, complete_event):
                yield completion

    kb = KeyBindings()
    @kb.add(Keys.ControlC)
    def _(event):
        event.app.exit(exception=KeyboardInterrupt)

    def get_prompt():
        return [
            ('class:prompt.parens', '('),
            ('class:prompt.name', 'searchCommand'),
            ('class:prompt.parens', ')'),
            ('class:prompt.dash', '-'),
            ('class:prompt.brackets', '['),
            ('class:prompt.white', 'add tool'),
            ('class:prompt.brackets', ']'),
            ('class:prompt.dash', '-'),
            ('class:prompt.brackets', '['),
            ('class:prompt.success', '✔'),
            ('class:prompt.brackets', ']'),
            ('class:prompt.white', ' > '),
        ]

    return PromptSession(
        completer=CategoryCompleter(sorted(search_command.categories.keys())),
        key_bindings=kb,
        style=prompt_style,
        message=get_prompt,
        validate_while_typing=False,
        multiline=False,
        complete_while_typing=False,
        complete_style='multi_column'
    )

def create_delete_category_prompt(search_command):
    prompt_style = Style.from_dict({
        'prompt.parens': '#5EBDAB',
        'prompt.name': '#fe013a bold',
        'prompt.dash': '#5EBDAB',
        'prompt.brackets': '#5EBDAB',
        'prompt.success': '#5EBDAB',
        'prompt.white': '#FFFFFF',
        'input': '#F5F5F5',
        'completion-menu': 'bg:#131419 #474747',
        'completion-menu.completion': 'bg:#131419 #347cf1',
        'completion-menu.completion.current': 'bg:#FEA44C #FFFFFF bold',
    })

    class DeleteCategoryCompleter(Completer):
        def __init__(self, categories):
            self.categories = categories

        def get_completions(self, document, complete_event):
            word = document.get_word_before_cursor()
            word_normalized = normalize_text(word).lower() if word and normalize_text(word) else ""
            if 'q'.startswith(word_normalized):
                yield Completion(
                    'q',
                    start_position=-len(word),
                    display=HTML('[q] Exit mode'),
                    style='class:completion-menu.completion'
                )
            for category in self.categories:
                if normalize_text(category).lower().startswith(word_normalized):
                    yield Completion(
                        category,
                        start_position=-len(word),
                        display=HTML(f'📂 {category}'),
                        style='class:completion-menu.completion'
                    )

        async def get_completions_async(self, document, complete_event):
            for completion in self.get_completions(document, complete_event):
                yield completion

    kb = KeyBindings()
    @kb.add(Keys.ControlC)
    def _(event):
        event.app.exit(exception=KeyboardInterrupt)

    def get_prompt():
        return [
            ('class:prompt.parens', '('),
            ('class:prompt.name', 'searchCommand'),
            ('class:prompt.parens', ')'),
            ('class:prompt.dash', '-'),
            ('class:prompt.brackets', '['),
            ('class:prompt.white', 'delete category'),
            ('class:prompt.brackets', ']'),
            ('class:prompt.dash', '-'),
            ('class:prompt.brackets', '['),
            ('class:prompt.success', '✔'),
            ('class:prompt.brackets', ']'),
            ('class:prompt.white', ' > '),
        ]

    return PromptSession(
        completer=DeleteCategoryCompleter(sorted(search_command.categories.keys())),
        key_bindings=kb,
        style=prompt_style,
        message=get_prompt,
        validate_while_typing=False,
        multiline=False,
        complete_while_typing=True,
        complete_style='multi_column'
    )

def create_delete_tool_prompt(search_command):
    prompt_style = Style.from_dict({
        'prompt.parens': '#5EBDAB',
        'prompt.name': '#fe013a bold',
        'prompt.dash': '#5EBDAB',
        'prompt.brackets': '#5EBDAB',
        'prompt.success': '#5EBDAB',
        'prompt.white': '#FFFFFF',
        'input': '#F5F5F5',
        'completion-menu': 'bg:#131419 #474747',
        'completion-menu.completion': 'bg:#131419 #347cf1',
        'completion-menu.completion.current': 'bg:#FEA44C #FFFFFF bold',
    })

    class DeleteToolCompleter(Completer):
        def __init__(self, tools):
            self.tools = tools

        def get_completions(self, document, complete_event):
            word = document.get_word_before_cursor()
            word_normalized = normalize_text(word).lower() if word and normalize_text(word) else ""
            if 'q'.startswith(word_normalized):
                yield Completion(
                    'q',
                    start_position=-len(word),
                    display=HTML('[q] Exit mode'),
                    style='class:completion-menu.completion'
                )
            for tool in self.tools:
                if normalize_text(tool).lower().startswith(word_normalized):
                    yield Completion(
                        tool,
                        start_position=-len(word),
                        display=HTML(f'🔧 {tool}'),
                        style='class:completion-menu.completion'
                    )

        async def get_completions_async(self, document, complete_event):
            for completion in self.get_completions(document, complete_event):
                yield completion

    kb = KeyBindings()
    @kb.add(Keys.ControlC)
    def _(event):
        event.app.exit(exception=KeyboardInterrupt)

    def get_prompt():
        return [
            ('class:prompt.parens', '('),
            ('class:prompt.name', 'searchCommand'),
            ('class:prompt.parens', ')'),
            ('class:prompt.dash', '-'),
            ('class:prompt.brackets', '['),
            ('class:prompt.white', 'delete tool'),
            ('class:prompt.brackets', ']'),
            ('class:prompt.dash', '-'),
            ('class:prompt.brackets', '['),
            ('class:prompt.success', '✔'),
            ('class:prompt.brackets', ']'),
            ('class:prompt.white', ' > '),
        ]

    tools = sorted(search_command.tool_to_file.keys())
    return PromptSession(
        completer=DeleteToolCompleter(tools),
        key_bindings=kb,
        style=prompt_style,
        message=get_prompt,
        validate_while_typing=False,
        multiline=False,
        complete_while_typing=True,
        complete_style='multi_column'
    )

def clear_screen(search_command):
    try:
        if os.name in ('posix', 'nt'):
            os.system('clear' if os.name == 'posix' else 'cls')
        else:
            print(f"{Colors.RED}[-]{Colors.RESET} Screen clearing not supported on this system.")
    except OSError as e:
        print(f"{Colors.RED}[-]{Colors.RESET} Error clearing screen: {e}")

def show_help(search_command):
    clear_screen(search_command)
    total_width = 79
    title = " COMMAND HELP "
    side_width = (total_width - len(title) - 4) // 2
    print(f"{Colors.BLUE}{Colors.BOLD}╓{'─' * side_width}╢{Colors.WHITE}{title}{Colors.BLUE}╟{'─' * side_width}╖{Colors.RESET}\n")
    print(f"  {Colors.GREEN}{'Command'.ljust(22)}{'Alias'.ljust(15)}{'Description'.ljust(40)}{Colors.RESET}")
    print(f"  {'─' * 22}{'─' * 12}{'─' * 40}")
    commands = [
        ("<tool>", "", "Search a tool (ex: NMAP)"),
        ("<category>", "", "Search a category (ex: RECONNAISSANCE)"),
        ("gtfsearch", "gtf", "Search in GTFOBins"),
        ("help", "h", "Show this help menu"),
        ("list tools", "lt", "List all tools"),
        ("list categories", "lc", "List all categories"),
        ("setip <IP>", "si", "Set $IP"),
        ("seturl <URL>", "su", "Set $URL"),
        ("refresh [config]", "r", "Reload tools or clear config"),
        ("exit", "q", "Exit the program"),
    ]
    for cmd, alias, desc in commands:
        print(f"  {Colors.GREEN}➜ {Colors.RESET}{cmd.ljust(22)}{Colors.GRAY}{alias.ljust(10)}{Colors.WHITE}{desc.ljust(40)}{Colors.RESET}")
    print("\n")
    print(f"  {Colors.GREEN}📦 CREATION AND MANAGEMENT OF COMMANDS AND CATEGORIES{Colors.RESET}")
    print(f"  {'─' * 22}{'─' * 50}")
    management_commands = [
        ("add categories", "ac", f"Create new category - {Colors.GREEN}interactive{Colors.WHITE}"),
        ("add tools", "at", f"Create new tool - {Colors.GREEN}interactive{Colors.WHITE}"),
        ("edit <tool>", "e", "Edit tool file"),
        ("delete category", "dc", f"Delete a category - {Colors.GREEN}interactive{Colors.WHITE}"),
        ("delete tool", "dt", f"Delete a tool - {Colors.GREEN}interactive{Colors.WHITE}"),
    ]
    for cmd, alias, desc in management_commands:
        print(f"  {Colors.GREEN}➜ {Colors.RESET}{cmd.ljust(22)}{Colors.GRAY}{alias.ljust(10)}{Colors.WHITE}{desc.ljust(40)}{Colors.RESET}")
    print("\n")
    print(f"  {Colors.GREEN}{'Shortcut'.ljust(22)}{'Description'.ljust(40)}{Colors.RESET}")
    print(f"  {'─' * 22}{'─' * 35}")
    shortcuts = [
        ("Ctrl + L", "Clear the screen"),
        ("Ctrl + T", "List tools quickly"),
        ("Ctrl + K", "List categories quickly"),
        ("Ctrl + E", "Edit last searched tool"),
        ("Ctrl + R", "Reload tools"),
        ("Ctrl + C", "Exit immediately"),
    ]
    for shortcut, desc in shortcuts:
        print(f"  {Colors.GREEN}• {Colors.RESET}{shortcut.ljust(20)}{Colors.WHITE}{desc.ljust(40)}{Colors.RESET}")
    print(f"\n{Colors.BLUE}{Colors.BOLD}╙{'─' * (total_width - 2)}╜{Colors.RESET}\n")

def print_header(search_command):
    clear_screen(search_command)
    
    banner_lines = [
        " ┌─┐┌─┐┌─┐┬─┐┌─┐┬ ┬╔═╗┌─┐┌┬┐┌┬┐┌─┐┌┐┌┌┬┐",
        " └─┐├┤ ├─┤├┬┘│  ├─┤║  │ │││││││├─┤│││ ││",
        " └─┘└─┘┴ ┴┴└─└─┘┴ ┴╚═╝└─┘┴ ┴┴ ┴┴ ┴┘└┘─┴┘",
    ]
    
    pink = "\033[38;2;242;4;90m"
    RESET = "\033[0m"
    
    colored_lines = []
    for i, line in enumerate(banner_lines):
        if i == len(banner_lines) - 1:
            colored_line = f"{pink}{line}{Colors.BOLD} V.{__version__}{RESET}"
        else:
            colored_line = f"{pink}{line}{RESET}"
        colored_lines.append(colored_line)
    
    gradient_banner = "\n".join(colored_lines)
    
    centered_banner = "\n".join(f"\t\t{line}" for line in gradient_banner.split("\n"))
    
    info_banner = f'''\n{centered_banner}

{Colors.BLUE}+ -- --=[ 📂 {Colors.RESET}Available Categories  {Colors.BLUE}{Colors.BOLD} :{Colors.RESET} {len(search_command.categories)}{Colors.RESET}{Colors.BLUE}\t\t\t   ]{Colors.RESET}
{Colors.BLUE}+ -- --=[ 🔧 {Colors.RESET}Total Tools    {Colors.BLUE}{Colors.BOLD}        :{Colors.RESET} {sum(len(tools) for tools in search_command.tools_by_category.values())}{Colors.RESET}{Colors.BLUE}\t\t\t   ]{Colors.RESET}
{Colors.BLUE}+ -- --=[ {Colors.RESET}{Colors.BOLD}{Colors.ORANGE} +{Colors.RESET} Created by             {Colors.BLUE}{Colors.BOLD}:{Colors.RESET} Jordan (SkyW4r33x) 🐉{Colors.RESET}{Colors.BLUE}\t   ]{Colors.RESET}
{Colors.BLUE}+ -- --=[ {Colors.RESET}{Colors.BOLD}{Colors.ORANGE} +{Colors.RESET} Repository             {Colors.BLUE}{Colors.BOLD}:{Colors.RESET} https://github.com/SkyW4r33x{Colors.RESET}{Colors.BLUE} ]{Colors.RESET}

{Colors.BLUE}+ -- --=[ {Colors.RESET}{Colors.BOLD}{Colors.GREEN} ➜{Colors.RESET} Type {Colors.BLUE}{Colors.BOLD}help{Colors.RESET} to see commands.\t\t\t\t   {Colors.BLUE}]{Colors.RESET}
{Colors.BLUE}+ -- --=[ {Colors.RESET}{Colors.BOLD}{Colors.GREEN} ➜{Colors.RESET} Use {Colors.BLUE}{Colors.BOLD}Tab{Colors.RESET} for autocomplete or arrows for history.\t   {Colors.BLUE}]{Colors.RESET}\n'''
    
    print(info_banner)

def colorize_command(line: str) -> str:
    in_quotes = False
    quote_char = None
    parts = []
    current_part = ""
    comment_part = ""

    try:
        i = 0
        while i < len(line):
            char = line[i]
            if char in ['"', "'"]:
                if not in_quotes:
                    if current_part:
                        parts.append(current_part)
                        current_part = ""
                    in_quotes = True
                    quote_char = char
                    current_part = char
                elif char == quote_char:
                    current_part += char
                    parts.append(current_part)
                    current_part = ""
                    in_quotes = False
                    quote_char = None
                else:
                    current_part += char
            elif char == '#' and not in_quotes:
                if current_part:
                    parts.append(current_part)
                    current_part = ""
                comment_part = line[i:]
                break
            elif char.isspace() and not in_quotes:
                if current_part:
                    parts.append(current_part)
                    current_part = ""
                parts.append(char)
            else:
                current_part += char
            i += 1

        if current_part:
            parts.append(current_part)

        colored_parts = []
        is_first_word = True

        for i, part in enumerate(parts):
            if '▶' in part:
                parts[i] = part.replace('▶', f"{Colors.RED}➤{Colors.RESET}")

        for part in parts:
            if part.isspace():
                colored_parts.append(part)
                continue

            if is_first_word and not part.startswith('-'):
                colored_parts.append(f"{Colors.LIGHT_BLUE}{part}{Colors.RESET}")
                is_first_word = False
            elif part.startswith('$'):
                colored_parts.append(f"{Colors.BLUE}{part}{Colors.RESET}")
            elif (part.startswith('"') and part.endswith('"')) or (part.startswith("'") and part.endswith("'")):
                colored_parts.append(f"{Colors.ORANGE}{part}{Colors.RESET}")
            elif part.startswith('-'):
                colored_parts.append(f"{Colors.GREEN}{part}{Colors.RESET}")
            else:
                colored_parts.append(part)

        if comment_part:
            comment_part = f"{Colors.GRAY}{comment_part}{Colors.RESET}"

        return ''.join(colored_parts) + comment_part
    except ValueError as e:
        handle_exception(f"Error coloring command", e)
        return line

def format_results(search_command, results: List[str]) -> List[str]:
    formatted_results = []
    
    i = 0
    while i < len(results):
        line = results[i]
        if '[+]' in line and not re.match(r'\[\+\].*\[\+\]', line.strip()):
            i += 1
            continue
        elif '[*]' in line:
            parts = line.split('[*]')
            if len(parts) < 2 or not parts[1].strip():
                i += 1
                continue
            formatted_results.append("")
            tool_name = parts[1].strip()
            category = search_command.tool_to_category.get(tool_name, "No category")
            
            if search_command.search_mode == "category":
                separator = f"{Colors.INTENSE_RED}{Colors.BOLD}[+] ════════[ {tool_name} ]════════[+]{Colors.RESET}\n"
            else:
                separator = f"{Colors.INTENSE_RED}{Colors.BOLD}[+] ══[ {tool_name} ]══[+]══[{Colors.WHITE} {category} {Colors.INTENSE_RED}]══[+]{Colors.RESET}\n"
            formatted_results.append(separator)
            i += 1
        elif line.strip().startswith('*'):
            formatted_results.append("")
            subtitle = line.strip().lstrip('*').strip()
            formatted_results.append(f"{Colors.INTENSE_RED}{Colors.BOLD}[+] ══[ {subtitle} ]══[+]{Colors.RESET}\n")
            i += 1
        elif '▶' in line:
            formatted_results.append(colorize_command(line))
            block_lines = []
            j = i + 1
            while j < len(results):
                next_line = results[j]
                if next_line.startswith('[*]') or next_line.startswith('[+]') or next_line.strip().startswith('*') or '▶' in next_line:
                    break
                if next_line.strip():
                    block_lines.append(colorize_command(next_line))
                j += 1
            formatted_results.extend(block_lines)
            formatted_results.append("")
            i = j
        else:
            if line.strip():
                formatted_results.append(colorize_command(line))
                formatted_results.append("")
            i += 1
    return formatted_results

def display_results(search_command, results: List[str], title: str):
    clear_screen(search_command)

    print(f"\n{Colors.BLUE}{Colors.BOLD} {title}{Colors.RESET}\n")
    
    if not results:
        print(f"{Colors.RED}[-]{Colors.RESET} No results found.")
    else:
        formatted_results = format_results(search_command, results)
        cleaned_results = []
        last_was_empty = False

        for line in formatted_results:
            if line.strip() == "":
                if not last_was_empty and cleaned_results:
                    cleaned_results.append(line)
                last_was_empty = True
            else:
                if line.startswith('[+]'):
                    cleaned_results.append(f"{Colors.INTENSE_RED}{Colors.BOLD}{line}{Colors.RESET}")
                elif line.startswith('▶'):
                    cleaned_results.append(f"{Colors.GREEN}{line}{Colors.RESET}")
                else:
                    cleaned_results.append(line)
                last_was_empty = False

        for line in cleaned_results:
            print(line)

    print(" ")

def display_in_columns(items: List[str], title: str, item_color: str, items_per_page: int = 20, compact_mode: bool = False, item_type: str = "tools", interactive: bool = True, custom_footer: bool = False):
    total_items = len(items)
    item_type_label = "categories" if item_type == "categories" else "tools"
    
    try:
        term_width = shutil.get_terminal_size().columns
    except Exception:
        term_width = 80

    max_item_length = max(len(strip_ansi_codes(item)) for item in items) + 6 if items else 10  
    icon = "📂" if item_type == "categories" else "🔧"
    
    if compact_mode:
        print(f"{Colors.BLUE}{Colors.BOLD}{title}{Colors.RESET}")
        print(f"{item_color}Total: {total_items} {item_type_label}{Colors.RESET}")
        if not items:
            print(f"{Colors.RED}[-] No {item_type_label} available.{Colors.RESET}")
        else:
            for idx, item in enumerate(items, 1):
                print(f"{item_color}{idx}. {icon} {item}{Colors.RESET}")
        if interactive:
            if custom_footer:
                footer_text = f"Use {Colors.GREEN}q{Colors.RESET} to exit"
                footer_plain = "Use q to exit"
            else:
                footer_text = f"Use {Colors.GREEN}Tab{Colors.RESET} to autocomplete, {Colors.GREEN}Enter{Colors.RESET} to select, {Colors.GREEN}q{Colors.RESET} to exit"
                footer_plain = "Use Tab to autocomplete, Enter to select, q to exit"
            footer_padding = max(0, (term_width - len(footer_plain)) // 2)
            print(" " * footer_padding + footer_text)
    else:
        min_col_width = max_item_length + 4
        max_columns = min(8, total_items) if item_type == "categories" else total_items
        num_columns = min(max_columns, max(1, term_width // min_col_width))
        col_width = max(min_col_width, (term_width - 20) // num_columns)
        rows = (total_items + num_columns - 1) // num_columns

        print(f"{Colors.BLUE}{Colors.BOLD}╓{'─' * (term_width - 2)}╖{Colors.RESET}")
        print(f" {Colors.BOLD}{title.center(term_width - 2)}{Colors.RESET}")
        print(f"{Colors.BLUE}╟{'─' * (term_width - 2)}╢{Colors.RESET}")

        if not items:
            print(f"{Colors.RED}[-] No {item_type_label} available.{Colors.RESET}".center(term_width))
        else:
            matrix = []
            for i in range(rows):
                matrix.append([None] * num_columns)
            
            for idx, item in enumerate(items):
                col = idx // rows
                row = idx % rows
                if row < rows and col < num_columns:
                    matrix[row][col] = (idx + 1, item)

            total_content_width = num_columns * col_width
            left_margin = max(2, (term_width - total_content_width) // 2)
            
            for row_data in matrix:
                row_content = " " * left_margin
                for col_data in row_data:
                    if col_data is not None:
                        item_num, item_text = col_data
                        max_display_length = min(len(strip_ansi_codes(item_text)), col_width - 8)
                        formatted_item = f"{item_color}{item_num}. {icon} {Colors.WHITE}{item_text[:max_display_length]}{'...' if len(item_text) > max_display_length else ''}{Colors.RESET}"
                        visible_length = len(strip_ansi_codes(formatted_item))
                        padding = max(0, col_width - visible_length)
                        row_content += formatted_item + " " * padding
                    else:
                        row_content += " " * col_width
                print(row_content.rstrip())

        print(f"{Colors.BLUE}╟{'─' * (term_width - 2)}╢{Colors.RESET}")
        if interactive:
            if custom_footer:
                footer_text = f"Use {Colors.GREEN}q{Colors.RESET} to exit"
                footer_plain = "Use q to exit"
            else:
                footer_text = f"Use {Colors.GREEN}Tab{Colors.RESET} to autocomplete, {Colors.GREEN}Enter{Colors.RESET} to select, {Colors.GREEN}q{Colors.RESET} to exit"
                footer_plain = "Use Tab to autocomplete, Enter to select, q to exit"
            footer_padding = max(0, (term_width - len(footer_plain)) // 2)
            print(" " * footer_padding + footer_text)
        print(f"{Colors.BLUE}{Colors.BOLD}╙{'─' * (term_width - 2)}╜{Colors.RESET}\n")

def list_categories(search_command, interactive=True, custom_footer=False):
    clear_screen(search_command)
    categories = sorted(search_command.categories.keys())
    display_in_columns(categories, "📂 AVAILABLE CATEGORIES", Colors.ORANGE, item_type="categories", interactive=interactive, custom_footer=custom_footer)

def list_tools(search_command, interactive=True, custom_footer=False):
    clear_screen(search_command)
    tools = sorted([tool for tools in search_command.tools_by_category.values() for tool in tools if tool in search_command.tool_to_file])
    if not tools:
        print(f"{Colors.RED}[-] No valid tools found.{Colors.RESET}")
        return
    display_in_columns(tools, "🔧 AVAILABLE TOOLS", Colors.AQUA, item_type="tools", interactive=interactive, custom_footer=custom_footer)

def display_edit_help(search_command):
    print(f"{Colors.BLUE}[ℹ] {Colors.RESET}Usage: {Colors.GREEN}edit <tool>{Colors.RESET} (example: edit NMAP)")
    print(f"{Colors.BLUE}[ℹ] {Colors.RESET}Shortcut: {Colors.GREEN}Ctrl+E{Colors.RESET} to edit the last searched tool.")
    print(f"{Colors.GREEN}[+] {Colors.RESET}Available tools: {Colors.CYAN}{', '.join(sorted(search_command.tool_to_file.keys()))}{Colors.RESET}\n")

def spinner(msg="Loading...", chars=['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']):
    def spin():
        for char in itertools.cycle(chars):
            if not hasattr(t, 'do_run') or not t.do_run:
                break
            sys.stdout.write(f'\r{msg} {char}')
            sys.stdout.flush()
            time.sleep(0.1)
    t = threading.Thread(target=spin)
    t.do_run = True
    t.start()
    return t