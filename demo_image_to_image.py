#!/usr/bin/env python3
"""
Demo Image-to-Image Generation với Gemini AI
Tạo ảnh mới dựa trên nhân vật từ ảnh input
"""

import os
import base64
import requests
from google import genai

# API key
API_KEY = "AIzaSyAhC-zhBuMwgtgBIKCxCbwvrmIQ_hOYQvE"

def test_image_to_image_with_webapp():
    """Test image-to-image thông qua webapp API"""
    
    # 1. Upload ảnh
    print("🔄 Bước 1: Upload ảnh nhân vật...")
    
    # Tạo ảnh test đơn giản (hoặc sử dụng ảnh có sẵn)
    test_image_path = "test_character.jpg"
    
    if not os.path.exists(test_image_path):
        print("⚠️ Tạo ảnh test mẫu...")
        # Tạo một ảnh test đơn giản bằng PIL hoặc lấy ảnh có sẵn
        from PIL import Image, ImageDraw
        
        # Tạo ảnh đơn giản với hình tròn (đại diện nhân vật)
        img = Image.new('RGB', (300, 400), color='white')
        draw = ImageDraw.Draw(img)
        draw.ellipse([100, 100, 200, 200], fill='blue')  # Đầu nhân vật
        draw.rectangle([125, 200, 175, 300], fill='red')  # Thân nhân vật
        img.save(test_image_path)
        print(f"✅ Đã tạo ảnh test: {test_image_path}")
    
    # Upload ảnh qua API
    try:
        with open(test_image_path, 'rb') as f:
            files = {'image': f}
            response = requests.post('http://localhost:5000/api/upload-image', files=files)
        
        if response.status_code == 200:
            upload_result = response.json()
            uploaded_image_path = upload_result['image_path']
            print(f"✅ Upload thành công: {uploaded_image_path}")
        else:
            print(f"❌ Upload thất bại: {response.text}")
            return
    except Exception as e:
        print(f"❌ Lỗi upload: {e}")
        return
    
    # 2. Tạo batch task với ảnh input
    print("\n🔄 Bước 2: Tạo batch task với image-to-image...")
    
    test_prompts = [
        "Tạo nhân vật này trong phong cảnh rừng rậm với ánh sáng mặt trời",
        "Đặt nhân vật này vào thế giới khoa học viễn tưởng với tàu vũ trụ",
        "Nhân vật này trong phong cảnh thành phố hiện đại vào ban đêm",
        "Tạo nhân vật này trong không gian vũ trụ với các ngôi sao",
        "Nhân vật này trong phong cảnh cổ tích với lâu đài"
    ]
    
    try:
        response = requests.post('http://localhost:5000/api/tasks', json={
            'prompts': test_prompts,
            'name': 'Image-to-Image Demo',
            'input_image_path': uploaded_image_path
        })
        
        if response.status_code == 200:
            task_result = response.json()
            task_id = task_result['task_id']
            print(f"✅ Tạo task thành công: {task_id}")
            
            # 3. Theo dõi progress
            print(f"\n🔄 Bước 3: Theo dõi progress của task {task_id}...")
            
            import time
            for i in range(30):  # Theo dõi tối đa 30 lần (5 phút)
                try:
                    response = requests.get(f'http://localhost:5000/api/tasks/{task_id}')
                    if response.status_code == 200:
                        task_info = response.json()
                        status = task_info['status']
                        completed = task_info['completed_count']
                        total = task_info['total_count']
                        
                        print(f"📊 Progress: {completed}/{total} - Status: {status}")
                        
                        if status in ['completed', 'failed', 'partial']:
                            print(f"✅ Task hoàn thành với status: {status}")
                            
                            # Hiển thị kết quả
                            for result in task_info['results']:
                                if result['status'] == 'success':
                                    print(f"🎨 Ảnh tạo thành công: {result['image_path']}")
                                else:
                                    print(f"❌ Lỗi: {result['error']}")
                            break
                    else:
                        print(f"❌ Lỗi khi lấy thông tin task: {response.text}")
                        break
                        
                except Exception as e:
                    print(f"❌ Lỗi: {e}")
                    break
                
                time.sleep(10)  # Đợi 10 giây
            
            print("\n🎉 Demo hoàn thành!")
            
        else:
            print(f"❌ Tạo task thất bại: {response.text}")
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")

def test_direct_api_call():
    """Test trực tiếp với Gemini API (không qua webapp)"""
    print("🔬 Test trực tiếp với Gemini API...")
    
    try:
        client = genai.Client(api_key=API_KEY)
        
        # Tạo ảnh test đơn giản nếu chưa có
        test_image_path = "direct_test_character.png"
        if not os.path.exists(test_image_path):
            from PIL import Image, ImageDraw
            
            img = Image.new('RGB', (200, 300), color='white')
            draw = ImageDraw.Draw(img)
            draw.ellipse([75, 50, 125, 100], fill='green')  # Đầu
            draw.rectangle([85, 100, 115, 180], fill='yellow')  # Thân
            draw.rectangle([75, 180, 95, 220], fill='orange')  # Chân trái
            draw.rectangle([105, 180, 125, 220], fill='orange')  # Chân phải
            img.save(test_image_path)
        
        # Encode ảnh
        with open(test_image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        print(f"🖼️ Sử dụng ảnh: {test_image_path}")
        
        # Gửi request với ảnh + prompt
        response = client.models.generate_content(
            model="gemini-2.5-flash-image-preview",
            contents=[
                {
                    "parts": [
                        {
                            "text": "Tạo một hình ảnh mới với nhân vật trong ảnh này trong phong cảnh núi non với hoàng hôn"
                        },
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": image_data
                            }
                        }
                    ]
                }
            ]
        )
        
        print("✅ Response nhận được từ Gemini:")
        print(f"Type: {type(response)}")
        
        if response.candidates and response.candidates[0].content:
            for i, part in enumerate(response.candidates[0].content.parts):
                if hasattr(part, 'inline_data') and part.inline_data:
                    # Lưu ảnh output
                    import base64
                    image_data = base64.b64decode(part.inline_data.data)
                    output_filename = f"direct_output_{i}.png"
                    
                    with open(output_filename, "wb") as f:
                        f.write(image_data)
                    
                    print(f"✅ Ảnh đã được tạo: {output_filename}")
                else:
                    print(f"📝 Text content: {part.text if hasattr(part, 'text') else 'No text'}")
        else:
            print("❌ Không có content trong response")
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")

def main():
    """Hàm chính"""
    print("🚀 Demo Image-to-Image Generation với Gemini AI")
    print("=" * 60)
    
    print("Chọn loại test:")
    print("1. Test qua Webapp API (cần chạy server)")
    print("2. Test trực tiếp với Gemini API")
    print("3. Test cả hai")
    
    choice = input("Nhập lựa chọn (1/2/3): ").strip()
    
    if choice == "1":
        print("\n🎯 Test qua Webapp API...")
        test_image_to_image_with_webapp()
    elif choice == "2":
        print("\n🎯 Test trực tiếp với Gemini API...")
        test_direct_api_call()
    elif choice == "3":
        print("\n🎯 Test trực tiếp với Gemini API...")
        test_direct_api_call()
        print("\n" + "=" * 40)
        print("🎯 Test qua Webapp API...")
        test_image_to_image_with_webapp()
    else:
        print("Lựa chọn không hợp lệ. Chạy test trực tiếp...")
        test_direct_api_call()

if __name__ == "__main__":
    main()
