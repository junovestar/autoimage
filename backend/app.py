#!/usr/bin/env python3
"""
Backend Flask cho webapp tạo ảnh hàng loạt với Gemini AI
Quản lý nhiều API keys và retry logic
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import base64
import time
import threading
from datetime import datetime, timedelta
import requests
from google import genai
from google.genai import types
import uuid
from werkzeug.utils import secure_filename
import shutil
import re
from PIL import Image

app = Flask(__name__)
CORS(app)

class PromptProcessor:
    """Xử lý và phân tách prompt từ text"""
    
    def __init__(self, generator):
        self.generator = generator
    
    def split_prompts_ai(self, text):
        """Sử dụng AI để phân tách text thành các prompt riêng biệt"""
        available_keys = self.generator.get_available_key()
        if not available_keys:
            return {
                'success': False,
                'error': 'Không có API key khả dụng để xử lý prompt'
            }
        
        api_key = available_keys[0]
        
        try:
            client = genai.Client(api_key=api_key)
            
            # Prompt để yêu cầu AI phân tách
            system_prompt = f"""
Bạn là một AI chuyên gia trong việc phân tách text thành các yêu cầu tạo ảnh riêng biệt.
NHIỆM VỤ: Phân tích đoạn text sau và trích xuất ra các prompt tạo ảnh cụ thể, KHÔNG phải tạo mẫu hay ví dụ.

TEXT CẦN PHÂN TÁCH:
"{text}"

QUY TẮC:
1. Chỉ trích xuất các yêu cầu tạo ảnh thực sự từ text
2. KHÔNG tạo thêm prompt mẫu hay ví dụ
3. Mỗi prompt phải là một yêu cầu cụ thể để tạo ảnh
4. Nếu text chỉ có 1 ý tưởng, chỉ trả về 1 prompt
5. Nếu text có nhiều ý tưởng riêng biệt, tách thành nhiều prompt

TRẢ VỀ DẠNG JSON:
{{
    "prompts": [
        "yêu cầu tạo ảnh 1",
        "yêu cầu tạo ảnh 2"
    ],
    "count": số lượng prompt thực tế,
    "analysis": "Phân tích: đã tìm thấy X yêu cầu tạo ảnh cụ thể"
}}

CHÚ Ý: Chỉ trả về JSON, không thêm text khác.
"""
            
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    {
                        "parts": [
                            {
                                "text": system_prompt
                            }
                        ]
                    }
                ]
            )
            
            if response.candidates and response.candidates[0].content:
                response_text = ""
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_text += part.text
                
                # Tìm JSON trong response
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                        prompts = result.get('prompts', [])
                        
                        # Validate prompts
                        if not prompts or not isinstance(prompts, list):
                            return {
                                'success': False,
                                'error': 'AI không trả về danh sách prompt hợp lệ'
                            }
                        
                        # Lọc prompts rỗng
                        prompts = [p.strip() for p in prompts if p.strip()]
                        
                        if not prompts:
                            return {
                                'success': False,
                                'error': 'Không tìm thấy prompt nào hợp lệ'
                            }
                        
                        return {
                            'success': True,
                            'prompts': prompts,
                            'count': len(prompts),
                            'analysis': result.get('analysis', 'Đã phân tách thành công'),
                            'api_key_used': api_key[-8:]
                        }
                        
                    except json.JSONDecodeError:
                        return {
                            'success': False,
                            'error': 'Không thể parse response từ AI'
                        }
                else:
                    return {
                        'success': False,
                        'error': 'AI không trả về JSON hợp lệ'
                    }
            else:
                return {
                    'success': False,
                    'error': 'Không nhận được response từ AI'
                }
                
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                self.generator.mark_key_failed(api_key)
                return {
                    'success': False,
                    'error': 'API key đã hết quota, vui lòng thử lại sau'
                }
            else:
                return {
                    'success': False,
                    'error': f'Lỗi khi xử lý prompt: {error_msg}'
                }
    
    def split_prompts_simple(self, text):
        """Phân tách prompt đơn giản bằng regex (fallback)"""
        # Các pattern để nhận diện prompt
        patterns = [
            r'(\d+\.\s*[^0-9\n]+)',  # 1. prompt
            r'([•-]\s*[^\n]+)',      # • prompt hoặc - prompt
            r'([^\n]+(?=\n\d+\.))',  # prompt trước số thứ tự
            r'([^\n]+(?=\n[•-]))',   # prompt trước bullet point
        ]
        
        prompts = []
        
        # Tìm tất cả matches
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            for match in matches:
                prompt = match.strip()
                if prompt and len(prompt) > 5:  # Prompt phải có ít nhất 5 ký tự
                    prompts.append(prompt)
        
        # Nếu không tìm thấy pattern nào, chia theo dòng
        if not prompts:
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if line and len(line) > 10:  # Dòng phải có ít nhất 10 ký tự
                    prompts.append(line)
        
        return {
            'success': True,
            'prompts': prompts,
            'count': len(prompts),
            'analysis': f'Đã phân tách bằng pattern matching, tìm thấy {len(prompts)} prompt',
            'api_key_used': 'pattern'
        }

# Cấu hình
CONFIG_FILE = "config.json"
TASK_FILE = "tasks.json"

# Cấu hình upload ảnh
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

class GeminiImageGenerator:
    def __init__(self):
        self.api_keys = []
        self.failed_keys = {}  # key -> last_fail_time
        self.load_config()
        
    def load_config(self):
        """Load cấu hình từ file"""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.api_keys = config.get('api_keys', [])
        
        # Thêm API keys mặc định nếu chưa có
        default_api_keys = [
            "AIzaSyCUSYj3VnQ6m1yxeSmavtocdYDimAID7Kc",
            "AIzaSyCwgVeKOtVsN8CPS-sAhz0os6IslgRs-YE", 
            "AIzaSyDYYLscEI4SaWKPocveKo4aG1ma4clc4PA",
            "AIzaSyClZFBCA_uXJLwBYG0rV3j0-flFEH6SyOU"
        ]
        
        added_count = 0
        for key in default_api_keys:
            if key not in self.api_keys:
                self.api_keys.append(key)
                added_count += 1
        
        if added_count > 0:
            self.save_config()
            print(f"🔑 Đã thêm {added_count} API keys mặc định")
            print(f"📊 Tổng số API keys: {len(self.api_keys)}")
    
    def save_config(self):
        """Lưu cấu hình vào file"""
        config = {
            'api_keys': self.api_keys
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def add_api_key(self, key):
        """Thêm API key mới"""
        if key not in self.api_keys:
            self.api_keys.append(key)
            self.save_config()
            return True
        return False
    
    def remove_api_key(self, key):
        """Xóa API key"""
        if key in self.api_keys:
            self.api_keys.remove(key)
            self.save_config()
            return True
        return False
    
    def get_available_key(self):
        """Lấy API key có sẵn (không bị fail gần đây)"""
        current_time = datetime.now()
        
        # Lọc keys không bị fail hoặc đã hết thời gian chờ
        available_keys = []
        for key in self.api_keys:
            if key not in self.failed_keys:
                available_keys.append(key)
            else:
                # Kiểm tra xem đã hết thời gian chờ chưa (5 phút)
                fail_time = self.failed_keys[key]
                if current_time - fail_time > timedelta(minutes=5):
                    available_keys.append(key)
                    del self.failed_keys[key]  # Xóa khỏi danh sách failed
        
        return available_keys
    
    def mark_key_failed(self, api_key):
        """Đánh dấu API key bị fail"""
        self.failed_keys[api_key] = datetime.now()
    
    def generate_image(self, prompt, task_id, input_image_path=None):
        """Tạo ảnh với retry logic - hỗ trợ image input"""
        max_retries = len(self.api_keys) * 2  # Thử mỗi key 2 lần
        retry_count = 0
        
        while retry_count < max_retries:
            # Lấy API key có sẵn
            available_keys = self.get_available_key()
            if not available_keys:
                return {
                    'success': False,
                    'error': 'Tất cả API keys đều không khả dụng. Thử lại sau 5 phút.'
                }
            
            api_key = available_keys[0]
            
            try:
                client = genai.Client(api_key=api_key)
                
                # Chuẩn bị content parts
                parts = []

                # Nếu có ảnh input, thêm text và image
                if input_image_path and os.path.exists(input_image_path):
                    # Text trước, image sau
                    parts.append({
                        "text": f"Generate a new image based on this reference image. Description: {prompt}"
                    })
                    
                    try:
                        with open(input_image_path, "rb") as image_file:
                            image_data = base64.b64encode(image_file.read()).decode('utf-8')

                        # Xác định mime type
                        file_ext = os.path.splitext(input_image_path)[1].lower()
                        mime_type = {
                            '.jpg': 'image/jpeg',
                            '.jpeg': 'image/jpeg',
                            '.png': 'image/png',
                            '.webp': 'image/webp'
                        }.get(file_ext, 'image/jpeg')

                        parts.append({
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_data
                            }
                        })

                        print(f"🖼️ Thêm ảnh input: {input_image_path}")

                    except Exception as e:
                        print(f"⚠️ Lỗi khi đọc ảnh input: {e}")
                        # Fallback to text-only if image fails
                        parts = [
                            {
                                "text": f"Create a beautiful image of: {prompt}. Make it realistic and detailed."
                            }
                        ]
                else:
                    # Model này yêu cầu TEXT + IMAGE input, tạo ảnh mẫu
                    parts = [
                        {
                            "text": f"Create a beautiful image of: {prompt}. Make it realistic and detailed."
                        }
                    ]
                    
                    # Tạo ảnh mẫu đơn giản (1x1 pixel trắng)
                    try:
                        from PIL import Image
                        import io
                        
                        # Tạo ảnh 1x1 pixel trắng
                        sample_img = Image.new('RGB', (1, 1), color='white')
                        buffer = io.BytesIO()
                        sample_img.save(buffer, format='PNG')
                        sample_base64 = base64.b64encode(buffer.getvalue()).decode()
                        
                        parts.append({
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": sample_base64
                            }
                        })
                        
                        print(f"🖼️ Sử dụng ảnh mẫu cho text-only request")
                        
                    except Exception as e:
                        print(f"⚠️ Lỗi khi tạo ảnh mẫu: {e}")
                        # Fallback sang model text-only
                        return {
                            'success': False,
                            'error': f'Model yêu cầu input image. Vui lòng upload ảnh hoặc sử dụng model khác.',
                            'api_key_used': api_key[-8:]
                        }
                
                print(f"🚀 Gửi request đến Gemini API với {len(parts)} parts")
                print(f"📝 Prompt: {prompt}")
                
                # Sử dụng model image generation với config đúng
                response = client.models.generate_content(
                    model="gemini-2.0-flash-preview-image-generation",
                    contents=[
                        {
                            "parts": parts
                        }
                    ],
                    config=types.GenerateContentConfig(
                        response_modalities=['IMAGE', 'TEXT']
                    )
                )
                
                print(f"✅ Nhận được response từ Gemini API")
                print(f"🔍 Response type: {type(response)}")
                print(f"🔍 Response candidates: {len(response.candidates) if response.candidates else 0}")
                
                if response.candidates:
                    print(f"🔍 First candidate type: {type(response.candidates[0])}")
                    if hasattr(response.candidates[0], 'content'):
                        print(f"🔍 Content type: {type(response.candidates[0].content)}")
                        print(f"🔍 Content parts: {len(response.candidates[0].content.parts) if response.candidates[0].content.parts else 0}")
                
                if response.candidates and response.candidates[0].content:
                    has_image = False
                    text_response = ""
                    
                    print(f"🔍 Debug: Response có {len(response.candidates[0].content.parts)} parts")
                    
                    # Kiểm tra các parts trong response
                    for i, part in enumerate(response.candidates[0].content.parts):
                        print(f"🔍 Debug: Part {i} - Type: {type(part)}")
                        print(f"🔍 Debug: Part {i} - Dir: {[attr for attr in dir(part) if not attr.startswith('_')]}")
                        
                        # Kiểm tra nếu part có inline_data (image)
                        if hasattr(part, 'inline_data') and part.inline_data:
                            has_image = True
                            print(f"🖼️ Tìm thấy image data!")
                            print(f"🖼️ Mime type: {part.inline_data.mime_type}")
                            print(f"🖼️ Data length: {len(part.inline_data.data)}")
                            
                            try:
                                # Data đã là bytes, không cần decode base64
                                image_data = part.inline_data.data
                                filename = f"images/{task_id}_{uuid.uuid4().hex[:8]}.png"
                                
                                os.makedirs("images", exist_ok=True)
                                with open(filename, "wb") as f:
                                    f.write(image_data)
                                
                                print(f"✅ Đã lưu ảnh: {filename}")
                                
                                # Trả về filename thay vì full path
                                filename_only = os.path.basename(filename)
                                return {
                                    'success': True,
                                    'filename': filename_only,
                                    'api_key_used': api_key[-8:]
                                }
                            except Exception as e:
                                print(f"❌ Lỗi khi lưu ảnh: {e}")
                                return {
                                    'success': False,
                                    'error': f'Lỗi khi lưu ảnh: {str(e)}',
                                    'api_key_used': api_key[-8:]
                                }
                        
                        # Kiểm tra nếu part có text
                        elif hasattr(part, 'text') and part.text:
                            text_response += part.text
                            print(f"📝 Text response: {part.text[:100]}...")
                        
                        # Kiểm tra các thuộc tính khác có thể chứa image data
                        elif hasattr(part, 'function_call'):
                            print(f"🔍 Function call part: {part.function_call}")
                        elif hasattr(part, 'file_data'):
                            print(f"🔍 File data part: {part.file_data}")
                        else:
                            print(f"🔍 Unknown part type: {type(part)}")
                            print(f"🔍 Part attributes: {[attr for attr in dir(part) if not attr.startswith('_')]}")
                    
                    # Nếu không tìm thấy image trong response
                    if not has_image:
                        print(f"⚠️ Không tìm thấy image trong response. Text: {text_response[:200]}...")
                        
                        # Kiểm tra nếu text response cho biết lý do không tạo được ảnh
                        if "cannot" in text_response.lower() or "not supported" in text_response.lower() or "error" in text_response.lower():
                            return {
                                'success': False,
                                'error': f'Model không thể tạo ảnh: {text_response[:200]}...',
                                'api_key_used': api_key[-8:]
                            }
                        else:
                            # Đánh dấu API key này bị fail và thử lại
                            self.mark_key_failed(api_key)
                            retry_count += 1
                            time.sleep(2)  # Delay ngắn trước khi thử lại
                            continue
                
                # Nếu không có content trong response
                self.mark_key_failed(api_key)
                retry_count += 1
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    self.mark_key_failed(api_key)
                    retry_count += 1
                    time.sleep(2)  # Delay ngắn trước khi thử lại
                else:
                    return {
                        'success': False,
                        'error': f'Lỗi API: {error_msg}'
                    }
        
        return {
            'success': False,
            'error': f'Đã thử {max_retries} lần nhưng không thành công'
        }

# Khởi tạo generator
generator = GeminiImageGenerator()

# Khởi tạo prompt processor
prompt_processor = PromptProcessor(generator)

class CharacterAnalyzer:
    """Phân tích nhân vật từ ảnh để đồng bộ"""
    def __init__(self, generator):
        self.generator = generator
    
    def analyze_character(self, image_path):
        """Phân tích nhân vật từ ảnh"""
        try:
            # Sử dụng Gemini để phân tích ảnh thay vì tạo ảnh
            available_keys = self.generator.get_available_key()
            if not available_keys:
                return {
                    'success': False,
                    'error': 'Không có API key khả dụng để phân tích nhân vật'
                }
            
            api_key = available_keys[0]
            
            try:
                client = genai.Client(api_key=api_key)
                
                # Đọc ảnh
                with open(image_path, "rb") as image_file:
                    image_data = base64.b64encode(image_file.read()).decode('utf-8')
                
                # Xác định mime type
                file_ext = os.path.splitext(image_path)[1].lower()
                mime_type = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.webp': 'image/webp'
                }.get(file_ext, 'image/jpeg')
                
                # Prompt để phân tích nhân vật - tập trung vào màu sắc và yếu tố nhận dạng
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

                KHÔNG mô tả:
                - Hành động cụ thể (đang chạy, đang ngồi, etc.)
                - Biểu cảm tạm thời (đang cười, đang khóc, etc.)
                - Tình huống cụ thể

                Trả về mô tả chi tiết và có cấu trúc về màu sắc của nhân vật và tổng thể ảnh để AI có thể tái tạo nhân vật này với cùng phong cách màu sắc một cách chính xác nhất.
                """
                
                # Gọi Gemini để phân tích ảnh
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[
                        {
                            "parts": [
                                {
                                    "text": analysis_prompt
                                },
                                {
                                    "inline_data": {
                                        "mime_type": mime_type,
                                        "data": image_data
                                    }
                                }
                            ]
                        }
                    ]
                )
                
                if response.candidates and response.candidates[0].content:
                    analysis_text = ""
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'text') and part.text:
                            analysis_text += part.text
                    
                    if analysis_text.strip():
                        return {
                            'success': True,
                            'analysis': analysis_text.strip()
                        }
                    else:
                        return {
                            'success': False,
                            'error': 'AI không trả về phân tích nhân vật'
                        }
                else:
                    return {
                        'success': False,
                        'error': 'Không nhận được response từ AI'
                    }
                    
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    self.generator.mark_key_failed(api_key)
                    return {
                        'success': False,
                        'error': 'API key đã hết quota, vui lòng thử lại sau'
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Lỗi khi phân tích nhân vật: {error_msg}'
                    }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Lỗi khi phân tích nhân vật: {str(e)}'
            }
    
    def enhance_prompt_with_character(self, original_prompt, character_analysis):
        """Tăng cường prompt với thông tin nhân vật và màu sắc tổng thể"""
        if not character_analysis:
            return original_prompt
        
        # Tạo prompt tăng cường với thông tin nhân vật và màu sắc tổng thể
        enhanced_prompt = f"{original_prompt}, với nhân vật có đặc điểm: {character_analysis}, sử dụng cùng phong cách màu sắc và ánh sáng như ảnh mẫu"
        return enhanced_prompt

# Thêm vào sau class PromptProcessor
character_analyzer = CharacterAnalyzer(generator)

class TaskManager:
    def __init__(self):
        self.tasks = {}
        self.queue = []  # Hàng đợi các task chờ xử lý
        self.is_processing = False  # Trạng thái đang xử lý
        self.load_tasks()
        
        # Bắt đầu worker thread để xử lý hàng đợi
        self.worker_thread = threading.Thread(target=self.queue_worker, daemon=True)
        self.worker_thread.start()
    
    def load_tasks(self):
        """Load danh sách tasks từ file"""
        if os.path.exists(TASK_FILE):
            with open(TASK_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.tasks = data.get('tasks', {})
                self.queue = data.get('queue', [])
    
    def save_tasks(self):
        """Lưu tasks và queue vào file"""
        data = {
            'tasks': self.tasks,
            'queue': self.queue
        }
        with open(TASK_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def create_task(self, prompts, batch_name="Batch", input_image_path=None, auto_start=True):
        """Tạo task mới với hỗ trợ input image và tùy chọn auto start"""
        task_id = str(uuid.uuid4())
        
        task = {
            'id': task_id,
            'name': batch_name,
            'prompts': prompts,
            'input_image_path': input_image_path,
            'total_count': len(prompts),
            'completed_count': 0,
            'failed_count': 0,
            'status': 'pending',  # pending, queued, processing, completed, failed, partial
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'results': [],
            'auto_start': auto_start  # Có tự động chạy không
        }
        
        self.tasks[task_id] = task
        self.save_tasks()
        
        # Thêm vào hàng đợi nếu auto_start = True
        if auto_start:
            self.add_to_queue(task_id)
        else:
            print(f"📋 Task {task_id} được tạo và chờ chạy thủ công")
        
        return task_id
    
    def add_to_queue(self, task_id):
        """Thêm task vào hàng đợi"""
        if task_id not in self.queue and task_id in self.tasks:
            self.queue.append(task_id)
            self.tasks[task_id]['status'] = 'queued'
            self.tasks[task_id]['updated_at'] = datetime.now().isoformat()
            self.save_tasks()
            print(f"📋 Đã thêm task {task_id} vào hàng đợi")
            # Kích hoạt worker thread
            self.process_queue()
    
    def remove_from_queue(self, task_id):
        """Xóa task khỏi hàng đợi"""
        if task_id in self.queue:
            self.queue.remove(task_id)
            if self.tasks[task_id]['status'] == 'queued':
                self.tasks[task_id]['status'] = 'pending'
            self.save_tasks()
            print(f"📋 Đã xóa task {task_id} khỏi hàng đợi")
    
    def start_task_manual(self, task_id):
        """Chạy task thủ công"""
        if task_id not in self.tasks:
            return {'success': False, 'error': 'Task không tồn tại'}
        
        task = self.tasks[task_id]
        if task['status'] in ['completed', 'failed']:
            return {'success': False, 'error': 'Task đã hoàn thành'}
        
        if task_id not in self.queue:
            self.add_to_queue(task_id)
        
        return {'success': True, 'message': 'Task đã được thêm vào hàng đợi'}
    
    def queue_worker(self):
        """Worker thread để xử lý hàng đợi"""
        while True:
            try:
                if self.queue and not self.is_processing:
                    task_id = self.queue[0]
                    self.is_processing = True
                    self.remove_from_queue(task_id)
                    self.process_task(task_id)
                    self.is_processing = False
                else:
                    time.sleep(2)  # Chờ 2 giây trước khi kiểm tra lại
            except Exception as e:
                print(f"❌ Lỗi trong queue worker: {e}")
                self.is_processing = False
                time.sleep(5)
    
    def process_queue(self):
        """Kích hoạt xử lý hàng đợi"""
        # Không cần làm gì, worker thread sẽ tự động xử lý
        pass
    
    def get_queue_status(self):
        """Lấy trạng thái hàng đợi"""
        return {
            'queue': self.queue,
            'is_processing': self.is_processing,
            'queue_length': len(self.queue),
            'next_task': self.queue[0] if self.queue else None
        }
    
    def process_task(self, task_id):
        """Xử lý task trong background"""
        task = self.tasks[task_id]
        task['status'] = 'processing'
        task['updated_at'] = datetime.now().isoformat()
        self.save_tasks()
        
        for i, prompt in enumerate(task['prompts']):
            try:
                result = generator.generate_image(prompt, task_id, task.get('input_image_path'))
                
                if result['success']:
                    task['results'].append({
                        'prompt': prompt,
                        'filename': result['filename'],
                        'api_key_used': result['api_key_used'],
                        'status': 'success',
                        'timestamp': datetime.now().isoformat()
                    })
                    task['completed_count'] += 1
                else:
                    task['results'].append({
                        'prompt': prompt,
                        'error': result['error'],
                        'status': 'failed',
                        'timestamp': datetime.now().isoformat()
                    })
                    task['failed_count'] += 1
                
                task['updated_at'] = datetime.now().isoformat()
                self.save_tasks()
                
                # Delay giữa các request
                time.sleep(1)
                
            except Exception as e:
                task['results'].append({
                    'prompt': prompt,
                    'error': str(e),
                    'status': 'failed',
                    'timestamp': datetime.now().isoformat()
                })
                task['failed_count'] += 1
                task['updated_at'] = datetime.now().isoformat()
                self.save_tasks()
        
        # Cập nhật trạng thái cuối
        if task['failed_count'] == task['total_count']:
            task['status'] = 'failed'
        elif task['completed_count'] == task['total_count']:
            task['status'] = 'completed'
        else:
            task['status'] = 'partial'
        
        # Xóa ảnh input tạm thời sau khi hoàn thành
        if task.get('input_image_path'):
            try:
                if os.path.exists(task['input_image_path']):
                    os.remove(task['input_image_path'])
                    print(f"🗑️ Đã xóa ảnh input tạm thời: {task['input_image_path']}")
            except Exception as e:
                print(f"⚠️ Không thể xóa ảnh input: {e}")
        
        task['updated_at'] = datetime.now().isoformat()
        self.save_tasks()
    
    def delete_task(self, task_id):
        """Xóa task và các file liên quan"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            
            # Xóa các file ảnh được tạo (sử dụng filename thay vì image_path)
            for result in task.get('results', []):
                if result.get('status') == 'success' and result.get('filename'):
                    filename = result['filename']
                    image_path = os.path.join(os.path.dirname(__file__), 'images', filename)
                    if os.path.exists(image_path):
                        try:
                            os.remove(image_path)
                            print(f"🗑️ Đã xóa file ảnh: {filename}")
                        except Exception as e:
                            print(f"⚠️ Không thể xóa file {filename}: {e}")
            
            # Xóa task khỏi memory và file
            del self.tasks[task_id]
            self.save_tasks()
            
            return True
        return False

# Khởi tạo task manager
task_manager = TaskManager()

def allowed_file(filename):
    """Kiểm tra file có được phép upload không"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return "Gemini AI Image Generator Backend"

@app.route('/api/keys', methods=['GET'])
def get_api_keys():
    """Lấy danh sách API keys"""
    return jsonify({
        'keys': generator.api_keys,
        'total': len(generator.api_keys)
    })

@app.route('/api/keys', methods=['POST'])
def add_api_key():
    """Thêm API key mới"""
    data = request.json
    key = data.get('key')
    
    if not key:
        return jsonify({'error': 'API key không được để trống'}), 400
    
    # Kiểm tra format API key
    if not key.startswith('AIza') or len(key) < 30:
        return jsonify({'error': 'API key không đúng định dạng. Phải bắt đầu bằng "AIza" và có ít nhất 30 ký tự'}), 400
    
    if generator.add_api_key(key):
        print(f"✅ Đã thêm API key: {key[-8:]}")
        return jsonify({'message': 'Thêm API key thành công'})
    else:
        return jsonify({'error': 'API key đã tồn tại trong hệ thống'}), 400

@app.route('/api/keys/<key_suffix>', methods=['DELETE'])
def remove_api_key(key_suffix):
    """Xóa API key theo suffix"""
    for key in generator.api_keys:
        if key.endswith(key_suffix):
            if generator.remove_api_key(key):
                return jsonify({'message': 'Xóa API key thành công'})
            break
    
    return jsonify({'error': 'Không tìm thấy API key'}), 404

@app.route('/api/tasks', methods=['POST'])
def create_batch_task():
    """Tạo task tạo ảnh hàng loạt với hỗ trợ input image và character sync"""
    data = request.json
    prompts = data.get('prompts', [])
    batch_name = data.get('name', 'Batch')
    input_image_path = data.get('input_image_path')  # Path đến ảnh input
    character_sync = data.get('character_sync', False)  # Bật đồng bộ nhân vật
    character_analysis = data.get('character_analysis')  # Phân tích nhân vật
    auto_start = data.get('auto_start', True)  # Tùy chọn tự động chạy
    
    if not prompts:
        return jsonify({'error': 'Danh sách prompts không được để trống'}), 400
    
    if not generator.api_keys:
        return jsonify({'error': 'Chưa có API key nào được cấu hình'}), 400
    
    # Kiểm tra input image nếu có
    if input_image_path and not os.path.exists(input_image_path):
        return jsonify({'error': f'Không tìm thấy ảnh input: {input_image_path}'}), 400
    
    # Nếu bật character sync nhưng chưa có phân tích, tự động phân tích
    if character_sync and not character_analysis and input_image_path:
        print("🔄 Tự động phân tích nhân vật...")
        analysis_result = character_analyzer.analyze_character(input_image_path)
        if analysis_result['success']:
            character_analysis = analysis_result['analysis']
            print("✅ Phân tích nhân vật thành công")
        else:
            print(f"⚠️ Lỗi phân tích nhân vật: {analysis_result['error']}")
    
    # Tăng cường prompts với thông tin nhân vật nếu có
    enhanced_prompts = []
    for prompt in prompts:
        if character_sync and character_analysis:
            enhanced_prompt = character_analyzer.enhance_prompt_with_character(prompt, character_analysis)
            enhanced_prompts.append(enhanced_prompt)
        else:
            enhanced_prompts.append(prompt)
    
    task_id = task_manager.create_task(enhanced_prompts, batch_name, input_image_path, auto_start)
    
    status_message = 'và bắt đầu xử lý' if auto_start else 'và chờ chạy thủ công'
    character_message = ' (với đồng bộ nhân vật)' if character_sync else ''
    
    return jsonify({
        'task_id': task_id,
        'message': f'Tạo task thành công {status_message}{character_message}',
        'auto_start': auto_start,
        'character_sync': character_sync
    })

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Lấy danh sách tasks (sắp xếp theo thời gian tạo mới nhất)"""
    tasks = list(task_manager.tasks.values())
    # Sắp xếp theo thời gian tạo, mới nhất lên đầu
    tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return jsonify({
        'tasks': {task['id']: task for task in tasks},
        'total': len(tasks)
    })

@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """Lấy thông tin chi tiết task"""
    if task_id in task_manager.tasks:
        return jsonify(task_manager.tasks[task_id])
    else:
        return jsonify({'error': 'Không tìm thấy task'}), 404

@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Xóa task và các file liên quan"""
    if task_manager.delete_task(task_id):
        return jsonify({'message': 'Xóa task thành công'})
    else:
        return jsonify({'error': 'Không tìm thấy task'}), 404

@app.route('/api/status', methods=['GET'])
def get_status():
    """Lấy trạng thái hệ thống"""
    available_keys = generator.get_available_key()
    failed_keys = len(generator.failed_keys)
    
    # Thống kê tasks
    total_tasks = len(task_manager.tasks)
    pending_tasks = sum(1 for task in task_manager.tasks.values() if task['status'] == 'pending')
    queued_tasks = sum(1 for task in task_manager.tasks.values() if task['status'] == 'queued')
    processing_tasks = sum(1 for task in task_manager.tasks.values() if task['status'] == 'processing')
    completed_tasks = sum(1 for task in task_manager.tasks.values() if task['status'] == 'completed')
    failed_tasks = sum(1 for task in task_manager.tasks.values() if task['status'] == 'failed')
    
    # Trạng thái hàng đợi
    queue_status = task_manager.get_queue_status()
    
    return jsonify({
        'total_api_keys': len(generator.api_keys),
        'available_keys': len(available_keys),
        'failed_keys': failed_keys,
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'queued_tasks': queued_tasks,
        'processing_tasks': processing_tasks,
        'completed_tasks': completed_tasks,
        'failed_tasks': failed_tasks,
        'queue': queue_status
    })

@app.route('/api/queue/status', methods=['GET'])
def get_queue_status():
    """Lấy trạng thái hàng đợi"""
    return jsonify(task_manager.get_queue_status())

@app.route('/api/queue/add/<task_id>', methods=['POST'])
def add_to_queue(task_id):
    """Thêm task vào hàng đợi"""
    if task_id not in task_manager.tasks:
        return jsonify({'error': 'Task không tồn tại'}), 404
    
    task_manager.add_to_queue(task_id)
    return jsonify({'message': 'Đã thêm task vào hàng đợi'})

@app.route('/api/queue/remove/<task_id>', methods=['POST'])
def remove_from_queue(task_id):
    """Xóa task khỏi hàng đợi"""
    if task_id not in task_manager.tasks:
        return jsonify({'error': 'Task không tồn tại'}), 404
    
    task_manager.remove_from_queue(task_id)
    return jsonify({'message': 'Đã xóa task khỏi hàng đợi'})

@app.route('/api/tasks/<task_id>/start', methods=['POST'])
def start_task_manual(task_id):
    """Chạy task thủ công"""
    if task_id not in task_manager.tasks:
        return jsonify({'error': 'Task không tồn tại'}), 404
    
    result = task_manager.start_task_manual(task_id)
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400

@app.route('/api/download-image/<path:filename>')
def download_single_image(filename):
    """Tải một ảnh cụ thể"""
    try:
        image_path = os.path.join(os.path.dirname(__file__), 'images', filename)
        if not os.path.exists(image_path):
            return jsonify({'error': 'Không tìm thấy file ảnh'}), 404
        
        return send_file(
            image_path,
            mimetype='image/png',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': f'Lỗi khi tải ảnh: {str(e)}'}), 500

@app.route('/api/split-prompts', methods=['POST'])
def split_prompts():
    """Phân tách text thành các prompt riêng biệt"""
    data = request.json
    text = data.get('text', '').strip()
    use_ai = data.get('use_ai', True)  # Mặc định sử dụng AI
    
    if not text:
        return jsonify({'error': 'Text không được để trống'}), 400
    
    if not generator.api_keys:
        return jsonify({'error': 'Chưa có API key nào được cấu hình'}), 400
    
    # Chọn method phân tách
    if use_ai:
        result = prompt_processor.split_prompts_ai(text)
    else:
        result = prompt_processor.split_prompts_simple(text)
    
    if result['success']:
        return jsonify({
            'success': True,
            'prompts': result['prompts'],
            'count': result['count'],
            'analysis': result.get('analysis', ''),
            'api_key_used': result.get('api_key_used', '')
        })
    else:
        return jsonify({
            'success': False,
            'error': result['error']
        }), 400

@app.route('/api/upload-image', methods=['POST'])
def upload_image():
    """Upload ảnh input - chỉ lưu tạm thời để xử lý"""
    if 'image' not in request.files:
        return jsonify({'error': 'Không có file ảnh'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Không có file được chọn'}), 400

    if file and allowed_file(file.filename):
        # Tạo thư mục tạm thời nếu chưa có
        temp_folder = 'temp_input_images'
        os.makedirs(temp_folder, exist_ok=True)

        # Tạo tên file tạm thời với ID duy nhất
        original_filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")  # Thêm microseconds
        unique_id = uuid.uuid4().hex[:8]  # Thêm ID duy nhất
        temp_filename = f"{timestamp}_{unique_id}_{original_filename}"

        temp_file_path = os.path.join(temp_folder, temp_filename)
        file.save(temp_file_path)

        print(f"📁 Đã upload ảnh mới: {temp_filename}")

        return jsonify({
            'message': 'Upload ảnh thành công',
            'image_path': temp_file_path,
            'filename': temp_filename
        })
    else:
        return jsonify({'error': 'Định dạng file không được hỗ trợ'}), 400

@app.route('/api/images/<path:filename>')
def serve_image(filename):
    """Phục vụ file ảnh"""
    try:
        # Sử dụng đường dẫn tuyệt đối đến thư mục images
        image_path = os.path.join(os.path.dirname(__file__), 'images', filename)
        return send_file(image_path, mimetype='image/png')
    except FileNotFoundError:
        return jsonify({'error': 'Không tìm thấy file ảnh'}), 404

@app.route('/api/download-all-images/<task_id>')
def download_all_images(task_id):
    """Tải tất cả ảnh của một task dưới dạng ZIP"""
    try:
        import zipfile
        from io import BytesIO
        
        if task_id not in task_manager.tasks:
            return jsonify({'error': 'Không tìm thấy task'}), 404
        
        task = task_manager.tasks[task_id]
        images_dir = os.path.join(os.path.dirname(__file__), 'images')
        
        # Thu thập các ảnh thành công
        successful_images = []
        for i, result in enumerate(task.get('results', []), 1):
            if result.get('status') == 'success' and result.get('filename'):
                image_filename = result.get('filename')
                image_path = os.path.join(images_dir, image_filename)
                if os.path.exists(image_path):
                    prompt = result.get('prompt', f'prompt_{i}')
                    safe_prompt = "".join(c for c in prompt if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    zip_filename = f"{safe_prompt}_{i}_{image_filename}"
                    successful_images.append({
                        'image_path': image_path,
                        'zip_filename': zip_filename
                    })
        
        # Kiểm tra có ảnh thành công không
        if not successful_images:
            return jsonify({'error': 'Không có ảnh thành công nào để tải xuống'}), 400
        
        # Tạo file ZIP trong memory
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Thêm từng ảnh thành công vào ZIP
            for image_info in successful_images:
                zip_file.write(image_info['image_path'], image_info['zip_filename'])
        
        zip_buffer.seek(0)
        
        # Trả về file ZIP
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"task_{task_id}_images.zip"
        )
        
    except Exception as e:
        return jsonify({'error': f'Lỗi khi tạo file ZIP: {str(e)}'}), 500

@app.route('/api/analyze-character', methods=['POST'])
def analyze_character():
    """Phân tích nhân vật từ ảnh"""
    try:
        data = request.json
        image_path = data.get('image_path')
        
        if not image_path:
            return jsonify({'error': 'Thiếu đường dẫn ảnh'}), 400
        
        if not os.path.exists(image_path):
            return jsonify({'error': 'Không tìm thấy file ảnh'}), 400
        
        result = character_analyzer.analyze_character(image_path)
        
        if result['success']:
            return jsonify({
                'success': True,
                'analysis': result['analysis']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Lỗi server: {str(e)}'
        }), 500

def cleanup_temp_images():
    """Xóa các ảnh input tạm thời cũ"""
    temp_folder = 'temp_input_images'
    if os.path.exists(temp_folder):
        try:
            import shutil
            shutil.rmtree(temp_folder)
            print(f"🗑️ Đã xóa thư mục temp input images: {temp_folder}")
        except Exception as e:
            print(f"⚠️ Không thể xóa temp folder: {e}")

if __name__ == '__main__':
    # Tạo thư mục cần thiết
    os.makedirs('images', exist_ok=True)
    
    # Cleanup ảnh temp cũ khi khởi động
    cleanup_temp_images()
    
    print("🚀 Khởi động Gemini Image Generator Backend")
    print(f"📊 Số API keys đã cấu hình: {len(generator.api_keys)}")
    print(f"📋 Số tasks đã lưu: {len(task_manager.tasks)}")
    print(f"📁 Thư mục images: images/")
    print(f"🗑️ Ảnh input sẽ được xóa sau khi xử lý")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
