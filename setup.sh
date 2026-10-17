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

# 2. Run the automated Python setup
$PYTHON_BIN hbm.py setup

echo "Making ./hbm executable..."
chmod +x hbm hbm.py mcp_drive.py

if [ -d "$HOME/.local/bin" ] || mkdir -p "$HOME/.local/bin" 2>/dev/null; then
    ln -sf "$SCRIPT_DIR/hbm" "$HOME/.local/bin/hbm"
    echo "Linked 'hbm' globally to ~/.local/bin/hbm"
fi

echo "============================================================"
echo "  🎉 All Done! Test it right now with:"
echo "     hbm fetch https://example.com"
echo "============================================================"
