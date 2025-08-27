@echo off
title Gemini AI Image Generator
color 0b

echo.
echo ========================================
echo    🚀 GEMINI AI IMAGE GENERATOR
echo ========================================
echo.

echo 🔍 Kiểm tra cấu trúc thư mục...
if not exist "backend\app.py" (
    echo ❌ Không tìm thấy backend\app.py
    echo 📁 Đảm bảo bạn đang ở thư mục gốc của dự án
    pause
    exit /b 1
)

if not exist "frontend\package.json" (
    echo ❌ Không tìm thấy frontend\package.json
    echo 📁 Đảm bảo bạn đang ở thư mục gốc của dự án
    pause
    exit /b 1
)

echo ✅ Cấu trúc thư mục hợp lệ
echo.

echo 🐍 Khởi động Python backend...
cd backend
start "Backend" cmd /k "python app.py"
cd ..

echo ⏳ Đợi backend khởi động (5 giây)...
timeout /t 5 /nobreak > nul

echo ⚛️ Khởi động React frontend...
cd frontend
set BROWSER=none
start "Frontend" cmd /k "npm start"
cd ..

echo ⏳ Đợi frontend load (10 giây)...
timeout /t 10 /nobreak > nul

echo 🌐 Đang mở trình duyệt...
start http://localhost:3000
timeout /t 2 /nobreak > nul

echo.
echo ========================================
echo           ✅ KHỞI ĐỘNG THÀNH CÔNG!
echo ========================================
echo.
echo 🌐 Frontend: http://localhost:3000
echo 🔧 Backend:  http://localhost:5000
echo.
echo 💡 HƯỚNG DẪN SỬ DỤNG:
echo    1. Thêm API keys trong tab "Cài đặt"
echo    2. Tạo ảnh trong tab "Tạo ảnh"
echo    3. Xem lịch sử trong tab "Lịch sử"
echo.
echo 📝 Lưu ý: 
echo    - Tasks chạy ngay cả khi tắt trình duyệt
echo    - Có thể upload ảnh để tạo Image-to-Image
echo    - Sử dụng "Phân tách prompt" để xử lý nhiều prompt
echo.
echo 🔄 Để dừng: Đóng các cửa sổ terminal
echo.
echo 💬 Ứng dụng đang chạy... Giữ cửa sổ này mở
pause > nul
