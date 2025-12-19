@echo off
REM Windows batch file launcher for Stock OHLC Dashboard
REM Checks and installs packages, then runs the dashboard

echo ============================================================
echo Stock OHLC Analysis Admin Dashboard - Launcher
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.7 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo Python found!
echo.

REM Check if pip is available
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not available!
    pause
    exit /b 1
)

echo Checking and installing required packages...
echo.

REM Install packages from requirements.txt
python -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo.
    echo WARNING: Some packages may not have installed correctly.
    echo You can try installing manually: pip install -r requirements.txt
    echo.
    pause
)

echo.
echo ============================================================
echo Starting Dashboard...
echo ============================================================
echo.
echo The dashboard will open in your default web browser.
echo If it doesn't open automatically, go to: http://localhost:8501
echo.
echo Press Ctrl+C to stop the server.
echo.

REM Run Streamlit dashboard
streamlit run dashboard.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo Dashboard exited with an error.
    pause
)

