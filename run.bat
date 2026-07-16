@echo off
REM ── ACEForge — launch from source ─────────────────────────────────────────
REM Runs the app the same way as: python -B -m aceforge.main
REM Double-click this file, or run it from PowerShell/cmd.

REM cd to this script's own folder so it works no matter where it's launched from
cd /d "%~dp0"

title ACEForge
echo Starting ACEForge...
echo.

python -B -m aceforge.main

REM Keep the window open if it crashed so the traceback stays readable
if errorlevel 1 (
    echo.
    echo ACEForge exited with an error. Press any key to close.
    pause >nul
)
