#!/usr/bin/env bash
# ==============================================================================
# Home-Browser MCP (HBM) — One-Click Automated Setup
# Works on macOS, Linux (Debian/Ubuntu/Arch/Fedora), and Raspberry Pi
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "  🚀 Starting Home-Browser MCP One-Click Setup"
echo "============================================================"

# 1. Check Git installation
if ! command -v git >/dev/null 2>&1; then
    echo "⚠️  Git not detected. Installing Git..."
    if [ "$(uname)" = "Darwin" ]; then
        if command -v brew >/dev/null 2>&1; then
            brew install git || true
        else
            echo "Prompting Xcode Command Line Tools for Git..."
            xcode-select --install 2>/dev/null || true
        fi
    elif [ "$(id -u)" -eq 0 ]; then
        if command -v apt-get >/dev/null 2>&1; then
            apt-get update -qq && apt-get install -y git
        elif command -v dnf >/dev/null 2>&1; then
            dnf install -y git
        elif command -v pacman >/dev/null 2>&1; then
            pacman -Sy --noconfirm git
        fi
    elif command -v sudo >/dev/null 2>&1; then
        if command -v apt-get >/dev/null 2>&1; then
            sudo apt-get update -qq && sudo apt-get install -y git
        elif command -v dnf >/dev/null 2>&1; then
            sudo dnf install -y git
        elif command -v pacman >/dev/null 2>&1; then
            sudo pacman -Sy --noconfirm git
        fi
    else
        echo "Note: Git could not be installed automatically. Please install git."
    fi
fi

# 2. Detect Python 3
PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "❌ Error: Python 3 is not installed. Please install Python 3.10+ first."
    exit 1
fi

echo "Using Python: $($PYTHON_BIN --version)"

# 2. Check for ensurepip / python3-venv on Debian/Ubuntu/Proxmox
if ! $PYTHON_BIN -c "import ensurepip" >/dev/null 2>&1; then
    echo "⚠️  Debian/Ubuntu/Proxmox detected without python3-venv."
    if [ "$(id -u)" -eq 0 ]; then
        echo "Installing python3-venv & python3-pip as root..."
        apt-get update -qq && apt-get install -y python3-venv python3-pip
    elif command -v sudo >/dev/null 2>&1; then
        echo "Installing python3-venv & python3-pip with sudo..."
        sudo apt-get update -qq && sudo apt-get install -y python3-venv python3-pip
    else
        echo "❌ Missing python3-venv. Please run: apt install -y python3-venv python3-pip"
        exit 1
    fi
fi

# 3. Optional Tailscale Detection & Prompt
if ! command -v tailscale >/dev/null 2>&1; then
    echo ""
    echo "------------------------------------------------------------"
    echo "  🌐 Tailscale Network (Recommended for Remote AI Bots)"
    echo "------------------------------------------------------------"
    echo "Tailscale connects cloud bots (Muse, Groq) to your home computer"
    echo "privately without needing open router ports."
    echo ""
    INSTALL_TS="n"
    if [ -t 0 ] || [ -c /dev/tty ]; then
        read -r -p "Would you like to install Tailscale now? [y/N]: " INSTALL_TS < /dev/tty 2>/dev/null || INSTALL_TS="n"
    fi
    if [[ "$INSTALL_TS" =~ ^[Yy]$ ]]; then
        echo "Installing Tailscale..."
        if [ "$(uname)" = "Darwin" ]; then
            if command -v brew >/dev/null 2>&1; then
                brew install --cask tailscale 2>/dev/null || brew install tailscale 2>/dev/null || true
            else
                echo "Please install Tailscale for macOS from: https://tailscale.com/download/mac"
            fi
        else
            # Linux (Debian, Ubuntu, Proxmox, Raspberry Pi, etc.)
            curl -fsSL https://tailscale.com/install.sh | sh || true
        fi
        echo "👉 Once installed, run 'tailscale up' to log in and get your private IP."
        echo ""
    else
        echo "Skipping Tailscale install (you can install anytime from https://tailscale.com/download)."
    fi
elif ! tailscale ip -4 >/dev/null 2>&1; then
    echo "💡 Note: Tailscale is installed but not active. Run 'tailscale up' to connect."
fi

# 4. Run the automated Python setup
$PYTHON_BIN hbm.py setup

echo "Making ./hbm executable..."
chmod +x hbm hbm.py mcp_drive.py

# Link hbm to system PATH based on OS and permissions
if [ -w "/usr/local/bin" ]; then
    ln -sf "$SCRIPT_DIR/hbm" /usr/local/bin/hbm
    echo "Linked 'hbm' globally to /usr/local/bin/hbm"
elif command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
    sudo ln -sf "$SCRIPT_DIR/hbm" /usr/local/bin/hbm
    echo "Linked 'hbm' globally to /usr/local/bin/hbm"
elif [ -d "$HOME/.local/bin" ] || mkdir -p "$HOME/.local/bin" 2>/dev/null; then
    ln -sf "$SCRIPT_DIR/hbm" "$HOME/.local/bin/hbm"
    echo "Linked 'hbm' to ~/.local/bin/hbm"
fi

# Detect whether hbm is directly in the active PATH
CMD_CALL="./hbm"
if command -v hbm >/dev/null 2>&1; then
    CMD_CALL="hbm"
elif [ -x "/usr/local/bin/hbm" ] && echo ":$PATH:" | grep -q ":/usr/local/bin:"; then
    CMD_CALL="hbm"
elif [ -x "$HOME/.local/bin/hbm" ] && echo ":$PATH:" | grep -q ":$HOME/.local/bin:"; then
    CMD_CALL="hbm"
fi

echo "============================================================"
echo "  🎉 Setup Finished! Generating your AI & MCP configs..."
echo "============================================================"

# Display the ready-to-copy AI & MCP configuration snippets
"$SCRIPT_DIR/hbm" config
