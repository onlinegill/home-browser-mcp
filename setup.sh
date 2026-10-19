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

# 1. Detect Python 3
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

# 3. Run the automated Python setup
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
echo "  🎉 All Done! Test it right now with:"
echo "     $CMD_CALL fetch https://example.com"
if [ "$CMD_CALL" = "./hbm" ]; then
    echo ""
    echo "  (Use '$CMD_CALL' while in this directory, or add ~/.local/bin to your PATH)"
fi
echo "============================================================"
