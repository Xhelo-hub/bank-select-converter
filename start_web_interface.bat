@echo off
title Albanian Bank Statement Converter - Web Interface

echo.
echo ====================================================
echo  Albanian Bank Statement Converter - Web Interface
echo ====================================================
echo.
echo Starting the web application...
echo.

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run setup first by executing: python -m venv .venv
    echo Then activate it and install requirements: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment and start Flask app
call .venv\Scripts\activate.bat

REM Check if Flask is installed
python -c "import flask" 2>nul
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install packages!
        pause
        exit /b 1
    )
)

echo.
echo Web interface will open automatically in your browser...
echo.
echo Available at:
echo   - Local:    http://127.0.0.1:5000
echo   - Network:  http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the Flask application
python app.py

pause