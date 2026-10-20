@echo off
setlocal
echo ============================================================
echo   Home-Browser MCP - Automated Windows Setup
echo ============================================================

set "SCRIPT_DIR=%~dp0"
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_BIN=python"
) else (
    where py >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set "PYTHON_BIN=py"
    ) else (
        echo [ERROR] Python 3 is not installed or not in your PATH.
        echo Please install Python 3.10+ from https://www.python.org or Microsoft Store.
        exit /b 1
    )
)

echo Using Python:
%PYTHON_BIN% --version

REM Check Git
where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [NOTICE] Git is not installed. Checking for winget...
    where winget >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo Installing Git via winget...
        winget install --id Git.Git -e --source winget --silent --accept-source-agreements --accept-package-agreements
    ) else (
        echo [NOTICE] Git not found. You can install it from https://git-scm.com/download/win
    )
)

%PYTHON_BIN% "%SCRIPT_DIR%hbm.py" setup

echo.
echo ============================================================
echo   Setup Finished! Generating your AI & MCP configs...
echo ============================================================
%PYTHON_BIN% "%SCRIPT_DIR%hbm.py" config
