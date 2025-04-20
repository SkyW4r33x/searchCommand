#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
═════════════════════════[searchCommand]════════════════════════════
Autor       : Jordan Cueva Mendoza (aka SkyW4r33x)
Repositorio : https://github.com/SkyW4r33x

Descripción :
Esta herramienta fue creada como un recurso de apoyo tanto para quienes 
se están iniciando en el mundo de la ciberseguridad, como para usuarios 
avanzados que buscan una forma rápida y ordenada de acceder a comandos
útiles espero que sea de su agrado y recuerda siempre...

                        H4PPY H4CK1NG
═══════════════════════════════════════════════════════════════════
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import signal
import difflib
import argparse
import time
import unicodedata
import urllib.parse
from typing import List, Dict, Optional, Tuple
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import ANSI, HTML
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.application import get_app

__version__ = "0.1"

if os.name == 'nt':
    print(f"\033[38;2;212;25;25m⚠️ Este programa solo funciona en sistemas Linux\033[0m")
    sys.exit(1)

class Colors:
    RESET = "\033[0m"
    RED = "\033[38;2;212;25;25m"
    LIGHT_BLUE = "\033[38;2;73;174;230m"
    BLUE = "\033[38;2;54;123;240m"
    ORANGE = "\033[38;2;254;164;76m"
    AQUA = "\033[38;2;71;212;185m"
    WHITE = "\033[38;2;255;255;255m"
    GREEN = "\033[32m"
    BOLD = "\033[1m"
    INTENSE_RED = "\033[38;2;255;0;0m"
    GRAY = "\033[38;2;128;128;128m"

def normalize_text(text: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', text.lower())
        if unicodedata.category(c) != 'Mn'
    )

class SearchCommand:
    def __init__(self, file_path: str = None):
        if os.geteuid() == 0 and 'SUDO_USER' in os.environ:
            user_home = os.path.expanduser(f"~{os.environ['SUDO_USER']}")
        else:
            user_home = os.path.expanduser('~')
        
        self.file_path = file_path if file_path else os.path.join(user_home, 'referencestuff/utilscommon')
        self.ip_value = None  
        self.url_value = None  
        self.recent_ips = []  
        self.recent_urls = []  
        self.last_command_success = True
        self.last_results_count = 0
        self.current_category = ""
        self.last_query = ""
        
        self.tools = []
        self.tools_by_category = {}
        self.categories = {}

        try:
            print(f"{Colors.BLUE}Cargando herramientas desde {self.file_path}...{Colors.RESET}", end="", flush=True)
            self.categories = self._parse_categories_and_content()
            for category, content in self.categories.items():
                category_tools = []
                for line in content:
                    if line.strip().startswith('[*]'):
                        try:
                            tool = line.split('[*]')[1].strip()
                            if tool:
                                category_tools.append(tool)
                        except IndexError:
                            self._handle_exception(f"⚠️ Línea mal formada en categoría {category}", Exception(f"{line}"), False)
                self.tools.extend(category_tools)
                self.tools_by_category[category] = category_tools
            
            print(f"\r{Colors.GREEN}✅ {Colors.WHITE}{Colors.BOLD}{len(self.tools)} herramientas cargadas en {len(self.categories)} categorías.{Colors.RESET}")
        except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
            self._handle_exception("⚠️ Error al leer el archivo", e, True)
        except ValueError as e:
            self._handle_exception("⚠️ Error al parsear el contenido", e, True)
        except IndexError as e:
            self._handle_exception("⚠️ Error al procesar herramientas (formato inválido)", e, True)

        try:
            self.prompt_style = Style.from_dict({
                'prompt.parens': '#5EBDAB',
                'prompt.name': '#367bf0 bold',
                'prompt.dash': '#5EBDAB',
                'prompt.brackets': '#5EBDAB',
                'prompt.success': '#5EBDAB',
                'prompt.failure': '#EC0101',
                'prompt.white': '#FFFFFF',
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
        except ValueError as e:
            self._handle_exception("⚠️ Error al configurar estilos", e, True)
        
        try:
            self.completer = EnhancedCompleter(
                categories=list(self.categories.keys()),
                tools=self.tools,
                tools_by_category=self.tools_by_category,
                recent_ips=self.recent_ips,
                recent_urls=self.recent_urls
            )
        except TypeError as e:
            self._handle_exception("⚠️ Error al inicializar autocompletado", e, True)

    def _handle_exception(self, error_msg: str, e: Exception, exit_on_error: bool = False):
        print(f"{Colors.RED}{Colors.BOLD}{error_msg}: {e}{Colors.RESET}")
        if exit_on_error:
            sys.exit(1)

    def _clear_screen(self):
        try:
            if os.name == 'posix':
                os.system('clear')
            else:
                print(f"{Colors.RED}{Colors.BOLD}⚠️ {Colors.WHITE}{Colors.BOLD}Limpieza de pantalla no soportada en este sistema.{Colors.RESET}")
        except OSError as e:
            print(f"{Colors.RED}{Colors.BOLD}⚠️ {Colors.WHITE}{Colors.BOLD}Error al limpiar pantalla: {e}{Colors.RESET}")

    def _read_file(self) -> List[str]:
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Archivo no encontrado en {self.file_path}")
        if os.path.getsize(self.file_path) == 0:
            raise ValueError(f"El archivo {self.file_path} está vacío")
        
        lines = []
        encodings = ['utf-8', 'iso-8859-1']
        last_error = None
        for encoding in encodings:
            try:
                with open(self.file_path, 'r', encoding=encoding) as file:
                    for line in file:
                        lines.append(line.rstrip('\n'))
                if not any('[+]' in line or '[*]' in line for line in lines):
                    print(f"{Colors.RED}{Colors.BOLD}⚠️ {Colors.WHITE}{Colors.BOLD}El archivo parece no tener un formato válido. Continuando con recuperación...{Colors.RESET}")
                return lines
            except PermissionError as e:
                raise PermissionError(f"No tienes permisos para leer {self.file_path}") from e
            except UnicodeDecodeError as e:
                last_error = e
                continue
        raise UnicodeDecodeError(
            f"No se pudo decodificar {self.file_path} con las codificaciones soportadas. Último error: {last_error}",
            last_error.object, last_error.start, last_error.end, "Codificación desconocida"
        ) if last_error else UnicodeDecodeError("Error desconocido", "", 0, 0, "Sin detalles")

    def _validate_and_parse(self, lines: List[str]) -> Tuple[Dict[str, List[str]], bool]:
        categories = {}
        current_category = None
        current_content = []
        valid_format = True

        category_pattern = r'\[\+\]------------------------------\[ (.*?) \]------------------------------\[\+\]'
        tool_pattern = r'.*\[\*\].*'

        for line in lines:
            category_match = re.match(category_pattern, line.strip())
            if category_match:
                if current_category and current_content:
                    categories[current_category] = current_content
                current_category = category_match.group(1)
                current_content = [line]
            elif current_category:
                current_content.append(line)
            elif line.strip() and not re.match(tool_pattern, line) and not line.strip().startswith('#'):
                valid_format = False

        if current_category and current_content:
            categories[current_category] = current_content

        if not valid_format or not categories:
            print(f"{Colors.RED}{Colors.BOLD}⚠️ {Colors.WHITE}{Colors.BOLD}El archivo {self.file_path} contiene líneas inesperadas.{Colors.RESET}")
            print(f"{Colors.BLUE}ℹ Intentando modo recuperación...{Colors.RESET}")
            categories = self._recover_parse(lines)
            if not categories:
                raise ValueError("Falló la recuperación. Verifica el formato del archivo.")
            print(f"{Colors.GREEN}{Colors.BOLD}✔ {Colors.WHITE}{Colors.BOLD}Recuperación exitosa. Algunas secciones pueden estar incompletas.{Colors.RESET}")

        return categories, valid_format

    def _recover_parse(self, lines: List[str]) -> Dict[str, List[str]]:
        categories = {}
        current_category = "Sin categoría"
        current_content = []

        for line in lines:
            if '[+]' in line or '[*]' in line or '▶' in line:
                if current_content and current_content != [line]:
                    categories[current_category] = current_content
                if '[+]' in line:
                    current_category = line.strip().replace('[+]', '').strip() or "Sin categoría"
                current_content = [line]
            elif line.strip():
                current_content.append(line)

        if current_content:
            categories[current_category] = current_content
        return categories

    def _parse_categories_and_content(self) -> Dict[str, List[str]]:
        lines = self._read_file()
        categories, _ = self._validate_and_parse(lines)
        return categories

    def _normalize_url(self, url: str) -> str:
        """Normaliza una URL eliminando dobles barras y asegurando un formato correcto."""
        # Parsear la URL
        parsed = urllib.parse.urlparse(url)
        # Reconstruir la URL, eliminando dobles barras en el path
        path = re.sub(r'/+', '/', parsed.path.lstrip('/'))
        # Asegurar que la URL tenga un esquema (http por defecto si no se especifica)
        scheme = parsed.scheme if parsed.scheme else 'http'
        # Reconstruir la URL
        normalized = urllib.parse.urlunparse((
            scheme,
            parsed.netloc,
            path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        return normalized

    def _replace_variables(self, command: str) -> str:
        """Reemplaza $IP y $URL en un comando con los valores almacenados, si existen."""
        if '$IP' in command and self.ip_value:
            command = command.replace('$IP', self.ip_value)
        if '$URL' in command and self.url_value:
            # Normalizar la URL antes de reemplazar
            normalized_url = self._normalize_url(self.url_value)
            # Reemplazar $URL y limpiar dobles barras
            command = command.replace('$URL', normalized_url)
            # Limpiar cualquier doble barra resultante
            command = re.sub(r'(https?://[^/]+)//+', r'\1/', command)
        return command

    def _search_generic(self, query: str, search_type: str) -> List[str]:
        try:
            query_normalized = normalize_text(query)
            results = []
            if search_type == "category":
                best_match = None
                for category in self.categories:
                    cat_normalized = normalize_text(category)
                    if cat_normalized == query_normalized:
                        self.current_category = category
                        self.last_query = category
                        self.last_results_count = len(self.categories[category][1:] if len(self.categories[category]) > 1 else self.categories[category])
                        return self.categories[category][1:] if len(self.categories[category]) > 1 else self.categories[category]
                    elif query_normalized in cat_normalized and not best_match:
                        best_match = category
                if best_match:
                    self.current_category = best_match
                    self.last_query = best_match
                    self.last_results_count = len(self.categories[best_match][1:] if len(self.categories[best_match]) > 1 else self.categories[best_match])
                    return self.categories[best_match][1:] if len(self.categories[best_match]) > 1 else self.categories[best_match]
                self.current_category = ""
                self.last_query = ""
                self.last_results_count = 0
                return []
            elif search_type == "tool":
                for category, content in self.categories.items():
                    tool_found = False
                    for i, line in enumerate(content):
                        try:
                            line_normalized = normalize_text(line)
                            if '[*]' in line and query_normalized in line_normalized:
                                tool_found = True
                                results.append(line)
                                self.last_query = line.split('[*]')[1].strip()
                            elif tool_found and '▶' in line:
                                block = [content[i]]
                                for j in range(i + 1, len(content)):
                                    if '[*]' in content[j] or '[+]' in content[j]:
                                        break
                                    if content[j].strip():
                                        block.append(content[j])
                                results.extend(block)
                                break
                            elif '▶' in line and query_normalized in line_normalized:
                                block = [content[i]]
                                for j in range(i + 1, len(content)):
                                    if '[*]' in content[j] or '[+]' in content[j] or '▶' in content[j]:
                                        break
                                    if content[j].strip():
                                        block.append(content[j])
                                results.extend(block)
                                break
                        except IndexError as e:
                            self._handle_exception("⚠️ Formato inválido en línea de herramienta", e)
                            continue
                self.last_results_count = len(results)
                self.current_category = ""
                return results
            return []
        except AttributeError as e:
            self._handle_exception(f"⚠️ Error al buscar por {search_type}", e)
            return []

    def search_by_category(self, query: str) -> List[str]:
        return self._search_generic(query, "category")

    def search_by_tool(self, query: str) -> List[str]:
        return self._search_generic(query, "tool")

    def show_help(self):
        self._clear_screen()
        print(f"{Colors.BLUE}{Colors.BOLD}╔═════════════════════[ MENÚ DE AYUDA ]═════════════════════╗{Colors.RESET}")
        print("")
        print(f"{Colors.BLUE}▣ COMANDOS:{Colors.RESET}")
        print(f"   {Colors.GREEN}>_{Colors.RESET} <comando>            Buscar un comando específico")
        print(f"   {Colors.GREEN}•{Colors.RESET}  help (h)             Mostrar este mensaje de ayuda")
        print(f"   {Colors.GREEN}•{Colors.RESET}  list tools (lt)      Listar todas las herramientas")
        print(f"   {Colors.GREEN}•{Colors.RESET}  list categories (lc) Listar todas las categorías")
        print(f"   {Colors.GREEN}•{Colors.RESET}  setip <IP>           Configurar $IP para comandos")
        print(f"   {Colors.GREEN}•{Colors.RESET}  seturl <URL>         Configurar $URL para comandos")
        print(f"   {Colors.GREEN}•{Colors.RESET}  clear (c)            Limpiar la pantalla")
        print(f"   {Colors.GREEN}•{Colors.RESET}  exit (q)             Salir del programa")
        print("")
        print(f"{Colors.BLUE}▣ ATAJOS DE TECLADO:{Colors.RESET}")
        print(f"   {Colors.GREEN}•{Colors.RESET}  Ctrl + L             Limpiar la pantalla")
        print(f"   {Colors.GREEN}•{Colors.RESET}  Ctrl + T             Listar herramientas rápidamente")
        print(f"   {Colors.GREEN}•{Colors.RESET}  Ctrl + K             Listar categorías rápidamente")
        print(f"   {Colors.GREEN}•{Colors.RESET}  Ctrl + C             Salir inmediatamente")
        print("")
        print(f"{Colors.BLUE}{Colors.BOLD}╚═══════════════════════════════════════════════════════════╝{Colors.RESET}")
        print()

    def print_header(self):
        self._clear_screen()
        banner = f'''
{Colors.BLUE}{Colors.BOLD}╔══════════════════[ searchCommand v.{__version__} ]══════════════════╗{Colors.RESET}

    {Colors.ORANGE}{Colors.BOLD}#{Colors.RESET} Categorías Disponibles  : {len(self.categories)}
    {Colors.ORANGE}{Colors.BOLD}#{Colors.RESET} Creado por              : Jordan (SkyW4r33x)
    {Colors.ORANGE}{Colors.BOLD}#{Colors.RESET} Repositorio             : https://github.com/SkyW4r33x

    {Colors.BLUE}{Colors.BOLD}[{Colors.RESET}{Colors.BOLD}{Colors.GREEN}~{Colors.RESET}{Colors.BOLD}{Colors.BLUE}]{Colors.RESET} Escribe {Colors.BLUE}{Colors.BOLD}help{Colors.RESET} para ver los comandos.
    {Colors.BLUE}{Colors.BOLD}[{Colors.RESET}{Colors.BOLD}{Colors.GREEN}~{Colors.RESET}{Colors.BOLD}{Colors.BLUE}]{Colors.RESET} Usa {Colors.BLUE}{Colors.BOLD}Tab{Colors.RESET} para autocompletar.
            
{Colors.BLUE}{Colors.BOLD}╚═══════════════════════════════════════════════════════════╝{Colors.RESET}\n'''
        print(banner)

    def _colorize_command(self, line: str) -> str:
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
                    parts[i] = part.replace('▶', f"{Colors.RED}▶{Colors.RESET}")

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
            self._handle_exception("⚠️ Error al colorear comando", e)
            return line

    def _format_results(self, results: List[str]) -> List[str]:
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
                formatted_results.append(f"{Colors.INTENSE_RED}{Colors.BOLD}[+] ══════════[ {tool_name} ]══════════ [+]{Colors.RESET}")
                i += 1
            elif line.strip().startswith('*'):
                formatted_results.append("")  
                subtitle = line.strip().lstrip('*').strip()
                formatted_results.append(f"{Colors.INTENSE_RED}{Colors.BOLD}[+] ══════════[ {subtitle} ]══════════ [+]{Colors.RESET}")
                i += 1
            elif '▶' in line:
                modified_line = self._replace_variables(line)
                formatted_results.append(self._colorize_command(modified_line))
                block_lines = []
                j = i + 1
                while j < len(results):
                    next_line = results[j]
                    if next_line.startswith('[*]') or next_line.startswith('[+]') or next_line.strip().startswith('*') or '▶' in next_line:
                        break
                    if next_line.strip():
                        modified_next_line = self._replace_variables(next_line)
                        block_lines.append(self._colorize_command(modified_next_line))
                    j += 1
                formatted_results.extend(block_lines)
                formatted_results.append("")  
                i = j
            else:
                if line.strip():
                    modified_line = self._replace_variables(line)
                    formatted_results.append(self._colorize_command(modified_line))
                    formatted_results.append("")  
                i += 1
        return formatted_results

    def _display_results(self, results: List[str], title: str):
        self._clear_screen()
        print(f"\n{Colors.BLUE}🔍 {title}{Colors.RESET}\n")
        
        if not results:
            print(f"{Colors.RED}{Colors.BOLD}⚠️ {Colors.WHITE}{Colors.BOLD}No se encontraron resultados.{Colors.RESET}")
        else:
            formatted_results = self._format_results(results)
            cleaned_results = []
            last_was_empty = False
            for line in formatted_results:
                if line.strip() == "":
                    if not last_was_empty and cleaned_results:
                        cleaned_results.append(line)
                    last_was_empty = True
                else:
                    cleaned_results.append(line)
                    last_was_empty = False
            for line in cleaned_results:
                print(line)
        print()

    def _strip_ansi_codes(self, text: str) -> str:
        ansi_escape = re.compile(r'\033\[[0-9;]*[mK]')
        return ansi_escape.sub('', text)

    def _display_in_columns(self, items: List[str], title: str, item_color: str):
        self._clear_screen()
        total_items = len(items)
        print(f"{Colors.BLUE}{Colors.BOLD}╔═══════════════════[ {title} ]═══════════════════╗{Colors.RESET}")
        print(f"  {item_color}Total:{Colors.RESET} {total_items} ítems")
        print("")
        
        if not items:
            print(f"  {Colors.RED}{Colors.BOLD}⚠️ {Colors.WHITE}{Colors.BOLD}No hay ítems disponibles.{Colors.RESET}")
            print("")
            print(f"{Colors.BLUE}{Colors.BOLD}╚══════════════════════════════════════════════════════════════════╝{Colors.RESET}")
            return
        
        try:
            col_width = max(len(self._strip_ansi_codes(item)) for item in items) + 5
        except ValueError as e:
            self._handle_exception("⚠️ Error al calcular ancho de columna", e)
            col_width = 30
        
        rows = (len(items) + 1) // 2
        left_column = items[:rows]
        right_column = items[rows:]
        
        for i in range(rows):
            line = ""
            if i < len(left_column):
                item = f"  {item_color}•{Colors.RESET} {left_column[i]}"
                visible_length = len(self._strip_ansi_codes(item))
                padding = col_width - visible_length
                line += item + (" " * padding)
            else:
                line += " " * col_width
            
            if i < len(right_column):
                item = f"  {item_color}•{Colors.RESET} {right_column[i]}"
                line += item
            
            print(line)
        
        print("")
        print(f"{Colors.BLUE}{Colors.BOLD}╚══════════════════════════════════════════════════════════════════╝{Colors.RESET}")
        print()

    def _list_tools(self):
        self._display_in_columns(self.tools, "HERRAMIENTAS DISPONIBLES", Colors.ORANGE)

    def _list_categories(self):
        self._display_in_columns(list(self.categories.keys()), "CATEGORÍAS DISPONIBLES", Colors.GREEN)

    def _handle_internal_command(self, query: str) -> bool:
        query_lower = query.lower().strip()
        aliases = {
            'h': 'help',
            'lt': 'list tools',
            'lc': 'list categories',
            'c': 'clear',
            'q': 'exit',
            'si': 'setip',
            'su': 'seturl'
        }
        
        query_parts = query_lower.split(maxsplit=1)
        command = query_parts[0]
        args = query_parts[1] if len(query_parts) > 1 else ''
        
        command = aliases.get(command, command)
        
        if command == 'help':
            self.show_help()
            return True
        elif command == 'clear':
            self._clear_screen()
            self.print_header()
            return True
        elif command == 'list tools':
            self._list_tools()
            return True
        elif command == 'list categories':
            self._list_categories()
            return True
        elif command == 'exit':
            print(f"\n\t\t\t{Colors.RED}H4PPY H4CK1NG{Colors.RESET}")
            sys.exit(0)
        elif command == 'setip':
            if not args:
                if self.ip_value:
                    print(f"{Colors.BLUE}[ℹ] {Colors.RESET}Valor actual de $IP: {self.ip_value}")
                else:
                    print(f"{Colors.BLUE}[ℹ] {Colors.RESET}No se ha configurado un valor para $IP")
                print(f"{Colors.GREEN}[+] {Colors.RESET}Uso: {Colors.GRAY}setip <IP> (ejemplo: setip 192.168.1.1){Colors.RESET}")
                print(f"{Colors.GREEN}[+] {Colors.RESET}Para limpiar: {Colors.GRAY}setip clear{Colors.RESET}\n")
            elif args == 'clear':
                self.ip_value = None
                print(f"{Colors.GREEN}✔ {Colors.RESET}$IP ha sido limpiado. Los comandos usarán '$IP' por defecto.")
            else:
                try:
                    import ipaddress
                    ipaddress.ip_address(args)
                    self.ip_value = args
                    if args not in self.recent_ips:
                        self.recent_ips.append(args)
                        if len(self.recent_ips) > 5:
                            self.recent_ips.pop(0)
                    print(f"{Colors.GREEN}✔ {Colors.RESET}$IP configurado como: {args}")
                except ValueError:
                    domain_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$'
                    if re.match(domain_pattern, args) and 1 < len(args) <= 255:
                        self.ip_value = args
                        if args not in self.recent_ips:
                            self.recent_ips.append(args)
                            if len(self.recent_ips) > 5:
                                self.recent_ips.pop(0)
                        print(f"{Colors.GREEN}[✔] {Colors.RESET}$IP configurado como: {args}")
                    else:
                        print(f"{Colors.RED}⚠️ {Colors.RESET}Entrada inválida. Debe ser una IP válida o un dominio.")
                        print(f"{Colors.BLUE}Uso:{Colors.RESET} setip <IP> (ejemplo: setip 192.168.1.1)")
            return True
        elif command == 'seturl':
            if not args:
                if self.url_value:
                    print(f"{Colors.BLUE}[ℹ] {Colors.RESET}Valor actual de $URL: {self.url_value}")
                else:
                    print(f"{Colors.BLUE}[ℹ] {Colors.RESET}No se ha configurado un valor para $URL")
                print(f"{Colors.GREEN}[+]{Colors.RESET} Uso: {Colors.GRAY}seturl <URL> (ejemplo: seturl http://ejemplo.com ){Colors.RESET}")
                print(f"{Colors.GREEN}[+]{Colors.RESET} Para limpiar: {Colors.GRAY}seturl clear{Colors.RESET}\n")
            elif args == 'clear':
                self.url_value = None
                print(f"{Colors.GREEN}✔ {Colors.RESET}$URL ha sido limpiado. Los comandos usarán '$URL' por defecto.")
            else:
                url_pattern = r'^(https?://)?[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}(/.*)?$'
                if re.match(url_pattern, args):
                    normalized_url = self._normalize_url(args)
                    self.url_value = normalized_url
                    if normalized_url not in self.recent_urls:
                        self.recent_urls.append(normalized_url)
                        if len(self.recent_urls) > 5:
                            self.recent_urls.pop(0)
                    print(f"{Colors.GREEN}✔ {Colors.RESET}$URL configurado como: {normalized_url}")
                else:
                    print(f"{Colors.RED}⚠️ {Colors.RESET}Entrada inválida. Debe ser una URL válida (ejemplo: http://example.com).")
                    print(f"{Colors.BLUE}Uso:{Colors.RESET} seturl <URL> (ejemplo: seturl http://example.com)")
            return True
        return False

    def interactive_menu(self):
        self._clear_screen()
        self.print_header()

        kb = KeyBindings()
        
        @kb.add(Keys.ControlL)
        def clear_screen(event):
            self._clear_screen()
            self.print_header()
            event.app.renderer.reset()
            event.app.invalidate()

        @kb.add(Keys.ControlT)
        def list_tools(event):
            self._list_tools()
            event.app.renderer.reset()
            event.app.invalidate()

        @kb.add(Keys.ControlK)
        def list_categories(event):
            self._list_categories()
            event.app.renderer.reset()
            event.app.invalidate()

        @kb.add(Keys.ControlC)
        def exit_program(event):
            print(f"\n\t\t\t{Colors.RED}H4PPY H4CK1NG{Colors.RESET}")
            sys.exit(0)

        last_resize = 0
        def handle_resize(signum, frame):
            nonlocal last_resize
            current_time = time.time()
            if current_time - last_resize > 0.2:
                self._clear_screen()
                self.print_header()
                app = get_app()
                app.renderer.reset()
                app._redraw()
            last_resize = current_time

        try:
            signal.signal(signal.SIGWINCH, handle_resize)
        except ValueError as e:
            print(f"{Colors.RED}{Colors.BOLD}⚠️ {Colors.WHITE}{Colors.BOLD}No se pudo configurar el manejo de redimensionamiento: {e}{Colors.RESET}")

        def get_prompt():
            display_query = self.last_query if self.last_query else "~"
            if self.last_command_success:
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

        session = PromptSession(
            completer=self.completer,
            key_bindings=kb,
            style=self.prompt_style,
            message=get_prompt,
            validate_while_typing=False,
            multiline=False,
            erase_when_done=True
        )

        try:
            while True:
                try:
                    query = session.prompt().strip()

                    if query.lower() in ['exit', 'q']:
                        print(f"\n\t\t\t{Colors.RED}H4PPY H4CK1NG{Colors.RESET}")
                        break
                    
                    if not query:
                        print(f"{Colors.BLUE}ℹ {Colors.RESET}Ingresa un comando o 'help' para ayuda")
                        self.last_command_success = True
                        continue
                    
                    if self._handle_internal_command(query):
                        self.last_command_success = True
                        self.last_query = ""
                        continue
                    
                    category_results = self.search_by_category(query)
                    if category_results:
                        self._display_results(category_results, f"{Colors.LIGHT_BLUE}Resultados para Categoría: {Colors.RESET}{query.upper()}")
                        self.last_command_success = True
                        continue

                    tool_results = self.search_by_tool(query)
                    if tool_results:
                        self._display_results(tool_results, f"{Colors.ORANGE}Resultados para Herramienta: {Colors.RESET}{query.upper()}")
                        self.last_command_success = True
                        continue

                    all_options = list(self.categories.keys()) + self.tools
                    suggestions = difflib.get_close_matches(normalize_text(query), [normalize_text(opt) for opt in all_options], n=3, cutoff=0.6)
                    if suggestions:
                        print(f"{Colors.RED}{Colors.BOLD}⚠️ {Colors.WHITE}{Colors.BOLD}No se encontraron resultados para: {query}{Colors.RESET}")
                        print(f"{Colors.BLUE}ℹ {Colors.RESET}¿Quizás quisiste decir: {', '.join(suggestions)}?")
                    else:
                        print(f"{Colors.RED}{Colors.BOLD}⚠️ {Colors.WHITE}{Colors.BOLD}No se encontraron resultados para: {query}{Colors.RESET}\n")
                    self.last_command_success = False
                    self.last_query = ""

                except KeyboardInterrupt:
                    print(f"\n{Colors.RESET}", end="")
                    print(f"\n\t\t\t{Colors.RED}H4PPY H4CK1NG{Colors.RESET}")
                    sys.exit(0)
        finally:
            print(f"{Colors.RESET}", end="")

    def run_query(self, query: str):
        category_results = self.search_by_category(query)
        if category_results:
            self._display_results(category_results, f"{Colors.LIGHT_BLUE}Resultados para Categoría: {Colors.RESET}{query.upper()}")
            return

        tool_results = self.search_by_tool(query)
        if tool_results:
            self._display_results(tool_results, f"{Colors.ORANGE}Resultados para Herramienta: {Colors.RESET}{query.upper()}")
            return

        all_options = list(self.categories.keys()) + self.tools
        suggestions = difflib.get_close_matches(normalize_text(query), [normalize_text(opt) for opt in all_options], n=3, cutoff=0.6)
        
        self._clear_screen()
        print(f"{Colors.BLUE}{Colors.BOLD}╔════════════════════[ RESULTADOS DE BÚSQUEDA ]════════════════════╗{Colors.RESET}")
        print(f"  {Colors.RED}{Colors.BOLD}⚠️ {Colors.WHITE}{Colors.BOLD}No se encontraron resultados para: {Colors.WHITE}{query}{Colors.RESET}")
        print(f"  {Colors.BLUE}──────────────────────────────────────────────────────{Colors.RESET}")
        
        if suggestions:
            print(f"  {Colors.LIGHT_BLUE}ℹ Sugerencias:{Colors.RESET}")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"    {Colors.ORANGE}•{Colors.RESET} {suggestion}")
        else:
            print(f"  {Colors.LIGHT_BLUE}ℹ No hay sugerencias disponibles.{Colors.RESET}")
        
        print(f"{Colors.BLUE}{Colors.BOLD}╚══════════════════════════════════════════════════════════════════╝{Colors.RESET}")
        print()

class EnhancedCompleter(Completer):
    def __init__(self, categories: List[str], tools: List[str], tools_by_category: Dict[str, List[str]], recent_ips: List[str] = None, recent_urls: List[str] = None):
        self.original_categories = categories
        self.original_tools = tools
        self.categories_normalized = [normalize_text(cat) for cat in categories]
        self.tools_normalized = [normalize_text(tool) for tool in tools]
        self.tools_by_category = tools_by_category
        self.recent_ips = recent_ips or []
        self.recent_urls = recent_urls or []
        self.tool_to_category = {}
        try:
            for category, tools in tools_by_category.items():
                for tool in tools:
                    self.tool_to_category[normalize_text(tool)] = category
        except TypeError:
            print(f"{Colors.RED}{Colors.BOLD}⚠️ {Colors.WHITE}{Colors.BOLD}Error al construir autocompletado: Datos inválidos{Colors.RESET}")
        self.internal_commands = [
            ('help', 'Mostrar menú de ayuda'),
            ('clear', 'Limpiar pantalla'),
            ('list tools', 'Listar herramientas'),
            ('list categories', 'Listar categorías'),
            ('setip', 'Configurar $IP para comandos'),
            ('seturl', 'Configurar $URL para comandos'),
            ('exit', 'Salir del programa')
        ]
        self.command_to_alias = {
            'help': 'h',
            'clear': 'c',
            'list tools': 'lt',
            'list categories': 'lc',
            'setip': 'si',
            'seturl': 'su',
            'exit': 'q'
        }

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        word = document.get_word_before_cursor()
        word_normalized = normalize_text(word)
        completions = []

        parts = text.strip().split()
        is_setip_arg = len(parts) >= 2 and normalize_text(parts[0]) in ['setip', 'si']
        is_seturl_arg = len(parts) >= 2 and normalize_text(parts[0]) in ['seturl', 'su']

        if not (is_setip_arg or is_seturl_arg):
            for cmd, meta in self.internal_commands:
                if word_normalized in normalize_text(cmd):
                    alias = self.command_to_alias.get(cmd, cmd[:2])
                    display_text = f'[{alias}]'.ljust(5) + f' {cmd}'
                    completions.append((0, Completion(
                        cmd,
                        start_position=-len(word),
                        display=HTML(display_text),
                        display_meta=meta,
                        style='class:completion-menu.completion'
                    )))

        if not (is_setip_arg or is_seturl_arg):
            for orig_cat, norm_cat in zip(self.original_categories, self.categories_normalized):
                if word_normalized in norm_cat:
                    match_priority = 0 if norm_cat == word_normalized else 1
                    completions.append((match_priority, Completion(
                        orig_cat,
                        start_position=-len(word),
                        display=HTML(f'📁 {orig_cat}'),
                        display_meta=f'{len(self.tools_by_category.get(orig_cat, []))} herramientas',
                        style='class:completion-menu.category-completion'
                    )))

        if not (is_setip_arg or is_seturl_arg):
            for orig_tool, norm_tool in zip(self.original_tools, self.tools_normalized):
                if word_normalized in norm_tool:
                    match_priority = 0 if norm_tool == word_normalized else 1
                    category = self.tool_to_category.get(norm_tool, "")
                    completions.append((match_priority, Completion(
                        orig_tool,
                        start_position=-len(word),
                        display=HTML(f'🔧 {orig_tool}'),
                        display_meta=f'Categoría: {category}' if category else '',
                        style='class:completion-menu.tool-completion'
                    )))

        if is_setip_arg:
            for ip in self.recent_ips:
                if word_normalized in normalize_text(ip):
                    match_priority = 0 if normalize_text(ip) == word_normalized else 1
                    completions.append((match_priority, Completion(
                        ip,
                        start_position=-len(word),
                        display=HTML(f'🌐 {ip}'),
                        display_meta='IP o dominio reciente',
                        style='class:completion-menu.tool-completion'
                    )))

        if is_seturl_arg:
            for url in self.recent_urls:
                if word_normalized in normalize_text(url):
                    match_priority = 0 if normalize_text(url) == word_normalized else 1
                    completions.append((match_priority, Completion(
                        url,
                        start_position=-len(word),
                        display=HTML(f'🌐 {url}'),
                        display_meta='URL reciente',
                        style='class:completion-menu.tool-completion'
                    )))

        seen = set()
        for priority, completion in sorted(completions, key=lambda x: x[0]):
            if completion.text not in seen:
                seen.add(completion.text)
                yield completion

def main():
    parser = argparse.ArgumentParser(description="Herramienta de búsqueda de comandos para pentesting.")
    parser.add_argument('-q', '--query', help="Consulta para buscar directamente y salir.")
    
    try:
        args = parser.parse_args()
    except SystemExit as e:
        if e.code != 0:
            print(f"{Colors.RED}{Colors.BOLD}⚠️ {Colors.WHITE}{Colors.BOLD}Error al parsear argumentos{Colors.RESET}")
            sys.exit(1)
        sys.exit(0)

    try:
        search_tool = SearchCommand()
        print()
        if args.query:
            search_tool.run_query(args.query)
        else:
            search_tool.interactive_menu()
    except (FileNotFoundError, ValueError) as e:
        print(f"{Colors.RED}{Colors.BOLD}⚠️ {Colors.WHITE}{Colors.BOLD}Error en la ejecución: {e}{Colors.RESET}")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"{Colors.RESET}", end="")
        print(f"\n\t\t\t{Colors.RED}H4PPY H4CK1NG{Colors.RESET}")
        sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"{Colors.RESET}", end="")
        print(f"\n\t\t\t{Colors.RED}H4PPY H4CK1NG{Colors.RESET}")
        sys.exit(0)
