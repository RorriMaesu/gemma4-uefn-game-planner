@echo off
title Gemma 4 UEFN Game Planner Setup Launcher
echo Starting installer and bootstrapper...
:: Prevent Windows security warning prompts for scripts from the internet
set SEE_MASK_NOZONECHECKS=1
powershell -Command "Unblock-File '%~dp0setup.ps1'"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Setup encountered an issue. Press any key to close.
    pause >nul
)
