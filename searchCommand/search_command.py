from prompt_toolkit.application import get_app
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
import os
import pwd
import sys
import signal
from config import Config, Colors, __version__
from gtfsearch import GTFSearch
from completer import EnhancedCompleter
from utils import normalize_text, handle_exception, replace_variables, normalize_url, strip_ansi_codes
from services import create_directory, check_directory_permissions, read_tool_file, sanitize_file_path, get_safe_editor, load_tools, parse_directory_structure
from ui import init_prompt_session, clear_screen, show_help, print_header, colorize_command, format_results, display_results, display_in_columns, list_categories, list_tools, display_edit_help, spinner
from scanner import search_generic, search_by_category, search_by_tool
from handlers import handle_internal_command, handle_resize
from fuzzywuzzy import process

if os.name == 'nt':
    print(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} This program is designed for Linux/macOS. On Windows, use WSL for better compatibility.")

class SearchCommand:
    def __init__(self, interactive=True):
        self.interactive = interactive
        user_home = os.path.expanduser('~')
        if os.geteuid() == 0 and 'SUDO_USER' in os.environ:
            sudo_user = os.environ.get('SUDO_USER')
            try:
                pwd.getpwnam(sudo_user)
                user_home = os.path.expanduser(f"~{sudo_user}")
            except KeyError:
                print(f"{Colors.RED}[-]{Colors.RESET} Invalid SUDO_USER. Using current user directory.")
        
        self.root_dir = os.path.join(user_home, Config.ROOT_DIR_NAME)
        self.ip_value = None
        self.url_value = None
        self.recent_ips = []
        self.recent_urls = []
        self.last_command_success = True
        self.last_results_count = 0
        self.current_category = ""
        self.search_mode = ""
        self.last_query = ""
        
        self.tools_by_category = {}
        self.categories = {}
        self.tool_to_category = {}
        self.tool_to_file = {}
        self.prompt_session = None
        self.gtf_search = GTFSearch(from_search_command=True)

        try:
            create_directory(self.root_dir)
            check_directory_permissions(self.root_dir)
        except PermissionError as e:
            handle_exception("Directory permission error", e, True)

        self._load_tools()
        self._init_prompt_session()

    def _load_tools(self, interactive=None):
        load_tools(self, interactive)

    def _init_prompt_session(self):
        init_prompt_session(self)

    def _clear_screen(self):
        clear_screen(self)

    def show_help(self):
        show_help(self)

    def print_header(self):
        print_header(self)

    def _display_results(self, results: List[str], title: str):
        display_results(self, results, title)

    def _format_results(self, results: List[str]) -> List[str]:
        return format_results(self, results)

    def _colorize_command(self, line: str) -> str:
        return colorize_command(line)

    def _display_in_columns(self, items: List[str], title: str, item_color: str, items_per_page: int = 20, compact_mode: bool = False, item_type: str = "tools", interactive: bool = True):
        display_in_columns(items, title, item_color, items_per_page, compact_mode, item_type, interactive)

    def _list_categories(self, interactive=True):
        list_categories(self, interactive)

    def _list_tools(self, interactive=True):
        list_tools(self, interactive)

    def _display_edit_help(self):
        display_edit_help(self)

    def _search_generic(self, query: str, search_type: str) -> List[str]:
        return search_generic(self, query, search_type)

    def search_by_category(self, query: str) -> List[str]:
        return search_by_category(self, query)

    def search_by_tool(self, query: str) -> List[str]:
        return search_by_tool(self, query)

    def _handle_internal_command(self, query: str) -> bool:
        return handle_internal_command(self, query)

    def _handle_resize(self, signum, frame):
        handle_resize(self, signum, frame)

    def interactive_menu(self):
        signal.signal(signal.SIGWINCH, self._handle_resize)
        
        try:
            clear_screen(self)
            print_header(self)
            
            while True:
                try:
                    query = self.prompt_session.prompt().strip()

                    if query.lower() in ['exit', 'q']:
                        print(f"\n\t\t\t{Colors.RED}{Colors.BOLD}H4PPY H4CK1NG{Colors.RESET}")
                        break
                    
                    if not query:
                        print(f"{Colors.BLUE}[ℹ]{Colors.RESET} Enter a command, tool or {Colors.GREEN}help{Colors.RESET} for help.\n")
                        self.last_command_success = True
                        continue
                    
                    if self._handle_internal_command(query):
                        self.last_command_success = True
                        self.last_query = ""
                        continue
                    
                    query_normalized = normalize_text(query)
                    if query_normalized is None:
                        print(f"{Colors.RED}[✘]{Colors.RESET} Invalid query.\n")
                        self.last_command_success = False
                        self.last_query = ""
                        continue

                    category_results = self.search_by_category(query)
                    if category_results:
                        self._display_results(
                            category_results, 
                            f"{Colors.BLUE}{Colors.BOLD}▌ {Colors.WHITE}{Colors.BOLD}Category: {Colors.RESET}{Colors.GRAY}{query.upper()}{Colors.RESET}\n"
                        )
                        self.last_command_success = True
                        continue

                    tool_results = self.search_by_tool(query)
                    if tool_results:
                        self._display_results(
                            tool_results, 
                            f"{Colors.ORANGE}{Colors.BOLD}▌ {Colors.WHITE}{Colors.BOLD}Tool: {Colors.RESET}{Colors.GRAY}{query.upper()}{Colors.RESET}\n"
                        )
                        self.last_command_success = True
                        continue

                    all_options = (
                        list(self.categories.keys()) + 
                        [tool for tools in self.tools_by_category.values() for tool in tools]
                    )
                    all_options_normalized = [
                        normalize_text(opt) for opt in all_options 
                        if normalize_text(opt)
                    ]
                    
                    suggestions = process.extract(
                        query_normalized, 
                        all_options_normalized, 
                        limit=3, 
                        scorer=process.fuzz.partial_ratio
                    )
                    
                    valid_suggestions = [
                        all_options[all_options_normalized.index(s[0])] 
                        for s in suggestions if s[1] >= 80
                    ]
                    
                    print(f"{Colors.RED}{Colors.BOLD}[✘] {Colors.RESET}No results for: {Colors.WHITE}{query}")
                    
                    if valid_suggestions:
                        print(f"{Colors.LIGHT_BLUE}💡 Maybe you meant?{Colors.RESET}")
                        for suggestion in valid_suggestions:
                            print(f"   {Colors.GREEN}▶{Colors.RESET} {Colors.CYAN}{suggestion}{Colors.RESET}")
                    else:
                        print(f"{Colors.ORANGE}[!]{Colors.RESET} No suggestions available.")
                    
                    print()
                    self.last_command_success = False
                    self.last_query = ""

                except KeyboardInterrupt:
                    print(f"\n{Colors.RESET}", end="")
                    print(f"\n\t\t\t{Colors.RED}{Colors.BOLD}H4PPY H4CK1NG{Colors.RESET}")
                    sys.exit(0)
                    
        finally:
            signal.signal(signal.SIGWINCH, signal.SIG_DFL)
            print(f"{Colors.RESET}", end="")

    def run_query(self, query: str):
        query = query.strip()
        if not query:
            print(f"{Colors.RED}[-]{Colors.RESET} Error: No valid query provided.")
            sys.exit(1)

        if not self.tools_by_category:
            self._load_tools(interactive=False)

        if self._handle_internal_command(query):
            return

        query_normalized = normalize_text(query)
        if query_normalized is None:
            print(f"{Colors.RED}[✘]{Colors.RESET} Invalid query.")
            sys.exit(1)

        category_results = self.search_by_category(query)
        if category_results:
            self._display_results(
                category_results,
                f"{Colors.BLUE}{Colors.BOLD}▌ {Colors.WHITE}{Colors.BOLD}Category: {Colors.RESET}{Colors.GRAY}{query.upper()}{Colors.RESET}\n"
            )
            return

        tool_results = self.search_by_tool(query)
        if tool_results:
            self._display_results(
                tool_results,
                f"{Colors.ORANGE}{Colors.BOLD}▌ {Colors.WHITE}{Colors.BOLD}Tool: {Colors.RESET}{Colors.GRAY}{query.upper()}{Colors.RESET}\n"
            )
            return

        all_options = (
            list(self.categories.keys()) +
            [tool for tools in self.tools_by_category.values() for tool in tools]
        )
        all_options_normalized = [
            normalize_text(opt) for opt in all_options if normalize_text(opt)
        ]

        suggestions = process.extract(
            query_normalized,
            all_options_normalized,
            limit=3,
            scorer=process.fuzz.partial_ratio
        )

        valid_suggestions = [
            all_options[all_options_normalized.index(s[0])]
            for s in suggestions if s[1] >= 80
        ]

        print(f"{Colors.RED}{Colors.BOLD}[✘] {Colors.RESET}No results for: {Colors.WHITE}{query}")
        if valid_suggestions:
            print(f"{Colors.LIGHT_BLUE}💡 Maybe you meant?{Colors.RESET}")
            for suggestion in valid_suggestions:
                print(f"   {Colors.GREEN}▶{Colors.RESET} {Colors.CYAN}{suggestion}{Colors.RESET}")
        else:
            print(f"{Colors.ORANGE}[!]{Colors.RESET} No suggestions available.")
        print()
        sys.exit(1)