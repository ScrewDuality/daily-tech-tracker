import os
import requests
import json
import google.generativeai as genai
from datetime import datetime
from pathlib import Path

# 1. 取得 API Key 並設定大腦 (我們使用 latest!)
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-flash-latest')

print("📡 正在從 Hacker News 抓取最新資訊...")

# 2. 爬蟲：抓取 Hacker News 上最新的 5 篇文章標題
response = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json")
top_story_ids = response.json()[:5]

raw_news_data = ""
for story_id in top_story_ids:
    story = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json").json()
    raw_news_data += f"- {story.get('title')}\n"

print(f"📥 抓取完成，原始雜訊如下：\n{raw_news_data}")
print("🧠 正在呼叫 Gemini 進行降噪與 JSON 結構化...\n")

# 3. 核心 Prompt：強制 AI 輸出我們需要的 JSON 格式
prompt = f"""
你是一個專屬的硬體與科技情報助理。請閱讀以下最新的新聞標題，並判斷它們的性質。
請絕對遵守以下規則：
1. 只輸出純 JSON 格式的陣列（Array），不要有任何 Markdown 標記，也不要說任何廢話。
2. 陣列中的每個物件必須包含以下 key：
   - "title": 新聞標題
   - "category": 類別 (Software/Hardware/AI/Other)
   - "interest_level": 你認為身為一個嵌入式系統與硬體研發工程師，對這則新聞的興趣程度 (High/Medium/Low)

以下是今天的新聞：
{raw_news_data}
"""

# 4. 呼叫大腦並印出結果
try:
    ai_response = model.generate_content(prompt)
    
    # 驗證 AI 是否乖乖吐出 JSON
    clean_json_text = ai_response.text.strip().removeprefix("```json").removesuffix("```").strip()
    structured_data = json.loads(clean_json_text)
    
    print("✅ AI 整理完畢，準備寫入資料庫的 JSON 格式如下：")
    print(json.dumps(structured_data, indent=2, ensure_ascii=False))
    
    # 5. 保存到 GitHub Pages 資料夾
    output_dir = Path("docs")
    output_dir.mkdir(exist_ok=True)
    
    # 生成帶時間戳的 JSON
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "articles": structured_data
    }
    
    output_file = output_dir / "daily_news.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 數據已保存到 {output_file}")

except json.JSONDecodeError:
    print("❌ 錯誤：AI 沒有輸出標準的 JSON 格式！")
    print("AI 實際輸出：\n", ai_response.text)
except Exception as e:
    print(f"❌ 發生未知的錯誤：{e}")