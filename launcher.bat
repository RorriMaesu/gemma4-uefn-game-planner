@echo off
title Gemma 4 UEFN Game Planner Setup Launcher
echo Starting installer and bootstrapper...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Setup encountered an issue. Press any key to close.
    pause >nul
)
