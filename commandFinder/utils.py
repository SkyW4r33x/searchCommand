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
import pwd
from collections import defaultdict
from requests.adapters import HTTPAdapter
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
from urllib3.exceptions import InsecureRequestWarning
from urllib3.util.retry import Retry
from fuzzywuzzy import process

warnings.filterwarnings("ignore", category=InsecureRequestWarning, module="urllib3")

def normalize_text(text: str) -> str:
    normalized = ''.join(
        c for c in unicodedata.normalize('NFD', text.lower())
        if unicodedata.category(c) != 'Mn' and (c.isalnum() or c.isspace())
    ).strip()
    return normalized if normalized else None

def normalize_url(url: str) -> str:
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

def replace_variables(command: str, ip_value: Optional[str], url_value: Optional[str]) -> str:
    if '$IP' in command and ip_value:
        command = command.replace('$IP', ip_value)
    if '$URL' in command and url_value:
        command = command.replace('$URL', url_value)
        command = re.sub(r'(https?://[^/]+)//+', r'\1/', command)
    return command

def strip_ansi_codes(text: str) -> str:
    ansi_escape = re.compile(r'\033\[[0-9;]*[mK]')
    return ansi_escape.sub('', text)

def handle_exception(error_msg: str, e: Exception, exit_on_error: bool = False):
    print(f"{Colors.RED}[-]{Colors.RESET} {error_msg}: {e}")
    if exit_on_error:
        sys.exit(1)

def sanitize_name(name: str) -> str:
    name = re.sub(r'[^a-zA-Z0-9_-]', '', name.strip())  
    if len(name) > 50 or len(name) < 1 or name in ['.', '..']:  
        raise ValueError("Invalid name: must have between 1 and 50 valid characters, without reserved names.")
    return name