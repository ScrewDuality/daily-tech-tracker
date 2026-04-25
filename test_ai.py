#!/usr/bin/env python3
import os
import google.generativeai as genai

# 1. 取得儲存在 GitHub Secrets 中的 API Key
# 注意：在 Codespaces 本地測試時，你可以暫時手動輸入字串，但推送到 GitHub 後會改讀 Secrets
api_key = os.getenv("GEMINI_API_KEY") 

if not api_key:
    print("錯誤：找不到 GEMINI_API_KEY。請確認環境變數已設定。")
else:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-flash-latest')
    
    # 2. 進行簡單的硬體邏輯測試
    prompt = "請簡述為什麼在車用電路中，MOSFET 需要符合 AEC-Q101 認證？"
    
    try:
        response = model.generate_content(prompt)
        print("--- AI 回應測試成功 ---")
        print(response.text)
    except Exception as e:
        print(f"呼叫 API 時發生錯誤：{e}")
    print("测试完成")