@echo off
chcp 65001 > nul
title EyeTracker AI (Debug Console)
cd /d "%~dp0"

echo ========================================================
echo   EyeTracker AI - Режим отладки (консоль)
echo ========================================================

".venv\Scripts\python.exe" gui_app.py
pause
