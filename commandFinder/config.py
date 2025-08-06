#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "4.0.0"

class Config:
    ROOT_DIR_NAME = 'referencestuff'
    DEFAULT_PERMS = 0o750
    MAX_FILE_SIZE = 10 * 1024 * 1024

class Colors:
    RESET = "\033[0m"
    RED = "\033[38;2;212;25;25m"
    TITLE = "\033[38;2;254;1;58m"
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
