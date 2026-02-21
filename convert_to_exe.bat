@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   Python to EXE Converter
echo ========================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b
)

:: Check for PyInstaller (Try both case variants)
python -m PyInstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    python -m pyinstaller --version >nul 2>&1
    if !errorlevel! neq 0 (
        echo [INFO] PyInstaller not found. Installing...
        pip install pyinstaller
    )
)

:: Try to find the execution command
set "PYCMD=python -m PyInstaller"
python -m PyInstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    set "PYCMD=python -m pyinstaller"
    python -m pyinstaller --version >nul 2>&1
    if !errorlevel! neq 0 (
        :: Try direct command if it's in PATH
        pyinstaller --version >nul 2>&1
        if !errorlevel! equ 0 (
            set "PYCMD=pyinstaller"
        ) else (
            echo [ERROR] Could not start PyInstaller. 
            echo Please try running: pip install --upgrade pyinstaller
            pause
            exit /b
        )
    )
)

echo [INFO] Converting shutdown.py to EXE using: !PYCMD!
echo [INFO] This might take a minute...

:: Run PyInstaller
!PYCMD! --onefile --noconsole --clean --name "ShutdownManager" shutdown.py

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   SUCCESS: EXE created in 'dist' folder
    echo ========================================
    echo.
    echo Cleaning up temporary build files...
    if exist "build" rm /s /q "build"
    if exist "ShutdownManager.spec" del /q "ShutdownManager.spec"
    echo Done.
) else (
    echo.
    echo [ERROR] Conversion failed.
    echo.
)

pause
