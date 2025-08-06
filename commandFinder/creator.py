import os
import shutil
import sys
import subprocess
from prompt_toolkit.application import get_app
from utils import sanitize_name, normalize_text
from config import Config, Colors
from services import sanitize_file_path, get_safe_editor
from ui import clear_screen, list_categories, list_tools, create_add_tool_prompt, create_add_category_prompt, print_header, create_delete_category_prompt, create_delete_tool_prompt

class Creator:
    def __init__(self, search_command):
        self.search_command = search_command
        self.root_dir = search_command.root_dir

    def _create_category(self):
        clear_screen(self.search_command)
        list_categories(self.search_command, custom_footer=True)
        prompt_session = create_add_category_prompt(self.search_command)
        try:
            category_name = prompt_session.prompt().strip()
        except (KeyboardInterrupt, EOFError):
            clear_screen(self.search_command)
            print_header(self.search_command)
            return
        if category_name.lower() == 'q':
            clear_screen(self.search_command)
            print_header(self.search_command)
            return
        try:
            category_name = sanitize_name(category_name)
            category_norm = normalize_text(category_name)
            if category_norm in [normalize_text(c).lower() for c in self.search_command.categories.keys()]:
                print(f"{Colors.RED}[✘] The category '{category_name}' already exists.{Colors.RESET}")
                clear_screen(self.search_command)
                print_header(self.search_command)
                return
            category_path = os.path.normpath(os.path.join(self.root_dir, category_name))
            os.makedirs(category_path, mode=Config.DEFAULT_PERMS, exist_ok=False)
            os.chown(category_path, os.getuid(), os.getgid())
            print(f"{Colors.GREEN}[✔] Category '{category_name}' created successfully.{Colors.RESET}")
            self._refresh_tools()
            clear_screen(self.search_command)
            print_header(self.search_command)
        except (ValueError, OSError, PermissionError) as e:
            print(f"{Colors.RED}[-] Error: {e}{Colors.RESET}")
            clear_screen(self.search_command)
            print_header(self.search_command)

    def _create_tool(self):
        clear_screen(self.search_command)
        if not self.search_command.categories:
            print(f"{Colors.RED}[-] No categories. Create one first with 'add categories'.{Colors.RESET}")
            clear_screen(self.search_command)
            print_header(self.search_command)
            return
        list_categories(self.search_command, custom_footer=True)
        prompt_session = create_add_tool_prompt(self.search_command)
        try:
            category_choice = prompt_session.prompt().strip()
        except (KeyboardInterrupt, EOFError):
            clear_screen(self.search_command)
            print_header(self.search_command)
            return
        if category_choice.lower() == 'q':
            clear_screen(self.search_command)
            print_header(self.search_command)
            return
        
        if not category_choice:
            print(f"{Colors.RED}[-] You must select a category.{Colors.RESET}")
            clear_screen(self.search_command)
            print_header(self.search_command)
            return
            
        categories = sorted(self.search_command.categories.keys())
        category = None
        
        if category_choice.isdigit():
            idx = int(category_choice) - 1
            category = categories[idx] if 0 <= idx < len(categories) else None
        else:
            category_norm = normalize_text(category_choice)
            if category_norm is not None:
                category_norm = category_norm.lower()
                category = next((c for c in categories if normalize_text(c) and normalize_text(c).lower() == category_norm), None)
            else:
                category = next((c for c in categories if c.lower() == category_choice.lower()), None)
        
        if not category:
            print(f"{Colors.RED}[-] {Colors.RESET}Invalid category: '{category_choice}'.")
            print(f"{Colors.BLUE}[ℹ] {Colors.RESET}Available categories: {', '.join(categories)}")
            clear_screen(self.search_command)
            print_header(self.search_command)
            return
            
        tool_name = input(f"{Colors.BLUE}[ℹ] {Colors.RESET}Enter the name of the new tool: ").strip()
        
        if not tool_name:
            print(f"{Colors.RED}[-] {Colors.RESET}The tool name cannot be empty.")
            clear_screen(self.search_command)
            print_header(self.search_command)
            return
            
        try:
            tool_name = sanitize_name(tool_name)
            tool_norm = normalize_text(tool_name)
            
            if tool_norm is not None:
                tool_norm = tool_norm.lower()
                existing_tools = [normalize_text(t).lower() for t in self.search_command.tool_to_file.keys() if normalize_text(t) is not None]
                if tool_norm in existing_tools:
                    raise ValueError(f"The tool {Colors.BLUE}{tool_name}{Colors.RESET} already exists (ignoring case).")
            else:
                if tool_name.lower() in [t.lower() for t in self.search_command.tool_to_file.keys()]:
                    raise ValueError(f"The tool '{tool_name}' already exists.")
            
            confirm = input(f"Create '{tool_name}' in '{category}'? (y/n): ").strip().lower()
            if confirm != 'y':
                clear_screen(self.search_command)
                print_header(self.search_command)
                return
            tool_path = os.path.normpath(os.path.join(self.root_dir, category, f"{tool_name}.txt"))
            sanitize_file_path(tool_path, self.root_dir)
            default_content = """
# Example of how tools should be organized for correct display.
# Important: Descriptions must start with the symbol '▶' as shown below.

▶ Search specific command:  
   searchCommand nmap

▶ Show general help:  
   searchCommand -h

▶ List available categories:  
   searchCommand --list-categories

▶ List all tools:  
   searchCommand --list-tools
   """
            with open(tool_path, 'w', encoding='utf-8') as f:
                f.write(default_content)
            os.chmod(tool_path, Config.DEFAULT_PERMS)
            os.chown(tool_path, os.getuid(), os.getgid())
            print(f"{Colors.GREEN}[✔] Tool '{tool_name}' created in '{category}'.{Colors.RESET}")
            self._refresh_tools()
            clear_screen(self.search_command)
            print_header(self.search_command)
        except (ValueError, OSError, PermissionError) as e:
            print(f"{Colors.RED}[-] Error: {e}{Colors.RESET}")
            clear_screen(self.search_command)
            print_header(self.search_command)

    def _edit_tool(self, tool_choice: str):
        clear_screen(self.search_command)
        if not tool_choice:
            if self.search_command.last_query and self.search_command.last_query in self.search_command.tool_to_file:
                tool_choice = self.search_command.last_query
            else:
                print(f"{Colors.RED}[-] No recent tool. Use 'edit <tool>'.{Colors.RESET}")
                self.search_command._display_edit_help()
                input("Press Enter to continue...")
                clear_screen(self.search_command)
                print_header(self.search_command)
                return
        list_tools(self.search_command)
        tools = sorted(self.search_command.tool_to_file.keys())
        if tool_choice.isdigit():
            idx = int(tool_choice) - 1
            tool = tools[idx] if 0 <= idx < len(tools) else None
        else:
            tool_norm = normalize_text(tool_choice)
            if tool_norm is not None:
                tool_norm = tool_norm.lower()
                tool = next((t for t in tools if normalize_text(t) and normalize_text(t).lower() == tool_norm), None)
            else:
                tool = next((t for t in tools if t.lower() == tool_choice.lower()), None)
        
        if not tool:
            print(f"{Colors.RED}[-] Invalid tool.{Colors.RESET}")
            input("Press Enter to continue...")
            clear_screen(self.search_command)
            print_header(self.search_command)
            return
        editor_path = get_safe_editor()
        if not editor_path:
            print(f"{Colors.RED}[-] No compatible editor found (nano, vim, vi).{Colors.RESET}")
            input("Press Enter to continue...")
            clear_screen(self.search_command)
            print_header(self.search_command)
            return
        try:
            file_path = sanitize_file_path(self.search_command.tool_to_file[tool], self.search_command.root_dir)
            subprocess.run([editor_path, file_path], check=True)
            editor_name = os.path.basename(editor_path)
            print(f"\n{Colors.GREEN}[✔] Opening '{tool}' with {editor_name}. Use 'refresh' to reload changes.{Colors.RESET}")
            self._refresh_tools()
            clear_screen(self.search_command)
            print_header(self.search_command)
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError) as e:
            print(f"{Colors.RED}[-] Error opening editor: {e}{Colors.RESET}")
            clear_screen(self.search_command)
            print_header(self.search_command)

    def _delete_category(self, category_choice: str):
        clear_screen(self.search_command)
        if not self.search_command.categories:
            print(f"{Colors.RED}[-] No categories to delete.{Colors.RESET}")
            clear_screen(self.search_command)
            print_header(self.search_command)
            return

        if not category_choice:  
            print(f"{Colors.BLUE}[ℹ] {Colors.RESET}No category specified. Select one to delete (or q to exit).")
            list_categories(self.search_command, custom_footer=True)
            prompt_session = create_delete_category_prompt(self.search_command)
            try:
                category_choice = prompt_session.prompt().strip()
            except (KeyboardInterrupt, EOFError):
                clear_screen(self.search_command)
                print_header(self.search_command)
                return
            if category_choice.lower() == 'q':
                clear_screen(self.search_command)
                print_header(self.search_command)
                return

        category = None
        categories = sorted(self.search_command.categories.keys())

        if category_choice.isdigit():
            idx = int(category_choice) - 1
            category = categories[idx] if 0 <= idx < len(categories) else None
        else:
            category_norm = normalize_text(category_choice)
            if category_norm is not None:
                category_norm = category_norm.lower()
                for c in categories:
                    normalized_c = normalize_text(c)
                    if normalized_c and normalized_c.lower() == category_norm:
                        category = c
                        break
                    elif c.lower() == category_choice.lower():
                        category = c
                        break
            else:
                category = next((c for c in categories if c.lower() == category_choice.lower()), None)

        if not category:
            print(f"{Colors.RED}[-] Invalid category: '{category_choice}'.{Colors.RESET}")
            clear_screen(self.search_command)
            print_header(self.search_command)
            return

        confirm = input(f"Delete category '{category}' and all its tools? (y/n): ").strip().lower()
        if confirm != 'y':
            clear_screen(self.search_command)
            print_header(self.search_command)
            return
        try:
            category_path = os.path.normpath(os.path.join(self.root_dir, category))
            sanitize_file_path(category_path, self.root_dir)
            if os.path.exists(category_path):
                shutil.rmtree(category_path)
                print(f"{Colors.GREEN}[✔] Category '{category}' deleted.{Colors.RESET}")
                self._refresh_tools()
                clear_screen(self.search_command)
                print_header(self.search_command)
            else:
                print(f"{Colors.RED}[-] The category '{category}' does not exist in the file system.{Colors.RESET}")
                clear_screen(self.search_command)
                print_header(self.search_command)
        except (OSError, PermissionError, ValueError) as e:
            print(f"{Colors.RED}[-] Error deleting category: {e}{Colors.RESET}")
            clear_screen(self.search_command)
            print_header(self.search_command)

    def _delete_tool(self, tool_choice: str):
        clear_screen(self.search_command)
        if not self.search_command.tool_to_file:
            print(f"{Colors.RED}[-] No tools to delete.{Colors.RESET}")
            clear_screen(self.search_command)
            print_header(self.search_command)
            return

        if not tool_choice:  
            print(f"{Colors.BLUE}[ℹ] {Colors.RESET}No tool specified. Select one to delete (or q to exit).")
            list_tools(self.search_command, custom_footer=True)
            prompt_session = create_delete_tool_prompt(self.search_command)
            try:
                tool_choice = prompt_session.prompt().strip()
            except (KeyboardInterrupt, EOFError):
                clear_screen(self.search_command)
                print_header(self.search_command)
                return
            if tool_choice.lower() == 'q':
                clear_screen(self.search_command)
                print_header(self.search_command)
                return

        tool = None
        tools = sorted(self.search_command.tool_to_file.keys())
        if tool_choice.isdigit():
            idx = int(tool_choice) - 1
            tool = tools[idx] if 0 <= idx < len(tools) else None
        else:
            tool_norm = normalize_text(tool_choice)
            if tool_norm is not None:
                tool_norm = tool_norm.lower()
                tool = next((t for t in tools if normalize_text(t) and normalize_text(t).lower() == tool_norm), None)
            else:
                tool = next((t for t in tools if t.lower() == tool_choice.lower()), None)

        if not tool:
            print(f"{Colors.RED}[-] Invalid tool: '{tool_choice}'.{Colors.RESET}")
            clear_screen(self.search_command)
            print_header(self.search_command)
            return

        confirm = input(f"Delete tool '{tool}'? (y/n): ").strip().lower()
        if confirm != 'y':
            clear_screen(self.search_command)
            print_header(self.search_command)
            return
        try:
            tool_path = sanitize_file_path(self.search_command.tool_to_file[tool], self.search_command.root_dir)
            if os.path.exists(tool_path):
                os.remove(tool_path)
                print(f"{Colors.GREEN}[✔] Tool '{tool}' deleted.{Colors.RESET}")
                self._refresh_tools()
                clear_screen(self.search_command)
                print_header(self.search_command)
            else:
                print(f"{Colors.RED}[-] The tool '{tool}' does not exist.{Colors.RESET}")
                clear_screen(self.search_command)
                print_header(self.search_command)
        except (OSError, PermissionError, ValueError) as e:
            print(f"{Colors.RED}[-] Error deleting tool: {e}{Colors.RESET}")
            clear_screen(self.search_command)
            print_header(self.search_command)

    def _refresh_tools(self):
        self.search_command._load_tools()
        self.search_command._init_prompt_session()