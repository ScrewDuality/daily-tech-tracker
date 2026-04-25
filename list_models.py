import os
import google.generativeai as genai

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

print("🔍 正在查詢你的 API Key 可以使用的模型清單...\n")

# 列出所有支援生成內容 (generateContent) 的模型
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"✅ 可用模型名稱: {m.name}")