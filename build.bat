@echo off
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   ACEForge Build Script
echo   Compiles ACEForge into a standalone Windows executable
echo ============================================================
echo.

:: ── Check Python ─────────────────────────────────────────────────────────────
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH.
    echo         Please install Python 3.10+ from https://python.org
    echo         Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [OK] Python %PYVER% found.

:: ── Check pip ────────────────────────────────────────────────────────────────
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pip not found. Please reinstall Python.
    pause
    exit /b 1
)

:: ── Install / upgrade dependencies ───────────────────────────────────────────
echo.
echo [STEP 1/4] Installing dependencies...
echo.
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet
python -m pip install pyinstaller --quiet

if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo [OK] Dependencies installed.

:: ── Check reference files ────────────────────────────────────────────────────
echo.
echo [STEP 2/4] Checking reference files...
echo.

set MISSING_REFS=0
set REF_DIR=aceforge\references

if not exist "%REF_DIR%\enums.md" (
    echo [WARN] Missing: %REF_DIR%\enums.md
    set MISSING_REFS=1
)
if not exist "%REF_DIR%\did_values.md" (
    echo [WARN] Missing: %REF_DIR%\did_values.md
    set MISSING_REFS=1
)
if not exist "%REF_DIR%\icons.md" (
    echo [WARN] Missing: %REF_DIR%\icons.md
    set MISSING_REFS=1
)

if !MISSING_REFS! equ 1 (
    echo.
    echo [WARN] Some reference files are missing from aceforge\references\
    echo        AI Mode will not work correctly without them.
    echo        Copy files from ace-content-generator.skill before distributing.
    echo        Continuing build anyway...
    echo.
)

if !MISSING_REFS! equ 0 (
    echo [OK] All reference files present.
)

:: ── PyInstaller build ────────────────────────────────────────────────────────
echo.
echo [STEP 3/4] Building executable with PyInstaller...
echo        This may take 2-5 minutes.
echo.

if exist "dist\ACEForge" (
    echo Cleaning previous build...
    rmdir /s /q "dist\ACEForge" 2>nul
)
if exist "build" (
    rmdir /s /q "build" 2>nul
)

python -m PyInstaller ACEForge.spec --noconfirm --clean

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] PyInstaller build failed.
    echo         Check the output above for details.
    pause
    exit /b 1
)

:: ── Verify output ────────────────────────────────────────────────────────────
if not exist "dist\ACEForge\ACEForge.exe" (
    echo [ERROR] Build completed but ACEForge.exe not found in dist\ACEForge\
    pause
    exit /b 1
)

echo.
echo [STEP 4/4] Build complete!
echo.
echo ============================================================
echo   SUCCESS!
echo   Executable: dist\ACEForge\ACEForge.exe
echo.
echo   To run directly: dist\ACEForge\ACEForge.exe
echo.
echo   To create an installer:
echo     1. Install NSIS from https://nsis.sourceforge.io
echo     2. Right-click installer.nsi → Compile NSIS Script
echo        OR run: installer_build.bat
echo ============================================================
echo.

:: ── Offer to launch ──────────────────────────────────────────────────────────
set /p LAUNCH="Launch ACEForge now? (y/n): "
if /i "%LAUNCH%"=="y" (
    start "" "dist\ACEForge\ACEForge.exe"
)

pause
