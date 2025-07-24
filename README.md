![Banner](https://i.imgur.com/NII8Wbr.jpeg)

**searchCommand** is a Python-based tool designed for pentesters and cybersecurity enthusiasts. It provides an interactive interface to search and explore Linux pentesting commands, organized by categories and tools, with features like autocompletion, syntax highlighting, and a Kali Linux-inspired design. Perfect for learning, quick command reference, or execution directly from the terminal.

**Author**: Jordan aka SkyW4r33x  
**Version**: 4.0.0  

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
  - [Interactive Mode](#interactive-mode)
  - [Internal Commands](#internal-commands)
  - [Non-Interactive Search](#non-interactive-search)
- [GTFSearch Usage](#gtfsearch-usage)
  - [Interactive Mode](#gtfsearch-interactive-mode)
  - [Internal Commands](#gtfsearch-internal-commands)
  - [Non-Interactive Search](#gtfsearch-non-interactive-search)
- [Command Storage Format](#command-storage-format)
  - [Directory Structure](#directory-structure)
  - [Tool File Format](#tool-file-format)
- [Interactive Prompt](#interactive-prompt)
  - [searchCommand Prompt](#searchcommand-prompt)
  - [GTFSearch Prompt](#gtfsearch-prompt)
- [Uninstallation](#uninstallation)
- [Tested Terminals](#tested-terminals)
- [Known Issues](#known-issues)
- [Troubleshooting](#troubleshooting)
- [Credits](#credits)

## Features

- **Interactive Interface**: Search commands using a Kali-style prompt with autocompletion (Tab) and keyboard shortcuts.
- **Organized Commands**: Commands are categorized in a customizable `referencestuff` directory for easy access.
- **Syntax Highlighting**: Commands, parameters, and comments are color-coded for clarity.
- **Smart Suggestions**: Suggests similar commands if the entered one is not found.
- **Customizable**: Define your own commands and categories in the `referencestuff` directory.

## Prerequisites

- **Operating System**: Linux (tested on Kali, Parrot, and Ubuntu).
- **Dependencies**: Python 3.6+, `git`, and `sudo` permissions for installation.
- **Terminal**: Recommended terminals include Terminator, GNOME Terminal, or Parrot Terminal for optimal compatibility.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/SkyW4r33x/searchCommand.git
   cd searchCommand
   ```
2. Run the installer script to set up a virtual environment and install dependencies:
   ```bash
   chmod +x kali-install.sh
   sudo ./kali-install.sh
   ```
   - Select `1) Install SearchCommand v4.0.0 (removes previous versions)` from the menu.

## SearchCommand Usage

### Interactive Mode

Launch `searchCommand` without arguments to enter interactive mode:
```bash
searchCommand
```

- **Search Tools**: Type a tool name (e.g., `nmap`) and press Enter.
- **Search Categories**: Type a category name (e.g., `RECONOCIMIENTO`).
- **Autocompletion**: Press `Tab` to autocomplete categories, tools, or commands.
- **Keyboard Shortcuts**:
  - `Ctrl + L`: Clear the screen.
  - `Ctrl + T`: List all tools.
  - `Ctrl + K`: List all categories.
  - `Ctrl + E`: Edit the last searched tool.
  - `Ctrl + R`: Reload tools.
  - `Ctrl + C`: Exit.

### Internal Commands

- `help` (or `h`): Display the help menu.
- `list tools` (or `lt`): List all available tools.
- `list categories` (or `lc`): List all categories.
- `setip <IP|domain>` (or `si`): Set the `$IP` variable (e.g., `setip 192.168.1.1` or `setip example.com`).
- `seturl <URL>` (or `su`): Set the `$URL` variable (e.g., `seturl http://example.com`).
- `refresh` (or `r`): Reload tools; `refresh config` resets variables.
- `edit <tool>` (or `e`): Edit a tool using `nano`, `vim`, or `vi`.
- `gtfsearch <binary>` (or `gtf`): Search GTFOBins (e.g., `gtfsearch nmap`).
- `add categories` (or `ac`): Create a new category interactively.
- `add tools` (or `at`): Add a new tool to a category interactively.
- `delete category <category>` (or `dc`): Delete a category interactively.
- `delete tool <tool>` (or `dt`): Delete a tool interactively.
- `exit` (or `q`): Exit the program.

### Non-Interactive Search

Search for a specific command directly:
```bash
searchCommand nmap
```

## GTFSearch Usage

### Interactive Mode

Launch `gtfsearch` without arguments to enter interactive mode:
```bash
gtfsearch
```

- **Search Binaries**: Type a binary name (e.g., `nmap`) and press Enter.
- **Autocompletion**: Press `Tab` to autocomplete binaries or internal commands.
- **Keyboard Shortcuts**:
  - `Ctrl + L`: Clear the screen.
  - `Ctrl + K`: List all binaries.
  - `Ctrl + C`: Exit.

### Internal Commands

- `help` (or `h`): Display the help menu.
- `list binaries` (or `lb`): List all available binaries.
- `exit` (or `q`): Exit the program.

### Non-Interactive Search

Search for a specific binary directly:
```bash
gtfsearch nmap
```

## Command Storage Format

Commands are stored in the `~/referencestuff` directory, organized by categories and tools.

### Directory Structure

```
~/referencestuff/
├── RECONOCIMIENTO/
│   ├── NMAP.txt
│   └── OTRA_HERRAMIENTA.txt
├── EXPLOTACIÓN/
│   ├── METASPLOIT.txt
│   └── OTRA_HERRAMIENTA.txt
```

### Tool File Format

Each tool file (e.g., `NMAP.txt`) follows this format:
```
Descripción:▶ [Command description]
Comando: [Full command]

* Optional subtitle
Descripción:▶ [Another description]
Comando: [Another command]
```

**Example**:
```
# Example of how tools should be organized for correct display.
# Important: Descriptions must start with the symbol '▶' as shown below.

▶ Search specific command:  
   searchCommand nmap

▶ Show general help:  
   searchCommand -h

▶ List available categories:  
   searchCommand --list-categories

▶ List all tools:  
   searchCommand --list-tools
```

**Notes**:
- **Location**: Commands are stored in category folders under `~/referencestuff`.
- **Strict Format**: Lines must start with `Descripción:▶` and `Comando:` to avoid errors.
- **Variables**: `$IP` and `$URL` are automatically substituted if set.
- **Error Handling**: Missing or incorrectly formatted files trigger errors. Use `refresh` to reload.

## Interactive Prompt

### searchCommand Prompt

The `searchCommand` prompt provides an intuitive interface with autocompletion and real-time context display (current category or tool). Below are the supported scenarios:

| Scenario                     | Description                                          | Example Visual                                                                |
|------------------------------|-----------------------------------------------------|------------------------------------------------------------------------------|
| Correct Input                | User enters a valid command.                        | ![Correct Input](https://i.imgur.com/0bCUGfh.png)                            |
| Incorrect Input              | User enters an unrecognized command.                | ![Incorrect Input](https://i.imgur.com/Q7v8nWK.png)                          |
| Current Category/Tool        | Displays the current navigation context.            | ![Current Category](https://i.imgur.com/FiGVVG0.png)                         |
| Autocompletion               | Dynamic suggestions while typing.                   | ![Autocompletion](https://i.imgur.com/6gsHK32.png)                           |
| Interface Overview           | Shows available categories and tools.               | ![Interface](https://i.imgur.com/IBEoQOz.png)                                |

[Watch the demo video](https://i.imgur.com/OkKMFUy.mp4)

### GTFSearch Prompt

The `gtfsearch` prompt (integrated with `searchCommand`) supports binary and function searches with autocompletion and status indicators (✔ for success, ✘ for error).

| Scenario                     | Description                                          | Example Visual                                                                |
|------------------------------|-----------------------------------------------------|------------------------------------------------------------------------------|
| Correct Input                | User enters a valid binary.                         | ![Correct Input](https://i.imgur.com/tZjRcC5.png)                            |
| Incorrect Input              | User enters an unrecognized binary.                 | ![Incorrect Input](https://i.imgur.com/xG8uJw5.png)                          |
| Autocompletion               | Dynamic suggestions for binaries or commands.       | ![Autocompletion](https://i.imgur.com/UIhgMKn.png)                           |
| Interface Overview           | Shows available binaries and commands.              | ![Interface](https://i.imgur.com/Ij3Y6cY.png)                                |

## Uninstallation

To uninstall `searchCommand`:
```bash
sudo ./kali-install.sh
```
Select `2) Uninstall SearchCommand (removes everything)` to delete all installed files.

## Tested Terminals

The tool has been tested on the following Linux terminals:

| Terminal        | Status                                                                 |
|-----------------|------------------------------------------------------------------------|
| Kitty           | Functional with limitations: `Ctrl + L` clears the screen, but history reappears on scroll-up; partial icon rendering. |
| Terminator      | Fully functional with no known issues.                                 |
| GNOME Terminal  | Fully functional with no known issues.                                 |
| Parrot Terminal | Fully functional with no known issues.                                 |

**Note**: For the best experience in Kitty, consider switching to Terminator, GNOME Terminal, or Parrot Terminal to avoid scroll-up history issues.

## Known Issues

- **Configuration Errors**: If `referencestuff` is missing or incorrectly formatted, the tool will fail to load. Ensure proper setup during installation.
- **Kitty Terminal**: `Ctrl + L` clears the screen, but scroll-up history reappears. Other terminals may show inconsistent colors or formatting.
- **GTFOBins**: Limited to supported binaries; ensure a stable internet connection for queries.

## Troubleshooting

- **Installation Fails**: Ensure `git` and Python 3.6+ are installed, and run `kali-install.py` with `sudo`.
- **Commands Not Found**: Run `refresh` to reload tools or verify the `~/referencestuff` directory structure.
- **Formatting Issues**: Check that tool files follow the exact `Descripción:▶` and `Comando:` format.
- **Terminal Issues**: Switch to a fully compatible terminal like Terminator or GNOME Terminal for optimal performance.

## Credits

This tool is inspired by the `utilscommon` notes from **[S1R3N](https://github.com/OHDUDEOKNICE)**, originally designed as terminal-accessible aliases. It has been enhanced with an interactive command search feature for a better user experience.

**H4PPY H4CK1NG!**