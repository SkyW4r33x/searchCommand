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
        temp_dir = tempfile.mkdtemp()
        try:
            subprocess.run([sys.executable, "-m", "venv", os.path.join(temp_dir, "venv")], check=True)
            pip_path = os.path.join(temp_dir, "venv", "bin", "pip")
            subprocess.run([pip_path, "install", "colorama>=0.4.6"], check=True)
            subprocess.run([os.path.join(temp_dir, "venv", "bin", "python")] + sys.argv, check=True)
            sys.exit(0)
        except subprocess.CalledProcessError as e:
            print(f"Error: No se pudo instalar colorama: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

Fore, Style = ensure_colorama()
os.system("clear")

GREEN, YELLOW, RED, CYAN, BLUE, MAGENTA = Fore.GREEN, Fore.YELLOW, Fore.RED, Fore.CYAN, Fore.BLUE, Fore.MAGENTA
RESET, BOLD = Style.RESET_ALL, Style.BRIGHT

__version__ = "0.6"

VENV_DIR = "/opt/searchCommand_venv"
BIN_DIR = "/usr/local/bin"
SCRIPT_DIR = "/usr/bin"
SEARCHCOMMAND_URL = "https://raw.githubusercontent.com/SkyW4r33x/searchCommand/main/searchCommand.py"
REFERENCESTUFF_URL = "https://raw.githubusercontent.com/SkyW4r33x/searchCommand/main/referencestuff.zip"

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
    signature_color = "\033[38;5;85m"
    centered_signature = " " * ((banner_width - len(signature)) // 2) + f"{signature_color}{signature}{RESET}"
    return f"{gradient_banner}\n{centered_signature}\n"

BANNER = create_gradient_banner()
SEPARATOR = f"\n{BLUE}══════[ 🔍 Instalador searchCommand ]══════{RESET}\n"

def log_info(msg, secondary=False, delay=0):
    prefix = f"{CYAN}[INFO]{RESET}" if secondary else f"{GREEN}[INFO]{RESET}"
    print(f"{prefix} {msg}")
    if delay:
        sleep(delay)

def log_warn(msg, delay=0):
    print(f"\n{YELLOW}[WARN]{RESET} {BOLD}{msg}{RESET}", flush=True)
    if delay:
        sleep(delay)

def log_error(msg, exit_code=1):
    print(f"\n{RED}[ERROR]{RESET} {BOLD}{msg}{RESET}", file=sys.stderr)
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

def compute_md5(file_path):
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except OSError:
        return None

def cleanup(full_cleanup=True):
    log_info("Limpiando archivos existentes...", delay=0.5)
    paths = [
        os.path.join(BIN_DIR, "searchCommand.py"),
        os.path.join(SCRIPT_DIR, "searchCommand"),
        VENV_DIR,
    ]
    if full_cleanup:
        paths.append(os.path.expanduser(f"~{SUDO_USER}/referencestuff"))
    
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
    print(f"\n{BLUE}>>{RESET} {prompt} [{BOLD}{default}{RESET}]: ", end="", flush=True)
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        user_input = ""
        while True:
            char = sys.stdin.read(1)
            if char in ("\n", "\r"):
                print()
                return user_input or default
            elif char == "\x03":
                raise KeyboardInterrupt
            elif char == "\x7f":
                if user_input:
                    user_input = user_input[:-1]
                    print("\b \b", end="", flush=True)
            elif char == "\033":
                sys.stdin.read(2)
                continue
            elif char.isprintable():
                user_input += char
                print(char, end="", flush=True)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        print()

def get_user_choice():
    while True:
        try:
            os.system("clear")
            print(BANNER)
            print(f"\n{BOLD}{GREEN}[1]{RESET} Instalar searchCommand (completo con referencestuff)")
            print(f"{BOLD}{GREEN}[2]{RESET} Actualizar solo searchCommand")
            print(f"{BOLD}{GREEN}[3]{RESET} Actualizar solo referencestuff")
            print(f"{BOLD}{GREEN}[4]{RESET} Desinstalar searchCommand")
            print(f"{BOLD}{GREEN}[5]{RESET} Salir (predeterminado)")
            choice = get_input("Selecciona una opción", default="5")
            if choice in ["1", "2", "3", "4", "5"]:
                return choice
            os.system("clear")
            log_warn("Opción inválida. Usa 1, 2, 3, 4 o 5.", delay=0.1)
        except KeyboardInterrupt:
            print()
            log_info("Interrupción detectada. Saliendo...", delay=0.5)
            sys.exit(0)

def install_referencestuff_from_zip(zip_path, destino, pw):
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
            log_error("El ZIP no contiene directorio 'referencestuff'.")
        
        if os.path.exists(destino):
            log_warn(f"El directorio {destino} ya existe. ¿Sobreescribir? (S/n)", delay=0.5)
            if get_input("S/n", default="S").lower() != "s":
                log_info("Instalación de referencestuff cancelada.", secondary=True, delay=0.2)
                return False
        
        if os.path.exists(destino):
            try:
                shutil.rmtree(destino)
                log_info(f"Directorio existente {destino} eliminado.", secondary=True, delay=0.2)
            except OSError as e:
                log_error(f"No se pudo eliminar {destino}: {e}")
        
        try:
            shutil.move(extracted_ref, destino)
            for root, dirs, files in os.walk(destino):
                for d in dirs:
                    dir_path = os.path.join(root, d)
                    os.chmod(dir_path, 0o755)
                    os.chown(dir_path, pw.pw_uid, pw.pw_gid)
                for f in files:
                    file_path = os.path.join(root, f)
                    os.chmod(file_path, 0o644)
                    os.chown(file_path, pw.pw_uid, pw.pw_gid)
            os.chmod(destino, 0o750)
            os.chown(destino, pw.pw_uid, pw.pw_gid)
            stat_info = os.stat(destino)
            if stat_info.st_uid != pw.pw_uid or stat_info.st_gid != pw.pw_gid:
                log_error(f"El directorio {destino} no tiene el propietario correcto (esperado: {SUDO_USER}).")
            log_info(f"referencestuff instalado en {BOLD}{YELLOW}{destino}{RESET}.", secondary=True, delay=0.2)
            return True
        except OSError as e:
            log_error(f"Error al instalar referencestuff: {e}")
            return False

def update_referencestuff(pw):
    destino = os.path.expanduser(f"~{SUDO_USER}/referencestuff")
    log_info("Descargando referencestuff.zip desde el repositorio...", delay=0.2)
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, "referencestuff.zip")
        try:
            subprocess.run(["wget", "--quiet", "-O", zip_path, REFERENCESTUFF_URL], check=True)
            log_info("referencestuff.zip descargado correctamente.", secondary=True, delay=0.2)
        except subprocess.CalledProcessError:
            log_error("No se pudo descargar referencestuff.zip. Verifica tu conexión.")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                if zip_ref.testzip() is not None:
                    log_error("El archivo referencestuff.zip está corrupto.")
                log_info("Archivo ZIP verificado.", secondary=True, delay=0.2)
                temp_extract = os.path.join(temp_dir, "extracted")
                zip_ref.extractall(temp_extract)
        except IOError:
            log_error("El archivo referencestuff.zip no es un ZIP válido.")
        
        extracted_ref = os.path.join(temp_extract, "referencestuff")
        if not os.path.exists(extracted_ref):
            log_error("El ZIP no contiene directorio 'referencestuff'.")
        
        if os.path.exists(destino):
            log_warn(f"El directorio {destino} ya existe. ¿Sobreescribir? (S/n)", delay=0.5)
            if get_input("S/n", default="S").lower() != "s":
                log_info("Actualización de referencestuff cancelada.", secondary=True, delay=0.2)
                return
        
        if os.path.exists(destino):
            try:
                shutil.rmtree(destino)
                log_info(f"Directorio existente {destino} eliminado.", secondary=True, delay=0.2)
            except OSError as e:
                log_error(f"No se pudo eliminar {destino}: {e}")
        
        try:
            shutil.move(extracted_ref, destino)
            for root, dirs, files in os.walk(destino):
                for d in dirs:
                    dir_path = os.path.join(root, d)
                    os.chmod(dir_path, 0o755)
                    os.chown(dir_path, pw.pw_uid, pw.pw_gid)
                for f in files:
                    file_path = os.path.join(root, f)
                    os.chmod(file_path, 0o644)
                    os.chown(file_path, pw.pw_uid, pw.pw_gid)
            os.chmod(destino, 0o750)
            os.chown(destino, pw.pw_uid, pw.pw_gid)
            stat_info = os.stat(destino)
            if stat_info.st_uid != pw.pw_uid or stat_info.st_gid != pw.pw_gid:
                log_error(f"El directorio {destino} no tiene el propietario correcto (esperado: {SUDO_USER}).")
            log_info(f"referencestuff actualizado en {BOLD}{YELLOW}{destino}{RESET}.", secondary=True, delay=0.2)
        except OSError as e:
            log_error(f"Error al actualizar referencestuff: {e}")

def download_temp_file(url, temp_file_path):
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        with open(temp_file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except requests.exceptions.RequestException as e:
        log_error(f"Error downloading file from {url}: {e}")
        return False

def install_search_command(full_install=True):
    required_files = ["searchCommand.py", "requirements.txt"]
    if full_install:
        required_files.append("referencestuff.zip")
    pw = pwd.getpwnam(SUDO_USER)
    
    for file in required_files:
        if not os.path.exists(file):
            log_error(f"Archivo {BOLD}{RED}{file}{RESET} no encontrado en el directorio actual.")
    
    target_script = os.path.join(BIN_DIR, "searchCommand.py")
    if full_install and os.path.exists(target_script):
        log_warn(f"searchCommand.py ya existe en {BOLD}{YELLOW}{BIN_DIR}{RESET}. ¿Sobreescribir? (S/n)", delay=0.5)
        if get_input("S/n", default="S").lower() != "s":
            log_info("Instalación cancelada.", delay=0.5)
            sys.exit(0)
    elif not full_install:
        log_info("Buscando actualizaciones de searchCommand.py...", delay=0.2)
        temp_file = tempfile.mktemp(suffix=".py")
        if not download_temp_file(SEARCHCOMMAND_URL, temp_file):
            log_error("No se pudo descargar searchCommand.py desde el repositorio.")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return
        
        if not os.path.exists(target_script):
            log_error(f"No se encuentra el archivo local en {target_script}.")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return
        
        downloaded_md5 = compute_md5(temp_file)
        existing_md5 = compute_md5(target_script)
        
        if downloaded_md5 == existing_md5:
            log_info("No se encontraron actualizaciones disponibles para searchCommand.py.", secondary=True, delay=0.2)
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return
        else:
            log_info("¡Se encontraron actualizaciones para searchCommand.py!", secondary=True, delay=0.2)
            log_warn("¿Deseas proceder con la actualización? (S/n)", delay=0.5)
            if get_input("S/n", default="S").lower() == "s":
                try:
                    log_info("Actualizando searchCommand.py...", secondary=True, delay=0.2)
                    shutil.copy2(temp_file, target_script)
                    os.chmod(target_script, 0o755)
                    os.chown(target_script, pw.pw_uid, pw.pw_gid)
                    stat_info = os.stat(target_script)
                    if stat_info.st_uid != pw.pw_uid or stat_info.st_gid != pw.pw_gid:
                        log_error(f"Archivo {target_script} tiene propietario incorrecto (esperado: {SUDO_USER}).")
                    log_info(f"searchCommand.py actualizado en {BOLD}{YELLOW}{target_script}{RESET}.", secondary=True, delay=0.2)
                except OSError as e:
                    log_error(f"Error al actualizar searchCommand.py: {e}")
                finally:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
            else:
                log_info("Actualización de searchCommand.py cancelada.", secondary=True, delay=0.2)
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                return
    
    print(SEPARATOR)
    log_info(f"Iniciando {'instalación completa' if full_install else 'actualización de searchCommand'}...", delay=0.2)

    try:
        if full_install:
            cleanup(full_cleanup=False)
            shutil.copy("searchCommand.py", target_script)
            os.chmod(target_script, 0o755)
            os.chown(target_script, pw.pw_uid, pw.pw_gid)
            stat_info = os.stat(target_script)
            if stat_info.st_uid != pw.pw_uid or stat_info.st_gid != pw.pw_gid:
                log_error(f"Archivo {target_script} tiene propietario incorrecto (esperado: {SUDO_USER}).")
            log_info(f"searchCommand.py instalado en {BOLD}{YELLOW}{target_script}{RESET}.", secondary=True, delay=0.2)

            destino = os.path.expanduser(f"~{SUDO_USER}/referencestuff")
            if install_referencestuff_from_zip("referencestuff.zip", destino, pw):
                log_info("referencestuff instalado correctamente.", secondary=True, delay=0.2)
            else:
                log_info("referencestuff no instalado debido a cancelación o error.", secondary=True, delay=0.2)

        if full_install:
            if os.path.exists(VENV_DIR):
                log_warn(f"El entorno virtual en {VENV_DIR} ya existe. ¿Regenerar? (S/n)", delay=0.5)
                if get_input("S/n", default="S").lower() != "s":
                    log_info("Reutilizando entorno virtual existente.", secondary=True, delay=0.2)
                else:
                    shutil.rmtree(VENV_DIR)
                    subprocess.run(["python3", "-m", "venv", VENV_DIR], check=True, capture_output=True, text=True)
                    log_info("Entorno virtual regenerado.", secondary=True, delay=0.2)
            else:
                log_info(f"Creando entorno virtual en {BOLD}{YELLOW}{VENV_DIR}{RESET}...", delay=0.2)
                subprocess.run(["python3", "-m", "venv", VENV_DIR], check=True, capture_output=True, text=True)

            pip_path = os.path.join(VENV_DIR, "bin", "pip")
            
            required_packages = [
                "fuzzywuzzy>=0.18.0",
                "prompt_toolkit>=3.0.0",
                "requests>=2.28.0",
                "packaging>=23.0"
            ]
            with open("requirements.txt", "r") as f:
                req_packages = [line.strip().split("#")[0].strip() for line in f if line.strip() and not line.strip().startswith("#")]
            all_packages = list(set(required_packages + req_packages))
            if not all_packages:
                log_error("No se encontraron dependencias válidas para instalar.")
            
            for i, package in enumerate(all_packages, 1):
                max_len = max(len(p) for p in all_packages) + 20
                msg = f"Instalando {package} ({i}/{len(all_packages)})"
                print(f"{GREEN}[INFO]{RESET} {msg:<{max_len}}", end="", flush=True)
                subprocess.run([pip_path, "install", package], check=True, capture_output=True, text=True)
                print(f"\r{GREEN}[INFO]{RESET} {msg:<{max_len}} {GREEN}✓{RESET}")

            script_content = f"#!/bin/sh\nexec {VENV_DIR}/bin/python3 {target_script} \"$@\""
            script_path = os.path.join(SCRIPT_DIR, "searchCommand")
            temp_script = "searchCommand_temp"
            
            if os.path.exists(temp_script):
                if os.path.isdir(temp_script):
                    shutil.rmtree(temp_script)
                else:
                    os.remove(temp_script)
            if os.path.exists(script_path):
                if os.path.isdir(script_path):
                    shutil.rmtree(script_path)
                else:
                    os.remove(script_path)
            
            with open(temp_script, "w") as f:
                f.write(script_content)
            shutil.move(temp_script, script_path)
            os.chmod(script_path, 0o755)
            log_info("Script ejecutable creado.", secondary=True, delay=0.2)

        print(SEPARATOR)
        log_info(f"¡{'Instalación' if full_install else 'Actualización'} completada con éxito, crack!", delay=0.2)
        print(f"[{GREEN}✓{RESET}] Usa {BLUE}{BOLD}searchCommand{RESET} desde la terminal 😎")
        print(f"\n\t\t{BOLD}{RED}H4PPY H4CK1NG ! ! !{RESET}\n")

    except (subprocess.CalledProcessError, OSError) as e:
        log_error(f"Falló la instalación: {str(e)}")
        cleanup(full_cleanup=False)

def uninstall_search_command():
    print(SEPARATOR)
    log_info("Iniciando desinstalación...", delay=0.2)
    log_warn("¿Eliminar también el directorio referencestuff? (S/n)", delay=0.5)
    full_cleanup = get_input("S/n", default="S").lower() == "s"
    cleanup(full_cleanup=full_cleanup)
    print(SEPARATOR)
    log_info("Desinstalación completada, crack 😎.", delay=0.2)

def main():
    choice = get_user_choice()
    if choice == "1":
        install_search_command(full_install=True)
    elif choice == "2":
        install_search_command(full_install=False)
    elif choice == "3":
        print(SEPARATOR)
        log_info("Iniciando actualización de referencestuff...", delay=0.2)
        update_referencestuff(pwd.getpwnam(SUDO_USER))
        print(SEPARATOR)
        log_info("Actualización de referencestuff completada, crack 😎.", delay=0.2)
    elif choice == "4":
        uninstall_search_command()
    else:
        log_info("Saliendo...", delay=0.5)

if __name__ == "__main__":
    main()
