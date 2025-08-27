@echo off
echo Installing Dependencies for Gemini AI Image Generator...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    pause
    exit /b 1
)

echo Installing Python dependencies...
cd backend
pip install -r requirements.txt
cd ..

echo.
echo Installing Node.js dependencies...
cd frontend
npm install
cd ..

echo.
echo Dependencies installation completed!
echo.
echo You can now run the application using:
echo - run.bat (for both services)
echo - run-backend.bat (for backend only)
echo - run-frontend.bat (for frontend only)
echo.
pause
