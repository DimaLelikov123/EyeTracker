@echo off
title EyeTracker
cd /d "%~dp0"

if not exist "%~dp0.venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment .venv not found in %~dp0
    echo Please make sure .venv exists.
    pause
    exit /b 1
)

"%~dp0.venv\Scripts\python.exe" "%~dp0gui_app.py"
if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with error.
    pause
)
