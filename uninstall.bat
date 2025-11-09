@echo off
REM Uninstall script for Hanzi Deck Statistics Anki addon
REM This script removes the addon from the Anki addons21 folder

echo ========================================
echo Hanzi Deck Statistics - Uninstaller
echo ========================================
echo.

REM Get Anki addons folder path
set ANKI_ADDONS=%APPDATA%\Anki2\addons21

REM Check if Anki addons folder exists
if not exist "%ANKI_ADDONS%" (
    echo ERROR: Anki addons folder not found at:
    echo %ANKI_ADDONS%
    echo.
    pause
    exit /b 1
)

REM Set target folder
set TARGET_FOLDER=%ANKI_ADDONS%\hanzi_deck_stats

REM Check if addon is installed
if not exist "%TARGET_FOLDER%" (
    echo Addon is not currently installed.
    echo Expected location: %TARGET_FOLDER%
    echo.
    pause
    exit /b 0
)

echo Found addon installation at:
echo %TARGET_FOLDER%
echo.
set /p CONFIRM="Are you sure you want to uninstall? (Y/N): "

if /i not "%CONFIRM%"=="Y" (
    echo.
    echo Uninstallation cancelled.
    pause
    exit /b 0
)

echo.
echo Removing addon...
rmdir /s /q "%TARGET_FOLDER%"

echo.
echo ========================================
echo Uninstallation Complete!
echo ========================================
echo.
echo The addon has been removed from Anki.
echo Please restart Anki for changes to take effect.
echo.
pause
