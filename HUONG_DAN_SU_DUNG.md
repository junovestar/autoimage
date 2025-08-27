# HƯỚNG DẪN SỬ DỤNG TÍNH NĂNG PHÂN TÍCH NHÂN VẬT

## 🎯 Tổng quan
Tính năng phân tích nhân vật cho phép bạn upload ảnh nhân vật mẫu và tự động trích xuất thông tin màu sắc, đặc điểm để tạo ra các ảnh mới với cùng nhân vật đó.

## 🚀 Cách sử dụng

### Bước 1: Khởi động ứng dụng
```bash
# Chạy cả backend và frontend
start.bat

# Hoặc chạy riêng lẻ
run-backend.bat
run-frontend.bat
```

### Bước 2: Upload ảnh nhân vật
1. Mở trình duyệt và truy cập `http://localhost:3000`
2. Chọn tab "Tạo ảnh"
3. Trong phần "Upload ảnh nhân vật", click "Chọn ảnh"
4. Chọn ảnh nhân vật mẫu (hỗ trợ PNG, JPG, JPEG, WEBP)

### Bước 3: Bật đồng bộ nhân vật
1. Sau khi upload ảnh thành công, tích vào checkbox "Bật đồng bộ hóa nhân vật"
2. Click nút "Phân tích nhân vật" để AI phân tích đặc điểm

### Bước 4: Xem kết quả phân tích
AI sẽ trả về thông tin chi tiết về nhân vật và màu sắc tổng thể của ảnh:
```
MÀU SẮC CHI TIẾT CỦA NHÂN VẬT:
- Màu tóc: nâu đậm
- Màu mắt: xanh dương nhạt  
- Màu da: trắng hồng
- Màu trang phục chính: áo trắng, quần jean xanh
- Màu phụ kiện: giày trắng

MÀU SẮC TỔNG THỂ CỦA ẢNH:
- Tone màu chính: ấm áp
- Màu sắc chủ đạo: trắng, xanh, nâu
- Màu background: gradient xanh nhạt
- Ánh sáng và bóng đổ: ánh sáng tự nhiên, soft
- Độ tương phản: trung bình
- Độ bão hòa màu: muted

KIỂU DÁNG VÀ PHONG CÁCH:
- Kiểu tóc: dài thẳng
- Kiểu trang phục: casual
- Phong cách thời trang: hiện đại

PHONG CÁCH NGHỆ THUẬT:
- Loại: anime
- Độ chi tiết: cao
- Phong cách vẽ: cell-shaded
- Kỹ thuật màu sắc: flat colors với shading nhẹ

YẾU TỐ NHẬN DẠNG:
- Phụ kiện đặc biệt: kính tròn
- Họa tiết trang phục: không có
- Chi tiết đặc biệt: không có
```

### Bước 5: Tạo prompts
1. Nhập các prompt mô tả hành động/tình huống mới
2. Ví dụ: "đang đọc sách", "đang nấu ăn", "đang chơi game"
3. AI sẽ tự động kết hợp thông tin nhân vật vào prompt

### Bước 6: Tạo batch và chạy
1. Đặt tên batch
2. Click "Tạo batch"
3. Theo dõi tiến độ trong tab "Lịch sử"

## 📝 Ví dụ sử dụng

### Ví dụ 1: Nhân vật anime
**Ảnh mẫu**: Nhân vật anime nữ với tóc đen dài, mắt xanh, mặc áo trắng

**Prompts tạo**:
- "đang cầm hoa hồng"
- "đang ngồi trên ghế sofa"
- "đang nhìn ra cửa sổ"

**Kết quả**: 3 ảnh với cùng nhân vật nhưng khác hành động

### Ví dụ 2: Nhân vật realistic
**Ảnh mẫu**: Nhân vật nam với tóc nâu ngắn, mắt nâu, mặc áo sơ mi trắng

**Prompts tạo**:
- "đang làm việc tại văn phòng"
- "đang đi dạo trong công viên"
- "đang uống cà phê"

**Kết quả**: 3 ảnh với cùng nhân vật nhưng khác môi trường

## 🎨 Lưu ý quan trọng

### 1. Chất lượng ảnh mẫu
- ✅ Ảnh rõ nét, nhân vật chiếm phần lớn khung hình
- ✅ Ánh sáng tốt, màu sắc chính xác
- ✅ Nhân vật nhìn thẳng hoặc 3/4 mặt
- ❌ Ảnh mờ, nhân vật quá nhỏ
- ❌ Ảnh có nhiều nhân vật
- ❌ Ảnh có background phức tạp

### 2. Prompt hiệu quả
- ✅ Mô tả hành động cụ thể: "đang đọc sách", "đang nấu ăn"
- ✅ Mô tả môi trường: "trong văn phòng", "ngoài trời"
- ✅ Mô tả thời gian: "buổi sáng", "hoàng hôn"
- ❌ Prompt quá phức tạp hoặc mơ hồ
- ❌ Prompt có nhiều nhân vật khác

### 3. Phong cách nghệ thuật
- Đảm bảo prompt phù hợp với phong cách của nhân vật mẫu
- Nếu nhân vật là anime, prompt nên phù hợp với phong cách anime
- Nếu nhân vật là realistic, prompt nên phù hợp với phong cách realistic

## 🔧 Xử lý lỗi thường gặp

### 1. Lỗi "Không có API key khả dụng"
- Kiểm tra tab "Cài đặt" và thêm API key mới
- Đảm bảo API key có quota còn lại

### 2. Lỗi "AI không trả về phân tích nhân vật"
- Thử lại với ảnh khác rõ nét hơn
- Đảm bảo ảnh có nhân vật rõ ràng

### 3. Lỗi "Model không thể tạo ảnh"
- Kiểm tra prompt có phù hợp không
- Thử prompt đơn giản hơn
- Đảm bảo API key có quyền tạo ảnh

### 4. Ảnh tạo ra không giống nhân vật mẫu
- Kiểm tra kết quả phân tích nhân vật có chính xác không
- Thử với ảnh mẫu khác rõ nét hơn
- Điều chỉnh prompt để nhấn mạnh đặc điểm nhân vật

## 📊 Theo dõi tiến độ

### Tab "Lịch sử"
- Xem danh sách tất cả tasks đã tạo
- Theo dõi trạng thái: pending, queued, processing, completed, failed
- Xem tiến độ hoàn thành: X/Y ảnh đã tạo

### Tab "Chi tiết"
- Xem từng ảnh được tạo
- Tải xuống ảnh đơn lẻ hoặc tất cả (ZIP)
- Xem thông tin API key được sử dụng

## 🚀 Mẹo sử dụng hiệu quả

### 1. Tạo nhiều biến thể
- Sử dụng cùng nhân vật với nhiều hành động khác nhau
- Tạo series ảnh kể chuyện
- Thử nghiệm với các môi trường khác nhau

### 2. Tối ưu prompt
- Bắt đầu với prompt đơn giản
- Dần dần thêm chi tiết phức tạp
- Ghi chép lại prompt hiệu quả

### 3. Quản lý API keys
- Thêm nhiều API keys để tăng tốc độ xử lý
- Theo dõi quota sử dụng
- Thay thế keys hết quota

### 4. Lưu trữ kết quả
- Tải xuống ảnh thành công ngay lập tức
- Tổ chức ảnh theo thư mục
- Backup các ảnh quan trọng

## 🎯 Kết luận
Tính năng phân tích nhân vật giúp bạn tạo ra các ảnh nhất quán với cùng một nhân vật, tiết kiệm thời gian và đảm bảo chất lượng. Hãy thử nghiệm và khám phá các khả năng của tính năng này!

