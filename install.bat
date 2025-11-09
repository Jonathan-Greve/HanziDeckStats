@echo off
REM Install script for Hanzi Deck Statistics Anki addon
REM This script copies the addon files to the Anki addons21 folder

echo ========================================
echo Hanzi Deck Statistics - Installer
echo ========================================
echo.

REM Get Anki addons folder path
set ANKI_ADDONS=%APPDATA%\Anki2\addons21

REM Check if Anki addons folder exists
if not exist "%ANKI_ADDONS%" (
    echo ERROR: Anki addons folder not found at:
    echo %ANKI_ADDONS%
    echo.
    echo Please make sure Anki is installed and has been run at least once.
    echo.
    pause
    exit /b 1
)

echo Found Anki addons folder:
echo %ANKI_ADDONS%
echo.

REM Set target folder
set TARGET_FOLDER=%ANKI_ADDONS%\hanzi_deck_stats

REM Check if addon is already installed
if exist "%TARGET_FOLDER%" (
    echo WARNING: Addon folder already exists.
    echo %TARGET_FOLDER%
    echo.
    set /p OVERWRITE="Do you want to overwrite it? (Y/N): "
    if /i not "%OVERWRITE%"=="Y" (
        echo.
        echo Installation cancelled.
        pause
        exit /b 0
    )
    echo.
    echo Removing old installation...
    rmdir /s /q "%TARGET_FOLDER%"
)

REM Create target folder
echo Creating addon folder...
mkdir "%TARGET_FOLDER%"

REM Copy Python files
echo Copying addon files...
copy /y "__init__.py" "%TARGET_FOLDER%\" >nul
copy /y "character_data.py" "%TARGET_FOLDER%\" >nul
copy /y "hanzi_detector.py" "%TARGET_FOLDER%\" >nul
copy /y "stats_calculator.py" "%TARGET_FOLDER%\" >nul
copy /y "stats_dialog.py" "%TARGET_FOLDER%\" >nul

REM Copy configuration files
copy /y "config.json" "%TARGET_FOLDER%\" >nul
copy /y "config.md" "%TARGET_FOLDER%\" >nul
copy /y "manifest.json" "%TARGET_FOLDER%\" >nul

REM Copy datasets folder
echo Copying datasets...
mkdir "%TARGET_FOLDER%\datasets"
copy /y "datasets\hsk30-chars.csv" "%TARGET_FOLDER%\datasets\" >nul
copy /y "datasets\mega_hanzi_compilation.csv" "%TARGET_FOLDER%\datasets\" >nul

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Addon installed to:
echo %TARGET_FOLDER%
echo.
echo IMPORTANT: Please restart Anki to load the addon.
echo After restarting, you can access it via:
echo Tools ^> Hanzi Deck Stats
echo.
pause
