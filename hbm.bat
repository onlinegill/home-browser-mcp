@echo off
setlocal
set "SCRIPT_DIR=%~dp0"

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python "%SCRIPT_DIR%hbm.py" %*
) else (
    where py >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        py "%SCRIPT_DIR%hbm.py" %*
    ) else (
        echo [ERROR] Python 3 not found in PATH.
        exit /b 1
    )
)
