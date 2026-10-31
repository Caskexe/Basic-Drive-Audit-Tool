@echo off
REM Basic Drive Audit Tool (BDAT) - build script
REM Author: CASK.exe - https://github.com/Caskexe
REM Builds a single portable exe into the dist folder using PyInstaller
REM Requirements: Python 3.8 or newer on PATH. PyInstaller is installed automatically if missing.

setlocal
cd /d "%~dp0"

set "APP_NAME=Basic Drive Audit Tool"
set "SCRIPT=drive-audit.py"
set "ICON=drive-audit.ico"

REM Check that Python is available
where python >nul 2>nul
if errorlevel 1 (
	echo Python was not found on PATH. Install Python 3.8 or newer and try again.
	pause
	exit /b 1
)

REM Check that the files we need are in this folder
if not exist "%SCRIPT%" (
	echo Could not find %SCRIPT% in this folder.
	pause
	exit /b 1
)
if not exist "%ICON%" (
	echo Could not find %ICON% in this folder. Run make-icon.py to create it ^(needs Pillow^).
	pause
	exit /b 1
)

REM Install PyInstaller only when it is missing
python -m PyInstaller --version >nul 2>nul
if errorlevel 1 (
	echo Installing PyInstaller...
	python -m pip install pyinstaller
	if errorlevel 1 (
		echo PyInstaller could not be installed.
		pause
		exit /b 1
	)
)

REM Remove output from any earlier build
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build one windowed exe with the icon embedded and bundled for the window title bar
echo Building "%APP_NAME%.exe"...
python -m PyInstaller --noconfirm --onefile --noconsole --name "%APP_NAME%" --icon "%ICON%" --add-data "%ICON%;." "%SCRIPT%"
if errorlevel 1 (
	echo Build failed. See the messages above.
	pause
	exit /b 1
)

REM Tidy up the temporary build files
if exist build rmdir /s /q build
if exist "%APP_NAME%.spec" del "%APP_NAME%.spec"

echo.
echo Done. Your exe is at: %~dp0dist\%APP_NAME%.exe
pause
endlocal
