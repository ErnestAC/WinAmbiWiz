```bat
@echo off
setlocal

echo ==========================================
echo AmbiWiz - Windows dependency installer
echo ==========================================
echo.

REM ============================================================
REM Check Python
REM ============================================================

where python >nul 2>&1

if errorlevel 1 (
    echo ERROR: Python was not found.
    echo.
    echo Install Python 3.10 or newer and make sure
    echo "Add Python to PATH" is enabled.
    echo.
    pause
    exit /b 1
)

echo Python found.
python --version
echo.


REM ============================================================
REM Upgrade pip
REM ============================================================

echo Upgrading pip...
python -m pip install --upgrade pip

if errorlevel 1 (
    echo.
    echo ERROR: Failed to upgrade pip.
    pause
    exit /b 1
)

echo.


REM ============================================================
REM Install AmbiWiz dependencies
REM ============================================================

echo Installing AmbiWiz dependencies...
echo.
echo   - dxcam
echo   - numpy
echo.

python -m pip install --upgrade dxcam numpy

if errorlevel 1 (
    echo.
    echo ERROR: Dependency installation failed.
    echo.
    pause
    exit /b 1
)

echo.


REM ============================================================
REM Verify dependencies
REM ============================================================

echo ==========================================
echo Verifying installation
echo ==========================================
echo.

python -c "import dxcam; print('DXcam: OK')"

if errorlevel 1 (
    echo.
    echo ERROR: DXcam could not be imported.
    pause
    exit /b 1
)

python -c "import numpy; print('NumPy: OK - ' + numpy.__version__)"

if errorlevel 1 (
    echo.
    echo ERROR: NumPy could not be imported.
    pause
    exit /b 1
)

echo.


REM ============================================================
REM Finished
REM ============================================================

echo ==========================================
echo Installation complete
echo ==========================================
echo.
echo AmbiWiz is ready to run.
echo.
echo Run AmbiWiz with:
echo.
echo     python ambiwiz.py
echo.

pause
```
