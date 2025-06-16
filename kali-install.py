#!/usr/bin/env python3

import os
import sys
import subprocess
import shutil
import zipfile
import tempfile
import hashlib
import requests
from time import sleep
import pwd
import tty
import termios

def ensure_colorama():
    try:
        import colorama
        from colorama import init, Fore, Style
        init()
        return Fore, Style
    except ImportError:
        print("Instalando dependencia colorama...")
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                venv_path = os.path.join(temp_dir, "venv")
                subprocess.run([sys.executable, "-m", "venv", venv_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                pip_path = os.path.join(venv_path, "bin", "pip")
                subprocess.run([pip_path, "install", "colorama>=0.4.6"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run([os.path.join(venv_path, "bin", "python")] + sys.argv, check=True)
                sys.exit(0)
            except subprocess.CalledProcessError as e:
                print(f"Error: No se pudo instalar colorama: {e}", file=sys.stderr)
                sys.exit(1)

Fore, Style = ensure_colorama()
os.system("clear")

GREEN, YELLOW, RED, CYAN, BLUE = Fore.GREEN, Fore.YELLOW, Fore.RED, Fore.CYAN, Fore.BLUE
RESET, BOLD = Style.RESET_ALL, Style.BRIGHT

__version__ = "0.9.3"

VENV_DIR = "/opt/searchCommand_venv"
BIN_DIR = "/usr/local/bin"
SCRIPT_DIR = "/usr/bin"
SEARCHCOMMAND_URL = "https://raw.githubusercontent.com/SkyW4r33x/searchCommand/main/searchCommand.py"
REFERENCESTUFF_URL = "https://raw.githubusercontent.com/SkyW4r33x/searchCommand/main/referencestuff.zip"

PYTHON_SCRIPTS = ["searchCommand.py", "gtfsearch.py"]

def create_gradient_banner():
    banner_lines = [
        " ┌─┐┌─┐┌─┐┬─┐┌─┐┬ ┬╔═╗┌─┐┌┬┐┌┬┐┌─┐┌┐┌┌┬┐",
        " └─┐├┤ ├─┤├┬┘│  ├─┤║  │ │││││││├─┤│││ ││",
        " └─┘└─┘┴ ┴┴└─└─┘┴ ┴╚═╝└─┘┴ ┴┴ ┴┴ ┴┘└┘─┴┘",
    ]
    signature = f"╚═[ SkyW4r33x | v.{__version__} ]═╝"
    gradient_colors = ["\033[38;5;75m", "\033[38;5;79m", "\033[38;5;85m"]
    banner_width = len(banner_lines[0])
    gradient_banner = "\n".join(f"{gradient_colors[i]}{line}{RESET}" for i, line in enumerate(banner_lines))
    centered_signature = " " * ((banner_width - len(signature)) // 2) + f"{gradient_colors[-1]}{signature}{RESET}"
    return f"{gradient_banner}\n{centered_signature}\n"

BANNER = create_gradient_banner()
SEPARATOR = f"\n{BLUE}══════[ 🔍 Instalador searchCommand ]══════{RESET}\n"

def log_info(msg, secondary=False, delay=0):
    prefix = f"{CYAN}[INFO]{RESET}" if secondary else f"{GREEN}[INFO]{RESET}"
    print(f"{prefix} {msg}", flush=True)
    if delay:
        sleep(delay)

def log_warn(msg, delay=0):
    print(f"\n{YELLOW}[WARN]{RESET} {msg}", flush=True)
    if delay:
        sleep(delay)

def log_error(msg, exit_code=1):
    print(f"\n{RED}[ERROR]{RESET} {msg}", file=sys.stderr)
    sys.exit(exit_code)

def check_requirements():
    if not shutil.which("python3"):
        log_error("Python3 no está instalado. Instálalo con 'sudo apt install python3'.")
    if os.geteuid() != 0:
        log_error("Este script requiere privilegios de root. Usa sudo.")
    if not shutil.which("wget"):
        log_error("wget no está instalado. Instálalo con 'sudo apt install wget'.")
    global SUDO_USER
    SUDO_USER = os.environ.get("SUDO_USER")
    if not SUDO_USER:
        log_error("No se pudo determinar el usuario que ejecutó sudo.")

check_requirements()

def compute_file_hash(file_path, hash_type="md5"):
    hasher = hashlib.md5() if hash_type == "md5" else hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except OSError:
        return None

def is_installed():
    paths = [
        os.path.join(BIN_DIR, "searchCommand.py"),
        os.path.join(BIN_DIR, "gtfsearch.py"),
        VENV_DIR,
    ]
    return any(os.path.exists(path) for path in paths)

def has_referencestuff():
    return os.path.exists(os.path.expanduser(f"~{SUDO_USER}/referencestuff"))

def cleanup(full_cleanup=True):
    paths = [
        os.path.join(BIN_DIR, "searchCommand.py"),
        os.path.join(BIN_DIR, "gtfsearch.py"),
        os.path.join(SCRIPT_DIR, "searchCommand"),
        VENV_DIR,
    ]
    if full_cleanup:
        paths.append(os.path.expanduser(f"~{SUDO_USER}/referencestuff"))
        paths.append(os.path.expanduser(f"~{SUDO_USER}/.data"))  # Agregar .data a la limpieza
    
    for path in paths:
        if os.path.exists(path):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                log_info(f"Eliminado {path}", secondary=True, delay=0.2)
            except OSError as e:
                log_error(f"No se pudo limpiar {path}: {e}")

def get_input(prompt, default=""):
    print(f"\n{BLUE}>>{RESET} {prompt} [{default}]: ", end="", flush=True)
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        user_input = ""
        while True:
            char = sys.stdin.read(1)
            if char in ("\n", "\r"):
                print()  # Nueva línea
                print("\r", end="", flush=True)  # Resetear cursor
                return user_input or default
            elif char == "\x03":
                raise KeyboardInterrupt
            elif char == "\x7f":
                if user_input:
                    user_input = user_input[:-1]
                    print("\b \b", end="", flush=True)
            elif char == "\033":
                sys.stdin.read(2)
            elif char.isprintable():
                user_input += char
                print(char, end="", flush=True)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def get_user_choice():
    while True:
        try:
            os.system("clear")
            print(BANNER)
            print(f"\n{GREEN}[1]{RESET} Instalar searchCommand completo (searchCommand + gtfsearch + referencestuff + .data)")
            print(f"{GREEN}[2]{RESET} Actualizar solo scripts de Python (searchCommand + gtfsearch)")  
            print(f"{GREEN}[3]{RESET} Actualizar solo referencestuff")
            print(f"{GREEN}[4]{RESET} Desinstalar searchCommand")
            print(f"{GREEN}[5]{RESET} Salir (predeterminado)")
            choice = get_input("Selecciona una opción", default="5")
            if choice in ["1", "2", "3", "4", "5"]:
                return choice
            os.system("clear")
            log_warn("Opción inválida. Usa 1, 2, 3, 4 o 5.", delay=1)
        except KeyboardInterrupt:
            log_info("Interrumpido. Saliendo...", delay=0.5)
            sys.exit(0)

def install_referencestuff(zip_path, dest_dir, pw):
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                if zip_ref.testzip() is not None:
                    log_error("El archivo referencestuff.zip está corrupto.")
                temp_extract = os.path.join(temp_dir, "extracted")
                zip_ref.extractall(temp_extract)
        except zipfile.BadZipFile:
            log_error("El archivo referencestuff.zip no es un ZIP válido.")
        
        extracted_ref = os.path.join(temp_extract, "referencestuff")
        if not os.path.exists(extracted_ref):
            log_error("El ZIP no contiene el directorio 'referencestuff'.")
        
        if os.path.exists(dest_dir):
            log_warn(f"El directorio {dest_dir} ya existe. ¿Sobreescribir? (s/N)", delay=0.5)
            if get_input("s/N", default="N").lower() != "s":
                log_info("Instalación de referencestuff cancelada.", secondary=True, delay=0.2)
                return False
        
        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir)
            log_info(f"Directorio existente {dest_dir} eliminado.", secondary=True, delay=0.2)
        
        shutil.move(extracted_ref, dest_dir)
        for root, dirs, files in os.walk(dest_dir):
            for d in dirs:
                os.chmod(os.path.join(root, d), 0o755)
                os.chown(os.path.join(root, d), pw.pw_uid, pw.pw_gid)
            for f in files:
                os.chmod(os.path.join(root, f), 0o644)
                os.chown(os.path.join(root, f), pw.pw_uid, pw.pw_gid)
        os.chmod(dest_dir, 0o750)
        os.chown(dest_dir, pw.pw_uid, pw.pw_gid)
        
        stat_info = os.stat(dest_dir)
        if stat_info.st_uid != pw.pw_uid or stat_info.st_gid != pw.pw_gid:
            log_error(f"El directorio {dest_dir} tiene un propietario incorrecto (esperado: {SUDO_USER}).")
        log_info(f"referencestuff instalado en {dest_dir}.", secondary=True, delay=0.2)
        return True

def install_data_folder(src_dir, dest_dir, pw):
    try:
        if os.path.exists(dest_dir):
            log_warn(f"El directorio {dest_dir} ya existe. ¿Sobreescribir? (s/N)", delay=0.5)
            if get_input("s/N", default="N").lower() != "s":
                log_info("Instalación de .data cancelada.", secondary=True, delay=0.2)
                return False
            shutil.rmtree(dest_dir)
            log_info(f"Directorio existente {dest_dir} eliminado.", secondary=True, delay=0.2)

        shutil.copytree(src_dir, dest_dir)
        log_info(f"Carpeta .data copiada a {dest_dir}.", secondary=True, delay=0.2)

        for root, dirs, files in os.walk(dest_dir):
            for d in dirs:
                os.chmod(os.path.join(root, d), 0o755)
                os.chown(os.path.join(root, d), pw.pw_uid, pw.pw_gid)
            for f in files:
                os.chmod(os.path.join(root, f), 0o644)
                os.chown(os.path.join(root, f), pw.pw_uid, pw.pw_gid)
        os.chmod(dest_dir, 0o750)
        os.chown(dest_dir, pw.pw_uid, pw.pw_gid)

        stat_info = os.stat(dest_dir)
        if stat_info.st_uid != pw.pw_uid or stat_info.st_gid != pw.pw_gid:
            log_error(f"El directorio {dest_dir} tiene un propietario incorrecto (esperado: {SUDO_USER}).")
        log_info(f".data instalado en {dest_dir}.", secondary=True, delay=0.2)
        return True
    except OSError as e:
        log_error(f"No se pudo instalar .data: {e}")
        return False

def update_referencestuff(pw):
    dest_dir = os.path.expanduser(f"~{SUDO_USER}/referencestuff")
    log_info("Descargando referencestuff.zip...", delay=0.2)
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, "referencestuff.zip")
        try:
            subprocess.run(["wget", "--quiet", "-O", zip_path, REFERENCESTUFF_URL], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            log_info("referencestuff.zip descargado correctamente.", secondary=True, delay=0.2)
        except subprocess.CalledProcessError:
            log_error("No se pudo descargar referencestuff.zip. Verifica tu conexión.")
        
        return install_referencestuff(zip_path, dest_dir, pw)

def download_temp_file(url, temp_file_path):
    try:
        with requests.get(url, stream=True, timeout=30) as response:
            response.raise_for_status()
            with open(temp_file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        return True
    except requests.RequestException as e:
        log_error(f"No se pudo descargar desde {url}: {e}")
        return False

def install_search_command(full_install=True):
    required_files = PYTHON_SCRIPTS + ["requirements.txt"] if full_install else []
    if full_install:
        required_files.append("referencestuff.zip")
        if not os.path.exists(".data"):
            log_error("Carpeta .data no encontrada en el directorio actual.")
    
    pw = pwd.getpwnam(SUDO_USER)
    
    for script in PYTHON_SCRIPTS:
        if not os.path.exists(script):
            log_error(f"Archivo {script} no encontrado en el directorio actual.")
    
    if full_install:
        for file in required_files:
            if not os.path.exists(file):
                log_error(f"Archivo {file} no encontrado en el directorio actual.")
    
    existing_scripts = [script for script in PYTHON_SCRIPTS if os.path.exists(os.path.join(BIN_DIR, script))]
    if full_install and existing_scripts:
        script_list = ", ".join(existing_scripts)
        log_warn(f"Los siguientes scripts ya existen: {script_list}. ¿Sobreescribir? (s/N)", delay=0.5)
        if get_input("s/N", default="N").lower() != "s":
            log_info("Instalación cancelada.", delay=0.5)
            sys.exit(0)
    elif not full_install:
        log_info("Verificando actualizaciones para scripts de Python...", delay=0.2)
        scripts_to_update = []
        for script in PYTHON_SCRIPTS:
            local_path = script
            target_path = os.path.join(BIN_DIR, script)
            
            if not os.path.exists(target_path):
                log_error(f"No se encuentra el archivo instalado en {target_path}.")
                return
            
            if compute_file_hash(local_path) != compute_file_hash(target_path):
                scripts_to_update.append(script)
        
        if not scripts_to_update:
            log_info("No hay actualizaciones disponibles para los scripts de Python.", secondary=True, delay=0.2)
            return
        
        script_list = ", ".join(scripts_to_update)
        log_info(f"¡Actualizaciones encontradas para: {script_list}!", secondary=True, delay=0.2)
        log_warn("¿Deseas proceder con la actualización? (s/N)", delay=0.5)
        if get_input("s/N", default="N").lower() != "s":
            log_info("Actualización de scripts cancelada.", secondary=True, delay=0.2)
            return
    
    print(SEPARATOR)
    log_info(f"Iniciando {'instalación completa' if full_install else 'actualización de scripts'}...", delay=0.2)

    try:
        if full_install:
            cleanup(full_cleanup=False)
        
        for script in PYTHON_SCRIPTS:
            target_script = os.path.join(BIN_DIR, script)
            shutil.copy(script, target_script)
            os.chmod(target_script, 0o755)
            os.chown(target_script, pw.pw_uid, pw.pw_gid)
            log_info(f"{script} {'instalado' if full_install else 'actualizado'} en {target_script}.", secondary=True, delay=0.2)

        if full_install:
            dest_dir = os.path.expanduser(f"~{SUDO_USER}/referencestuff")
            if install_referencestuff("referencestuff.zip", dest_dir, pw):
                log_info("referencestuff instalado correctamente.", secondary=True, delay=0.2)

            data_src = ".data"
            data_dest = os.path.expanduser(f"~{SUDO_USER}/.data")
            if install_data_folder(data_src, data_dest, pw):
                log_info(".data instalado correctamente.", secondary=True, delay=0.2)

            if os.path.exists(VENV_DIR):
                log_warn(f"El entorno virtual en {VENV_DIR} ya existe. ¿Regenerar? (s/N)", delay=0.5)
                if get_input("s/N", default="N").lower() == "s":
                    shutil.rmtree(VENV_DIR)
                    subprocess.run(["python3", "-m", "venv", VENV_DIR], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    log_info("Entorno virtual regenerado.", secondary=True, delay=0.2)
                else:
                    log_info("Reutilizando entorno virtual existente.", secondary=True, delay=0.2)
            else:
                log_info(f"Creando entorno virtual en {VENV_DIR}...", delay=0.2)
                subprocess.run(["python3", "-m", "venv", VENV_DIR], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            pip_path = os.path.join(VENV_DIR, "bin", "pip")
            with open("requirements.txt", "r") as f:
                req_packages = [line.strip().split("#")[0].strip() for line in f if line.strip() and not line.strip().startswith("#")]
            
            for i, package in enumerate(req_packages, 1):
                max_len = max(len(p) for p in req_packages) + 20
                msg = f"Instalando {package} ({i}/{len(req_packages)})"
                print(f"{GREEN}[INFO]{RESET} {msg:<{max_len}}", end="", flush=True)
                subprocess.run([pip_path, "install", package], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"\r{GREEN}[INFO]{RESET} {msg:<{max_len}} {GREEN}✓{RESET}")

            script_content = f"#!/bin/sh\nexec {VENV_DIR}/bin/python3 {os.path.join(BIN_DIR, 'searchCommand.py')} \"$@\""
            script_path = os.path.join(SCRIPT_DIR, "searchCommand")
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_script:
                temp_script.write(script_content)
                temp_script_path = temp_script.name
            
            shutil.move(temp_script_path, script_path)
            os.chmod(script_path, 0o755)
            log_info(f"Script ejecutable creado en {script_path}.", secondary=True, delay=0.2)

        print(SEPARATOR)
        action = "Instalación completa" if full_install else "Actualización completada"
        log_info(f"{action} crack 😎", delay=0.2)
        print(f"[{GREEN}✓{RESET}] Usa {BLUE}searchCommand{RESET} desde la terminal (desde /usr/bin)")
        print(f"[{GREEN}✓{RESET}] Scripts Python en {BIN_DIR}: {', '.join(PYTHON_SCRIPTS)}")
        print(f"[{RED}#{RESET}] Hecha con corazón, en un mundo de mierda.")
        print(f"\n\t\t{BOLD}{RED}H4PPY H4CK1NG{RESET}\n")

    except (subprocess.CalledProcessError, OSError) as e:
        log_error(f"Falló la {'instalación' if full_install else 'actualización'}: {str(e)}")
        cleanup(full_cleanup=False)

def uninstall_search_command():
    print(SEPARATOR)
    if not is_installed():
        log_info("searchCommand no está instalado. No hay nada que desinstalar.", delay=0.5)
        print(SEPARATOR)
        return
    log_info("Iniciando desinstalación...", delay=0.2)
    full_cleanup = False
    if has_referencestuff() or os.path.exists(os.path.expanduser(f"~{SUDO_USER}/.data")):
        log_warn("¿Eliminar también los directorios referencestuff y .data? (s/N)", delay=0.5)
        full_cleanup = get_input("s/N", default="N").lower() == "s"
        print("\r", end="", flush=True)
    log_info("Limpiando archivos existentes...", delay=0.5)
    cleanup(full_cleanup=full_cleanup)
    print(SEPARATOR)
    log_info("Desinstalación completa crack 😎", delay=0.2)

def main():
    choice = get_user_choice()
    if choice == "1":
        install_search_command(full_install=True)
    elif choice == "2":
        install_search_command(full_install=False)
    elif choice == "3":
        print(SEPARATOR)
        log_info("Iniciando actualización de referencestuff...", delay=0.2)
        if update_referencestuff(pwd.getpwnam(SUDO_USER)):
            log_info("referencestuff actualizado correctamente.", delay=0.2)
        print(SEPARATOR)
    elif choice == "4":
        uninstall_search_command()
    else:
        log_info("Saliendo...", delay=0.5)

if __name__ == "__main__":
    main()
