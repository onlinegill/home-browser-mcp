# ==============================================================================
# Home-Browser MCP — Automated One-Click Setup for Windows PowerShell
# ==============================================================================
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Starting Home-Browser MCP Setup for Windows" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Detect Python
$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonCmd) {
    $PythonCmd = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $PythonCmd) {
    Write-Error "Python 3 is not installed or not in PATH. Please install Python 3.10+ from https://www.python.org"
    exit 1
}

$pyVersion = & $PythonCmd.Source --version
Write-Host "Using Python: $pyVersion" -ForegroundColor Green

# 2. Check Tailscale on Windows
$TailscaleCmd = Get-Command tailscale -ErrorAction SilentlyContinue
$tsInstalled = ($TailscaleCmd -ne $null) -or (Test-Path "C:\Program Files\Tailscale\tailscale.exe")

if (-not $tsInstalled) {
    Write-Host ""
    Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
    Write-Host "  Tailscale Network (Recommended for Remote AI Bots)" -ForegroundColor Yellow
    Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
    Write-Host "Tailscale connects cloud bots (Muse, Groq) to your home PC privately."
    
    $installTs = Read-Host "Would you like to install Tailscale now? [y/N]"
    if ($installTs -match "^[yY]$") {
        if (Get-Command winget -ErrorAction SilentlyContinue) {
            Write-Host "Installing Tailscale via winget..." -ForegroundColor Green
            winget install --id Tailscale.Tailscale --silent --accept-source-agreements --accept-package-agreements
        } else {
            Write-Host "Please download and install Tailscale for Windows: https://tailscale.com/download/windows" -ForegroundColor Yellow
        }
    }
}

# 3. Run hbm.py setup
& $PythonCmd.Source "$ScriptDir\hbm.py" setup

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Setup Finished! Generating your AI & MCP configs..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

& $PythonCmd.Source "$ScriptDir\hbm.py" config
