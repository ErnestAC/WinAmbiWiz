@echo off
setlocal

echo ==========================================
echo AmbiWiz - Windows dependency installer
echo ==========================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found.
    echo Install Python 3.10+ and make sure "Add Python to PATH" is enabled.
    pause
    exit /b 1
)

echo Python found.
python --version
echo.

echo Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Installing AmbiWiz dependencies...
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERROR: Dependency installation failed.
    pause
    exit /b 1
)

echo.
echo Installation complete.
echo.
echo Run AmbiWiz with:
echo     python ambiwiz.py
echo.
pause
