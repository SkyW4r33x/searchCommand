import os
import pwd
import re
import socket
import subprocess
import sys
import time
import shutil
import ipaddress
from urllib.parse import urlparse
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from config import Colors, Config
from utils import handle_exception, normalize_url, normalize_text
from services import get_safe_editor, sanitize_file_path
from ui import clear_screen, list_categories, list_tools
from prompt_toolkit import PromptSession
from creator import Creator

def handle_internal_command(search_command, query: str) -> bool:
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
        'gtf': 'gtfsearch',
        'ac': 'add categories',
        'at': 'add tools',
        'dc': 'delete category',
        'dt': 'delete tool'
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
        'gtfsearch': 'gtfsearch',
        'add categories': 'add categories',
        'add tools': 'add tools',
        'delete category': 'delete category',
        'delete tool': 'delete tool'
    }
    
    if query_lower.startswith('delete category') or query_lower.startswith('dc'):
        command = 'delete category'
        args = ''  
    elif query_lower.startswith('delete tool') or query_lower.startswith('dt'):
        command = 'delete tool'
        args = ''  
    else:
        query_parts = query.strip().split(maxsplit=1)
        command_input = query_parts[0].lower()
        args = query_parts[1] if len(query_parts) > 1 else ''
        
        command = aliases.get(command_input, commands.get(command_input, None))
        if not command:
            command = commands.get(query_lower, None)
    
    if not command:
        return False
    
    if command == 'help':
        search_command.show_help()
        return True
    elif command == 'clear':
        search_command._clear_screen()
        search_command.print_header()
        return True
    elif command == 'list tools':
        search_command._list_tools()
        return True
    elif command == 'list categories':
        search_command._list_categories()
        return True
    elif command == 'exit':
        print(f"\n\t\t\t\t\t{Colors.RED}{Colors.RESET}H4PPY H4CK1NG")
        sys.exit(0)
    elif command == 'setip':
        if len(args) > 255:
            print(f"{Colors.RED}[-] {Colors.RESET}Input too long. Maximum 255 characters.")
            return True
        if not args:
            if search_command.ip_value:
                print(f"{Colors.BLUE}[ℹ] {Colors.RESET}Current $IP value: {Colors.GREEN}{search_command.ip_value}{Colors.RESET}")
            else:
                print(f"{Colors.BLUE}[ℹ] {Colors.RESET}No value set for $IP")
            print(f"{Colors.GREEN}[+] {Colors.RESET}Usage: {Colors.GREEN}setip <IP|domain> (example: setip 192.168.1.1 or setip example.com)")
            print(f"{Colors.GREEN}[+] {Colors.RESET}To clear: {Colors.GREEN}setip clear{Colors.RESET}")
            print(f"{Colors.BLUE}[ℹ] {Colors.RESET}The IP/domain will be used in commands with $IP.\n")
            return True
        elif args.lower() == 'clear':
            search_command.ip_value = None
            print(f"{Colors.GREEN}[✔] {Colors.RESET}Successfully reset. Commands will use {Colors.GREEN}$IP{Colors.RESET} by default.\n")
            return True
        else:
            dangerous_patterns = r'[;&|`$(){}[\]<>]'
            if re.search(dangerous_patterns, args):
                print(f"{Colors.RED}[-] {Colors.RESET}Input contains disallowed characters.")
                return True
            try:
                ipaddress.ip_address(args)
                search_command.ip_value = args
                try:
                    socket.gethostbyname(args)
                    print(f"{Colors.GREEN}[✔] {Colors.RESET}$IP resolves correctly: {args}")
                except socket.gaierror:
                    print(f"{Colors.ORANGE}[-] {Colors.RESET}$IP does not resolve in DNS, but accepted: {args}")
            except ValueError:
                domain_pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
                if re.match(domain_pattern, args) and 1 < len(args) <= 255:
                    try:
                        socket.gethostbyname(args)
                        search_command.ip_value = args
                        print(f"{Colors.GREEN}[✔] {Colors.RESET}Domain resolves correctly: {args}")
                    except socket.gaierror:
                        print(f"{Colors.ORANGE}[-] {Colors.RESET}Domain does not resolve in DNS, but accepted: {args}")
                        search_command.ip_value = args
                else:
                    print(f"{Colors.RED}[-] {Colors.RESET}Invalid input. Must be a valid IP (ex: 192.168.1.1) or domain (example: example.com).")
                    return True
            if search_command.ip_value and args not in search_command.recent_ips:
                search_command.recent_ips.append(args)
                if len(search_command.recent_ips) > 5:
                    search_command.recent_ips.pop(0)
            print(f"{Colors.GREEN}[✔] {Colors.RESET}$IP set as: {Colors.GREEN}{args}{Colors.RESET}\n")
            return True
    elif command == 'seturl':
        if len(args) > 2048:
            print(f"{Colors.RED}[-] {Colors.RESET}Input too long. Maximum 2048 characters.")
            return True
        if not args:
            if search_command.url_value:
                print(f"{Colors.BLUE}[ℹ] {Colors.RESET}Current $URL value: {Colors.GREEN}{search_command.url_value}{Colors.RESET}")
            else:
                print(f"{Colors.BLUE}[ℹ] {Colors.RESET}No value set for $URL")
            print(f"{Colors.GREEN}[+] {Colors.RESET}Usage: {Colors.GREEN}seturl <URL> (example: seturl http://example.com)")
            print(f"{Colors.GREEN}[+] {Colors.RESET}To clear: {Colors.GREEN}seturl clear{Colors.RESET}")
            print(f"{Colors.BLUE}[ℹ] {Colors.RESET}The URL will be used in commands with $URL.\n")
            return True
        elif args.lower() == 'clear':
            search_command.url_value = None
            print(f"{Colors.GREEN}[✔] {Colors.RESET}Successfully reset. Commands will use {Colors.GREEN}$URL{Colors.RESET} by default.\n")
            return True
        else:
            dangerous_patterns = r'[;&|`$(){}[\]<>]'
            if re.search(dangerous_patterns, args):
                print(f"{Colors.RED}[-] {Colors.RESET}Input contains disallowed characters.")
                return True
            try:
                parsed = urlparse(args)
                if parsed.scheme not in ['http', 'https']:
                    print(f"{Colors.RED}[-] {Colors.RESET}Only URLs with http or https protocol are allowed.\n")
                    return True
                if not parsed.netloc:
                    print(f"{Colors.RED}[-] {Colors.RESET}Invalid input. Must be a valid URL (ex: http://example.com).")
                    return True
                skip_verification = False
                try:
                    ip = ipaddress.ip_address(parsed.netloc)
                    if ip.is_private:
                        skip_verification = True
                        print(f"{Colors.ORANGE}[!] {Colors.RESET}Private IP detected ({parsed.netloc}), skipping accessibility verification.")
                except ValueError:
                    pass
                
                try:
                    socket.gethostbyname(parsed.netloc)
                except socket.gaierror:
                    print(f"{Colors.RED}[-] {Colors.RESET}The domain/IP {parsed.netloc} is invalid or does not resolve. Verify the URL.")
                    return True
                
                search_command.url_value = args
                normalized_url = normalize_url(args)
                
                if not skip_verification:
                    try:
                        session = requests.Session()
                        retries = Retry(total=1, backoff_factor=0.1, status_forcelist=[429, 500, 502, 503, 504])
                        session.mount('https://', HTTPAdapter(max_retries=retries))
                        session.mount('http://', HTTPAdapter(max_retries=retries))
                        response = session.head(normalized_url, timeout=2, allow_redirects=True, verify=True)
                        if response.status_code < 400:
                            print(f"{Colors.GREEN}[✔] {Colors.RESET}$URL accessible: {Colors.BLUE}{args}{Colors.RESET} (Code: {response.status_code})")
                        else:
                            print(f"{Colors.ORANGE}[-] {Colors.RESET}URL not accessible (code: {response.status_code}), but added successfully")
                    except requests.exceptions.SSLError:
                        print(f"{Colors.RED}[-] {Colors.RESET}Invalid URL or unverifiable SSL certificate. Verify the domain.")
                        return True
                    except requests.RequestException:
                        print(f"{Colors.ORANGE}[-] {Colors.RESET}URL not accessible, but added successfully")
                else:
                    print(f"{Colors.ORANGE}[-] {Colors.RESET}Verification skipped for private IP, URL added successfully.")
                
                if args not in search_command.recent_urls:
                    search_command.recent_urls.append(args)
                    if len(search_command.recent_urls) > 5:
                        search_command.recent_urls.pop(0)
                print(f"{Colors.GREEN}[✔] {Colors.RESET}$URL set as: {Colors.GREEN}{args}{Colors.RESET}\n")
            except ValueError:
                print(f"{Colors.RED}[-] {Colors.RESET}Invalid input. Must be a valid URL (ex: http://example.com).")
            return True
    elif command == 'refresh':
        if args.lower() == 'config':
            search_command.ip_value = None
            search_command.url_value = None
            search_command.recent_ips.clear()
            search_command.recent_urls.clear()
            print(f"{Colors.GREEN}[✔] {Colors.RESET}Configuration reset (IP and URL cleared).")
        else:
            try:
                search_command._load_tools()
                search_command._init_prompt_session()
                search_command._clear_screen()
                print(f"{Colors.GREEN}[✔] {Colors.RESET}Tools reloaded successfully.\n")
            except (FileNotFoundError, PermissionError, ValueError) as e:
                handle_exception(f"Error reloading tools", e)
        return True
    elif command == 'edit':
        creator = Creator(search_command)
        creator._edit_tool(args)
        return True
    elif command == 'gtfsearch':
        clear_screen(search_command)
        search_command.gtf_search.run()
        clear_screen(search_command)
        search_command.print_header()
        return True
    elif command == 'add categories':
        creator = Creator(search_command)
        creator._create_category()
        return True
    elif command == 'add tools':
        creator = Creator(search_command)
        creator._create_tool()
        return True
    elif command == 'delete category':
        creator = Creator(search_command)
        creator._delete_category(args)
        return True
    elif command == 'delete tool':
        creator = Creator(search_command)
        creator._delete_tool(args)
        return True
    return False

def handle_resize(search_command, signum, frame):
    search_command._clear_screen()
    search_command.print_header()
    app = get_app()
    app.renderer.reset()
    app._redraw()