#!/usr/bin/env python3
"""
Demo kết nối với Gemini 2.5 Flash Image Preview
Tạo ảnh từ mô tả văn bản
"""

import os
import base64
from google import genai

# Thiết lập API key
API_KEY = "AIzaSyAhC-zhBuMwgtgBIKCxCbwvrmIQ_hOYQvE"

def test_gemini_connection():
    """Test kết nối cơ bản với Gemini API"""
    try:
        client = genai.Client(api_key=API_KEY)
        
        # Test với mô hình text thông thường trước
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Xin chào! Hãy giới thiệu về khả năng tạo ảnh của bạn"
        )
        
        print("✅ Kết nối thành công!")
        print("Phản hồi từ Gemini:")
        print(response.text)
        return True
        
    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}")
        return False

def generate_image(prompt):
    """Tạo ảnh từ mô tả văn bản"""
    try:
        client = genai.Client(api_key=API_KEY)
        
        print(f"🖼️ Đang tạo ảnh với prompt: {prompt}")
        
        # Sử dụng mô hình Gemini 2.5 Flash Image Preview cho tạo ảnh
        response = client.models.generate_content(
            model="gemini-2.5-flash-image-preview",
            contents=[
                {
                    "parts": [
                        {
                            "text": f"Tạo một hình ảnh: {prompt}"
                        }
                    ]
                }
            ]
        )
        
        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    # Lưu ảnh xuống file
                    image_data = base64.b64decode(part.inline_data.data)
                    filename = f"generated_image_{hash(prompt) % 10000}.png"
                    
                    with open(filename, "wb") as f:
                        f.write(image_data)
                    
                    print(f"✅ Ảnh đã được tạo và lưu thành: {filename}")
                    return filename
        
        print("❌ Không thể tạo ảnh - Không có dữ liệu ảnh trong response")
        return None
        
    except Exception as e:
        print(f"❌ Lỗi khi tạo ảnh: {e}")
        return None

def list_available_models():
    """Liệt kê các mô hình có sẵn"""
    try:
        client = genai.Client(api_key=API_KEY)
        models = client.models.list()
        
        print("📋 Các mô hình có sẵn:")
        image_models = []
        for model in models:
            print(f"  - {model.name}")
            if "image" in model.name.lower() or "imagen" in model.name.lower():
                image_models.append(model.name)
        
        print(f"\n🎨 Mô hình tạo ảnh có sẵn:")
        for model in image_models:
            print(f"  - {model}")
            
    except Exception as e:
        print(f"❌ Lỗi khi liệt kê mô hình: {e}")

def test_simple_image_generation():
    """Test tạo ảnh đơn giản"""
    try:
        client = genai.Client(api_key=API_KEY)
        
        print("🖼️ Thử tạo ảnh đơn giản...")
        
        response = client.models.generate_content(
            model="gemini-2.5-flash-image-preview",
            contents="Tạo một hình ảnh đơn giản về một trái táo đỏ"
        )
        
        print("✅ Response nhận được:")
        print(f"Type: {type(response)}")
        print(f"Content: {response.candidates[0].content if response.candidates else 'None'}")
        
        return response
        
    except Exception as e:
        print(f"❌ Lỗi test: {e}")
        return None

def main():
    """Hàm chính để test các tính năng"""
    print("🚀 Bắt đầu demo Gemini 2.5 Flash Image Preview")
    print("=" * 50)
    
    # Test kết nối
    if not test_gemini_connection():
        return
    
    print("\n" + "=" * 30)
    
    # Liệt kê mô hình có sẵn
    list_available_models()
    
    print("\n" + "=" * 30)
    
    # Test tạo ảnh đơn giản trước
    print("🎯 Test tạo ảnh đơn giản:")
    test_simple_image_generation()
    
    print("\n" + "=" * 30)
    
    # Test tạo ảnh với prompts khác nhau
    test_prompts = [
        "Một con mèo dễ thương đang ngủ trên ghế sofa",
        "Phong cảnh núi non vào buổi hoàng hôn",
        "Một cốc cà phê nghệ thuật với hoa văn latte",
        "Con robot thân thiện đang chơi với trẻ em"
    ]
    
    for prompt in test_prompts:
        print(f"\n🎨 Thử tạo ảnh: {prompt}")
        result = generate_image(prompt)
        if result:
            print(f"   ✅ Thành công: {result}")
        else:
            print(f"   ❌ Thất bại")
        
        print("-" * 30)

if __name__ == "__main__":
    main()
