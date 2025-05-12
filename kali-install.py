#!/usr/bin/env python3

import os
import sys
import subprocess
import shutil
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
        print("Colorama no está instalado globalmente. Creando entorno virtual temporal para el instalador...")
        temp_venv = "/tmp/searchCommand_installer_venv"
        
        if not os.path.exists(temp_venv):
            subprocess.run([sys.executable, "-m", "venv", temp_venv], check=True)
        
        pip_path = os.path.join(temp_venv, "bin", "pip")
        try:
            subprocess.run([pip_path, "install", "colorama>=0.4.6"], check=True)
        except subprocess.CalledProcessError:
            print("Error: No se pudo instalar colorama. Asegúrate de tener acceso a internet.")
            sys.exit(1)
        
        python_path = os.path.join(temp_venv, "bin", "python3")
        subprocess.run([python_path] + sys.argv, check=True)
        sys.exit(0) 

Fore, Style = ensure_colorama()
os.system("clear")

GREEN, YELLOW, RED, CYAN, BLUE, MAGENTA = Fore.GREEN, Fore.YELLOW, Fore.RED, Fore.CYAN, Fore.BLUE, Fore.MAGENTA
RESET, BOLD = Style.RESET_ALL, Style.BRIGHT

__version__ = "0.1"

VENV_DIR = "/opt/searchCommand_venv"
BIN_DIR = "/usr/local/bin"
SCRIPT_DIR = "/usr/bin"

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
    
    return f"{gradient_banner}\n{centered_signature}".rstrip()

BANNER = create_gradient_banner()
SEPARATOR = f"{BLUE}════════════════════════════════════════════{RESET}"

def log_info(msg, secondary=False, delay=0):
    prefix = f"{CYAN}[INFO]{RESET}" if secondary else f"{GREEN}[INFO]{RESET}"
    print(f"{prefix} {msg}")
    if delay:
        sleep(delay)

def log_warn(msg, delay=0):
    print(f"{YELLOW}[WARN]{RESET} {msg}", file=sys.stderr)
    if delay:
        sleep(delay)

def log_error(msg, exit_code=1):
    print(f"{RED}[ERROR]{RESET} {msg}", file=sys.stderr)
    sys.exit(exit_code)

if not shutil.which("python3"):
    log_error("Python3 no está instalado. Instálalo con 'sudo apt install python3'.")
if os.geteuid() != 0:
    log_error("Este script requiere privilegios de root. Usa sudo.")

SUDO_USER = os.environ.get("SUDO_USER")
if not SUDO_USER:
    log_error("No se pudo determinar el usuario que ejecutó sudo.")

def cleanup():
    log_warn("Limpiando archivos temporales...", delay=0.5)
    paths = [
        os.path.join(BIN_DIR, "searchCommand.py"),
        os.path.join(SCRIPT_DIR, "searchCommand"),
        VENV_DIR,
        os.path.expanduser(f"~{SUDO_USER}/referencestuff")
    ]
    for path in paths:
        if os.path.exists(path):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                log_info(f"{path} {BOLD}{RED}eliminado...{RESET}", secondary=True, delay=0.2)
            except OSError as e:
                log_warn(f"No se pudo limpiar {path}: {e}", delay=0.2)

def get_input(prompt, default=None):
    print(prompt, end="", flush=True)
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        user_input = ""
        while True:
            char = sys.stdin.read(1)
            if char in ("\n", "\r"):
                print()
                break
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
    return user_input.strip() or default

def get_user_choice():
    while True:
        try:
            print(BANNER)
            print(f"\n{GREEN}[1]{RESET} Instalar searchCommand")
            print(f"{GREEN}[2]{RESET} Desinstalar searchCommand")
            print(f"{GREEN}[3]{RESET} Salir")
            choice = get_input(f"{BLUE}>> {RESET}", default="3")
            if choice in ["1", "2", "3"]:
                return choice
            os.system("clear")
            log_warn("Opción inválida. Usa 1, 2 o 3.")
        except KeyboardInterrupt:
            print()
            log_info("Interrupción detectada. Saliendo...", delay=0.5)
            sys.exit(0)

def install_search_command():
    required_files = ["searchCommand.py", "requirements.txt"]
    for file in required_files:
        if not os.path.exists(file):
            log_error(f"No se encuentra {BOLD}{RED}{file}{RESET} en el directorio actual.")

    if not os.path.exists("referencestuff"):
        log_error(f"'referencestuff' no encontrado en el directorio actual. Es necesario para searchCommand.")

    target_script = os.path.join(BIN_DIR, "searchCommand.py")
    if os.path.exists(target_script):
        log_warn(f"searchCommand.py ya existe en {BOLD}{YELLOW}{BIN_DIR}{RESET}. ¿Sobrescribir? (S/n)", delay=0.2)
        if get_input("").lower() != "s":
            log_info("Instalación cancelada.", delay=0.5)
            sys.exit(0)

    print("\n" + SEPARATOR)
    log_info("Iniciando instalación...", delay=0.2)

    try:
        shutil.copy("searchCommand.py", target_script)

        destino = os.path.expanduser(f"~{SUDO_USER}/referencestuff")
        pw = pwd.getpwnam(SUDO_USER)
        if os.path.exists(destino):
            shutil.rmtree(destino)  
        shutil.copytree("referencestuff", destino, dirs_exist_ok=False)
        
       
        for root, dirs, files in os.walk(destino):
            for d in dirs:
                dir_path = os.path.join(root, d)
                os.chmod(dir_path, 0o755) 
                os.chown(dir_path, pw.pw_uid, pw.pw_gid)
            for f in files:
                file_path = os.path.join(root, f)
                os.chmod(file_path, 0o644) 
                os.chown(file_path, pw.pw_uid, pw.pw_gid)
        os.chmod(destino, 0o755)  
        os.chown(destino, pw.pw_uid, pw.pw_gid)
        
        
        stat_info = os.stat(destino)
        if stat_info.st_uid != pw.pw_uid or stat_info.st_gid != pw.pw_gid:
            log_error(f"El directorio {destino} no tiene el propietario correcto (esperado: {SUDO_USER})")
        if not os.access(destino, os.R_OK | os.X_OK):
            log_error(f"El directorio {destino} no tiene permisos de lectura/entrada para el usuario {SUDO_USER}.")
        log_info(f"Dando permisos correspondientes a {BOLD}{YELLOW}{destino}{RESET}.", secondary=True, delay=0.2)

        if os.path.exists(VENV_DIR):
            log_warn(f"El entorno virtual en {VENV_DIR} ya existe. ¿Regenerar? (S/n)", delay=0.2)
            if get_input("").lower() == "s":
                shutil.rmtree(VENV_DIR)
                subprocess.run(["python3", "-m", "venv", VENV_DIR], check=True, capture_output=True, text=True)
                log_info("Entorno virtual regenerado.", secondary=True, delay=0.2)
            else:
                log_info("Reutilizando entorno existente.", secondary=True, delay=0.2)
        else:
            log_info(f"Creando entorno virtual en {BOLD}{YELLOW}{VENV_DIR}...{RESET}", delay=0.2)
            subprocess.run(["python3", "-m", "venv", VENV_DIR], check=True, capture_output=True, text=True)

        pip_path = os.path.join(VENV_DIR, "bin", "pip")
        
        required_packages = [
            "fuzzywuzzy>=0.18.0",
            "prompt_toolkit>=3.0.0",
            "colorama>=0.4.6"
        ]
        with open("requirements.txt", "r") as f:
            req_packages = [line.strip().split("#")[0].strip() for line in f if line.strip() and not line.startswith("#")]
        all_packages = required_packages + req_packages
        if not all_packages:
            log_error("No se encontraron dependencias válidas para instalar.")
        
        
        for i, package in enumerate(all_packages, 1):
            print(f"{GREEN}> instalando {package} ({i}/{len(all_packages)}){RESET} ", end="")
            sys.stdout.flush()
            for frame in ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧"]:
                print(f"\r{GREEN}>{RESET} instalando {GREEN}{package} ({i}/{len(all_packages)}) [{frame}]{RESET}", end="")
                sleep(0.1)
            subprocess.run([pip_path, "install", package], check=True, capture_output=True, text=True)
            print(f"\r{GREEN}>{RESET} instalando {GREEN}{package} ({i}/{len(all_packages)}) [✓]{RESET}")

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
        os.chmod(target_script, 0o755)  
        os.chmod(script_path, 0o755)    
        log_info("Script ejecutable creado y permisos asignados.", secondary=True, delay=0.2)

        print(SEPARATOR + "\n")
        log_info("Instalación completada con éxito!", delay=0.2)
        print(f"[{GREEN}+{RESET}] Usa {BLUE}{BOLD}searchCommand{RESET} desde la terminal.")
        print(f"\n\t\t{BOLD}{RED}H4PPY H4CK1NG{RESET}")

    except subprocess.CalledProcessError as e:
        log_error(f"Error en subproceso: {e.stderr}")
        cleanup()
    except (PermissionError, OSError) as e:
        log_error(f"Error de permisos o sistema: {e}")
        cleanup()

def uninstall_search_command():
    print("\n" + SEPARATOR)
    log_info("Iniciando desinstalación...", delay=0.2)
    cleanup()
    print(SEPARATOR + "\n")
    log_info("Desinstalación completada.", delay=0.2)

choice = get_user_choice()
if choice == "1":
    install_search_command()
elif choice == "2":
    uninstall_search_command()
else:
    log_info("Saliendo...", delay=0.5)
