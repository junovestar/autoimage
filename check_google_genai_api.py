#!/usr/bin/env python3
"""
Script để kiểm tra API của thư viện google-genai
"""

from google import genai
import inspect

def check_genai_api():
    """Kiểm tra các functions và classes có sẵn"""
    print("🔍 Kiểm tra API của google.genai")
    print("=" * 40)
    
    # Kiểm tra genai module
    print("📝 genai module attributes:")
    for attr in dir(genai):
        if not attr.startswith('_'):
            print(f"  - {attr}")
    
    print("\n" + "=" * 40)
    
    # Kiểm tra Client class
    print("🔧 genai.Client methods:")
    client = genai.Client(api_key="test")
    for method in dir(client):
        if not method.startswith('_'):
            print(f"  - {method}")
    
    print("\n" + "=" * 40)
    
    # Kiểm tra models
    print("📋 genai.Client.models methods:")
    for method in dir(client.models):
        if not method.startswith('_'):
            print(f"  - {method}")
    
    print("\n" + "=" * 40)
    
    # Kiểm tra generate_content method
    print("🎯 generate_content method signature:")
    try:
        signature = inspect.signature(client.models.generate_content)
        print(f"  {signature}")
        
        # Kiểm tra docstring
        doc = client.models.generate_content.__doc__
        if doc:
            print(f"  📖 Docstring: {doc[:200]}...")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    print("\n" + "=" * 40)
    
    # Thử import types
    print("📦 Thử import types:")
    try:
        from google.generativeai import types
        print("  ✅ google.generativeai.types imported successfully")
        print("  📝 types attributes:")
        for attr in dir(types):
            if not attr.startswith('_'):
                print(f"    - {attr}")
    except Exception as e:
        print(f"  ❌ Error importing types: {e}")
    
    # Thử import từ genai
    print("\n📦 Thử import từ genai:")
    try:
        import google.genai.types
        print("  ✅ google.genai.types imported successfully")
        print("  📝 google.genai.types attributes:")
        for attr in dir(google.genai.types):
            if not attr.startswith('_'):
                print(f"    - {attr}")
    except Exception as e:
        print(f"  ❌ Error importing from genai: {e}")

if __name__ == "__main__":
    check_genai_api()
