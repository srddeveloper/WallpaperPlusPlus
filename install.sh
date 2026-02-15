#!/bin/bash

# ── Colors ────────────────────────────────────────────────────────────────────
RESET="\033[0m"
BOLD="\033[1m"
DIM="\033[2m"
GREEN="\033[38;5;154m"
RED="\033[38;5;203m"
CYAN="\033[38;5;51m"
WHITE="\033[97m"
GRAY="\033[38;5;245m"

# ── Banner ────────────────────────────────────────────────────────────────────
clear
echo ""
echo -e "${BOLD}${WHITE}  ██╗    ██╗ █████╗ ██╗     ██╗     ██████╗  █████╗ ██████╗ ███████╗██████╗ ${RESET}"
echo -e "${BOLD}${WHITE}  ██║    ██║██╔══██╗██║     ██║     ██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗${RESET}"
echo -e "${BOLD}${WHITE}  ██║ █╗ ██║███████║██║     ██║     ██████╔╝███████║██████╔╝█████╗  ██████╔╝${RESET}"
echo -e "${BOLD}${WHITE}  ██║███╗██║██╔══██║██║     ██║     ██╔═══╝ ██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗${RESET}"
echo -e "${BOLD}${WHITE}  ╚███╔███╔╝██║  ██║███████╗███████╗██║     ██║  ██║██║     ███████╗██║  ██║${RESET}"
echo -e "${BOLD}${WHITE}   ╚══╝╚══╝ ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝     ╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝${RESET}"
echo ""
echo -e "  ${BOLD}${WHITE}Wallpaper${GREEN}++${RESET}  ${GRAY}Custom wallpapers with desktop icons${RESET}"
echo -e "  ${DIM}${GRAY}github.com/srddeveloper/WallpaperPlusPlus${RESET}"
echo ""
echo -e "  ${GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""

# ── Helpers ───────────────────────────────────────────────────────────────────
step() { echo -e "  ${BOLD}${GREEN}→${RESET}  ${WHITE}$1${RESET}"; }
ok()   { echo -e "  ${GREEN}✓${RESET}  ${GRAY}$1${RESET}"; }
fail() { echo -e "  ${RED}✗${RESET}  ${RED}$1${RESET}"; exit 1; }
info() { echo -e "     ${GRAY}$1${RESET}"; }

spinner() {
    local pid=$1
    local msg=$2
    local frames=("⠋" "⠙" "⠹" "⠸" "⠼" "⠴" "⠦" "⠧" "⠇" "⠏")
    local i=0
    while kill -0 "$pid" 2>/dev/null; do
        printf "\r  ${GREEN}${frames[$i]}${RESET}  ${GRAY}%s${RESET}" "$msg"
        i=$(( (i+1) % 10 ))
        sleep 0.08
    done
    printf "\r                                              \r"
}

INSTALL_DIR="$HOME/.wallpaper-plus"
APP_FILE="$INSTALL_DIR/wallpaper_plus.py"
LAUNCH_FILE="$INSTALL_DIR/launch.sh"
RAW_URL="https://raw.githubusercontent.com/srddeveloper/WallpaperPlusPlus/main/wallpaper_plus.py"

# ── Step 1: macOS check ───────────────────────────────────────────────────────
step "Checking system..."
if [[ "$(uname)" != "Darwin" ]]; then
    fail "Wallpaper++ is macOS only."
fi
ok "macOS detected ($(sw_vers -productVersion))"
echo ""

# ── Step 2: Python check ──────────────────────────────────────────────────────
step "Locating Python..."
PYTHON=""
for candidate in python3 python; do
    if command -v "$candidate" &>/dev/null; then
        PYTHON=$(command -v "$candidate")
        break
    fi
done
if [[ -z "$PYTHON" ]]; then
    fail "Python 3 not found. Install from https://python.org"
fi
ok "Found Python at $PYTHON ($(${PYTHON} --version 2>&1))"
echo ""

# ── Step 3: Check pyobjc ──────────────────────────────────────────────────────
step "Checking dependencies..."
if ! "$PYTHON" -c "import objc" &>/dev/null; then
    info "pyobjc not found — installing..."
    "$PYTHON" -m pip install pyobjc pyobjc-framework-Cocoa --quiet &
    spinner $! "Installing pyobjc (this may take a minute)..."
    wait $!
    if ! "$PYTHON" -c "import objc" &>/dev/null; then
        fail "Failed to install pyobjc. Try: pip install pyobjc"
    fi
fi
ok "pyobjc ready"
echo ""

# ── Step 4: Install ───────────────────────────────────────────────────────────
step "Installing Wallpaper++..."
mkdir -p "$INSTALL_DIR"

curl -fsSL "$RAW_URL" -o "$APP_FILE" &
spinner $! "Downloading wallpaper_plus.py..."
wait $!

if [[ ! -f "$APP_FILE" ]]; then
    fail "Download failed. Check your connection or the repo URL."
fi
ok "Installed to $INSTALL_DIR"

cat > "$LAUNCH_FILE" << EOF
#!/bin/bash
"$PYTHON" "$APP_FILE"
EOF
chmod +x "$LAUNCH_FILE"

if [[ -d "/usr/local/bin" && -w "/usr/local/bin" ]]; then
    ln -sf "$LAUNCH_FILE" /usr/local/bin/wallpaper-plus
    ok "Symlinked → 'wallpaper-plus' command available"
fi
echo ""

# ── Step 5: Launch ────────────────────────────────────────────────────────────
step "Launching Wallpaper++..."
echo ""
echo -e "  ${GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
echo -e "  ${BOLD}${GREEN}All done!${RESET} ${WHITE}Wallpaper++ is starting...${RESET}"
echo ""
echo -e "  ${GRAY}To launch again anytime:${RESET}"
echo -e "  ${CYAN}wallpaper-plus${RESET}  ${GRAY}or${RESET}  ${CYAN}python3 ~/.wallpaper-plus/wallpaper_plus.py${RESET}"
echo ""

nohup "$PYTHON" "$APP_FILE" > /dev/null 2>&1 &
disown
