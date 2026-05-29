@echo off
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   ACEForge Installer Build Script
echo   Wraps dist\ACEForge\ into a Windows setup wizard
echo ============================================================
echo.

:: ── Check that PyInstaller step has been run ──────────────────────────────────
if not exist "dist\ACEForge\ACEForge.exe" (
    echo [ERROR] dist\ACEForge\ACEForge.exe not found.
    echo         Run build.bat first to compile the application.
    echo.
    pause
    exit /b 1
)
echo [OK] ACEForge.exe found in dist\ACEForge\

:: ── Check for LICENSE.txt ──────────────────────────────────────────────────────
if not exist "LICENSE.txt" (
    echo [WARN] LICENSE.txt not found. Creating placeholder...
    echo MIT License > LICENSE.txt
    echo. >> LICENSE.txt
    echo Copyright ^(c^) 2025 ACEForge Contributors >> LICENSE.txt
    echo. >> LICENSE.txt
    echo Permission is hereby granted, free of charge, to any person obtaining a copy >> LICENSE.txt
    echo of this software and associated documentation files ^(the "Software"^), to deal >> LICENSE.txt
    echo in the Software without restriction, including without limitation the rights >> LICENSE.txt
    echo to use, copy, modify, merge, publish, distribute, sublicense, and/or sell >> LICENSE.txt
    echo copies of the Software, and to permit persons to whom the Software is >> LICENSE.txt
    echo furnished to do so, subject to the following conditions: >> LICENSE.txt
    echo. >> LICENSE.txt
    echo The above copyright notice and this permission notice shall be included in all >> LICENSE.txt
    echo copies or substantial portions of the Software. >> LICENSE.txt
    echo. >> LICENSE.txt
    echo THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND. >> LICENSE.txt
)

:: ── Create installer_assets folder if missing ─────────────────────────────────
if not exist "installer_assets" (
    mkdir installer_assets
    echo [INFO] Created installer_assets\ folder.
    echo        Add aceforge.ico there for a custom installer icon.
    echo        Using NSIS default icon for now.
)

:: ── Patch installer.nsi if no icon exists ─────────────────────────────────────
if not exist "installer_assets\aceforge.ico" (
    echo [INFO] No icon found. Patching installer.nsi to skip icon...
    :: Use a temporary patched version without icon references
    powershell -Command "(Get-Content installer.nsi) -replace '!define MUI_ICON.*', '' -replace '!define MUI_UNICON.*', '' -replace 'VIAddVersionKey.*', '' | Set-Content installer_patched.nsi"
    set NSI_FILE=installer_patched.nsi
) else (
    set NSI_FILE=installer.nsi
)

:: ── Find NSIS ─────────────────────────────────────────────────────────────────
set NSIS_PATH=""

:: Common NSIS install locations
if exist "C:\Program Files (x86)\NSIS\makensis.exe" (
    set NSIS_PATH="C:\Program Files (x86)\NSIS\makensis.exe"
    goto :found_nsis
)
if exist "C:\Program Files\NSIS\makensis.exe" (
    set NSIS_PATH="C:\Program Files\NSIS\makensis.exe"
    goto :found_nsis
)

:: Check PATH
where makensis >nul 2>&1
if %errorlevel% equ 0 (
    set NSIS_PATH=makensis
    goto :found_nsis
)

echo.
echo [ERROR] NSIS (makensis.exe) not found.
echo.
echo   NSIS is a free tool that creates Windows installers.
echo   Download it from: https://nsis.sourceforge.io/Download
echo.
echo   1. Download and install NSIS (the .exe installer)
echo   2. Re-run this script
echo.
echo   Alternatively, you can compile the installer manually:
echo     Right-click installer.nsi → "Compile NSIS Script"
echo.
pause
exit /b 1

:found_nsis
echo [OK] NSIS found at: %NSIS_PATH%

:: ── Compile installer ─────────────────────────────────────────────────────────
echo.
echo [STEP] Compiling installer...
echo.

%NSIS_PATH% /V2 "%NSI_FILE%"

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] NSIS compilation failed.
    echo         Check the output above for details.
    if exist "installer_patched.nsi" del "installer_patched.nsi"
    pause
    exit /b 1
)

:: ── Cleanup temp files ───────────────────────────────────────────────────────
if exist "installer_patched.nsi" del "installer_patched.nsi"

:: ── Verify output ────────────────────────────────────────────────────────────
if not exist "ACEForge_1.0.0_Setup.exe" (
    echo [ERROR] Installer not found after compilation.
    pause
    exit /b 1
)

:: Get file size
for %%F in ("ACEForge_1.0.0_Setup.exe") do set FSIZE=%%~zF
set /a FSIZE_MB=!FSIZE! / 1048576

echo.
echo ============================================================
echo   SUCCESS!
echo.
echo   Installer: ACEForge_1.0.0_Setup.exe  (!FSIZE_MB! MB)
echo.
echo   Distribute this single file to your users.
echo   They double-click it, follow the wizard, and they're done.
echo.
echo   The installer:
echo     - Copies ACEForge to Program Files
echo     - Creates a Start Menu shortcut
echo     - Creates a Desktop shortcut
echo     - Registers in Add/Remove Programs
echo     - Includes an uninstaller
echo ============================================================
echo.

set /p OPEN="Open folder containing installer? (y/n): "
if /i "!OPEN!"=="y" explorer /select,"ACEForge_1.0.0_Setup.exe"

pause
