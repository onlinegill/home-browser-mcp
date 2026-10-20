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

%PYTHON_BIN% "%SCRIPT_DIR%hbm.py" setup

echo.
echo ============================================================
echo   Setup Finished! Generating your AI & MCP configs...
echo ============================================================
%PYTHON_BIN% "%SCRIPT_DIR%hbm.py" config
