#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# test
"""
═════════════════════════[searchCommand]════════════════════════════
Autor       : Jordan Cueva Mendoza (aka SkyW4r33x)
Repositorio : https://github.com/SkyW4r33x

Descripción :
Esta herramienta fue creada como un recurso de apoyo tanto para quienes  
se están iniciando en el mundo de la ciberseguridad, como para usuarios 
avanzados que buscan una forma rápida y ordenada de acceder a comandos
útiles. Incluye una interfaz intuitiva, validación mejorada y visualización optimizada.
Espero que sea de su agrado y recuerda siempre...

                        H4PPY H4CK1NG
═══════════════════════════════════════════════════════════════════
"""

import os
import re
import sys
import signal
import subprocess
import argparse
import time
import unicodedata
import urllib.parse
import socket
import warnings
from typing import List, Dict, Optional
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.application import get_app
from prompt_toolkit.history import FileHistory
from fuzzywuzzy import process

# Suprimir advertencias de urllib3 sobre conexiones HTTPS no verificadas
warnings.filterwarnings("ignore", category=Warning, module="urllib3")

__version__ = "1.3"

if os.name == 'nt':
    print(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} Este programa está diseñado para Linux/macOS. En Windows, usa WSL para mejor compatibilidad.")

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
    YELLOW = "\033[38;2;255;255;0m"

def normalize_text(text: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', text.lower())
        if unicodedata.category(c) != 'Mn'
    )

class SearchCommand:
    def __init__(self):
        if os.geteuid() == 0 and 'SUDO_USER' in os.environ:
            user_home = os.path.expanduser(f"~{os.environ['SUDO_USER']}")
        else:
            user_home = os.path.expanduser('~')
        
        self.root_dir = os.path.join(user_home, 'referencestuff')
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

        try:
            self._check_directory_permissions(self.root_dir)
        except PermissionError as e:
            self._handle_exception(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} Error de permisos en el directorio", e, True)

        self._load_tools()
        self._init_prompt_session()

    def _init_prompt_session(self):
        try:
            self.prompt_style = Style.from_dict({
                'prompt.parens': '#5EBDAB',
                'prompt.name': '#367bf0 bold',
                'prompt.dash': '#5EBDAB',
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
        except ValueError as e:
            self._handle_exception(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} Error al configurar estilos", e, True)

        try:
            self.completer = EnhancedCompleter(
                categories=list(self.categories.keys()),
                tools=[tool for tools in self.tools_by_category.values() for tool in tools],
                tools_by_category=self.tools_by_category,
                recent_ips=self.recent_ips,
                recent_urls=self.recent_urls,
                tool_to_category=self.tool_to_category,
                tool_to_file=self.tool_to_file
            )
        except TypeError as e:
            self._handle_exception(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} Error al inicializar autocompletado", e, True)

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

        @kb.add(Keys.ControlR)
        def refresh_tools(event):
            try:
                self._load_tools()
                self._init_prompt_session()
                self._clear_screen()
                self.print_header()
                print(f"{Colors.GREEN}⏳ {Colors.RESET}Herramientas recargadas exitosamente.\n")
            except Exception as e:
                self._handle_exception(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} Error al recargar herramientas", e)
            event.app.renderer.reset()
            event.app.invalidate()

        @kb.add(Keys.ControlE)
        def edit_last_tool(event):
            if self.last_query and self.last_query in self.tool_to_file:
                editor = os.environ.get('EDITOR')
                if not editor:
                    for default_editor in ['nano', 'vim', 'vi']:
                        if subprocess.run(['which', default_editor], capture_output=True, text=True).returncode == 0:
                            editor = default_editor
                            break
                    else:
                        print(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} No se encontró un editor compatible (nano, vim, vi). Configura $EDITOR.")
                        return
                file_path = self.tool_to_file[self.last_query]
                if not os.path.exists(file_path):
                    print(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} El archivo para '{self.last_query}' no existe en {file_path}.")
                    return
                try:
                    subprocess.run([editor, file_path], check=True)
                    print(f"{Colors.GREEN}[✔] {Colors.RESET}Abriendo {Colors.GREEN}{self.last_query}{Colors.RESET} en {editor}. Usa {Colors.BLUE}refresh{Colors.RESET} para recargar cambios.\n")
                except (subprocess.CalledProcessError, FileNotFoundError) as e:
                    print(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} Error al abrir el editor: {e}")
            else:
                print(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} No hay herramienta reciente para editar. Usa 'edit <herramienta>'.")
            event.app.renderer.reset()
            event.app.invalidate()

        @kb.add(Keys.ControlC)
        def exit_program(event):
            print(f"\n\t\t\t{Colors.RED}{Colors.BOLD}H4PPY H4CK1NG{Colors.RESET}")
            sys.exit(0)

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

        history_file = os.path.join(os.path.expanduser('~'), '.searchcommand_history')
        self.prompt_session = PromptSession(
            completer=self.completer,
            key_bindings=kb,
            style=self.prompt_style,
            message=get_prompt,
            validate_while_typing=False,
            multiline=False,
            erase_when_done=True,
            history=FileHistory(history_file)
        )

    def _handle_exception(self, error_msg: str, e: Exception, exit_on_error: bool = False):
        print(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET}{Colors.BOLD}{error_msg}: {e}{Colors.RESET}")
        if exit_on_error:
            sys.exit(1)

    def _clear_screen(self):
        try:
            if os.name in ('posix', 'nt'):
                os.system('clear' if os.name == 'posix' else 'cls')
            else:
                print(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} Limpieza de pantalla no soportada en este sistema.{Colors.RESET}")
        except OSError as e:
            print(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} Error al limpiar pantalla: {e}{Colors.RESET}")

    def _read_tool_file(self, file_path: str) -> List[str]:
        if not os.path.exists(file_path):
            return []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = [line.rstrip('\n') for line in file]
            return lines if lines else []
        except (PermissionError, UnicodeDecodeError) as e:
            return []

    def _check_directory_permissions(self, directory: str):
        if not os.access(directory, os.R_OK):
            raise PermissionError(f"No se tienen permisos de lectura para {directory}")
        for root, dirs, files in os.walk(directory):
            for d in dirs:
                if not os.access(os.path.join(root, d), os.R_OK):
                    raise PermissionError(f"No se tienen permisos de lectura para el directorio {os.path.join(root, d)}")
            for f in files:
                if not os.access(os.path.join(root, f), os.R_OK):
                    raise PermissionError(f"No se tienen permisos de lectura para el archivo {os.path.join(root, f)}")

    def _parse_directory_structure(self):
        if not os.path.exists(self.root_dir):
            raise FileNotFoundError(f"Directorio no encontrado en {self.root_dir}")

        self.tools_by_category = {}
        self.categories = {}
        self.tool_to_file = {}
        self.tool_to_category = {}
        seen_tools = set()
        duplicate_count = 0

        for category in os.listdir(self.root_dir):
            category_path = os.path.join(self.root_dir, category)
            if not os.path.isdir(category_path):
                continue
            
            tools = []
            for tool_file in os.listdir(category_path):
                if tool_file.endswith('.txt'):
                    tool_name = tool_file[:-4]
                    if tool_name in seen_tools:
                        print(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} Herramienta duplicada: '{tool_name}' en {category}. Ignorada.{Colors.RESET}")
                        duplicate_count += 1
                        continue
                    seen_tools.add(tool_name)
                    tools.append(tool_name)
                    tool_path = os.path.join(category_path, tool_file)
                    self.tool_to_file[tool_name] = tool_path
                    self.tool_to_category[tool_name] = category
            
            if tools:
                self.categories[category] = tools
                self.tools_by_category[category] = tools

        if not self.categories:
            raise ValueError("No se encontraron categorías con herramientas válidas en el directorio")

        total_tools = sum(len(tools) for tools in self.tools_by_category.values())
        print(f"{Colors.BLUE}[ℹ] {Colors.RESET}Cargadas {total_tools} herramientas únicas. {duplicate_count} duplicados ignorados.")

    def _load_tools(self):
        try:
            self._parse_directory_structure()
        except (FileNotFoundError, PermissionError) as e:
            self._handle_exception(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} Error al leer el directorio", e, True)
        except ValueError as e:
            self._handle_exception(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} Error al parsear el contenido", e, True)

    def _normalize_url(self, url: str) -> str:
        parsed = urllib.parse.urlparse(url)
        scheme = parsed.scheme if parsed.scheme in ['http', 'https'] else 'http'
        path = re.sub(r'/+', '/', parsed.path.lstrip('/'))
        normalized = urllib.parse.urlunparse((
            scheme,
            parsed.netloc.lower(),
            path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        return normalized

    def _replace_variables(self, command: str) -> str:
        if '$IP' in command and self.ip_value:
            command = command.replace('$IP', self.ip_value)
        if '$URL' in command and self.url_value:
            command = command.replace('$URL', self.url_value)
            command = re.sub(r'(https?://[^/]+)//+', r'\1/', command)
        return command

    def _search_generic(self, query: str, search_type: str) -> List[str]:
        try:
            query_normalized = normalize_text(query)
            results = []
            self.search_mode = search_type
            items = self.categories if search_type == "category" else self.tool_to_file
            item_normalized = {normalize_text(k): k for k in items.keys()}
            
            if query_normalized in item_normalized:
                key = item_normalized[query_normalized]
                if search_type == "category":
                    self.current_category = key
                    self.last_query = key
                    for tool in self.categories[key]:
                        results.append(f"[*] {tool}")
                        tool_content = self._read_tool_file(self.tool_to_file[tool])
                        results.extend([self._replace_variables(line) for line in tool_content if line.strip()])
                else:
                    self.current_category = self.tool_to_category.get(key, "")
                    self.last_query = key
                    tool_content = self._read_tool_file(self.tool_to_file[key])
                    results.append(f"[*] {key}")
                    results.extend([self._replace_variables(line) for line in tool_content if line.strip()])
                self.last_results_count = len(results)
                return results
            
            matches = process.extract(query_normalized, item_normalized.keys(), limit=1, scorer=process.fuzz.partial_ratio)
            if matches and matches[0][1] >= 80:
                key = item_normalized[matches[0][0]]
                if search_type == "category":
                    self.current_category = key
                    self.last_query = key
                    for tool in self.categories[key]:
                        results.append(f"[*] {tool}")
                        tool_content = self._read_tool_file(self.tool_to_file[tool])
                        results.extend([self._replace_variables(line) for line in tool_content if line.strip()])
                else:
                    self.current_category = self.tool_to_category.get(key, "")
                    self.last_query = key
                    tool_content = self._read_tool_file(self.tool_to_file[key])
                    results.append(f"[*] {key}")
                    results.extend([self._replace_variables(line) for line in tool_content if line.strip()])
                self.last_results_count = len(results)
                return results
            
            self.current_category = ""
            self.last_query = ""
            self.last_results_count = 0
            return []
        except AttributeError as e:
            self._handle_exception(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} Error al buscar por {search_type}", e)
            return []

    def search_by_category(self, query: str) -> List[str]:
        return self._search_generic(query, "category")

    def search_by_tool(self, query: str) -> List[str]:
        return self._search_generic(query, "tool")

    def show_help(self):
        self._clear_screen()
        print("")
        print(f"  {Colors.GREEN}{'Comando'.center(20)} {'Alias'.center(12)} {'Descripción'.center(32)}{Colors.RESET}")
        print(f"  {('─' * 20).center(20)} {('─' * 12).center(12)} {('─' * 32).center(32)}")
        commands = [
            ("➜", "<herramienta>", "", "Buscar una herramienta (ej: NMAP)"),
            ("➜", "<categoría>", "", "Buscar una categoría (ej: RECONOCIMIENTO)"),
            ("➜", "help", "h", "Mostrar este menú de ayuda"),
            ("➜", "list tools", "lt", "Listar todas las herramientas"),
            ("➜", "list categories", "lc", "Listar todas las categorías"),
            ("➜", "setip <IP>", "si", "Configurar $IP"),
            ("➜", "seturl <URL>", "su", "Configurar $URL"),
            ("➜", "edit <herramienta>", "e", "Editar herramienta"),
            ("➜", "refresh [config]", "r", "Recargar herramientas o limpiar config"),
            ("➜", "clear", "c", "Limpiar la pantalla"),
            ("➜", "exit", "q", "Salir del programa"),
        ]
        for icon, cmd, alias, desc in commands:
            print(f"  {Colors.GREEN}{icon:<3} {Colors.RESET}{cmd:<20} {Colors.GRAY}{alias:<10} {Colors.WHITE}{desc:<30}{Colors.RESET}")
        print("")
        print(f"  {Colors.GREEN}{'Atajo'.center(20)} {'Descripción'.center(40)}{Colors.RESET}")
        print(f"  {('─' * 20).center(20)} {('─' * 30).center(40)}")
        shortcuts = [
            ("•", "Ctrl + L", "Limpiar la pantalla"),
            ("•", "Ctrl + T", "Listar herramientas rápidamente"),
            ("•", "Ctrl + K", "Listar categorías rápidamente"),
            ("•", "Ctrl + E", "Editar última herramienta buscada"),
            ("•", "Ctrl + R", "Recargar herramientas"),
            ("•", "Ctrl + C", "Salir inmediatamente"),
        ]
        for icon, shortcut, desc in shortcuts:
            print(f"  {Colors.GREEN}{icon:<3}{Colors.RESET} {shortcut:<20} {Colors.WHITE}{desc:<40}{Colors.RESET}")
        print("")
        print()

    def print_header(self):
        self._clear_screen()
        banner = f'''
{Colors.GREEN}{Colors.BOLD}\t\t\tsearchCommand v.{__version__}{Colors.RESET}\t\t\t{Colors.BLUE}{Colors.BOLD}{Colors.RESET}

{Colors.BLUE}+ -- --=[ 📂 {Colors.RESET}Categorías Disponibles  {Colors.BLUE}{Colors.BOLD}:{Colors.RESET} {len(self.categories)}{Colors.RESET}{Colors.BLUE}\t\t\t\t]{Colors.RESET}
{Colors.BLUE}+ -- --=[ 🔧 {Colors.RESET}Herramientas Totales    {Colors.BLUE}{Colors.BOLD}:{Colors.RESET} {sum(len(tools) for tools in self.tools_by_category.values())}{Colors.RESET}{Colors.BLUE}\t\t\t\t]{Colors.RESET}
{Colors.BLUE}+ -- --=[ {Colors.RESET}{Colors.BOLD}{Colors.GREEN} ➜{Colors.RESET} Creado por              {Colors.BLUE}{Colors.BOLD}:{Colors.RESET} Jordan (SkyW4r33x){Colors.RESET}{Colors.BLUE}\t\t]{Colors.RESET}
{Colors.BLUE}+ -- --=[ {Colors.RESET}{Colors.BOLD}{Colors.GREEN} ➜{Colors.RESET} Repositorio             {Colors.BLUE}{Colors.BOLD}:{Colors.RESET} https://github.com/SkyW4r33x{Colors.RESET}{Colors.BLUE}\t]{Colors.RESET}

{Colors.BLUE}+ -- --=[ {Colors.RESET}{Colors.BOLD}{Colors.GREEN} ➜{Colors.RESET} Escribe {Colors.BLUE}{Colors.BOLD}help{Colors.RESET} para ver los comandos.\t\t\t{Colors.BLUE}]{Colors.RESET}
{Colors.BLUE}+ -- --=[ {Colors.RESET}{Colors.BOLD}{Colors.GREEN} ➜{Colors.RESET} Usa {Colors.BLUE}{Colors.BOLD}Tab{Colors.RESET} para autocompletar o flechas para historial.\t{Colors.BLUE}]{Colors.RESET}    
'''
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
            self._handle_exception(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} Error al colorear comando", e)
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
                category = self.tool_to_category.get(tool_name, "Sin categoría")
                
                if self.search_mode == "category":
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
                formatted_results.append(self._colorize_command(line))
                block_lines = []
                j = i + 1
                while j < len(results):
                    next_line = results[j]
                    if next_line.startswith('[*]') or next_line.startswith('[+]') or next_line.strip().startswith('*') or '▶' in next_line:
                        break
                    if next_line.strip():
                        block_lines.append(self._colorize_command(next_line))
                    j += 1
                formatted_results.extend(block_lines)
                formatted_results.append("")
                i = j
            else:
                if line.strip():
                    formatted_results.append(self._colorize_command(line))
                    formatted_results.append("")
                i += 1
        return formatted_results

    def _display_results(self, results: List[str], title: str):
        self._clear_screen()
        print(f"\n{Colors.BLUE}🔍 {title}{Colors.RESET}\n")
        
        if not results:
            print(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} No se encontraron resultados.{Colors.RESET}")
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
        
        item_type = "herramientas" if "HERRAMIENTAS" in title else "categorías"
        
        print(f"{Colors.BLUE}{Colors.BOLD}╔══════════════════════════╣ {title} ╠══════════════════════════╗{Colors.RESET}")
        print("")
        print(f"  {item_color}Total:{Colors.RESET} {total_items} {item_type}")
        print("")
        
        if not items:
            print(f"  {Colors.RED}{Colors.BOLD}[-]{Colors.RESET} No hay ítems disponibles.{Colors.RESET}")
            print("")
            print(f"{Colors.BLUE}{Colors.BOLD}╚═══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}\n")
            return
        
        try:
            col_width = 32 if "HERRAMIENTAS" in title else 45
            
            num_columns = 3 if "HERRAMIENTAS" in title else 2
            rows = (len(items) + num_columns - 1) // num_columns
            
            icon = "🔧" if "HERRAMIENTAS" in title else "📂"
            for i in range(rows):
                line = ""
                for col in range(num_columns):
                    idx = i + col * rows
                    if idx < len(items):
                        item = f"  {item_color}{icon}{Colors.RESET} {items[idx]}"
                        visible_length = len(self._strip_ansi_codes(item))
                        padding = col_width - visible_length
                        line += item + (" " * max(0, padding))
                    else:
                        line += " " * col_width
                print(line.rstrip())
        
            print("")
            print(f"{Colors.BLUE}{Colors.BOLD}╚═══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}\n")
        except ValueError as e:
            self._handle_exception(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} Error al calcular ancho de columna", e)
            self._display_in_columns_fallback(items, title, item_color)

    def _display_in_columns_fallback(self, items: List[str], title: str, item_color: str):
        self._clear_screen()
        item_type = "herramientas" if "HERRAMIENTAS" in title else "categorías"
        
        print(f"{Colors.BLUE}{Colors.BOLD}╔═══════════════════════════╣ {title} ╠═══════════════════════════╗{Colors.RESET}")
        print("")
        print(f"  {item_color}Total:{Colors.RESET} {len(items)} {item_type}")
        print("")
        icon = "🔧" if "HERRAMIENTAS" in title else "📂"
        for item in items:
            print(f"  {item_color}{icon}{Colors.RESET} {item}")
        print("")
        print(f"{Colors.BLUE}{Colors.BOLD}╚═══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}")

    def _list_tools(self):
        all_tools = sorted([tool for tools in self.tools_by_category.values() for tool in tools])
        self._display_in_columns(all_tools, "HERRAMIENTAS DISPONIBLES", Colors.ORANGE)

    def _list_categories(self):
        all_categories = sorted(self.categories.keys())
        self._display_in_columns(all_categories, "CATEGORÍAS DISPONIBLES", Colors.BLUE)

    def _display_edit_help(self):
        self._clear_screen()
        total_tools = sum(len(tools) for tools in self.tools_by_category.values())
        total_categories = len(self.categories)
        
        print(f"{Colors.BLUE}{Colors.BOLD}╔═══════════════════╣ HERRAMIENTAS DISPONIBLES ╠═══════════════════╗{Colors.RESET}")
        print(f"  {Colors.GREEN}Categorías:{Colors.RESET} {total_categories}  {Colors.ORANGE}Herramientas:{Colors.RESET} {total_tools}")
        print(f"  {Colors.BLUE}[ℹ] {Colors.RESET}Uso: {Colors.GRAY}edit <herramienta> (ejemplo: edit nmap) {Colors.RESET}")
        print(f"{Colors.BLUE}{Colors.BOLD}╚═══════════════════════════════════════════════════════════════════════╝{Colors.RESET}\n")

    def _handle_internal_command(self, query: str) -> bool:
        query_lower = query.lower().strip()
        
        aliases = {
            'h': 'help',
            'lt': 'list tools',
            'lc': 'list categories',
            'c': 'clear',
            'q': 'exit',
            'si': 'setip',
            'su': 'seturl',
            'r': 'refresh',
            'e': 'edit'
        }
        commands = {
            'help': 'help',
            'list tools': 'list tools',
            'list categories': 'list categories',
            'clear': 'clear',
            'exit': 'exit',
            'setip': 'setip',
            'seturl': 'seturl',
            'refresh': 'refresh',
            'edit': 'edit'
        }
        
        query_parts = query.strip().split(maxsplit=1)
        command_input = query_parts[0].lower()
        args = query_parts[1] if len(query_parts) > 1 else ''
        
        command = aliases.get(command_input, commands.get(command_input, None))
        if not command:
            command = commands.get(query_lower, None)
        
        if not command:
            return False
        
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
            print(f"\n\t\t\t\t\t{Colors.RED}{Colors.RESET}H4PPY H4CK1NG")
            sys.exit(0)
        elif command == 'setip':
            if not args:
                if self.ip_value:
                    print(f"{Colors.BLUE}[ℹ] {Colors.RESET}Valor actual de $IP: {Colors.GREEN}{self.ip_value}{Colors.RESET}")
                else:
                    print(f"{Colors.BLUE}[ℹ] {Colors.RESET}No se ha configurado un valor para $IP")
                print(f"{Colors.GREEN}[+] {Colors.RESET}Uso: {Colors.GREEN}setip <IP|dominio> (ejemplo: setip 192.168.1.1 o setip example.com)")
                print(f"{Colors.GREEN}[+] {Colors.RESET}Para limpiar: {Colors.GREEN}setipclear{Colors.RESET}")
                print(f"{Colors.BLUE}[ℹ] {Colors.RESET}La IP/dominio se usará en comandos con $IP.\n")
                return True
            elif args.lower() == 'clear':
                self._ip_value = None
                print(f"{Colors.GREEN}[✔] {Colors.RESET}Correctamente restablecido. Los comandos usarán colores_verdes {Colors.GREEN}$IP{Colors.RESET} por defecto.\n")
                return True
            else:
                try:
                    import ipaddress
                    ipaddress.ip_address(args)
                    self.ip_value = args
                    try:
                        socket.gethostbyname(args)
                        print(f"{Colors.GREEN}[✔] {Colors.RESET} $IP resuelve correctamente: {args}")
                    except socket.gaierror:
                        print(f"{Colors.ORANGE}[-] {Colors.RESET} $IP no resuelve en DNS, pero se acepta: {args}")
                except ValueError:
                    domain_pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
                    if re.match(domain_pattern, args) and 1 < len(args) <= 255:
                        try:
                            socket.gethostbyname(args)
                            self.ip_value = args
                            print(f"{Colors.GREEN}[✔] {Colors.RESET}Dominio resuelve correctamente: {args}")
                        except socket.gaierror:
                            print(f"{Colors.ORANGE}[-] {Colors.RESET} Dominio no resuelve en DNS, pero se acepta: {args}")
                            self.ip_value = args
                    else:
                        print(f"{Colors.RED}[-] {Colors.RESET} Entrada inválida. Debe ser una IP válida (ej: 192.168.1.1) o dominio (ejemplo: example.com).")
                        print(f"{Colors.BLUE}[ℹ] {Colors.RESET}Uso: setip <IP|dominio>| (ejemplo: setip 8.8.8.8)")
                        return True
                if self.ip_value and args not in self.recent_ips:
                    self.recent_ips.append(args)
                    if len(self.recent_ips) > 5:
                        self.recent_ips.pop(0)
                print(f"{Colors.GREEN}[✔] {Colors.RESET}$IP configurado como: {Colors.GREEN}{args}{Colors.RESET}\n")
                return True
        elif command == 'seturl':
            if not args:
                if self.url_value:
                    print(f"{Colors.BLUE}[ℹ] {Colors.RESET}Valor actual de $URL: {Colors.GREEN}{self.url_value}{Colors.RESET}")
                else:
                    print(f"{Colors.BLUE}[ℹ] {Colors.RESET}No se ha configurado un valor para $URL")
                print(f"{Colors.GREEN}[+] {Colors.RESET}Uso: {Colors.GREEN}seturl <URL> (ejemplo: seturl http://example.com, https://example.com/, http://10.10.10.20)")
                print(f"{Colors.GREEN}[+] {Colors.RESET}Para limpiar: {Colors.GREEN}seturl clear{Colors.RESET}")
                print(f"{Colors.BLUE}[ℹ] {Colors.RESET}La URL se usará en comandos con $URL.\n")
                return True
            elif args.lower() == 'clear':
                self.url_value = None
                print(f"{Colors.GREEN}[✔] {Colors.RESET}Correctamente restablecido. Los comandos usarán colores verdes {Colors.GREEN}$URL{Colors.RESET} por defecto.\n")
                return True
            else:
                url_pattern = r'^(https?://)?(([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}|(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}))(/.*)?$'
                if re.match(url_pattern, args):
                    self.url_value = args
                    normalized_url = self._normalize_url(args)
                    try:
                        import requests
                        response = requests.head(normalized_url, timeout=3, allow_redirects=True, verify=False)
                        if response.status_code < 400:
                            print(f"{Colors.GREEN}[✔] {Colors.RESET}$URL accesible: {Colors.BLUE}{args}{Colors.RESET} (Código: {response.status_code})")
                        else:
                            print(f"{Colors.ORANGE}[-] {Colors.RESET}URL no accesible (código: {response.status_code}), pero se agregó con éxito")
                    except (ImportError, requests.RequestException):
                        print(f"{Colors.ORANGE}[-] {Colors.RESET}URL no accesible, pero se agregó con éxito")
                    if args not in self.recent_urls:
                        self.recent_urls.append(args)
                        if len(self.recent_urls) > 5:
                            self.recent_urls.pop(0)
                    print(f"{Colors.GREEN}[✔] {Colors.RESET}$URL configurado como: {Colors.GREEN}{args}{Colors.RESET}\n")
                else:
                    print(f"{Colors.RED}[-] {Colors.RESET}Entrada inválida. Debe ser una URL válida (ej: http://example.com, https://example.com/, http://10.10.10.20).")
                    print(f"{Colors.BLUE}[ℹ] {Colors.RESET}Uso: seturl <URL> (ejemplo: seturl http://10.10.10.20)\n")
                return True
        elif command == 'refresh':
            if args.lower() == 'config':
                self.ip_value = None
                self.url_value = None
                self.recent_ips.clear()
                self.recent_urls.clear()
                print(f"{Colors.GREEN}[✔] {Colors.RESET}Configuración reiniciada (IP y URL limpiados).")
            else:
                try:
                    self._load_tools()
                    self._init_prompt_session()
                    self._clear_screen()
                    self.print_header()
                    print(f"{Colors.GREEN}⏳ {Colors.RESET}Herramientas recargadas exitosamente.\n")
                except Exception as e:
                    self._handle_exception(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} Error al recargar herramientas", e)
            return True
        elif command == 'edit':
            if not args:
                if self.last_query and self.last_query in self.tool_to_file:
                    editor = os.environ.get('EDITOR')
                    if not editor:
                        for default_editor in ['nano', 'vim', 'vi']:
                            if subprocess.run(['which', default_editor], capture_output=True, text=True).returncode == 0:
                                editor = default_editor
                                break
                        else:
                            print(f"{Colors.RED}[-] {Colors.RESET} No se encontró un editor compatible (nano, vim, vi). Configura $EDITOR.")
                            return True
                    file_path = self.tool_to_file[self.last_query]
                    if not os.path.exists(file_path):
                        print(f"{Colors.RED}[-]{Colors.RESET} El archivo para '{self.last_query}' no existe en {file_path}.")
                        return True
                    try:
                        subprocess.run([editor, file_path], check=True)
                        print(f"{Colors.GREEN}[✔] {Colors.RESET}Abriendo {self.last_query} en {editor}. Usa 'refresh' para recargar cambios.")
                    except (subprocess.CalledProcessError, FileNotFoundError) as e:
                        print(f"{Colors.RED}[-] {Colors.RESET} Error al abrir el editor: {e}")
                else:
                    self._display_edit_help()
            else:
                tool = args.strip()
                if tool in self.tool_to_file:
                    editor = os.environ.get('EDITOR')
                    if not editor:
                        for default_editor in ['nano', 'vim', 'vi']:
                            if subprocess.run(['which', default_editor], capture_output=True, text=True).returncode == 0:
                                editor = default_editor
                                break
                        else:
                            print(f"{Colors.RED}[-] {Colors.RESET} No se encontró un editor compatible (nano, vim, vi). Configura $EDITOR.")
                            return True
                    file_path = self.tool_to_file[tool]
                    if not os.path.exists(file_path):
                        print(f"{Colors.RED}[-]{Colors.RESET} El archivo para '{tool}' no existe en {file_path}.")
                        return True
                    try:
                        subprocess.run([editor, file_path], check=True)
                        print(f"{Colors.GREEN}[✔] {Colors.RESET}Abriendo {tool} en {editor}. Usa 'refresh' para recargar cambios.")
                    except (subprocess.CalledProcessError, FileNotFoundError) as e:
                        print(f"{Colors.RED}[-] {Colors.RESET} Error al abrir el editor: {e}")
                else:
                    self._clear_screen()
                    print(f"{Colors.RED}[-] {Colors.RESET} Herramienta '{tool}' no encontrada.")
                    self._display_edit_help()
            return True
        return False

    def interactive_menu(self):
        self._clear_screen()
        self.print_header()

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
            print(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} No se pudo configurar el manejo de redimensionamiento: {e}{Colors.RESET}")

        try:
            while True:
                try:
                    query = self.prompt_session.prompt().strip()

                    if query.lower() in ['exit', 'q']:
                        print(f"\n\t\t\t{Colors.RED}{Colors.BOLD}H4PPY H4CK1NG{Colors.RESET}")
                        break
                    
                    if not query:
                        print(f"{Colors.BLUE}[ℹ] {Colors.RESET}Ingresa un comando, herramienta o {Colors.GREEN}help{Colors.RESET} para ayuda.\n")
                        self.last_command_success = True
                        continue
                    
                    if self._handle_internal_command(query):
                        self.last_command_success = True
                        self.last_query = ""
                        continue
                    
                    category_results = self.search_by_category(query)
                    if category_results:
                        self._display_results(category_results, f"{Colors.BLUE}{Colors.BOLD}Resultados para Categoría: {Colors.RESET}{query.upper()}\n")
                        self.last_command_success = True
                        continue

                    tool_results = self.search_by_tool(query)
                    if tool_results:
                        self._display_results(tool_results, f"{Colors.ORANGE}Resultados para Herramienta: {Colors.RESET}{query.upper()}\n")
                        self.last_command_success = True
                        continue

                    all_options = list(self.categories.keys()) + [tool for tools in self.tools_by_category.values() for tool in tools]
                    all_options_normalized = [normalize_text(opt) for opt in all_options]
                    suggestions = process.extract(normalize_text(query), all_options_normalized, limit=3, scorer=process.fuzz.partial_ratio)
                    suggestions = [all_options[all_options_normalized.index(s[0])] for s in suggestions if s[1] >= 80]
                    if suggestions:
                        print(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} No se encontraron resultados para: {query}{Colors.RESET}\n")
                        print(f"{Colors.BLUE}[ℹ] {Colors.RESET}¿Quizás quisiste decir: {', '.join(suggestions)}?")
                    else:
                        print(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} No se encontraron resultados para: {query}{Colors.RESET}\n")
                    self.last_command_success = False
                    self.last_query = ""

                except KeyboardInterrupt:
                    print(f"\n{Colors.RESET}", end="")
                    print(f"\n\t\t\t{Colors.RED}{Colors.BOLD}H4PPY H4CK1NG{Colors.RESET}")
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

        self._clear_screen()
        print(f"{Colors.BLUE}🔍 Resultados de Búsqueda{Colors.RESET}\n")
        print(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} No se encontraron resultados para: {Colors.WHITE}{query}{Colors.RESET}")
        print(f"{Colors.BLUE}──────────────────────────────────────────────────────{Colors.RESET}")
        
        all_options = list(self.categories.keys()) + [tool for tools in self.tools_by_category.values() for tool in tools]
        all_options_normalized = [normalize_text(opt) for opt in all_options]
        suggestions = process.extract(normalize_text(query), all_options_normalized, limit=3, scorer=process.fuzz.partial_ratio)
        suggestions = [all_options[all_options_normalized.index(s[0])] for s in suggestions if s[1] >= 80]
        
        if suggestions:
            print(f"{Colors.LIGHT_BLUE}[ℹ] Sugerencias:{Colors.RESET}")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"    {Colors.ORANGE}•{Colors.RESET} {suggestion}")
        else:
            print(f"{Colors.LIGHT_BLUE}[ℹ] No hay sugerencias disponibles.{Colors.RESET}")
        
        print()

class EnhancedCompleter(Completer):
    def __init__(self, categories: List[str], tools: List[str], tools_by_category: Dict[str, List[str]], recent_ips: List[str], recent_urls: List[str], tool_to_category: Dict[str, str], tool_to_file: Dict[str, str]):
        self.original_categories = categories
        self.original_tools = [tool for tool in tools if tool in tool_to_file]
        self.categories_normalized = [normalize_text(cat) for cat in categories]
        self.tools_normalized = [normalize_text(tool) for tool in self.original_tools]
        self.tools_by_category = tools_by_category
        self.recent_ips = recent_ips
        self.recent_urls = recent_urls
        self.tool_to_category = tool_to_category
        self.tool_to_file = tool_to_file

        if not categories or not self.original_tools or not tools_by_category:
            print(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} Error: Datos de autocompletado vacíos o inválidos{Colors.RESET}")

        self.internal_commands = [
            ('help', 'Mostrar menú de ayuda'),
            ('clear', 'Limpiar pantalla'),
            ('list tools', 'Listar herramientas'),
            ('list categories', 'Listar categorías'),
            ('setip', 'Configurar $IP para comandos'),
            ('seturl', 'Configurar $URL para comandos'),
            ('refresh', 'Recargar herramientas o configuración'),
            ('edit', 'Editar archivo de herramienta'),
            ('exit', 'Salir del programa')
        ]
        self.command_to_alias = {
            'help': 'h',
            'clear': 'c',
            'list tools': 'lt',
            'list categories': 'lc',
            'setip': 'si',
            'seturl': 'su',
            'refresh': 'r',
            'edit': 'e',
            'exit': 'q'
        }

    def _normalize_url(self, url: str) -> str:
        parsed = urllib.parse.urlparse(url)
        path = re.sub(r'/+', '/', parsed.path.lstrip('/'))
        scheme = parsed.scheme if parsed.scheme in ['http', 'https'] else 'http'
        normalized = urllib.parse.urlunparse((
            scheme,
            parsed.netloc.lower(),
            path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        return normalized

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        word = document.get_word_before_cursor()
        word_normalized = normalize_text(word)
        completions = []

        parts = text.strip().split()
        is_setip_arg = len(parts) >= 2 and normalize_text(parts[0]) in ['setip', 'si']
        is_seturl_arg = len(parts) >= 2 and normalize_text(parts[0]) in ['seturl', 'su']
        is_refresh_arg = len(parts) >= 2 and normalize_text(parts[0]) in ['refresh', 'r']
        is_edit_arg = len(parts) >= 2 and normalize_text(parts[0]) in ['edit', 'e']

        if not (is_setip_arg or is_seturl_arg or is_refresh_arg or is_edit_arg):
            for cmd, meta in self.internal_commands:
                alias = self.command_to_alias.get(cmd, cmd[:2])
                display_text = f'[{alias}] {cmd}'
                if word_normalized in normalize_text(cmd):
                    completions.append((0, Completion(
                        cmd,
                        start_position=-len(word),
                        display=HTML(display_text),
                        display_meta=meta,
                        style='class:completion-menu.completion'
                    )))
                if word_normalized in normalize_text(alias):
                    completions.append((0, Completion(
                        cmd,
                        start_position=-len(word),
                        display=HTML(display_text),
                        display_meta=meta,
                        style='class:completion-menu.completion'
                    )))

        if is_refresh_arg:
            if word_normalized in normalize_text('config'):
                completions.append((0, Completion(
                    'config',
                    start_position=-len(word),
                    display=HTML('🔄 config'),
                    display_meta='Reiniciar configuración (IP y URL)',
                    style='class:completion-menu.completion'
                )))

        if is_edit_arg:
            for tool in self.original_tools:
                if word_normalized in normalize_text(tool):
                    match_priority = 0 if normalize_text(tool) == word_normalized else 1
                    category = self.tool_to_category.get(tool, "")
                    completions.append((match_priority, Completion(
                        tool,
                        start_position=-len(word),
                        display=HTML(f'🔧 {tool}'),
                        display_meta=f'Categoría: {category}' if category else 'Sin categoría',
                        style='class:completion-menu.tool-completion'
                    )))

        if not (is_setip_arg or is_seturl_arg or is_refresh_arg or is_edit_arg):
            for orig_cat, norm_cat in zip(self.original_categories, self.categories_normalized):
                if word_normalized in norm_cat:
                    match_priority = 0 if norm_cat == word_normalized else 1
                    completions.append((match_priority, Completion(
                        orig_cat,
                        start_position=-len(word),
                        display=HTML(f'📂 {orig_cat}'),
                        display_meta=f'{len(self.tools_by_category.get(orig_cat, []))} herramientas',
                        style='class:completion-menu.category-completion'
                    )))

        if not (is_setip_arg or is_seturl_arg or is_refresh_arg or is_edit_arg):
            for orig_tool, norm_tool in zip(self.original_tools, self.tools_normalized):
                if word_normalized in norm_tool:
                    match_priority = 0 if norm_tool == word_normalized else 1
                    category = self.tool_to_category.get(orig_tool, "")
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
                normalized_url = self._normalize_url(url)
                if word_normalized in normalize_text(normalized_url):
                    match_priority = 0 if normalize_text(normalized_url) == word_normalized else 1
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
            print(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} Error al parsear argumentos{Colors.RESET}")
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
        print(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} Error en la ejecución: {e}{Colors.RESET}")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"{Colors.RESET}", end="")
        print(f"\n\t\t\t{Colors.RED}{Colors.BOLD}H4PPY H4CK1NG{Colors.RESET}")
        sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"{Colors.RESET}", end="")
        print(f"\n\t\t\t{Colors.RED}{Colors.BOLD}H4PPY H4CK1NG{Colors.RESET}")
        sys.exit(0)
