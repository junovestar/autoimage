@echo off
title Gemini AI Image Generator - Simple Start
color 0b

echo.
echo ========================================
echo    🚀 GEMINI AI IMAGE GENERATOR
echo ========================================
echo.

echo 🔍 Kiểm tra cấu trúc thư mục...
if not exist "backend\app.py" (
    echo ❌ Không tìm thấy backend\app.py
    pause
    exit /b 1
)

if not exist "frontend\package.json" (
    echo ❌ Không tìm thấy frontend\package.json
    pause
    exit /b 1
)

echo ✅ Cấu trúc thư mục hợp lệ
echo.

echo 🐍 Khởi động Python backend...
cd backend
start "Backend" cmd /k "python app.py"
cd ..

echo ⏳ Đợi backend khởi động (8 giây)...
timeout /t 8 /nobreak > nul

echo ⚛️ Khởi động React frontend...
cd frontend
start "Frontend" cmd /k "npm start"
cd ..

echo ⏳ Đợi frontend load (15 giây)...
timeout /t 15 /nobreak > nul

echo 🌐 Đang mở trình duyệt...
start http://localhost:3000

echo.
echo ========================================
echo           ✅ KHỞI ĐỘNG THÀNH CÔNG!
echo ========================================
echo.
echo 🌐 Frontend: http://localhost:3000
echo 🔧 Backend:  http://localhost:5000
echo.
echo 💡 Nếu frontend chưa load, hãy:
echo    1. Kiểm tra cửa sổ Frontend terminal
echo    2. Đợi thêm vài giây
echo    3. Refresh trang web
echo.
echo 🔄 Để dừng: Đóng các cửa sổ terminal
echo.
pause
