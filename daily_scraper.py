import os
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import json
import time # 引入時間模組，避免爬太快被封鎖
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# 1. 喚醒大腦
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-flash-latest')

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

url = "https://technews.tw/"
print(f"📡 正在潛入 {url} 抓取首頁清單...")
response = requests.get(url, headers=headers)
response.encoding = 'utf-8'
soup = BeautifulSoup(response.text, "html.parser")

articles = soup.find_all("h1", class_="entry-title", limit=5) # 這次先抓 5 篇就好，避免等太久

raw_news_data = ""
for idx, article in enumerate(articles, 1):
    title = article.text.strip()
    link = article.find('a')['href'] if article.find('a') else ""
    
    print(f"  └ 正在鑽取內文 ({idx}/5): {title[:15]}...")
    
    # ==========================================
    # 🌟 新增：深層爬蟲邏輯 (進入文章內頁)
    # ==========================================
    article_content = "無內文"
    if link:
        try:
            # 點進去那篇文章
            article_resp = requests.get(link, headers=headers, timeout=5)
            article_resp.encoding = 'utf-8'
            article_soup = BeautifulSoup(article_resp.text, "html.parser")
            
            # 科技新報的內文通常包在 div.indent 裡面的 <p> 標籤
            # 我們抓取前 3 個段落，大約 300~500 字，對 AI 判斷已經非常足夠
            paragraphs = article_soup.select('div.indent p')
            if not paragraphs: # 如果找不到，退而求其次抓所有段落
                paragraphs = article_soup.find_all('p')
                
            # 將段落文字合併，並限制最多只取前 500 個字元 (省時間與 Token)
            article_content = " ".join([p.text.strip() for p in paragraphs[:3]])[:500]
            
            # 禮貌性暫停 1 秒，避免對科技新報伺服器造成壓力而被擋 IP
            time.sleep(1) 
            
        except Exception as e:
            article_content = f"抓取內文失敗: {e}"

    # 將標題與內文組合起來
    raw_news_data += f"新聞 {idx}:\n標題: {title}\n網址: {link}\n內文摘要: {article_content}...\n---\n"

print(f"\n📥 抓取完成！這次有包含內文了。")
print("🧠 正在呼叫 Gemini 進行深度分析...\n")

# 3. 呼叫 AI (Prompt 加上要求參考內文)
prompt = f"""
你是一位資深的硬體與嵌入式系統研發總監。請閱讀以下來自《科技新報》的最新新聞（包含內文摘要）。
請從「硬體研發、晶片設計、供應鏈變化、AI 終端應用」的角度，深入評估這些新聞對我們團隊的價值。

請絕對遵守以下規則：
1. 只輸出純 JSON 格式的陣列（Array），不要有 Markdown 標記，不要廢話。
2. JSON 陣列中的每個物件必須包含以下 key：
   - "title": 新聞標題
   - "url": 新聞連結
   - "core_insight": 根據內文，萃取出一句對工程師最有價值的核心情報 (20字內)
   - "rd_relevance": 研發關聯度 (High/Medium/Low)
   - "action_suggestion": 給我的具體行動建議 (例如：需留意 MOSFET 交期、可評估此新架構)

以下是今天的新聞資料：
{raw_news_data}
"""

try:
    ai_response = model.generate_content(prompt)
    clean_text = ai_response.text.strip().removeprefix("```json").removesuffix("```").strip()
    structured_data = json.loads(clean_text)
    
    print("✅ 深度分析完畢！結果如下：")
    print(json.dumps(structured_data, indent=2, ensure_ascii=False))
    
    # 4. 保存到 GitHub Pages 資料夾（支持台灣時間）
    output_dir = Path("docs")
    output_dir.mkdir(exist_ok=True)
    
    # 使用台灣時區生成時間戳
    tz = ZoneInfo("Asia/Taipei")
    now_taipei = datetime.now(tz)
    
    output_data = {
        "timestamp": now_taipei.isoformat(),
        "date": now_taipei.strftime("%Y-%m-%d"),
        "articles": structured_data
    }
    
    output_file = output_dir / "daily_news.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 數據已保存到 {output_file}")

except Exception as e:
    print(f"❌ 發生錯誤：{e}")