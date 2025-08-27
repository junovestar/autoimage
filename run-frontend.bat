@echo off
echo Starting Gemini AI Frontend...
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    pause
    exit /b 1
)

cd frontend
echo Starting React frontend on http://localhost:3000
npm start

pause
