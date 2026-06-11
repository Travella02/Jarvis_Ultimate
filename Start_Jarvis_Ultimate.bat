@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

python scripts\start_jarvis.py

if errorlevel 1 (
    echo.
    echo Jarvis exited with an error. Press any key to close this window.
    pause >nul
)
