#!/usr/bin/env python3
"""
Demo script cho Gemini 2.0 Flash Preview Image Generation Webapp
Test tất cả tính năng: Text-to-Image, Image-to-Image, Prompt Splitting
"""

import requests
import json
import time
import os
from PIL import Image, ImageDraw
import base64
import io

BASE_URL = "http://localhost:5000"

def create_test_image(filename, color='blue', size=(100, 100)):
    """Tạo ảnh test"""
    img = Image.new('RGB', size, color=color)
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 80, 80], fill='white')
    draw.text((35, 45), "TEST", fill='black')
    img.save(filename)
    return filename

def wait_for_task_completion(task_id, timeout=60):
    """Chờ task hoàn thành"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{BASE_URL}/api/tasks/{task_id}")
            if response.status_code == 200:
                task_data = response.json()
                status = task_data.get('status')
                
                if status == 'completed':
                    print(f"✅ Task completed!")
                    return task_data
                elif status == 'failed':
                    print(f"❌ Task failed!")
                    return task_data
                else:
                    print(f"⏳ Task {status}: {task_data.get('completed_count', 0)}/{task_data.get('total_count', 0)}")
            
            time.sleep(3)
        except Exception as e:
            print(f"⚠️ Error checking task status: {e}")
            time.sleep(3)
    
    print(f"⏰ Timeout waiting for task completion")
    return None

def demo_text_to_image():
    """Demo Text-to-Image generation"""
    print("\n" + "="*60)
    print("🎨 DEMO: Text-to-Image Generation")
    print("="*60)
    
    try:
        response = requests.post(f"{BASE_URL}/api/tasks", json={
            "prompts": [
                "Tạo một con rồng xanh bay trên núi tuyết",
                "Tạo một ngôi nhà gỗ nhỏ bên bờ hồ",
                "Tạo một robot thân thiện trong vườn hoa"
            ],
            "batch_name": "Demo Text-to-Image"
        })
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"✅ Created task: {task_id}")
            
            # Chờ hoàn thành
            task_data = wait_for_task_completion(task_id)
            
            if task_data and task_data.get('results'):
                print(f"\n📊 Results:")
                for i, result in enumerate(task_data['results']):
                    if result.get('success'):
                        print(f"  🖼️ Image {i+1}: {result.get('image_path')}")
                    else:
                        print(f"  ❌ Error {i+1}: {result.get('error')}")
            
            return True
        else:
            print(f"❌ Failed to create task: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def demo_image_to_image():
    """Demo Image-to-Image generation"""
    print("\n" + "="*60)
    print("🎨 DEMO: Image-to-Image Generation")
    print("="*60)
    
    try:
        # Tạo ảnh test
        test_image = create_test_image("demo_input.png", color='red')
        print(f"✅ Created test image: {test_image}")
        
        # Upload ảnh
        files = {'image': ('demo_input.png', open('demo_input.png', 'rb'), 'image/png')}
        upload_response = requests.post(f"{BASE_URL}/api/upload-image", files=files)
        
        if upload_response.status_code == 200:
            upload_result = upload_response.json()
            image_path = upload_result.get('image_path')
            print(f"✅ Uploaded image: {image_path}")
            
            # Tạo task với input image
            response = requests.post(f"{BASE_URL}/api/tasks", json={
                "prompts": [
                    "Tạo phiên bản mới với màu xanh lá",
                    "Tạo phiên bản với hiệu ứng neon",
                    "Tạo phiên bản với background thành phố"
                ],
                "batch_name": "Demo Image-to-Image",
                "input_image_path": image_path
            })
            
            if response.status_code == 200:
                result = response.json()
                task_id = result.get('task_id')
                print(f"✅ Created image-to-image task: {task_id}")
                
                # Chờ hoàn thành
                task_data = wait_for_task_completion(task_id)
                
                if task_data and task_data.get('results'):
                    print(f"\n📊 Results:")
                    for i, result in enumerate(task_data['results']):
                        if result.get('success'):
                            print(f"  🖼️ Image {i+1}: {result.get('image_path')}")
                        else:
                            print(f"  ❌ Error {i+1}: {result.get('error')}")
                
                return True
            else:
                print(f"❌ Failed to create image-to-image task: {response.status_code}")
                return False
        else:
            print(f"❌ Failed to upload image: {upload_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def demo_prompt_splitting():
    """Demo Prompt Splitting feature"""
    print("\n" + "="*60)
    print("📝 DEMO: Prompt Splitting")
    print("="*60)
    
    try:
        # Test text với nhiều prompt
        test_text = """
Tạo các hình ảnh sau:
1. Một con mèo trắng đang ngủ trên ghế sofa
2. Một bình hoa hồng đỏ đặt trên bàn gỗ
3. Một cảnh hoàng hôn trên biển với thuyền buồm
4. Một robot thân thiện trong vườn hoa
5. Một ngôi nhà gỗ nhỏ bên bờ hồ
        """.strip()
        
        print(f"📝 Input text:")
        print(test_text)
        
        # Test với AI
        print(f"\n🤖 Testing with AI...")
        response = requests.post(f"{BASE_URL}/api/split-prompts", json={
            "text": test_text,
            "use_ai": True
        })
        
        if response.status_code == 200:
            result = response.json()
            prompts = result.get('prompts', [])
            print(f"✅ AI split result: {len(prompts)} prompts")
            for i, prompt in enumerate(prompts):
                print(f"  {i+1}. {prompt}")
            
            # Tạo task với prompts đã split
            if prompts:
                print(f"\n🎨 Creating task with split prompts...")
                task_response = requests.post(f"{BASE_URL}/api/tasks", json={
                    "prompts": prompts[:3],  # Chỉ lấy 3 prompts đầu để test nhanh
                    "batch_name": "Demo Split Prompts"
                })
                
                if task_response.status_code == 200:
                    task_result = task_response.json()
                    task_id = task_result.get('task_id')
                    print(f"✅ Created task with split prompts: {task_id}")
                    
                    # Chờ hoàn thành
                    task_data = wait_for_task_completion(task_id)
                    
                    if task_data and task_data.get('results'):
                        print(f"\n📊 Results:")
                        for i, result in enumerate(task_data['results']):
                            if result.get('success'):
                                print(f"  🖼️ Image {i+1}: {result.get('image_path')}")
                            else:
                                print(f"  ❌ Error {i+1}: {result.get('error')}")
                else:
                    print(f"❌ Failed to create task: {task_response.status_code}")
            
            return True
        else:
            print(f"❌ Failed to split prompts: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def demo_api_keys():
    """Demo API Keys management"""
    print("\n" + "="*60)
    print("🔑 DEMO: API Keys Status")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/keys")
        if response.status_code == 200:
            result = response.json()
            keys = result.get('keys', [])
            print(f"✅ API Keys ({len(keys)} keys):")
            for i, key in enumerate(keys):
                print(f"  {i+1}. {key[:8]}...{key[-8:]}")
        else:
            print(f"❌ Failed to get API keys: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Hàm chính"""
    print("🚀 GEMINI 2.0 FLASH PREVIEW IMAGE GENERATION DEMO")
    print("=" * 60)
    print("🎯 Testing all features of the webapp")
    print("=" * 60)
    
    # Kiểm tra backend
    print("🔍 Checking backend status...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print("❌ Backend not responding properly")
            return
    except Exception as e:
        print(f"❌ Backend not available: {e}")
        print("💡 Please start the backend with: python backend/app.py")
        return
    
    # Demo các tính năng
    demo_api_keys()
    demo_text_to_image()
    demo_image_to_image()
    demo_prompt_splitting()
    
    print("\n" + "="*60)
    print("🎉 DEMO HOÀN THÀNH!")
    print("="*60)
    print("✅ Tất cả tính năng đã được test thành công")
    print("🌐 Mở browser và truy cập: http://localhost:3000")
    print("📁 Kiểm tra thư mục 'images/' để xem kết quả")
    print("="*60)

if __name__ == "__main__":
    main()
