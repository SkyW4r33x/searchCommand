#!/bin/bash

# ------------------ GLOBAL CONFIGURATION ----------------
readonly VERSION="4.0.0"
readonly BLUE=$'\033[38;2;39;127;255m'
readonly GREEN=$'\033[0;32m'
readonly RED=$'\033[0;31m'
readonly YELLOW=$'\033[1;33m'
readonly CYAN=$'\033[38;2;73;174;230m'
readonly PINK=$'\033[38;2;254;1;58m'
readonly WHITE=$'\033[38;2;255;255;255m'
readonly BOLD=$'\033[1m'
readonly RESET=$'\033[0m'

log_info() { echo -e "[${GREEN}${BOLD}➜${RESET}] $*"; }
log_warn() { echo -e "[${YELLOW}${BOLD}!${RESET}] $*" >&2; }
log_error() { echo -e "[${RED}${BOLD}✘${RESET}] $*" >&2; }

searchcommand() { echo -n "${BLUE}${BOLD}SearchCommand${RESET}"; }

spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='⣾⣷⣯⣟⡿⣿'
    local i=0
    while kill -0 $pid 2>/dev/null; do
        local temp=${spinstr#?}
        printf "\r[${GREEN}⏳${RESET}] %s ${GREEN}%s${RESET} " "$2" "${spinstr:0:1}"
        spinstr=$temp${spinstr%"${temp}"}
        sleep $delay
        ((i++))
        if [[ $i -eq ${#spinstr} ]]; then i=0; fi
    done
    wait $pid
    local exit_code=$?
    if [[ $exit_code -eq 0 ]]; then
        printf "\r[${GREEN}✔${RESET}] %s\n" "$2"
    else
        printf "\r[${RED}✘${RESET}] %s\n" "$2"
        return 1
    fi
    return 0
}

separator() {
    echo -e "${BLUE}\n══════════════════════════════════════════════════════════════════════════\n${RESET}"
}

is_installed() {
    if [ -d "/usr/local/bin/commandFinder" ] || [ -f "/usr/bin/searchcommand" ] || [ -f "/usr/bin/gtfsearch" ] || [ -d "$USER_HOME/referencestuff" ] || [ -d "$USER_HOME/.data" ] || [ -f "/usr/local/bin/commandFinder.py" ] || [ -f "/usr/local/bin/gtfsearch.py" ]; then
        return 0
    else
        return 1
    fi
}

uninstall_searchcommand() {
    if is_installed; then
        log_info "Previous installation detected. Uninstalling..."
    else
        log_info "No previous installation found."
        return 0
    fi

    rm -rf "$USER_HOME/.data" "$USER_HOME/referencestuff" /usr/share/gtfobins /usr/local/bin/commandFinder /usr/bin/searchcommand /usr/bin/gtfsearch /usr/local/bin/commandFinder.py /usr/local/bin/gtfsearch.py &>/dev/null
    rm -f "$USER_HOME/.gtfsearch_history" "$USER_HOME/.searchcommant_history" &>/dev/null

    for RC in ".bashrc" ".zshrc"; do
        RC_FILE="$USER_HOME/$RC"
        if [[ -f "$RC_FILE" ]]; then
            if grep -q '# GTFSCAN alias\|alias gtfsearch=' "$RC_FILE"; then
                sed -i '/# GTFSCAN alias/d' "$RC_FILE" &>/dev/null
                sed -i '/alias gtfsearch=/d' "$RC_FILE" &>/dev/null
                log_info "Alias removed from $RC"
                sleep 0.5
            fi
        fi
    done

    log_info "Uninstallation completed."
}

# ------------------ BANNER ----------------
show_banner() {
    clear
    echo -e "${PINK}${BOLD}"
    echo -e "\t\t┌─┐┌─┐┌─┐┬─┐┌─┐┬ ┬╔═╗┌─┐┌┬┐┌┬┐┌─┐┌┐┌┌┬┐"
    echo -e "\t\t└─┐├┤ ├─┤├┬┘│ ├─┤║ │ │││││││├─┤│││ ││"
    echo -e "\t\t└─┘└─┘┴ ┴┴└─└─┘┴ ┴╚═╝└─┘┴ ┴┴ ┴┴ ┴┘└┘─┴┘"
    echo -e "${RESET}\n"
    echo -e " ${BLUE}+ -- --=[${RESET} ${YELLOW}${BOLD}+${RESET} Created by ${BLUE}${BOLD}:${RESET} Jordan (SkyW4r33x) 🐉 ${BLUE}${BOLD}${RED}█${RESET}${WHITE}█${RESET}${RED}█${RESET} ${BLUE}${BOLD}]${RESET}"
    echo -e " ${BLUE}+ -- --=[${RESET} ${YELLOW}${BOLD}+${RESET} Repository ${BLUE}${BOLD}:${RESET} https://github.com/SkyW4r33x ${BLUE}${BOLD}]${RESET}\n\n"
}

show_menu() {
    separator
    log_info "Available options:"
    echo -e " ${BOLD}1)${RESET} Install $(searchcommand) ${BOLD}v${VERSION}${RESET} (removes previous versions)"
    echo -e " ${BOLD}2)${RESET} Uninstall $(searchcommand) (removes everything)"
    echo -e ""
}

show_usage_instructions() {
    clear
    echo -e "\n\t [${CYAN}${BOLD}+${RESET}]${BOLD} Usage instructions ${RESET}[${CYAN}${BOLD}+${RESET}]\n"
    
    echo -e "[${GREEN}${BOLD}➜${RESET}] ${BOLD}searchCommand:${RESET}"
    echo -e "${BLUE}─────────────────${RESET}"
    echo -e " [${BLUE}*${RESET}] Interactive mode: ${CYAN}searchCommand${RESET}"
    echo -e " [${BLUE}*${RESET}] Non-interactive mode: ${CYAN}searchCommand${RESET} ${GREEN}--help${RESET}"
    echo -e " [${BLUE}*${RESET}] Search for command: ${CYAN}searchCommand${RESET} nmap\n"
    
    echo -e "[${GREEN}${BOLD}➜${RESET}] ${BOLD}GTFSearch:${RESET}"
    echo -e "${BLUE}─────────────${RESET}"
    echo -e " [${BLUE}*${RESET}] Interactive mode: ${CYAN}gtfsearch${RESET}"
    echo -e " [${BLUE}*${RESET}] Non-interactive mode: ${CYAN}gtfsearch${RESET} ${GREEN}--help${RESET}"
    echo -e " [${BLUE}*${RESET}] Search binary: ${CYAN}gtfsearch${RESET} nmap"
    echo -e " [${BLUE}*${RESET}] Search SUID function: ${CYAN}gtfsearch${RESET} nmap ${GREEN}-t${RESET} SUID\n"
}

show_installation_summary() {
    echo -e "\n\t [${CYAN}${BOLD}+${RESET}]${BOLD} Installation summary [${CYAN}${BOLD}+${RESET}]"
    
    echo -e "\n[${GREEN}${BOLD}➜${RESET}] ${BOLD}searchCommand:${RESET}"
    echo -e "${BLUE}─────────────────${RESET}"
    echo -e " [${GREEN}✔${RESET}] Tools dir: ${BLUE}${BOLD}$USER_HOME/referencestuff${RESET}"
    echo -e " [${GREEN}✔${RESET}] Virtual environment: ${BLUE}${BOLD}/usr/local/bin/commandFinder/venv${RESET}"
    echo -e " [${GREEN}✔${RESET}] Main directory: ${BLUE}${BOLD}/usr/local/bin/commandFinder/${RESET}"
    echo -e " [${GREEN}✔${RESET}] Executable: ${BLUE}${BOLD}/usr/bin/searchcommand${RESET}\n"
    
    echo -e "[${GREEN}${BOLD}➜${RESET}] ${BOLD}GTFSearch:${RESET}"
    echo -e "${BLUE}─────────────${RESET}"
    echo -e " [${GREEN}✔${RESET}] GTFSearch: ${BLUE}${BOLD}/usr/bin/gtfsearch${RESET}"
    echo -e " [${GREEN}✔${RESET}] Data files: ${BLUE}${BOLD}$USER_HOME/.data${RESET}"
}

# ------------------ CORE FUNCTIONS ----------------
check_root() {
    log_info "Checking root permissions..."
    [[ $EUID -ne 0 ]] && { log_error "This script must be run as root\n\nUsage: ${GREEN}sudo${RESET} ${CYAN}bash${RESET} $0"; exit 1; }
    log_info "Root permissions confirmed."
}

detect_user() {
    REAL_USER=$(logname || echo "${SUDO_USER:-$USER}")
    USER_HOME="/home/$REAL_USER"
    log_info "Detected user: ${BLUE}${BOLD}$REAL_USER${RESET}"
}

install_dependencies() {
    log_info "Installing Python and dependencies..."
    apt update -qq &>/dev/null & spinner $! "Updating repositories..." || { log_error "Failed to update repositories"; return 1; }
    apt install -y python3 python3-venv python3-dev &>/dev/null & spinner $! "Installing Python dependencies..." || { log_error "Failed to install dependencies"; return 1; }
}

setup_python_environment() {
    log_info "Setting up Python virtual environment..."
    mkdir -p /usr/local/bin/commandFinder
    python3 -m venv /usr/local/bin/commandFinder/venv
    chown -R "$REAL_USER:$REAL_USER" /usr/local/bin/commandFinder/venv
    source /usr/local/bin/commandFinder/venv/bin/activate
    pip install --upgrade pip &>/dev/null & spinner $! "Upgrading pip..." || { log_error "Failed to upgrade pip"; return 1; }
    pip install rich prompt-toolkit fuzzywuzzy requests python-Levenshtein &>/dev/null & spinner $! "Installing required libraries..." || { log_error "Failed to install libraries"; return 1; }
    deactivate
    chown -R "$REAL_USER:$REAL_USER" /usr/local/bin/commandFinder/venv
    chmod -R 755 /usr/local/bin/commandFinder/venv
}

install_searchcommand() {
    separator
    log_info "Starting $(searchcommand) v${VERSION} installation..."

    mkdir -p "$USER_HOME/.data"
    cp .data/gtfobins.json "$USER_HOME/.data/gtfobins.json"
    chmod 644 "$USER_HOME/.data/gtfobins.json"
    chown -R "$REAL_USER:$REAL_USER" "$USER_HOME/.data"

    mkdir -p "$USER_HOME/referencestuff"
    cp -r referencestuff/* "$USER_HOME/referencestuff/"
    chown -R "$REAL_USER:$REAL_USER" "$USER_HOME/referencestuff"
    chmod -R 750 "$USER_HOME/referencestuff"

    log_info "Data files copied to ${BLUE}${BOLD}$USER_HOME/.data${RESET} and tools to ${BLUE}${BOLD}$USER_HOME/referencestuff${RESET}"

    install_dependencies || return 1
    setup_python_environment || return 1

    mkdir -p /usr/local/bin/commandFinder
    cp -r commandFinder/* /usr/local/bin/commandFinder/
    chown -R "$REAL_USER:$REAL_USER" /usr/local/bin/commandFinder
    chmod -R 755 /usr/local/bin/commandFinder
    chown -R "$REAL_USER:$REAL_USER" /usr/local/bin/commandFinder/venv
    chmod -R 755 /usr/local/bin/commandFinder/venv

    cat << EOF > /usr/bin/searchCommand
#!/bin/sh
exec /usr/local/bin/commandFinder/venv/bin/python3 /usr/local/bin/commandFinder/main.py "\$@"
EOF
    chmod +x /usr/bin/searchCommand

    cat << EOF > /usr/bin/gtfsearch
#!/bin/sh
exec /usr/local/bin/commandFinder/venv/bin/python3 /usr/local/bin/commandFinder/gtfsearch.py "\$@"
EOF
    chmod +x /usr/bin/gtfsearch

    log_info "Ownership changed to ${BLUE}${BOLD}$REAL_USER${RESET} for all searchCommand files"
    log_info "Main script installed at ${BLUE}${BOLD}/usr/bin/searchCommand${RESET} and GTFSearch at ${BLUE}${BOLD}/usr/bin/gtfsearch${RESET}"

    return 0
}

# ------------------ MAIN EXECUTION ----------------
main() {
    show_banner
    check_root
    detect_user

    prompt_status="${GREEN}✔${RESET}"

    while true; do
        show_banner
        check_root
        detect_user
        show_menu
        read -e -p "$(echo -e "${GREEN}┌──(${RESET}${BLUE}${BOLD}$REAL_USER${RESET}${GREEN})-[${RESET}${BOLD}SearchCommand${RESET}${GREEN}]-[${prompt_status}${GREEN}]${RESET}\n${GREEN}└──╼${RESET}${BLUE}$ ${RESET}")" choice

        case "$choice" in
            1|2) break ;;
            *) echo -e ""
               log_error "Invalid option. Please choose 1 or 2."
               prompt_status="${RED}✘ ERROR${RESET}"
               sleep 1
               clear ;;
        esac
    done

    case "$choice" in
        1)
            clear
            echo ""
            read -p "$(echo -e "[${YELLOW}${BOLD}!${RESET}] ${BOLD}Confirmation:${RESET} Are you sure you want to install? (y/n): ")" confirm
            [[ "$confirm" != [yY] ]] && { log_info "Installation ${GREEN}cancelled${RESET}."; exit 0; }
            uninstall_searchcommand
            if install_searchcommand; then
                separator
                sleep 3
                show_usage_instructions
                show_installation_summary
                echo -e "\n[${RED}${BOLD}#${RESET}] Made with heart${RED}${BOLD}❣${RESET}, in a world of shit 😎!\n"
                echo -e "\t\t${RED}${BOLD}H4PPY H4CK1NG${RESET}"
            fi
            ;;
        2)
            clear
            read -p "$(echo -e "\n[${BOLD}${YELLOW}!${RESET}] ${BOLD}Confirmation:${RESET} Are you sure you want to uninstall? (y/n): ")" confirm
            [[ "$confirm" != [yY] ]] && { log_info "Uninstallation cancelled."; exit 0; }
            uninstall_searchcommand
            echo -e "\n\t[${RED}${BOLD}#${RESET}] ${RED}${BOLD}SearchCommand${RESET} complete uninstallation 😎 CRACK!\n"
            ;;
    esac
}

main