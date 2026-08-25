@echo off
chcp 65001 >nul
cd /d "%~dp0"
python deploy.py
if %errorlevel% neq 0 (
    echo.
    pause
)
