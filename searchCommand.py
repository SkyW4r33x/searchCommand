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
útiles. Incluye una interfaz intuitiva, validación mejorada y visualización optimizada.
Espero que sea de su agrado y recuerda siempre...

                        H4PPY H4CK1NG
═══════════════════════════════════════════════════════════════════
"""

import argparse
import difflib
import hashlib
import ipaddress
import itertools
import os
import re
import requests
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import unicodedata
import urllib.parse
import warnings
from collections import defaultdict
from prompt_toolkit import PromptSession
from prompt_toolkit.application import get_app
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.styles import Style
from requests.adapters import HTTPAdapter
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
from urllib3.exceptions import InsecureRequestWarning
from urllib3.util.retry import Retry
from fuzzywuzzy import process

warnings.filterwarnings("ignore", category=InsecureRequestWarning, module="urllib3")

__version__ = "2.8.2"

if os.name == 'nt':
    print(f"{Colors.RED}{Colors.BOLD}[-]{Colors.RESET} Este programa está diseñado para Linux/macOS. En Windows, usa WSL para mejor compatibilidad.")

class Config:
    ROOT_DIR_NAME = 'referencestuff'
    UPDATE_URL = 'https://raw.githubusercontent.com/SkyW4r33x/searchCommand/refs/heads/main/searchCommand.py'
    DEFAULT_PERMS = 0o750
    MAX_FILE_SIZE = 10 * 1024 * 1024

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
    CYAN = "\033[36m"

def normalize_text(text: str) -> str:
    normalized = ''.join(
        c for c in unicodedata.normalize('NFD', text.lower())
        if unicodedata.category(c) != 'Mn' and (c.isalnum() or c.isspace())
    ).strip()
    return normalized if normalized else None

class SearchCommand:
    def __init__(self):
        import pwd
        user_home = os.path.expanduser('~')
        if os.geteuid() == 0 and 'SUDO_USER' in os.environ:
            sudo_user = os.environ.get('SUDO_USER')
            try:
                pwd.getpwnam(sudo_user)
                user_home = os.path.expanduser(f"~{sudo_user}")
            except KeyError:
                print(f"{Colors.RED}[-]{Colors.RESET} SUDO_USER inválido. Usando directorio del usuario actual.")
    
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

        try:
            self._create_directory(self.root_dir)
            self._check_directory_permissions(self.root_dir)
        except PermissionError as e:
            self._handle_exception(f"Error de permisos en el directorio", e, True)

        self._load_tools()
        self._init_prompt_session()

    def _create_directory(self, directory: str):
        try:
            if not os.path.exists(directory):
                os.makedirs(directory, mode=Config.DEFAULT_PERMS)
                if os.access(directory, os.W_OK):
                    os.chown(directory, os.getuid(), os.getgid())
                else:
                    raise PermissionError(f"No se tienen permisos para modificar {directory}")
        except PermissionError as e:
            self._handle_exception(f"Error de permisos en el directorio", e, True)

    def _init_prompt_session(self):
        try:
            self.prompt_style = Style.from_dict({
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
        except ValueError as e:
            self._handle_exception(f"Error al configurar estilos", e, True)

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
            self._handle_exception(f"Error al inicializar autocompletado", e, True)

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
                print(f"{Colors.GREEN}✔ {Colors.RESET}Herramientas recargadas exitosamente.\n")
            except (FileNotFoundError, PermissionError, ValueError) as e:
                self._handle_exception(f"Error al recargar herramientas", e)
            event.app.renderer.reset()
            event.app.invalidate()

        @kb.add(Keys.ControlE)
        def edit_last_tool(event):
            if self.last_query and self.last_query in self.tool_to_file:
                editor = self._get_safe_editor()
                if not editor:
                    print(f"{Colors.RED}[-]{Colors.RESET} No se encontró un editor compatible (nano, vim, vi).")
                    return
                try:
                    file_path = self._sanitize_file_path(self.tool_to_file[self.last_query])
                    subprocess.run([editor, file_path], check=True)
                    print(f"{Colors.GREEN}[✔] {Colors.RESET}Abriendo {Colors.GREEN}{self.last_query}{Colors.RESET} en {editor}. Usa {Colors.BLUE}refresh{Colors.RESET} para recargar cambios.\n")
                except (subprocess.CalledProcessError, FileNotFoundError, ValueError) as e:
                    print(f"{Colors.RED}[-]{Colors.RESET} Error al abrir el editor: {e}")
            else:
                print(f"{Colors.RED}[-]{Colors.RESET} No hay herramienta reciente para editar. Usa 'edit <herramienta>'.")
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

    def _get_safe_editor(self):
        allowed_editors = {
            'nano': '/bin/nano',
            'vim': '/usr/bin/vim',
            'vi': '/usr/bin/vi'
        }
        editor = os.environ.get('EDITOR', 'nano')
        editor_name = os.path.basename(editor).split()[0]
        return allowed_editors.get(editor_name) if os.path.exists(allowed_editors.get(editor_name, '')) else None

    def _sanitize_file_path(self, file_path: str) -> str:
        abs_path = os.path.abspath(file_path)
        root_abs = os.path.abspath(self.root_dir)
        if not abs_path.startswith(root_abs + os.sep):
            raise ValueError(f"Ruta inválida: {file_path}")
        if os.path.islink(file_path):
            raise ValueError(f"Enlaces simbólicos no permitidos: {file_path}")
        return abs_path

    def _calculate_sha256(self, file_path: str) -> str:
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except (FileNotFoundError, PermissionError) as e:
            self._handle_exception(f"Error al calcular hash SHA-256", e)
            return ""

    def update_script(self, restore: bool = False):
        script_path = "/usr/local/bin/searchCommand.py"
        backup_path = "/usr/local/bin/searchCommand.py.back"
        temp_path = "/tmp/searchCommand.py.temp"
        url = Config.UPDATE_URL

        if os.geteuid() != 0:
            print(f"{Colors.RED}[-]{Colors.RESET} Se requieren permisos de root para actualizar.\n")
            return

        if not os.access(os.path.dirname(script_path), os.W_OK):
            print(f"{Colors.RED}[-]{Colors.RESET} Permisos insuficientes para escribir en {os.path.dirname(script_path)}.")
            return

        if restore:
            if not os.path.exists(backup_path):
                print(f"{Colors.RED}[-]{Colors.RESET} No hay una versión anterior disponible para restaurar.")
                return
            try:
                if not os.access(script_path, os.W_OK):
                    print(f"{Colors.RED}[-]{Colors.RESET} Permisos insuficientes para escribir en {script_path}.")
                    return
                print(f"{Colors.BLUE}[ℹ] {Colors.RESET}Restaurando versión anterior...")
                shutil.move(backup_path, script_path)
                os.chmod(script_path, Config.DEFAULT_PERMS)
                os.chown(script_path, 0, os.stat(script_path).st_gid)
                print(f"{Colors.GREEN}[✔] {Colors.RESET}Restauración completada correctamente.")
                print(f"{Colors.BLUE}[ℹ] {Colors.RESET}Reinicia tu shell para aplicar los cambios.\n")
            except (PermissionError, OSError) as e:
                print(f"{Colors.RED}[-]{Colors.RESET} Error al restaurar el script: {e}")
            return

        try:
            socket.gethostbyname("github.com")
        except socket.gaierror:
            print(f"{Colors.RED}[-]{Colors.RESET} No hay conexión a Internet.")
            return

        try:
            session = requests.Session()
            retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
            session.mount('https://', HTTPAdapter(max_retries=retries))
            print(f"{Colors.BLUE}[ℹ] {Colors.RESET}Descargando la versión más reciente...")
            response = session.get(url, timeout=10, verify=True)
            response.raise_for_status()
            with open(temp_path, "wb") as f:
                f.write(response.content)
            time.sleep(1)

            current_hash = self._calculate_sha256(script_path)
            new_hash = self._calculate_sha256(temp_path)

            if not current_hash or not new_hash:
                print(f"{Colors.RED}[-]{Colors.RESET} Error al comparar versiones. Actualización cancelada.")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return

            if current_hash == new_hash:
                print(f"{Colors.GREEN}[✔] {Colors.RESET}Ya tienes la versión más reciente.\n")
                os.remove(temp_path)
                return

            print(f"{Colors.GREEN}[+] {Colors.RESET}Actualización disponible.")

            if not os.access(script_path, os.W_OK):
                print(f"{Colors.RED}[-]{Colors.RESET} Permisos insuficientes para escribir en {script_path}.")
                os.remove(temp_path)
                return

            if os.path.exists(script_path):
                print(f"{Colors.BLUE}[ℹ] {Colors.RESET}Respaldando versión actual...")
                try:
                    if os.path.exists(backup_path):
                        try:
                            os.remove(backup_path)
                        except PermissionError:
                            print(f"{Colors.RED}[-]{Colors.RESET} No se pudo eliminar el respaldo existente en {backup_path}.")
                            os.remove(temp_path)
                            return
                    shutil.copy2(script_path, backup_path)
                    os.chmod(backup_path, Config.DEFAULT_PERMS)
                    os.chown(backup_path, 0, os.stat(backup_path).st_gid)
                except PermissionError as e:
                    print(f"{Colors.RED}[-]{Colors.RESET} Error al crear respaldo en {backup_path}: {e}.")
                    os.remove(temp_path)
                    return

            shutil.move(temp_path, script_path)
            os.chmod(script_path, Config.DEFAULT_PERMS)
            os.chown(script_path, 0, os.stat(script_path).st_gid)
            print(f"{Colors.GREEN}[✔] {Colors.RESET}Actualización completada correctamente.")
            print(f"{Colors.BLUE}[ℹ] {Colors.RESET}Reinicia tu shell para aplicar los cambios.\n")
        except requests.exceptions.SSLError as e:
            print(f"{Colors.RED}[-]{Colors.RESET} Error de verificación SSL: {e}.")
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except requests.RequestException as e:
            print(f"{Colors.RED}[-]{Colors.RESET} Error al descargar la actualización: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except (PermissionError, OSError) as e:
            print(f"{Colors.RED}[-]{Colors.RESET} Error al actualizar el script: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def _handle_exception(self, error_msg: str, e: Exception, exit_on_error: bool = False):
        print(f"{Colors.RED}[-]{Colors.RESET} {error_msg}: {e}")
        if exit_on_error:
            sys.exit(1)

    def _clear_screen(self):
        try:
            if os.name in ('posix', 'nt'):
                os.system('clear' if os.name == 'posix' else 'cls')
            else:
                print(f"{Colors.RED}[-]{Colors.RESET} Limpieza de pantalla no soportada en este sistema.")
        except OSError as e:
            print(f"{Colors.RED}[-]{Colors.RESET} Error al limpiar pantalla: {e}")

    def _read_tool_file(self, file_path: str) -> List[str]:
        try:
            if os.path.getsize(file_path) > Config.MAX_FILE_SIZE:
                print(f"{Colors.RED}[-]{Colors.RESET} Archivo {file_path} excede el tamaño máximo permitido.")
                return []
            abs_path = self._sanitize_file_path(file_path)
            if not os.path.exists(abs_path):
                return []
            with open(abs_path, 'r', encoding='utf-8') as file:
                lines = [line.rstrip('\n') for line in file]
            return lines if lines else []
        except (PermissionError, UnicodeDecodeError, ValueError) as e:
            print(f"{Colors.RED}[-]{Colors.RESET} Error al leer el archivo {file_path}: {e}")
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

    def spinner(self, msg="Cargando...", chars=['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']):
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

    def _load_tools(self):
        self._clear_screen()
        try:
            self._parse_directory_structure()
        except (FileNotFoundError, ValueError) as e:
            print(f"{Colors.RED}[-] Error: {e}{Colors.RESET}")

    def _parse_directory_structure(self):
        if not os.path.exists(self.root_dir):
            raise FileNotFoundError(f"Directorio no encontrado en {self.root_dir}")

        self.tools_by_category = {}
        self.categories = {}
        self.tool_to_file = {}
        self.tool_to_category = {}
        seen_tools = set()
        duplicate_count = 0

        title = " CARGA DE HERRAMIENTAS "
        term_width = min(shutil.get_terminal_size().columns, 50)
        side_width = (term_width - len(title) - 4) // 2
        total_width = len(title) + 2 * side_width + 4
        spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

        def print_loading_box(spinner_char, clear_lines=0):
            if clear_lines > 0:
                sys.stdout.write(f"\033[{clear_lines}F\033[J")
            sys.stdout.write(f"{Colors.BLUE}{Colors.BOLD}╓{'─' * side_width}╢{Colors.WHITE}{title}{Colors.BLUE}╟{'─' * side_width}╖{Colors.RESET}\n")
            sys.stdout.write(f"  {Colors.GREEN}┃ {spinner_char}{Colors.RESET} Procesando...{' ' * (total_width - 20)}{Colors.RESET}\n")
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
            for category in sorted(os.listdir(self.root_dir)):
                category_path = os.path.join(self.root_dir, category)
                if not os.path.isdir(category_path):
                    continue

                tools = []
                for tool_file in sorted(os.listdir(category_path)):
                    if tool_file.endswith('.txt'):
                        tool_name = tool_file[:-4]
                        if tool_name in seen_tools:
                            sys.stdout.write(f"\r{' ' * total_width}\r{Colors.RED}[-]{Colors.RESET} Herramienta duplicada: '{tool_name}' en {category}. Ignorada.\n")
                            sys.stdout.flush()
                            time.sleep(0.5)
                            continue
                        seen_tools.add(tool_name)
                        tools.append(tool_name)
                        tool_path = os.path.join(category_path, tool_file)
                        self.tool_to_file[tool_name] = tool_path
                        self.tool_to_category[tool_name] = category

                if tools:
                    self.categories[category] = tools
                    self.tools_by_category[category] = tools

            elapsed_time = time.time() - start_time
            if elapsed_time < 1:
                time.sleep(1 - elapsed_time)

        finally:
            spinner_thread.join()

        if not self.categories:
            raise ValueError("No se encontraron categorías con herramientas válidas en el directorio")

        total_tools = sum(len(tools) for tools in self.tools_by_category.values())
        total_categories = len(self.categories)

        sys.stdout.write(f"\033[3F\033[J")
        sys.stdout.write(f"{Colors.BLUE}{Colors.BOLD}╓{'─' * side_width}╢{Colors.WHITE}{title}{Colors.BLUE}╟{'─' * side_width}╖{Colors.RESET}\n")
        sys.stdout.write(f"  {Colors.GREEN}┃ 📂{Colors.RESET} Categorías: {Colors.CYAN}{total_categories:>3}{Colors.RESET}\n")
        sys.stdout.write(f"  {Colors.GREEN}┃ 🔧{Colors.RESET} Herramientas: {Colors.CYAN}{total_tools:>3}{Colors.RESET}\n")
        if duplicate_count > 0:
            sys.stdout.write(f"  {Colors.YELLOW}┃ ⚠️{Colors.RESET} Dup: {Colors.YELLOW}{duplicate_count:>3}{Colors.RESET}\n")
        sys.stdout.write(f"{Colors.BLUE}{Colors.BOLD}╙{'─' * (total_width - 2)}╜{Colors.RESET}\n\n")
        sys.stdout.flush()
        time.sleep(1)

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
            if query_normalized is None:
                return []
            results = []
            self.search_mode = search_type
            items = self.categories if search_type == "category" else self.tool_to_file
            item_normalized = {normalize_text(k): k for k in items.keys() if normalize_text(k)}
            
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
            self._handle_exception(f"Error al buscar por {search_type}", e)
            return []

    def search_by_category(self, query: str) -> List[str]:
        return self._search_generic(query, "category")

    def search_by_tool(self, query: str) -> List[str]:
        return self._search_generic(query, "tool")

    def show_help(self):
        self._clear_screen()
        total_width = 79
        title = " AYUDA DE COMANDOS "
        side_width = (total_width - len(title) - 4) // 2

        print(f"{Colors.BLUE}{Colors.BOLD}╓{'─' * side_width}╢{Colors.WHITE}{title}{Colors.BLUE}╟{'─' * side_width}╖{Colors.RESET}\n")

        print(f"  {Colors.GREEN}{'Comando'.ljust(22)}{'Alias'.ljust(12)}{'Descripción'.ljust(40)}{Colors.RESET}")
        print(f"  {'─' * 22}{'─' * 12}{'─' * 40}")

        commands = [
            ("<herramienta>", "", "Buscar una herramienta (ej: NMAP)"),
            ("<categoría>", "", "Buscar una categoría (ej: RECONOCIMIENTO)"),
            ("help", "h", "Mostrar este menú de ayuda"),
            ("list tools", "lt", "Listar todas las herramientas"),
            ("list categories", "lc", "Listar todas las categorías"),
            ("setip <IP>", "si", "Configurar $IP"),
            ("seturl <URL>", "su", "Configurar $URL"),
            ("edit <herramienta>", "e", "Editar herramienta"),
            ("refresh [config]", "r", "Recargar herramientas o limpiar config"),
            ("update [-r]", "u", "Actualizar o restaurar versión anterior"),
            ("clear", "c", "Limpiar la pantalla"),
            ("exit", "q", "Salir del programa"),
        ]

        for cmd, alias, desc in commands:
            print(f"  {Colors.GREEN}➜ {Colors.RESET}{cmd.ljust(21)}{Colors.GRAY}{alias.ljust(11)}{Colors.WHITE}{desc.ljust(40)}{Colors.RESET}")

        print("")

        print(f"  {Colors.GREEN}{'Atajo'.ljust(22)}{'Descripción'.ljust(40)}{Colors.RESET}")
        print(f"  {'─' * 22}{'─' * 40}")

        shortcuts = [
            ("Ctrl + L", "Limpiar la pantalla"),
            ("Ctrl + T", "Listar herramientas rápidamente"),
            ("Ctrl + K", "Listar categorías rápidamente"),
            ("Ctrl + E", "Editar última herramienta buscada"),
            ("Ctrl + R", "Recargar herramientas"),
            ("Ctrl + C", "Salir inmediatamente"),
        ]

        for shortcut, desc in shortcuts:
            print(f"  {Colors.GREEN}• {Colors.RESET}{shortcut.ljust(20)}{Colors.WHITE}{desc.ljust(40)}{Colors.RESET}")

        print(f"\n{Colors.BLUE}{Colors.BOLD}╙{'─' * (total_width - 2)}╜{Colors.RESET}\n")

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
            self._handle_exception(f"Error al colorear comando", e)
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
        term_width = shutil.get_terminal_size().columns 

        print(f"\n{Colors.BLUE}{Colors.BOLD} {title}{Colors.RESET}\n")
        
        if not results:
            print(f"{Colors.RED}[-]{Colors.RESET} No se encontraron resultados.")
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

    def _strip_ansi_codes(self, text: str) -> str:
        ansi_escape = re.compile(r'\033\[[0-9;]*[mK]')
        return ansi_escape.sub('', text)

    def _display_in_columns(self, items: List[str], title: str, item_color: str, items_per_page: int = 20, compact_mode: bool = False, item_type: str = "herramientas"):
        self._clear_screen()
        total_items = len(items)
        item_type_label = "categorías" if item_type == "categorías" else "herramientas"
        
        try:
            term_width = shutil.get_terminal_size().columns
        except Exception:
            term_width = 80

        max_item_length = max(len(self._strip_ansi_codes(item)) for item in items) + 6 if items else 10  
        icon = "📂" if item_type == "categorías" else "🔧"
        
        if compact_mode:
            print(f"{Colors.BLUE}{Colors.BOLD}{title}{Colors.RESET}")
            print(f"{item_color}Total: {total_items} {item_type_label}{Colors.RESET}")
            if not items:
                print(f"{Colors.RED}[-] No hay {item_type_label} disponibles.{Colors.RESET}")
            else:
                for idx, item in enumerate(items, 1):
                    print(f"{item_color}{idx}. {icon} {item}{Colors.RESET}".center(term_width))
            print(f"Usa {Colors.GREEN}Tab{Colors.RESET} para autocompletar, {Colors.GREEN}Enter{Colors.RESET} para seleccionar, {Colors.GREEN}q{Colors.RESET} para salir".center(term_width))
        else:
            min_col_width = max_item_length + 4
            max_columns = min(8, total_items) if item_type == "categorías" else total_items
            num_columns = min(max_columns, max(1, term_width // min_col_width))
            col_width = max(min_col_width, (term_width - 20) // num_columns)
            rows = (total_items + num_columns - 1) // num_columns

            print(f"{Colors.BLUE}{Colors.BOLD}╓{'─' * (term_width - 2)}╖{Colors.RESET}")
            print(f" {Colors.BOLD}{title.center(term_width - 2)}{Colors.RESET}")
            print(f"{Colors.BLUE}╟{'─' * (term_width - 2)}╢{Colors.RESET}")

            if not items:
                print(f"{Colors.RED}[-] No hay {item_type_label} disponibles.{Colors.RESET}".center(term_width))
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
                            max_display_length = min(len(self._strip_ansi_codes(item_text)), col_width - 8)
                            formatted_item = f"{item_color}{item_num}. {icon} {Colors.WHITE}{item_text[:max_display_length]}{'...' if len(item_text) > max_display_length else ''}{Colors.RESET}"
                            visible_length = len(self._strip_ansi_codes(formatted_item))
                            padding = max(0, col_width - visible_length)
                            row_content += formatted_item + " " * padding
                        else:
                            row_content += " " * col_width
                    print(row_content.rstrip())

            print(f"{Colors.BLUE}╟{'─' * (term_width - 2)}╢{Colors.RESET}")
            footer_text = f"Usa {Colors.GREEN}Tab{Colors.RESET} para autocompletar, {Colors.GREEN}Enter{Colors.RESET} para seleccionar, {Colors.GREEN}q{Colors.RESET} para salir"

            footer_plain = f"Usa Tab para autocompletar, Enter para seleccionar, q para salir"
            footer_padding = max(0, (term_width - len(footer_plain)) // 2)
            print(" " * footer_padding + footer_text)
            print(f"{Colors.BLUE}{Colors.BOLD}╙{'─' * (term_width - 2)}╜{Colors.RESET}\n")

    def _list_categories(self):
        categories = sorted(self.categories.keys())
        self._display_in_columns(categories, "📂 CATEGORÍAS DISPONIBLES", Colors.ORANGE, item_type="categorías")

    def _list_tools(self):
        tools = sorted([tool for tools in self.tools_by_category.values() for tool in tools if tool in self.tool_to_file])
        if not tools:
            print(f"{Colors.RED}[-] No se encontraron herramientas válidas.{Colors.RESET}")
            return
        self._display_in_columns(tools, "🔧 HERRAMIENTAS DISPONIBLES", Colors.AQUA, item_type="herramientas")

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
            'e': 'edit',
            'u': 'update'
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
            'edit': 'edit',
            'update': 'update'
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
            if len(args) > 255:
                print(f"{Colors.RED}[-] {Colors.RESET}Entrada demasiado larga. Máximo 255 caracteres.")
                return True
            if not args:
                if self.ip_value:
                    print(f"{Colors.BLUE}[ℹ] {Colors.RESET}Valor actual de $IP: {Colors.GREEN}{self.ip_value}{Colors.RESET}")
                else:
                    print(f"{Colors.BLUE}[ℹ] {Colors.RESET}No se ha configurado un valor para $IP")
                print(f"{Colors.GREEN}[+] {Colors.RESET}Uso: {Colors.GREEN}setip <IP|dominio> (ejemplo: setip 192.168.1.1 o setip example.com)")
                print(f"{Colors.GREEN}[+] {Colors.RESET}Para limpiar: {Colors.GREEN}setip clear{Colors.RESET}")
                print(f"{Colors.BLUE}[ℹ] {Colors.RESET}La IP/dominio se usará en comandos con $IP.\n")
                return True
            elif args.lower() == 'clear':
                self.ip_value = None
                print(f"{Colors.GREEN}[✔] {Colors.RESET}Correctamente restablecido. Los comandos usarán {Colors.GREEN}$IP{Colors.RESET} por defecto.\n")
                return True
            else:
                try:
                    ipaddress.ip_address(args)
                    self.ip_value = args
                    try:
                        socket.gethostbyname(args)
                        print(f"{Colors.GREEN}[✔] {Colors.RESET}$IP resuelve correctamente: {args}")
                    except socket.gaierror:
                        print(f"{Colors.ORANGE}[-] {Colors.RESET}$IP no resuelve en DNS, pero se acepta: {args}")
                except ValueError:
                    domain_pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
                    if re.match(domain_pattern, args) and 1 < len(args) <= 255:
                        try:
                            socket.gethostbyname(args)
                            self.ip_value = args
                            print(f"{Colors.GREEN}[✔] {Colors.RESET}Dominio resuelve correctamente: {args}")
                        except socket.gaierror:
                            print(f"{Colors.ORANGE}[-] {Colors.RESET}Dominio no resuelve en DNS, pero se acepta: {args}")
                            self.ip_value = args
                    else:
                        print(f"{Colors.RED}[-] {Colors.RESET}Entrada inválida. Debe ser una IP válida (ej: 192.168.1.1) o dominio (ejemplo: example.com).")
                        return True
                if self.ip_value and args not in self.recent_ips:
                    self.recent_ips.append(args)
                    if len(self.recent_ips) > 5:
                        self.recent_ips.pop(0)
                print(f"{Colors.GREEN}[✔] {Colors.RESET}$IP configurado como: {Colors.GREEN}{args}{Colors.RESET}\n")
                return True
        elif command == 'seturl':
            if len(args) > 2048:
                print(f"{Colors.RED}[-] {Colors.RESET}Entrada demasiado larga. Máximo 2048 caracteres.")
                return True
            if not args:
                if self.url_value:
                    print(f"{Colors.BLUE}[ℹ] {Colors.RESET}Valor actual de $URL: {Colors.GREEN}{self.url_value}{Colors.RESET}")
                else:
                    print(f"{Colors.BLUE}[ℹ] {Colors.RESET}No se ha configurado un valor para $URL")
                print(f"{Colors.GREEN}[+] {Colors.RESET}Uso: {Colors.GREEN}seturl <URL> (ejemplo: seturl http://example.com)")
                print(f"{Colors.GREEN}[+] {Colors.RESET}Para limpiar: {Colors.GREEN}seturl clear{Colors.RESET}")
                print(f"{Colors.BLUE}[ℹ] {Colors.RESET}La URL se usará en comandos con $URL.\n")
                return True
            elif args.lower() == 'clear':
                self.url_value = None
                print(f"{Colors.GREEN}[✔] {Colors.RESET}Correctamente restablecido. Los comandos usarán {Colors.GREEN}$URL{Colors.RESET} por defecto.\n")
                return True
            else:
                try:
                    parsed = urlparse(args)
                    if parsed.scheme not in ['http', 'https']:
                        print(f"{Colors.RED}[-] {Colors.RESET}Solo se permiten URLs con protocolo http o https.\n")
                        return True
                    if not parsed.netloc:
                        print(f"{Colors.RED}[-] {Colors.RESET}Entrada inválida. Debe ser una URL válida (ej: http://example.com).")
                        return True
                    try:
                        socket.gethostbyname(parsed.netloc)
                    except socket.gaierror:
                        print(f"{Colors.RED}[-] {Colors.RESET}El dominio {parsed.netloc} no es válido o no se resuelve. Verifica la URL.")
                        return True
                    self.url_value = args
                    normalized_url = self._normalize_url(args)
                    try:
                        session = requests.Session()
                        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
                        session.mount('https://', HTTPAdapter(max_retries=retries))
                        response = session.head(normalized_url, timeout=3, allow_redirects=True, verify=True)
                        if response.status_code < 400:
                            print(f"{Colors.GREEN}[✔] {Colors.RESET}$URL accesible: {Colors.BLUE}{args}{Colors.RESET} (Código: {response.status_code})")
                        else:
                            print(f"{Colors.ORANGE}[-] {Colors.RESET}URL no accesible (código: {response.status_code}), pero se agregó con éxito")
                    except requests.exceptions.SSLError:
                        print(f"{Colors.RED}[-] {Colors.RESET}URL inválida o certificado SSL no verificable. Verifica el dominio.")
                        return True
                    except requests.RequestException:
                        print(f"{Colors.ORANGE}[-] {Colors.RESET}URL no accesible, pero se agregó con éxito")
                    if args not in self.recent_urls:
                        self.recent_urls.append(args)
                        if len(self.recent_urls) > 5:
                            self.recent_urls.pop(0)
                    print(f"{Colors.GREEN}[✔] {Colors.RESET}$URL configurado como: {Colors.GREEN}{args}{Colors.RESET}\n")
                except ValueError:
                    print(f"{Colors.RED}[-] {Colors.RESET}Entrada inválida. Debe ser una URL válida (ej: http://example.com).")
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
                    print(f"{Colors.GREEN}[✔] {Colors.RESET}Herramientas recargadas exitosamente.\n")
                except (FileNotFoundError, PermissionError, ValueError) as e:
                    self._handle_exception(f"Error al recargar herramientas", e)
            return True
        elif command == 'edit':
            if not args:
                if self.last_query and self.last_query in self.tool_to_file:
                    editor = self._get_safe_editor()
                    if not editor:
                        print(f"{Colors.RED}[-]{Colors.RESET} No se encontró un editor compatible (nano, vim, vi).")
                        return True
                    try:
                        file_path = self._sanitize_file_path(self.tool_to_file[self.last_query])
                        subprocess.run([editor, file_path], check=True)
                        print(f"{Colors.GREEN}[✔] {Colors.RESET}Abriendo {self.last_query} en {editor}. Usa 'refresh' para recargar cambios.")
                    except (subprocess.CalledProcessError, FileNotFoundError, ValueError) as e:
                        print(f"{Colors.RED}[-]{Colors.RESET} Error al abrir el editor: {e}")
                else:
                    self._display_edit_help()
            else:
                tool = args.strip()
                if tool in self.tool_to_file:
                    editor = self._get_safe_editor()
                    if not editor:
                        print(f"{Colors.RED}[-]{Colors.RESET} No se encontró un editor compatible (nano, vim, vi).")
                        return True
                    try:
                        file_path = self._sanitize_file_path(self.tool_to_file[tool])
                        subprocess.run([editor, file_path], check=True)
                        print(f"{Colors.GREEN}[✔] {Colors.RESET}Abriendo {tool} en {editor}. Usa 'refresh' para recargar cambios.")
                    except (subprocess.CalledProcessError, FileNotFoundError, ValueError) as e:
                        print(f"{Colors.RED}[-]{Colors.RESET} Error al abrir el editor: {e}")
                else:
                    self._clear_screen()
                    print(f"{Colors.RED}[-]{Colors.RESET} Herramienta '{tool}' no encontrada.")
                    self._display_edit_help()
            return True
        elif command == 'update':
            restore_flag = args.strip().lower() == '-r'
            self.update_script(restore=restore_flag)
            return True
        return False

    def _handle_resize(self, signum, frame):
        self._clear_screen()
        self.print_header()
        app = get_app()
        app.renderer.reset()
        app._redraw()

    def interactive_menu(self):
        self._clear_screen()
        self.print_header()

        try:
            signal.signal(signal.SIGWINCH, self._handle_resize)
            
            while True:
                try:
                    query = self.prompt_session.prompt().strip()

                    if query.lower() in ['exit', 'q']:
                        print(f"\n\t\t\t{Colors.RED}{Colors.BOLD}H4PPY H4CK1NG{Colors.RESET}")
                        break
                    
                    if not query:
                        print(f"{Colors.BLUE}ℹ{Colors.RESET}  Ingresa un comando, herramienta o {Colors.GREEN}help{Colors.RESET} para ayuda.\n")
                        self.last_command_success = True
                        continue
                    
                    if self._handle_internal_command(query):
                        self.last_command_success = True
                        self.last_query = ""
                        continue
                    
                    query_normalized = normalize_text(query)
                    if query_normalized is None:
                        print(f"{Colors.RED}[✘]{Colors.RESET} Consulta inválida.\n")
                        self.last_command_success = False
                        self.last_query = ""
                        continue

                    category_results = self.search_by_category(query)
                    if category_results:
                        self._display_results(
                            category_results, 
                            f"{Colors.BLUE}{Colors.BOLD}📂 Categoría: {Colors.WHITE}{query.upper()}{Colors.RESET}\n"
                        )
                        self.last_command_success = True
                        continue

                    tool_results = self.search_by_tool(query)
                    if tool_results:
                        self._display_results(
                            tool_results, 
                            f"{Colors.ORANGE}{Colors.BOLD}🔧 Herramienta: {Colors.WHITE}{query.upper()}{Colors.RESET}\n"
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
                    
                    print(f"{Colors.RED}{Colors.BOLD}[✘] {Colors.RESET}Sin resultados para: {Colors.WHITE}{query}")
                    
                    if valid_suggestions:
                        print(f"{Colors.LIGHT_BLUE}💡 ¿Quizás quisiste decir?{Colors.RESET}")
                        for suggestion in valid_suggestions:
                            print(f"   {Colors.GREEN}▶{Colors.RESET} {Colors.CYAN}{suggestion}{Colors.RESET}")
                    else:
                        print(f"{Colors.ORANGE}[!]{Colors.RESET} No hay sugerencias disponibles.")
                    
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

class EnhancedCompleter(Completer):
    def __init__(self, categories: List[str], tools: List[str], tools_by_category: Dict[str, List[str]], 
                 recent_ips: List[str], recent_urls: List[str], tool_to_category: Dict[str, str], 
                 tool_to_file: Dict[str, str]):
        self.original_categories = categories
        self.original_tools = [tool for tool in tools if tool in tool_to_file]
        self.categories_normalized = [normalize_text(cat) for cat in categories if normalize_text(cat)]
        self.tools_normalized = [normalize_text(tool) for tool in self.original_tools if normalize_text(tool)]
        self.tools_by_category = tools_by_category
        self.recent_ips = recent_ips
        self.recent_urls = recent_urls
        self.tool_to_category = tool_to_category
        self.tool_to_file = tool_to_file

        self._completion_cache = {}
        self._last_cache_clear = time.time()
        
        self.usage_stats = defaultdict(int)
        
        self._build_search_indices()

        if not categories or not self.original_tools or not tools_by_category:
            print(f"{Colors.RED}[-]{Colors.RESET} Error: Datos de autocompletado vacíos o inválidos")

        self._setup_internal_commands()

    def _build_search_indices(self):
        self.tool_ngram_index = defaultdict(list)
        self.category_ngram_index = defaultdict(list)
        
        for tool in self.original_tools:
            for ngram in self._generate_ngrams(normalize_text(tool), 2):
                self.tool_ngram_index[ngram].append(tool)
        
        for category in self.original_categories:
            for ngram in self._generate_ngrams(normalize_text(category), 2):
                self.category_ngram_index[ngram].append(category)

    def _generate_ngrams(self, text: str, n: int = 2) -> set:
        if not text or len(text) < n:
            return {text} if text else set()
        return {text[i:i+n] for i in range(len(text) - n + 1)}

    def _fuzzy_score(self, query: str, target: str) -> float:
        if not query or not target:
            return 0.0
            
        if query == target:
            return 1.0
            
        if target.startswith(query):
            return 0.9 + (len(query) / len(target)) * 0.1
            
        query_ngrams = self._generate_ngrams(query, 2)
        target_ngrams = self._generate_ngrams(target, 2)
        
        if not query_ngrams or not target_ngrams:
            return 0.0
            
        intersection = len(query_ngrams & target_ngrams)
        union = len(query_ngrams | target_ngrams)
        jaccard = intersection / union if union > 0 else 0.0
        
        consecutive_bonus = self._consecutive_match_bonus(query, target)
        
        return min(0.89, jaccard * 0.7 + consecutive_bonus * 0.3)

    def _consecutive_match_bonus(self, query: str, target: str) -> float:
        if not query or not target:
            return 0.0
            
        max_consecutive = 0
        current_consecutive = 0
        
        i = j = 0
        while i < len(query) and j < len(target):
            if query[i] == target[j]:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
                i += 1
            else:
                current_consecutive = 0
            j += 1
            
        return max_consecutive / len(query) if len(query) > 0 else 0.0

    def _setup_internal_commands(self):
        self.internal_commands = [
            ('help', 'Mostrar menú de ayuda'),
            ('clear', 'Limpiar pantalla'),
            ('list tools', 'Listar herramientas'),
            ('list categories', 'Listar categorías'),
            ('setip', 'Configurar $IP para comandos'),
            ('seturl', 'Configurar $URL para comandos'),
            ('refresh', 'Recargar herramientas o configuración'),
            ('edit', 'Editar archivo de herramienta'),
            ('update', 'Actualizar script o restaurar con -r'),
            ('exit', 'Salir del programa')
        ]
        self.command_to_alias = {
            'help': 'h', 'clear': 'c', 'list tools': 'lt', 'list categories': 'lc',
            'setip': 'si', 'seturl': 'su', 'refresh': 'r', 'edit': 'e', 
            'update': 'u', 'exit': 'q'
        }

    def _normalize_url(self, url: str) -> str:
        try:
            parsed = urllib.parse.urlparse(url)
            path = re.sub(r'/+', '/', parsed.path.lstrip('/'))
            scheme = parsed.scheme if parsed.scheme in ['http', 'https'] else 'http'
            return urllib.parse.urlunparse((
                scheme, parsed.netloc.lower(), path,
                parsed.params, parsed.query, parsed.fragment
            ))
        except Exception:
            return url

    def _parse_command_context(self, text: str) -> Dict[str, bool]:
        parts = text.strip().split()
        if len(parts) < 2:
            return {}
        
        first_cmd = normalize_text(parts[0])
        return {
            'is_setip_arg': first_cmd in ['setip', 'si'],
            'is_seturl_arg': first_cmd in ['seturl', 'su'],
            'is_refresh_arg': first_cmd in ['refresh', 'r'],
            'is_edit_arg': first_cmd in ['edit', 'e'],
            'is_update_arg': first_cmd in ['update', 'u']
        }

    def _clear_cache_if_needed(self):
        current_time = time.time()
        if current_time - self._last_cache_clear > 300:
            self._completion_cache.clear()
            self._last_cache_clear = current_time

    def _get_cached_completions(self, cache_key: str):
        self._clear_cache_if_needed()
        return self._completion_cache.get(cache_key)

    def _cache_completions(self, cache_key: str, completions: List):
        if len(self._completion_cache) < 100:
            self._completion_cache[cache_key] = completions

    def _smart_match_tools(self, query: str) -> List[Tuple[float, str, str]]:
        results = []
        query_norm = normalize_text(query)
        query_ngrams = self._generate_ngrams(query_norm, 2)
        
        candidates = set()
        for ngram in query_ngrams:
            candidates.update(self.tool_ngram_index.get(ngram, []))
        
        for tool in candidates:
            tool_norm = normalize_text(tool)
            score = self._fuzzy_score(query_norm, tool_norm)
            if score > 0.3:
                usage_bonus = min(0.1, self.usage_stats[tool] * 0.01)
                final_score = score + usage_bonus
                category = self.tool_to_category.get(tool, "")
                results.append((final_score, tool, category))
        
        return sorted(results, key=lambda x: x[0], reverse=True)

    def _smart_match_categories(self, query: str) -> List[Tuple[float, str]]:
        results = []
        query_norm = normalize_text(query)
        
        if not query_norm:
            return results
            
        for category in self.original_categories:
            cat_norm = normalize_text(category)
            if not cat_norm:
                continue
                
            score = self._fuzzy_score(query_norm, cat_norm)
            if score > 0.3:
                results.append((score, category))
                
        return sorted(results, key=lambda x: x[0], reverse=True)

    def _add_internal_command_completions(self, word: str, word_normalized: str, completions: List):
        for cmd, meta in self.internal_commands:
            alias = self.command_to_alias.get(cmd, cmd[:2])
            
            cmd_score = self._fuzzy_score(word_normalized, normalize_text(cmd))
            alias_score = self._fuzzy_score(word_normalized, normalize_text(alias))
            
            if cmd_score > 0.3 or alias_score > 0.3:
                score = max(cmd_score, alias_score)
                display_text = f'[{alias}] {cmd}'

                completions.append((-score, Completion( 
                    cmd,
                    start_position=-len(word),
                    display=HTML(display_text),
                    display_meta=meta,
                    style='class:completion-menu.completion'
                )))

    def _add_smart_tool_completions(self, word: str, word_normalized: str, completions: List, limit: int = 15):
        matches = self._smart_match_tools(word_normalized)
        
        for i, (score, tool, category) in enumerate(matches[:limit]):
            priority = 1.0 - score 
            completions.append((priority, Completion(
                tool,
                start_position=-len(word),
                display=HTML(f'🔧 {tool}'),
                display_meta=f'Categoría: {category}' if category else '',
                style='class:completion-menu.tool-completion'
            )))

    def _add_smart_category_completions(self, word: str, word_normalized: str, completions: List, limit: int = 10):
        matches = self._smart_match_categories(word_normalized)
        
        for score, category in matches[:limit]:
            priority = 1.0 - score
            tool_count = len(self.tools_by_category.get(category, []))
            completions.append((priority, Completion(
                category,
                start_position=-len(word),
                display=HTML(f'📂 {category}'),
                display_meta=f'{tool_count} herramientas',
                style='class:completion-menu.category-completion'
            )))

    def _add_smart_recent_completions(self, word: str, word_normalized: str, 
                                    items: List[str], icon: str, meta: str, completions: List):
        scored_items = []
        for item in items:
            item_norm = normalize_text(self._normalize_url(item) if 'URL' in meta else item)
            if item_norm:
                score = self._fuzzy_score(word_normalized, item_norm)
                if score > 0.3:
                    scored_items.append((score, item))
        
        for score, item in sorted(scored_items, key=lambda x: x[0], reverse=True)[:10]:
            priority = 1.0 - score
            completions.append((priority, Completion(
                item,
                start_position=-len(word),
                display=HTML(f'{icon} {item}'),
                display_meta=meta,
                style='class:completion-menu.tool-completion'
            )))

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        word = document.get_word_before_cursor()
        word_normalized = normalize_text(word)
        
        if word_normalized is None or len(word_normalized) == 0:
            return

        cache_key = f"{text}:{word}"
        cached = self._get_cached_completions(cache_key)
        if cached:
            for completion in cached:
                yield completion
            return

        completions = []
        context = self._parse_command_context(text)
        is_command_arg = any(context.values())

        if not is_command_arg:
            self._add_internal_command_completions(word, word_normalized, completions)
            self._add_smart_category_completions(word, word_normalized, completions)
            self._add_smart_tool_completions(word, word_normalized, completions)
        elif context.get('is_refresh_arg') and word_normalized in normalize_text('config'):
            completions.append((0, Completion('config', start_position=-len(word),
                display=HTML('🔄 config'), display_meta='Reiniciar configuración (IP y URL)',
                style='class:completion-menu.completion')))
        elif context.get('is_update_arg') and word_normalized in normalize_text('-r'):
            completions.append((0, Completion('-r', start_position=-len(word),
                display=HTML('-r'), display_meta='Restaurar versión anterior del script',
                style='class:completion-menu.completion')))
        elif context.get('is_edit_arg'):
            self._add_smart_tool_completions(word, word_normalized, completions)
        elif context.get('is_setip_arg'):
            self._add_smart_recent_completions(word, word_normalized, self.recent_ips, 
                '🌐', 'IP o dominio reciente', completions)
        elif context.get('is_seturl_arg'):
            self._add_smart_recent_completions(word, word_normalized, self.recent_urls, 
                '🌐', 'URL reciente', completions)

        seen = set()
        final_completions = []
        for priority, completion in sorted(completions, key=lambda x: x[0]):
            if completion.text not in seen:
                seen.add(completion.text)
                final_completions.append(completion)
                self.usage_stats[completion.text] += 1

        self._cache_completions(cache_key, final_completions)

        for completion in final_completions:
            yield completion

def main():
    parser = argparse.ArgumentParser(description="Herramienta de búsqueda de comandos para pentesting.")
    parser.add_argument('-q', '--query', help="Consulta para buscar directamente y salir.")
    
    try:
        args = parser.parse_args()
    except SystemExit as e:
        if e.code != 0:
            print(f"{Colors.RED}[-]{Colors.RESET} Error al parsear argumentos")
            sys.exit(1)
        sys.exit(0)

    try:
        search_tool = SearchCommand()
        print()
        if args.query:
            search_tool.run_query(args.query)
        else:
            search_tool.interactive_menu()
    except (FileNotFoundError, PermissionError, ValueError) as e:
        print(f"{Colors.RED}[-]{Colors.RESET} Error en la ejecución: {e}")
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
