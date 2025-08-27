# Gemini AI Image Generator Startup Script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   🚀 GEMINI AI IMAGE GENERATOR" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if backend and frontend exist
if (-not (Test-Path "backend\app.py")) {
    Write-Host "❌ Không tìm thấy backend\app.py" -ForegroundColor Red
    Read-Host "Nhấn Enter để thoát"
    exit 1
}

if (-not (Test-Path "frontend\package.json")) {
    Write-Host "❌ Không tìm thấy frontend\package.json" -ForegroundColor Red
    Read-Host "Nhấn Enter để thoát"
    exit 1
}

Write-Host "✅ Cấu trúc thư mục hợp lệ" -ForegroundColor Green
Write-Host ""

# Start backend
Write-Host "🐍 Khởi động Python backend..." -ForegroundColor Yellow
Start-Process -FilePath "cmd" -ArgumentList "/k", "cd backend && python app.py" -WindowStyle Normal
Write-Host "⏳ Đợi backend khởi động (8 giây)..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# Check if backend is running
$backendRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000" -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        $backendRunning = $true
        Write-Host "✅ Backend đã khởi động thành công" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️ Backend chưa sẵn sàng, tiếp tục..." -ForegroundColor Yellow
}

# Start frontend
Write-Host "⚛️ Khởi động React frontend..." -ForegroundColor Yellow
$env:BROWSER = "none"
Start-Process -FilePath "cmd" -ArgumentList "/k", "cd frontend && npm start" -WindowStyle Normal
Write-Host "⏳ Đợi frontend load (15 giây)..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Open browser
Write-Host "🌐 Đang mở trình duyệt..." -ForegroundColor Yellow
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "           ✅ KHỞI ĐỘNG THÀNH CÔNG!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "🔧 Backend:  http://localhost:5000" -ForegroundColor White
Write-Host ""
Write-Host "💡 Nếu frontend chưa load, hãy:" -ForegroundColor Yellow
Write-Host "   1. Kiểm tra cửa sổ Frontend terminal" -ForegroundColor White
Write-Host "   2. Đợi thêm vài giây" -ForegroundColor White
Write-Host "   3. Refresh trang web" -ForegroundColor White
Write-Host ""
Write-Host "🔄 Để dừng: Đóng các cửa sổ terminal" -ForegroundColor Yellow
Write-Host ""
Read-Host "Nhấn Enter để thoát"
