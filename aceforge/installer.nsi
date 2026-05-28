; ============================================================
; ACEForge NSIS Installer Script
; Requires NSIS 3.x — https://nsis.sourceforge.io/Download
;
; To compile:
;   Right-click this file → "Compile NSIS Script"
;   OR run installer_build.bat
;
; This script wraps the PyInstaller output (dist\ACEForge\)
; into a professional Windows installer wizard.
; ============================================================

;--------------------------------
; General
;--------------------------------

!define APPNAME       "ACEForge"
!define APPVERSION    "1.0.0"
!define APPFULLNAME   "ACEForge v${APPVERSION} — ACEmulator Content Generator"
!define PUBLISHER     "Shattered Dawn"
!define WEBSITE       "https://github.com/ACEmulator/ACE"
!define DESCRIPTION   "ACEmulator content generation tool for server administrators"

; Where PyInstaller output lives (relative to this .nsi file)
!define DIST_DIR      "dist\ACEForge"
!define ICON_PATH     "installer_assets\aceforge.ico"

; Registry key for uninstaller
!define REGKEY        "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"

Name "${APPFULLNAME}"
OutFile "ACEForge_${APPVERSION}_Setup.exe"
InstallDir "$PROGRAMFILES64\${APPNAME}"
InstallDirRegKey HKLM "Software\${APPNAME}" "InstallDir"
RequestExecutionLevel admin
BrandingText "${APPFULLNAME}"

;--------------------------------
; UI — Modern UI 2
;--------------------------------

!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON       "${ICON_PATH}"
!define MUI_UNICON     "${ICON_PATH}"

; Welcome page
!define MUI_WELCOMEPAGE_TITLE    "Welcome to ACEForge Setup"
!define MUI_WELCOMEPAGE_TEXT     "This wizard will install ACEForge ${APPVERSION} on your computer.$\r$\n$\r$\nACEForge is a content generation tool for ACEmulator server administrators. It includes a full Manual weenie editor (no internet required) and an AI generation mode powered by Anthropic's Claude.$\r$\n$\r$\nClick Next to continue."
!define MUI_FINISHPAGE_TITLE     "ACEForge Installation Complete"
!define MUI_FINISHPAGE_TEXT      "ACEForge has been installed successfully.$\r$\n$\r$\nOn first launch, go to Settings to configure your server name, WCID ranges, and optionally your Anthropic API key (required only for AI Mode).$\r$\n$\r$\nClick Finish to close this wizard."
!define MUI_FINISHPAGE_RUN       "$INSTDIR\ACEForge.exe"
!define MUI_FINISHPAGE_RUN_TEXT  "Launch ACEForge now"
!define MUI_FINISHPAGE_LINK      "ACEmulator GitHub"
!define MUI_FINISHPAGE_LINK_LOCATION "${WEBSITE}"

; Pages — Install
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Pages — Uninstall
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Language
!insertmacro MUI_LANGUAGE "English"

;--------------------------------
; Version Info (shows in file properties)
;--------------------------------

VIProductVersion "${APPVERSION}.0"
VIAddVersionKey "ProductName"      "${APPNAME}"
VIAddVersionKey "ProductVersion"   "${APPVERSION}"
VIAddVersionKey "CompanyName"      "${PUBLISHER}"
VIAddVersionKey "FileDescription"  "${DESCRIPTION}"
VIAddVersionKey "FileVersion"      "${APPVERSION}"
VIAddVersionKey "LegalCopyright"   "MIT License"

;--------------------------------
; Install Section
;--------------------------------

Section "ACEForge (required)" SecMain

    SectionIn RO  ; Required — cannot be deselected

    SetOutPath "$INSTDIR"

    ; Copy all PyInstaller output files
    File /r "${DIST_DIR}\*.*"

    ; Write install path to registry
    WriteRegStr HKLM "Software\${APPNAME}" "InstallDir" "$INSTDIR"
    WriteRegStr HKLM "Software\${APPNAME}" "Version"    "${APPVERSION}"

    ; Write uninstaller registry entries (Add/Remove Programs)
    WriteRegStr   HKLM "${REGKEY}" "DisplayName"          "${APPFULLNAME}"
    WriteRegStr   HKLM "${REGKEY}" "DisplayVersion"       "${APPVERSION}"
    WriteRegStr   HKLM "${REGKEY}" "Publisher"            "${PUBLISHER}"
    WriteRegStr   HKLM "${REGKEY}" "URLInfoAbout"         "${WEBSITE}"
    WriteRegStr   HKLM "${REGKEY}" "InstallLocation"      "$INSTDIR"
    WriteRegStr   HKLM "${REGKEY}" "UninstallString"      '"$INSTDIR\Uninstall.exe"'
    WriteRegStr   HKLM "${REGKEY}" "QuietUninstallString" '"$INSTDIR\Uninstall.exe" /S'
    WriteRegDWORD HKLM "${REGKEY}" "NoModify"             1
    WriteRegDWORD HKLM "${REGKEY}" "NoRepair"             1

    ; Estimate installed size for Add/Remove Programs
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "${REGKEY}" "EstimatedSize" "$0"

    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; Start Menu shortcuts
    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    CreateShortCut  "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" \
                    "$INSTDIR\ACEForge.exe" \
                    "" \
                    "$INSTDIR\ACEForge.exe" \
                    0 \
                    SW_SHOWNORMAL \
                    "" \
                    "ACEForge — ACEmulator Content Generator"
    CreateShortCut  "$SMPROGRAMS\${APPNAME}\Uninstall ACEForge.lnk" \
                    "$INSTDIR\Uninstall.exe"

    ; Desktop shortcut
    CreateShortCut  "$DESKTOP\ACEForge.lnk" \
                    "$INSTDIR\ACEForge.exe" \
                    "" \
                    "$INSTDIR\ACEForge.exe" \
                    0 \
                    SW_SHOWNORMAL \
                    "" \
                    "ACEForge — ACEmulator Content Generator"

SectionEnd

;--------------------------------
; Optional: Output Folder shortcut
;--------------------------------

Section /o "Create Documents shortcut" SecDocs

    CreateDirectory "$DOCUMENTS\ACEForge"
    CreateShortCut  "$SMPROGRAMS\${APPNAME}\ACEForge Output Folder.lnk" \
                    "$DOCUMENTS\ACEForge"

SectionEnd

;--------------------------------
; Uninstall Section
;--------------------------------

Section "Uninstall"

    ; Remove all installed files
    RMDir /r "$INSTDIR"

    ; Remove Start Menu folder
    RMDir /r "$SMPROGRAMS\${APPNAME}"

    ; Remove Desktop shortcut
    Delete "$DESKTOP\ACEForge.lnk"

    ; Remove registry entries
    DeleteRegKey HKLM "${REGKEY}"
    DeleteRegKey HKLM "Software\${APPNAME}"

    ; Note: User config in %APPDATA%\ACEForge is intentionally preserved
    ; so settings and WCID ranges survive reinstall.

SectionEnd

;--------------------------------
; Section Descriptions
;--------------------------------

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecMain} \
        "ACEForge application files. Required."
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDocs} \
        "Create a shortcut to the ACEForge output folder in your Documents."
!insertmacro MUI_FUNCTION_DESCRIPTION_END

;--------------------------------
; Installer Functions
;--------------------------------

Function .onInit
    ; Check for existing installation
    ReadRegStr $R0 HKLM "Software\${APPNAME}" "InstallDir"
    ${If} $R0 != ""
        MessageBox MB_YESNO|MB_ICONQUESTION \
            "ACEForge is already installed at:$\r$\n$R0$\r$\n$\r$\nDo you want to reinstall / upgrade?" \
            IDYES proceed
        Abort
        proceed:
    ${EndIf}
FunctionEnd

Function .onInstSuccess
    ; Nothing extra needed — MUI finish page handles launch
FunctionEnd
