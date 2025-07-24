#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 
# Author        : JordanSec aka (SkyW4r33x)
# Repository    : https://github.com/SkyW4r33x/searchCommand
# Description   : Command search tool for pentesting.

import argparse
import sys
from search_command import SearchCommand
from config import Colors

def main():
    parser = argparse.ArgumentParser(description="Command search tool for pentesting.")
    parser.add_argument('--list-categories', action='store_true', help="Show available categories.")
    parser.add_argument('--list-tools', action='store_true', help="Show all tools organized by category.")
    parser.add_argument('query_positional', nargs='?', help="Direct query (without flag, ex: 'searchCommand main.py nmap').")

    try:
        args = parser.parse_args()
    except SystemExit as e:
        if e.code != 0:
            print(f"{Colors.RED}[-]{Colors.RESET} Error parsing arguments")
            sys.exit(1)
        sys.exit(0)

    try:
        search_tool = SearchCommand(interactive=not (args.list_categories or args.list_tools or args.query_positional))

        if args.list_categories:
            search_tool._list_categories(interactive=False)
            sys.exit(0)

        if args.list_tools:
            search_tool._list_tools(interactive=False)
            sys.exit(0)

        query = args.query_positional
        if query:
            search_tool.run_query(query)
            sys.exit(0)

        search_tool.interactive_menu()
    except (FileNotFoundError, PermissionError, ValueError) as e:
        print(f"{Colors.RED}[-]{Colors.RESET} Execution error: {e}")
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
