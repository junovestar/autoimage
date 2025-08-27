# PHÂN TÍCH DỰ ÁN GEMINI AI IMAGE GENERATOR

## 🎯 Tổng quan dự án
Dự án này là một ứng dụng web tạo ảnh hàng loạt sử dụng Google Gemini AI, với khả năng đồng bộ hóa nhân vật và quản lý nhiều API keys.

## 🏗️ Kiến trúc hệ thống

### Backend (Flask)
- **File chính**: `backend/app.py`
- **Port**: 5000
- **Chức năng chính**:
  - Quản lý API keys Gemini
  - Tạo ảnh hàng loạt
  - Phân tích nhân vật từ ảnh
  - Quản lý hàng đợi tasks
  - Upload và xử lý ảnh

### Frontend (React)
- **File chính**: `frontend/src/App.js`
- **Port**: 3000 (với proxy đến backend 5000)
- **Chức năng chính**:
  - Giao diện người dùng
  - Quản lý API keys
  - Tạo và theo dõi tasks
  - Upload ảnh nhân vật
  - Xem kết quả và tải xuống

## 🔧 Các thành phần chính

### 1. GeminiImageGenerator
```python
class GeminiImageGenerator:
    - Quản lý danh sách API keys
    - Retry logic khi API key hết quota
    - Tạo ảnh với model gemini-2.0-flash-preview-image-generation
    - Hỗ trợ image-to-image và text-to-image
```

### 2. CharacterAnalyzer
```python
class CharacterAnalyzer:
    - Phân tích nhân vật từ ảnh upload
    - Trích xuất thông tin màu sắc chi tiết
    - Tăng cường prompt với thông tin nhân vật
```

### 3. TaskManager
```python
class TaskManager:
    - Quản lý hàng đợi tasks
    - Background processing
    - Lưu trữ kết quả
    - Theo dõi tiến độ
```

### 4. PromptProcessor
```python
class PromptProcessor:
    - Phân tách text thành các prompt riêng biệt
    - Sử dụng AI hoặc pattern matching
    - Hỗ trợ bulk text processing
```

## 🎨 Tính năng đồng bộ nhân vật

### Prompt phân tích nhân vật (Đã cải thiện với màu sắc tổng thể)
```python
analysis_prompt = """
Hãy phân tích các đặc điểm CỐ ĐỊNH của nhân vật và màu sắc tổng thể của ảnh này để AI có thể vẽ lại chính xác. Phân tích chi tiết theo thứ tự sau:

1. MÀU SẮC CHI TIẾT CỦA NHÂN VẬT:
   - Màu tóc: (mô tả chính xác màu sắc, ví dụ: nâu đậm, đen bóng, vàng hoe, xám bạc, etc.)
   - Màu mắt: (mô tả chính xác màu sắc, ví dụ: nâu đậm, xanh dương nhạt, xanh lá, đen, etc.)
   - Màu da: (mô tả chính xác màu sắc, ví dụ: trắng hồng, nâu sáng, nâu đậm, vàng nhạt, etc.)
   - Màu trang phục chính: (mô tả từng phần trang phục và màu sắc cụ thể)
   - Màu phụ kiện: (màu sắc của các phụ kiện như giày, túi, mũ, etc.)

2. MÀU SẮC TỔNG THỂ CỦA ẢNH:
   - Tone màu chính: (ấm áp, lạnh, trung tính, pastel, vibrant, etc.)
   - Màu sắc chủ đạo: (các màu chính xuất hiện trong ảnh)
   - Màu background: (màu nền chính, gradient, pattern, etc.)
   - Ánh sáng và bóng đổ: (ánh sáng tự nhiên, nhân tạo, soft, harsh, etc.)
   - Độ tương phản: (cao, trung bình, thấp)
   - Độ bão hòa màu: (cao, trung bình, thấp, muted, vibrant)

3. KIỂU DÁNG VÀ PHONG CÁCH:
   - Kiểu tóc: (dài, ngắn, xoăn, thẳng, buộc, etc.)
   - Kiểu trang phục: (casual, formal, sporty, vintage, etc.)
   - Phong cách thời trang: (hiện đại, cổ điển, streetwear, etc.)

4. PHONG CÁCH NGHỆ THUẬT:
   - Loại: anime, realistic, cartoon, chibi, semi-realistic, etc.
   - Độ chi tiết: cao, trung bình, thấp
   - Phong cách vẽ: cell-shaded, painterly, line art, etc.
   - Kỹ thuật màu sắc: (flat colors, shading, highlights, etc.)

5. YẾU TỐ NHẬN DẠNG:
   - Phụ kiện đặc biệt: (kính, khuyên tai, vòng tay, etc.)
   - Họa tiết trang phục: (hoa, kẻ sọc, chấm bi, etc.)
   - Chi tiết đặc biệt: (logo, brand, pattern, etc.)
"""
```

### Quy trình đồng bộ nhân vật
1. **Upload ảnh nhân vật** → Lưu tạm thời
2. **Phân tích nhân vật** → Trích xuất thông tin màu sắc và đặc điểm
3. **Tăng cường prompt** → Kết hợp thông tin nhân vật vào prompt
4. **Tạo ảnh** → Sử dụng prompt đã tăng cường
5. **Xóa ảnh tạm** → Dọn dẹp sau khi hoàn thành

## 🔄 API Endpoints

### Quản lý API Keys
- `GET /api/keys` - Lấy danh sách API keys
- `POST /api/keys` - Thêm API key mới
- `DELETE /api/keys/<suffix>` - Xóa API key

### Quản lý Tasks
- `GET /api/tasks` - Lấy danh sách tasks
- `POST /api/tasks` - Tạo task mới
- `GET /api/tasks/<id>` - Lấy chi tiết task
- `DELETE /api/tasks/<id>` - Xóa task
- `POST /api/tasks/<id>/start` - Chạy task thủ công

### Phân tích nhân vật
- `POST /api/analyze-character` - Phân tích nhân vật từ ảnh
- `POST /api/upload-image` - Upload ảnh nhân vật
- `POST /api/split-prompts` - Phân tách prompt từ text

### Tải xuống
- `GET /api/images/<filename>` - Xem ảnh
- `GET /api/download-image/<filename>` - Tải ảnh đơn
- `GET /api/download-all-images/<task_id>` - Tải tất cả ảnh (ZIP)

## 🚀 Cách chạy dự án

### 1. Khởi động Backend
```bash
cd backend
python app.py
```

### 2. Khởi động Frontend
```bash
cd frontend
npm start
```

### 3. Sử dụng batch files (Windows)
```bash
# Chạy cả backend và frontend
start.bat

# Chạy riêng backend
run-backend.bat

# Chạy riêng frontend
run-frontend.bat
```

## 📊 Cấu trúc dữ liệu

### Task Structure
```json
{
  "id": "uuid",
  "name": "Batch name",
  "prompts": ["prompt1", "prompt2"],
  "input_image_path": "path/to/image",
  "total_count": 2,
  "completed_count": 1,
  "failed_count": 0,
  "status": "processing",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00",
  "results": [
    {
      "prompt": "prompt1",
      "filename": "image1.png",
      "status": "success",
      "timestamp": "2024-01-01T00:00:00"
    }
  ]
}
```

### Config Structure
```json
{
  "api_keys": [
    "AIzaSyCUSYj3VnQ6m1yxeSmavtocdYDimAID7Kc",
    "AIzaSyCwgVeKOtVsN8CPS-sAhz0os6IslgRs-YE"
  ]
}
```

## 🎯 Tính năng nổi bật

### 1. Quản lý API Keys thông minh
- Tự động retry khi key hết quota
- Chờ 5 phút trước khi thử lại key bị lỗi
- Hỗ trợ nhiều keys đồng thời

### 2. Đồng bộ nhân vật chi tiết
- Phân tích màu sắc chính xác
- Trích xuất đặc điểm nhân vật
- Tăng cường prompt tự động

### 3. Hàng đợi xử lý
- Background processing
- Theo dõi tiến độ real-time
- Quản lý nhiều tasks đồng thời

### 4. Giao diện thân thiện
- Responsive design
- Real-time updates
- Drag & drop upload
- Preview ảnh

## 🔧 Cải thiện đã thực hiện

### 1. Prompt phân tích nhân vật
- ✅ Thêm chi tiết màu sắc cụ thể của nhân vật
- ✅ Thêm phân tích màu sắc tổng thể của ảnh (tone, background, ánh sáng)
- ✅ Cấu trúc phân tích rõ ràng với 5 nhóm thông tin
- ✅ Ví dụ màu sắc chi tiết và kỹ thuật màu sắc
- ✅ Phân loại thông tin theo nhóm logic

### 2. Tăng cường prompt
- ✅ Cải thiện cách kết hợp thông tin nhân vật
- ✅ Nhấn mạnh việc giữ nguyên màu sắc
- ✅ Cấu trúc prompt rõ ràng hơn

## 🚀 Hướng phát triển

### 1. Tính năng có thể thêm
- Lưu trữ nhân vật để tái sử dụng
- Template nhân vật
- Batch processing với nhiều nhân vật
- Export/Import cấu hình

### 2. Cải thiện hiệu suất
- Caching kết quả phân tích
- Parallel processing
- Optimize image handling

### 3. Tính năng nâng cao
- Style transfer
- Character pose control
- Background generation
- Multi-character scenes

