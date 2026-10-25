@echo off
setlocal
cd /d "%~dp0"

echo Building...
py -3 "%~dp0build-tools.py"
if errorlevel 1 (
    echo.
    echo Build failed. Check the messages above.
    pause
    exit /b 1
)

echo.
echo Build finished. Executables should be in the dist folder.
pause
