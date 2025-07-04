#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
import sys
import pwd
from rich import box
from pathlib import Path
from rich.console import Console
from rich.table import Table
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import Completer, Completion
from typing import List, Dict, Iterable, Optional
from rich.panel import Panel
from rich.text import Text

class SecurityValidator:
    DANGEROUS_PATTERNS = [
        r'[;&|`$(){}[\]<>]',
        r'\.\./',
        r'\\x[0-9a-fA-F]{2}',
        r'eval\s*\(',
        r'exec\s*\(',
        r'import\s+',
        r'__[a-zA-Z_]+__',
        r'subprocess',
        r'os\.',
        r'sys\.',
        r'open\s*\(',
        r'file\s*\(',
        r'input\s*\(',
        r'raw_input\s*\(',
    ]
    
    MAX_QUERY_LENGTH = 100
    MAX_PATH_LENGTH = 255
    
    @staticmethod
    def sanitize_input(user_input: str) -> str:
        if not isinstance(user_input, str):
            return ""
        
        sanitized = ''.join(char for char in user_input if char.isprintable() or char == '\n')
        sanitized = sanitized[:SecurityValidator.MAX_QUERY_LENGTH]
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        return sanitized
    
    @staticmethod
    def validate_query(query: str) -> tuple[bool, str]:
        if not query:
            return False, "Consulta vacía"
        
        if len(query) > SecurityValidator.MAX_QUERY_LENGTH:
            return False, f"Consulta demasiado larga (máximo {SecurityValidator.MAX_QUERY_LENGTH} caracteres)"
        
        for pattern in SecurityValidator.DANGEROUS_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return False, f"Patrón no permitido detectado: {pattern}"
        
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', query):
            return False, "Solo se permiten caracteres alfanuméricos, espacios, guiones y underscores"
        
        return True, "Válido"
    
    @staticmethod
    def validate_file_path(file_path: str) -> tuple[bool, str]:
        try:
            path = Path(file_path).resolve()
            
            allowed_dirs = []
            
            allowed_dirs.append(Path.home().resolve())
            
            if 'SUDO_USER' in os.environ:
                try:
                    original_user = os.environ['SUDO_USER']
                    user_info = pwd.getpwnam(original_user)
                    allowed_dirs.append(Path(user_info.pw_dir).resolve())
                except (KeyError, ImportError):
                    pass
            
            path_allowed = False
            for allowed_dir in allowed_dirs:
                try:
                    if str(path).startswith(str(allowed_dir)):
                        path_allowed = True
                        break
                except (OSError, ValueError):
                    continue
            
            if not path_allowed:
                return False, "Acceso denegado: archivo fuera de directorios permitidos"
            
            if len(str(path)) > SecurityValidator.MAX_PATH_LENGTH:
                return False, f"Ruta demasiado larga (máximo {SecurityValidator.MAX_PATH_LENGTH} caracteres)"
            
            if '..' in str(path):
                return False, "Path traversal detectado"
            
            return True, "Válido"
            
        except (OSError, ValueError) as e:
            return False, f"Ruta inválida: {str(e)}"

class SecureFileHandler:
    @staticmethod
    def safe_read_json(file_path: str) -> tuple[bool, any, str]:
        is_valid, error_msg = SecurityValidator.validate_file_path(file_path)
        if not is_valid:
            return False, None, error_msg
        
        try:
            if not os.path.exists(file_path):
                return False, None, f"Archivo no encontrado: {file_path}"
            
            if not os.access(file_path, os.R_OK):
                return False, None, f"Sin permisos de lectura: {file_path}"
            
            file_size = os.path.getsize(file_path)
            if file_size > 50 * 1024 * 1024:
                return False, None, "Archivo demasiado grande"
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return True, data, "Éxito"
            
        except json.JSONDecodeError as e:
            return False, None, f"Error de formato JSON: {str(e)}"
        except PermissionError:
            return False, None, "Sin permisos para acceder al archivo"
        except UnicodeDecodeError:
            return False, None, "Error de codificación del archivo"
        except Exception as e:
            return False, None, f"Error inesperado: {str(e)}"

class Colors:
    RESET = "\033[0m"
    RED = "\033[38;2;212;25;25m"
    LIGHT_BLUE = "\033[38;2;73;174;230m"
    GREEN = "\033[32m"
    WHITE = "\033[38;2;255;255;255m"
    GRAY = "\033[38;2;128;128;128m"
    YELLOW = "\033[38;2;255;255;0m"
    BLUE = "\033[34m"
    BOLD = "\033[1m"
    ORANGE = "\033[38;2;254;164;76m"

class SecureCustomCompleter(Completer):
    def __init__(self, command_pairs: List[tuple], binaries: List[str]):
        self.command_pairs = command_pairs
        self.binaries = [binary for binary in binaries if binary]
        self.all_completions = [f"[{alias}] {cmd}" for alias, cmd in command_pairs] + self.binaries

    def get_completions(self, document, complete_event) -> Iterable[Completion]:
        text = document.text_before_cursor.lower()
        
        completion_count = 0
        max_completions = 50
        
        for alias, cmd in self.command_pairs:
            if completion_count >= max_completions:
                break
            
            display_text = f"[{alias}] {cmd}"
            if text in alias.lower() or text in cmd.lower() or text in display_text.lower():
                yield Completion(
                    display_text,
                    start_position=-len(document.text_before_cursor),
                    style="bg:#1a1a1a #FFFFFF"
                )
                completion_count += 1
        
        for binary in self.binaries:
            if completion_count >= max_completions:
                break
            
            if text in binary.lower():
                yield Completion(
                    binary,
                    start_position=-len(document.text_before_cursor),
                    style="bg:#1a1a1a #FEA44C"
                )
                completion_count += 1

class GTFSearch:
    def __init__(self, root_dir: str):
        self.console = Console()
        
        root_dir = SecurityValidator.sanitize_input(root_dir)
        
        self.original_home = self._get_original_user_home()
        self.gtfobins_file = str(self.original_home / '.data' / 'gtfobins.json')
        
        self._debug_paths()
        
        self.gtfobins_data = self._load_gtfobins_secure()
        self.last_command_success = True
        
        self.prompt_style = Style.from_dict({
            'prompt.parens': '#5EBDAB',
            'prompt.name': '#fe013a bold',
            'prompt.dash': '#5EBDAB',
            'prompt.brackets': '#5EBDAB',
            'prompt.success': '#5EBDAB',
            'prompt.error': '#FF0000',
            'prompt.white': '#FFFFFF',
            'input': '#F5F5F5',
            'completion-menu': 'bg:#1a1a1a #474747',
            'completion-menu.completion': 'bg:#1a1a1a #FEA44C',
            'completion-menu.completion.current': 'bg:#347cf1 #FFFFFF bold',
            'scrollbar.background': 'bg:#1a1a1a',
            'scrollbar.button': 'bg:#474747',
        })
        
        self.prompt_session = self._init_secure_prompt_session()

    def _get_original_user_home(self) -> Path:
        methods_to_try = [
            lambda: os.environ.get('SUDO_USER'),
            lambda: os.environ.get('LOGNAME'),
            lambda: os.environ.get('USER') if os.environ.get('USER') != 'root' else None,
        ]
        
        for method in methods_to_try:
            try:
                original_user = method()
                if original_user and original_user != 'root':
                    user_info = pwd.getpwnam(original_user)
                    user_home = Path(user_info.pw_dir)
                    
                    if user_home.exists():
                        print(f"{Colors.GREEN}[✔]{Colors.RESET} Usando directorio del usuario original: {Colors.BLUE}{original_user}{Colors.RESET} -> {user_home}")
                        return user_home
                    else:
                        print(f"{Colors.YELLOW}[!]{Colors.RESET} Directorio home del usuario {original_user} no existe: {user_home}")
                        
            except (KeyError, OSError, AttributeError):
                continue
        
        current_home = Path.home()
        print(f"{Colors.YELLOW}[!]{Colors.RESET} No se pudo determinar el usuario original, usando directorio actual: {current_home}")
        return current_home

    def _debug_paths(self):
        print(f"{Colors.BLUE}[DEBUG]{Colors.RESET} Información de rutas:")
        print(f"  - Usuario actual: {Colors.GREEN}{os.getenv('USER', 'desconocido')}{Colors.RESET}")
        print(f"  - SUDO_USER: {Colors.GREEN}{os.getenv('SUDO_USER', 'no definido')}{Colors.RESET}")
        print(f"  - UID actual: {Colors.GREEN}{os.getuid()}{Colors.RESET}")
        print(f"  - Directorio home detectado: {Colors.GREEN}{self.original_home}{Colors.RESET}")
        print(f"  - Archivo GTFObins: {Colors.GREEN}{self.gtfobins_file}{Colors.RESET}")
        print(f"  - Archivo existe: {Colors.GREEN if os.path.exists(self.gtfobins_file) else Colors.RED}{'Sí' if os.path.exists(self.gtfobins_file) else 'No'}{Colors.RESET}")
        print()

    def _clear_screen_only(self):
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')

    def _clear_screen(self):
        self._clear_screen_only()
        self._show_help()

    def _load_gtfobins_secure(self) -> List[Dict]:
        success, data, error_msg = SecureFileHandler.safe_read_json(self.gtfobins_file)
        
        if not success:
            print(f"{Colors.RED}[-] Error al cargar GTFObins: {error_msg}{Colors.RESET}")
            
            alternative_paths = [
                Path.home() / '.data' / 'gtfobins.json',
                Path('/usr/share/gtfobins/gtfobins.json'),
                Path('./gtfobins.json'),
            ]
            
            for alt_path in alternative_paths:
                if alt_path.exists() and str(alt_path) != self.gtfobins_file:
                    print(f"{Colors.YELLOW}[!]{Colors.RESET} Intentando ruta alternativa: {alt_path}")
                    success, data, error_msg = SecureFileHandler.safe_read_json(str(alt_path))
                    if success:
                        print(f"{Colors.GREEN}[✔]{Colors.RESET} Archivo cargado desde: {alt_path}")
                        break
            
            if not success:
                print(f"{Colors.RED}[-] No se pudo cargar el archivo GTFObins desde ninguna ubicación{Colors.RESET}")
                return []
        
        if not isinstance(data, list):
            print(f"{Colors.RED}[-] Formato de datos inválido{Colors.RESET}")
            return []
        
        validated_data = []
        for item in data:
            if not isinstance(item, dict):
                continue
            
            if 'name' not in item or 'functions' not in item:
                continue
            
            name = str(item.get('name', '')).strip()
            if not name:
                continue
            
            if not re.match(r'^[a-zA-Z0-9\-_.+]+$', name):
                continue
            
            validated_item = {
                'name': name,
                'functions': []
            }
            
            if isinstance(item.get('functions'), list):
                for func in item['functions']:
                    if isinstance(func, dict):
                        validated_func = {}
                        
                        for field in ['function', 'description']:
                            if field in func:
                                value = str(func[field]).strip()
                                validated_func[field] = value
                        
                        if 'examples' in func and isinstance(func['examples'], list):
                            validated_examples = []
                            for example in func['examples']:
                                if isinstance(example, dict):
                                    validated_example = {}
                                    for ex_field in ['code', 'description']:
                                        if ex_field in example:
                                            value = str(example[ex_field]).strip()
                                            validated_example[ex_field] = value
                                    
                                    if validated_example:
                                        validated_examples.append(validated_example)
                            
                            validated_func['examples'] = validated_examples
                        
                        if validated_func:
                            validated_item['functions'].append(validated_func)
            
            if validated_item['functions']:
                validated_data.append(validated_item)
        
        return validated_data

    def _init_secure_prompt_session(self) -> PromptSession:
        kb = KeyBindings()
        
        @kb.add(Keys.ControlC)
        def _(event):
            print(f"\n\n{Colors.ORANGE}[!]{Colors.WHITE} Para salir correctamente, utiliza el comando {Colors.RED}{Colors.BOLD}q{Colors.RESET} o {Colors.RED}{Colors.BOLD}exit{Colors.RESET}.{Colors.RESET}\n")
            event.app.renderer.reset()
            event.app.invalidate()

        @kb.add(Keys.ControlL)
        def _(event):
            self._clear_screen()
            self.last_command_success = True
            event.app.renderer.reset()
            event.app.invalidate()

        @kb.add(Keys.ControlK)
        def _(event):
            self._clear_screen_only()
            self._list_commands()
            self.last_command_success = True
            event.app.renderer.reset()
            event.app.invalidate()

        def get_prompt():
            return [
                ('class:prompt.parens', '('),
                ('class:prompt.name', 'GTFsearch'),
                ('class:prompt.parens', ')'),
                ('class:prompt.dash', '-'),
                ('class:prompt.brackets', '['),
                ('class:prompt.success' if self.last_command_success else 'class:prompt.error', '✔' if self.last_command_success else '✘'),
                ('class:prompt.brackets', ']'),
                ('class:prompt.white', ' > '),
            ]

        command_pairs = [
            ('help', 'h'),
            ('list binaries', 'lt'),
            ('exit', 'q'),
        ]
        
        binaries = sorted({tool.get('name', '') for tool in self.gtfobins_data if tool.get('name')})
        completer = SecureCustomCompleter(command_pairs, binaries)
        
        history_file = str(self.original_home / '.gtfsearch_history')
        
        return PromptSession(
            completer=completer,
            key_bindings=kb,
            style=self.prompt_style,
            message=get_prompt,
            validate_while_typing=False,
            multiline=False,
            erase_when_done=True,
            history=FileHistory(history_file),
            complete_while_typing=True,
            complete_style='multi_column'
        )

    def _show_help(self):
        total_width = 60
        title = " AYUDA - GTFsearch "
        side_width = (total_width - len(title)) // 2
        print(f"{Colors.BLUE}{Colors.BOLD}╓{'─' * side_width}╢{Colors.WHITE}{Colors.BOLD}{title}{Colors.BLUE}╟{'─' * side_width}╖{Colors.RESET}\n")

        print(f"  {Colors.GREEN}{'Comando'.ljust(20)}{Colors.GREEN}{'Alias'.ljust(8)}{Colors.GREEN}{'Descripción'.ljust(32)}{Colors.RESET}")
        print(f"  {'─' * 20}{'─' * 8}{'─' * 32}")
        commands = [
            ("help", "h", "Mostrar este menú de ayuda"),
            ("list binaries", "lb", "Listar binarios"),
            ("exit", "q", "Volver a searchCommand"),
        ]
        for cmd, alias, desc in commands:
            print(f"  {Colors.GREEN}➜ {Colors.RESET}{cmd.ljust(19)}{Colors.GRAY}{alias.ljust(7)}{Colors.WHITE}{desc.ljust(32)}{Colors.RESET}")

        print("")
        print(f"  {Colors.GREEN}{'Atajo'.ljust(20)}{Colors.GREEN}{'Descripción'.ljust(32)}{Colors.RESET}")
        print(f"  {'─' * 20}{'─' * 32}")
        shortcuts = [
            ("Ctrl + L", "Limpiar la pantalla y mostrar ayuda"),
            ("Ctrl + C", "Mostrar mensaje de salida"),
            ("Ctrl + K", "Listar binarios rápidamente"),
        ]
        for shortcut, desc in shortcuts:
            print(f"  {Colors.GREEN}• {Colors.RESET}{shortcut.ljust(18)}{Colors.WHITE}{desc.ljust(32)}{Colors.RESET}")

        print(f"\n{Colors.BLUE}{Colors.BOLD}╙{'─' * (2 * side_width + len(title) + 1)}╜{Colors.RESET}\n")

    def _list_commands(self):
        if not self.gtfobins_data:
            self.console.print("\n[red]No se encontraron resultados[/red]\n")
            return

        self._clear_screen_only()
        self.console.print(f"\n[bold #fe013a]🔰 GTFSearch [/bold #fe013a] [dim bright_white]Security Toolkit[/dim bright_white]")
        total_binaries = len([tool for tool in self.gtfobins_data if 'name' in tool and 'functions' in tool])
        self.console.print(f"[bold bright_blue]Available:[/bold bright_blue] [bright_yellow]{total_binaries}[/bright_yellow] [dim #ffff]binarios disponibles[/dim #ffff]")
        self.console.print()

        table = Table(
            show_header=True,
            header_style="bold white on #23242f",
            border_style="dim #23242f",
            show_lines=True,
            padding=(0, 1),
            expand=False,
            row_styles=["", "on #23242f"],
            box=box.HEAVY
        )

        table.add_column("BINARY", style="#fe013a", no_wrap=False, justify="left", min_width=20)
        table.add_column("AVAILABLE FUNCTIONS", style="#fe013a", no_wrap=False)

        for i, tool in enumerate(sorted(self.gtfobins_data, key=lambda x: x.get('name', ''))):
            if 'name' not in tool or 'functions' not in tool:
                continue

            binary_name = tool['name']
            functions = tool.get('functions', [])
            function_names = sorted(set(
                f.get('function', '') for f in functions if f.get('function')
            ))
            functions_str = ", ".join(function_names) if function_names else "Sin funciones"
            row_style = "bold" if i % 2 == 0 else ""
            table.add_row(binary_name, functions_str, style=row_style)

        self.console.print(table)
        self.console.print()

    def _handle_internal_command(self, query: str) -> Optional[bool]:
        query = query.lower().strip()
        
        if len(query) > 100:
            print(f"{Colors.RED}[-] Comando demasiado largo{Colors.RESET}")
            return None
        
        if query in ['help', 'h']:
            self._clear_screen_only()
            self._show_help()
            return True
        elif query in ['list binaries', 'lt', 'lb']:
            self._clear_screen_only()
            self._list_commands()
            return True
        elif query in ['exit', 'q']:
            print(f"{Colors.GREEN}[✔] Volviendo al modo searchCommand...{Colors.RESET}")
            return False
        
        return None

    def _search_gtfobins_secure(self, query: str) -> List[Dict]:
        query = query.lower().strip()
        
        if len(query) < 2:
            return []

        results = []
        result_count = 0
        max_results = 100
        
        for entry in self.gtfobins_data:
            if result_count >= max_results:
                break
            
            binary = entry.get("name", "").lower()
            if not binary:
                continue
            
            if binary == query:
                for function in entry.get("functions", []):
                    if result_count >= max_results:
                        break
                    
                    function_name = function.get("function", "")
                    for example in function.get("examples", []):
                        if result_count >= max_results:
                            break
                        
                        results.append({
                            "binary": entry.get("name", ""),
                            "function": function_name,
                            "function_desc": function.get("description", ""),
                            "code": example.get("code", ""),
                            "example_desc": example.get("description", "")
                        })
                        result_count += 1
        
        return results

    def _print_separator(self):
        terminal_width = self.console.size.width
        separator_line = "━" * (terminal_width - 4)
        self.console.print(f"\n[dim #23242f]  {separator_line}[/dim #23242f]\n")

    def _format_text_with_wrap(self, text: str, max_line_length: int = 90) -> str:
        if not text:
            return ""
        
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append("")
                continue
            
            if len(line) <= max_line_length:
                formatted_lines.append(line)
            else:
                words = line.split()
                current_line = []
                current_length = 0
                
                for word in words:
                    if current_length + len(word) + 1 <= max_line_length:
                        current_line.append(word)
                        current_length += len(word) + 1
                    else:
                        if current_line:
                            formatted_lines.append(' '.join(current_line))
                        current_line = [word]
                        current_length = len(word)
                
                if current_line:
                    formatted_lines.append(' '.join(current_line))
        
        return '\n'.join(formatted_lines)

    def _display_results(self, results: List[Dict]):
        self._clear_screen_only()
        
        if not results:
            self.console.print(f"\n[red]No se encontraron resultados[/red]\n")
            return
        
        results = results[:50]
        
        unique_binaries = len(set(result["binary"] for result in results))
        self.console.print(f"\n[bold #fe013a]🔰 GTFSearch[/bold #fe013a] [dim bright_white]Security Toolkit[/dim bright_white]")
        stats_line = f"[bright_yellow]{unique_binaries}[/bright_yellow] [dim #ffff]Binario[/dim #ffff] [bright_black]•[/bright_black] [bright_yellow]{len(results)}[/bright_yellow] [dim #ffff]técnicas disponibles[/dim #ffff]"
        self.console.print(f"[bold bright_blue]Found:[/bold bright_blue] {stats_line}")

        results_by_binary = {}
        for result in results:
            binary = result["binary"]
            if binary not in results_by_binary:
                results_by_binary[binary] = []
            results_by_binary[binary].append(result)
        
        for binary_idx, (binary, binary_results) in enumerate(results_by_binary.items()):
            self.console.print(f"\n[bold #fe013a]▌ [/bold #fe013a][bold #ffff]BINARIO BUSCADO:[/bold #ffff] [bold green]{binary}[/bold green]\n")

            functions_by_type = {}
            for result in binary_results:
                func_type = result["function"]
                if func_type not in functions_by_type:
                    functions_by_type[func_type] = []
                functions_by_type[func_type].append(result)
            
            for func_idx, (function, func_results) in enumerate(functions_by_type.items()):
                if func_idx > 0:
                    self._print_separator()
                
                self.console.print()
                self.console.print(f"[bold blue]🔒 {function.upper()}[/bold blue]\n")
                
                if func_results[0].get("function_desc"):
                    self.console.print(f"[bold #05A1F7] ▌ Description:[/bold #05A1F7]")
                    
                    desc_text = func_results[0]["function_desc"]
                    formatted_desc = self._format_text_with_wrap(desc_text)
                    
                    for line in formatted_desc.split('\n'):
                        if line.strip():
                            self.console.print(f"  [white]{line}[/white]")
                        else:
                            self.console.print()
                    
                    self.console.print()
                
                for example_idx, result in enumerate(func_results):
                    if len(func_results) > 1:
                        self.console.print(f"[dim #fe013a]• Ejemplo: {example_idx + 1}[/dim #fe013a]")
                    else:
                        self.console.print(f"[blue]➤ Implementation[/blue]")
                    
                    if result.get("example_desc"):
                        example_desc = self._format_text_with_wrap(result["example_desc"])
                        for line in example_desc.split('\n'):
                            if line.strip():
                                self.console.print(f"  [italic yellow]{line}[/italic yellow]")
                    
                    if code := result.get("code"):
                        code = code.replace('\\n', '\n').strip()
                        
                        if result.get("example_desc"):
                            self.console.print(f"💻 [bold white]Código:[/bold white]")
                        
                        self.console.print()
                        
                        code_text = Text(code, style="#ea382d")
                        code_panel = Panel(
                            code_text,
                            style="on #3a0000",
                            padding=(1, 2, 1, 2),
                            border_style="#3a0000"
                        )
                        
                        self.console.print(code_panel)
                        
                        if example_idx < len(func_results) - 1:
                            self.console.print()

                

        self.console.print()
        # Agregar separador final después de mostrar todos los resultados
        terminal_width = self.console.size.width
        final_separator = "━" * (terminal_width - 4)
        self.console.print(f"[dim #23242f]  {final_separator}[/dim #23242f]")
        self.console.print()

    def run(self):
        self._clear_screen()
        
        while True:
            try:
                query = self.prompt_session.prompt()
                
                if not query or not query.strip():
                    self._clear_screen()
                    self.last_command_success = False
                    print(f"{Colors.LIGHT_BLUE}[ℹ]{Colors.RESET} Ingresa un término de búsqueda o 'exit' para volver.")
                    continue
                
                query_clean = query.strip().lower()
                if query_clean.startswith('['):
                    query_clean = query_clean.split(']')[-1].strip()
                
                if len(query_clean) > 100:
                    self._clear_screen()
                    self.last_command_success = False
                    print(f"{Colors.RED}[-] Búsqueda demasiado larga{Colors.RESET}")
                    continue
                
                command_result = self._handle_internal_command(query_clean)
                if command_result is False:
                    self._clear_screen()
                    self.last_command_success = True
                    print(f"{Colors.GREEN}{Colors.BOLD}[✔]{Colors.RESET} Volviendo al modo searchCommand...")
                    break
                elif command_result is True:
                    self.last_command_success = True
                elif len(query_clean.strip()) < 2:
                    self._clear_screen()
                    self.last_command_success = False
                    print(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} La búsqueda debe tener al menos 2 caracteres.")
                else:
                    results = self._search_gtfobins_secure(query_clean)
                    self._display_results(results)
                    self.last_command_success = bool(results)
                    if not results:
                        self._clear_screen()
                        print(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} No se encontraron resultados para {Colors.GRAY}{query_clean}{Colors.RESET}.\n")
                
            except KeyboardInterrupt:
                print(f"\n{Colors.ORANGE}[!]{Colors.WHITE} Usa 'exit' o 'q' para salir correctamente.{Colors.RESET}")
                continue
            except Exception as e:
                print(f"{Colors.RED}[-] Error inesperado: {str(e)[:100]}{Colors.RESET}")
                self.last_command_success = False
                continue
        
        return "exit_gtfsearch"
