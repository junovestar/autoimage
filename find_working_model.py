#!/usr/bin/env python3
"""
Script để tìm model Gemini hoạt động với free tier và image generation
"""

import os
import json
from google import genai
import time
from datetime import datetime

# API key để test
API_KEY = "AIzaSyAhC-zhBuMwgtgBIKCxCbwvrmIQ_hOYQvE"

# Danh sách models để test
MODELS_TO_TEST = [
    "gemini-2.0-flash-preview-image-generation",
    "gemini-2.0-flash-image-preview", 
    "gemini-2.0-flash",
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-1.5-flash-image-preview"
]

def test_model(model_name, api_key):
    """Test một model cụ thể"""
    print(f"\n🔍 Testing model: {model_name}")
    print(f"🔑 API Key: {api_key[-8:]}...")
    
    try:
        client = genai.Client(api_key=api_key)
        
        # Test với text-only request
        print(f"  📝 Testing text-only request...")
        
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    {
                        "parts": [
                            {
                                "text": "Tạo một hình ảnh đơn giản: một ngôi nhà nhỏ màu xanh"
                            }
                        ]
                    }
                ]
            )
            
            if response.candidates and response.candidates[0].content:
                has_image = False
                has_text = False
                
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        has_image = True
                        print(f"  ✅ SUCCESS: Model trả về ảnh!")
                        
                        # Lưu ảnh test
                        import base64
                        image_data = base64.b64decode(part.inline_data.data)
                        test_filename = f"test_{model_name.replace('-', '_')}.png"
                        with open(test_filename, "wb") as f:
                            f.write(image_data)
                        print(f"  💾 Ảnh đã lưu: {test_filename}")
                        
                    elif hasattr(part, 'text') and part.text:
                        has_text = True
                        print(f"  📝 Text response: {part.text[:100]}...")
                
                if has_image:
                    return {
                        'status': 'success',
                        'model': model_name,
                        'type': 'image_generation',
                        'message': 'Model hỗ trợ image generation'
                    }
                elif has_text:
                    return {
                        'status': 'success',
                        'model': model_name,
                        'type': 'text_only',
                        'message': 'Model chỉ hỗ trợ text'
                    }
                else:
                    return {
                        'status': 'error',
                        'model': model_name,
                        'message': 'Không có content'
                    }
            else:
                print(f"  ❌ ERROR: Không có content trong response")
                return {
                    'status': 'error',
                    'model': model_name,
                    'message': 'Không có content'
                }
                
        except Exception as e:
            error_str = str(e)
            print(f"  ❌ ERROR: {error_str}")
            
            if "RESOURCE_EXHAUSTED" in error_str:
                return {
                    'status': 'quota_exceeded',
                    'model': model_name,
                    'message': 'API key đã hết quota'
                }
            elif "PERMISSION_DENIED" in error_str:
                return {
                    'status': 'permission_denied',
                    'model': model_name,
                    'message': 'API key không có quyền truy cập model này'
                }
            elif "INVALID_ARGUMENT" in error_str:
                return {
                    'status': 'invalid_argument',
                    'model': model_name,
                    'message': 'Invalid argument - có thể model không hỗ trợ text-only'
                }
            elif "NOT_FOUND" in error_str:
                return {
                    'status': 'not_found',
                    'model': model_name,
                    'message': 'Model không tồn tại'
                }
            else:
                return {
                    'status': 'error',
                    'model': model_name,
                    'message': error_str
                }
                
    except Exception as e:
        print(f"  ❌ CRITICAL ERROR: {e}")
        return {
            'status': 'critical_error',
            'model': model_name,
            'message': f'Không thể tạo client: {e}'
        }

def main():
    """Hàm chính"""
    print("🚀 Gemini Models Finder - Tìm model hoạt động với free tier")
    print("=" * 70)
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔑 API Key: {API_KEY[-8:]}...")
    print(f"📋 Total models to test: {len(MODELS_TO_TEST)}")
    
    results = []
    
    for i, model_name in enumerate(MODELS_TO_TEST, 1):
        print(f"\n{'='*60}")
        print(f"🔍 Testing Model {i}/{len(MODELS_TO_TEST)}")
        print(f"{'='*60}")
        
        result = test_model(model_name, API_KEY)
        results.append(result)
        
        # Delay giữa các models
        time.sleep(2)
    
    # Tóm tắt kết quả
    print(f"\n{'='*70}")
    print("📊 SUMMARY RESULTS")
    print(f"{'='*70}")
    
    working_models = []
    text_only_models = []
    quota_exceeded_models = []
    error_models = []
    
    for result in results:
        model_name = result['model']
        status = result['status']
        
        print(f"\n🔍 {model_name}:")
        print(f"  Status: {status}")
        print(f"  Message: {result.get('message', 'N/A')}")
        
        if status == 'success' and result.get('type') == 'image_generation':
            print(f"  ✅ HOẠT ĐỘNG - Image Generation!")
            working_models.append(model_name)
        elif status == 'success' and result.get('type') == 'text_only':
            print(f"  📝 HOẠT ĐỘNG - Text Only")
            text_only_models.append(model_name)
        elif status == 'quota_exceeded':
            print(f"  ⚠️ HẾT QUOTA")
            quota_exceeded_models.append(model_name)
        else:
            print(f"  ❌ KHÔNG HOẠT ĐỘNG")
            error_models.append(model_name)
    
    print(f"\n{'='*70}")
    print("🎯 RECOMMENDATIONS:")
    print(f"{'='*70}")
    
    if working_models:
        print(f"✅ WORKING MODELS (Image Generation): {', '.join(working_models)}")
        print("   - Có thể sử dụng cho webapp")
        print("   - Hỗ trợ text-to-image")
        
    if text_only_models:
        print(f"📝 TEXT-ONLY MODELS: {', '.join(text_only_models)}")
        print("   - Chỉ hỗ trợ text generation")
        print("   - Không phù hợp cho image generation")
        
    if quota_exceeded_models:
        print(f"⚠️ QUOTA EXCEEDED MODELS: {', '.join(quota_exceeded_models)}")
        print("   - Đã hết quota free tier")
        print("   - Cần chờ reset hoặc upgrade")
        
    if error_models:
        print(f"❌ ERROR MODELS: {', '.join(error_models)}")
        print("   - Có lỗi khác")
        
    if not working_models:
        print("❌ KHÔNG CÓ MODEL NÀO HỖ TRỢ IMAGE GENERATION!")
        print("   - Có thể cần tạo API key mới")
        print("   - Hoặc tất cả models đã hết quota")
    
    print(f"\n🔧 NEXT STEPS:")
    if working_models:
        print("   1. Cập nhật backend để sử dụng model đầu tiên trong danh sách")
        print("   2. Test với webapp")
        print("   3. Monitor free tier limits")
    else:
        print("   1. Tạo API keys mới trong Google AI Studio")
        print("   2. Kiểm tra billing và quota settings")
        print("   3. Thử với các tài khoản khác")

if __name__ == "__main__":
    main()
