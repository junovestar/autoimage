@echo off
echo Starting Gemini AI Backend...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

cd backend
echo Starting Flask backend on http://localhost:5000
python app.py

pause
