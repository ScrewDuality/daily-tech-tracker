import os
import sys
import re

# Fix for Windows terminal Unicode output issues
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import requests
from bs4 import BeautifulSoup
from bs4 import XMLParsedAsHTMLWarning, FeatureNotFound
import google.generativeai as genai
import json
import time # 引入時間模組，避免爬太快被封鎖
import warnings
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

SCRAPE_MINUTES_THRESHOLD = int(os.getenv("SCRAPE_MINUTES_THRESHOLD", "60"))
OUTPUT_DIR = Path("docs")
OUTPUT_FILE = OUTPUT_DIR / "daily_news.json"

# 1. 喚醒大腦
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

OUTPUT_DIR.mkdir(exist_ok=True)

# 台北時區
TZ = ZoneInfo("Asia/Taipei")

# 解析時間
def parse_date_string(date_str: str) -> str:
    if not date_str:
        return ""
    date_str = date_str.strip()
    match = re.search(r"(\d{4})\D+(\d{1,2})\D+(\d{1,2})\D+(\d{1,2}):(\d{2})", date_str)
    if match:
        year, month, day, hour, minute = match.groups()
        return datetime(int(year), int(month), int(day), int(hour), int(minute), tzinfo=TZ).isoformat()
    try:
        dt = parsedate_to_datetime(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=TZ)
        return dt.astimezone(TZ).isoformat()
    except Exception:
        try:
            dt = datetime.fromisoformat(date_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=TZ)
            return dt.astimezone(TZ).isoformat()
        except Exception:
            return ""


def fetch_technews_articles(limit: int = 3) -> list[dict]:
    print("📡 正在從 TechNews RSS 抓取最新新聞...")
    feed_url = "https://technews.tw/rss"
    response = requests.get(feed_url, headers=headers, timeout=10)

    try:
        soup = BeautifulSoup(response.content, 'xml')
    except FeatureNotFound:
        warnings.filterwarnings('ignore', category=XMLParsedAsHTMLWarning)
        soup = BeautifulSoup(response.content, 'html.parser')

    items = soup.find_all('item')

    articles = []
    for item in items[:limit]:
        title = item.title.get_text(strip=True) if item.title else ""
        # TechNews RSS 使用 guid 作為 URL
        guid_elem = item.find('guid')
        url = guid_elem.get_text(strip=True) if guid_elem else ""

        # TechNews RSS 使用 pubdate (全小寫)
        pub_date_elem = item.find('pubdate')
        published_at = parse_date_string(pub_date_elem.get_text(strip=True)) if pub_date_elem else ""

        # 獲取摘要
        description_elem = item.find('description')
        if description_elem:
            summary = BeautifulSoup(description_elem.get_text(strip=True), 'html.parser').get_text(separator=' ', strip=True)[:400]
        else:
            summary = ""

        articles.append({
            "source": "TechNews",
            "title": title,
            "url": url,
            "published_at": published_at,
            "summary": summary
        })

    print(f"📥 TechNews RSS 抓取完成，取得 {len(articles)} 篇文章")
    return articles


def fetch_theverge_articles(limit: int = 3) -> list[dict]:
    print("📡 正在從 The Verge Tech RSS 抓取最新新聞...")
    feed_url = "https://www.theverge.com/rss/tech/index.xml"
    response = requests.get(feed_url, headers=headers, timeout=10)

    # The Verge 使用 Atom 格式，需要特殊處理
    try:
        soup = BeautifulSoup(response.content, 'xml')
    except FeatureNotFound:
        warnings.filterwarnings('ignore', category=XMLParsedAsHTMLWarning)
        soup = BeautifulSoup(response.content, 'html.parser')

    # Atom 格式使用 'entry' 而不是 'item'
    entries = soup.find_all('entry')

    articles = []
    for entry in entries[:limit]:  # 使用切片而不是 limit 參數
        # Atom 格式的標籤處理
        title_elem = entry.find('title')
        title = title_elem.get_text(strip=True) if title_elem else ""

        # Atom 格式的連結處理
        link_elem = entry.find('link', {'rel': 'alternate'})
        if link_elem:
            url = link_elem.get('href', '')
        else:
            # 備用：查找任何 link 標籤
            link_elem = entry.find('link')
            url = link_elem.get('href', '') if link_elem else ""

        # Atom 格式的時間處理
        updated_elem = entry.find('updated')
        published_at = parse_date_string(updated_elem.get_text(strip=True)) if updated_elem else ""

        # Atom 格式的摘要處理
        summary_elem = entry.find('summary') or entry.find('content')
        if summary_elem:
            summary = BeautifulSoup(summary_elem.get_text(strip=True), 'html.parser').get_text(separator=' ', strip=True)[:400]
        else:
            summary = ""

        articles.append({
            "source": "The Verge",
            "title": title,
            "url": url,
            "published_at": published_at,
            "summary": summary
        })

    print(f"📥 The Verge RSS 抓取完成，取得 {len(articles)} 篇文章")
    return articles


def fetch_hackaday_articles(limit: int = 3) -> list[dict]:
    print("📡 正在從 Hackaday RSS 抓取最新新聞...")
    feed_url = "https://hackaday.com/feed/"
    response = requests.get(feed_url, headers=headers, timeout=10)

    try:
        soup = BeautifulSoup(response.content, 'xml')
    except FeatureNotFound:
        warnings.filterwarnings('ignore', category=XMLParsedAsHTMLWarning)
        soup = BeautifulSoup(response.content, 'html.parser')

    items = soup.find_all('item')

    articles = []
    for item in items[:limit]:
        title = item.title.get_text(strip=True) if item.title else ""
        # Hackaday RSS 使用 guid 作為 URL
        guid_elem = item.find('guid')
        url = guid_elem.get_text(strip=True) if guid_elem else ""

        # Hackaday RSS 使用 pubdate (全小寫)
        pub_date_elem = item.find('pubdate')
        published_at = parse_date_string(pub_date_elem.get_text(strip=True)) if pub_date_elem else ""

        # 獲取摘要
        description_elem = item.find('description')
        if description_elem:
            summary = BeautifulSoup(description_elem.get_text(strip=True), 'html.parser').get_text(separator=' ', strip=True)[:400]
        else:
            summary = ""

        articles.append({
            "source": "Hackaday",
            "title": title,
            "url": url,
            "published_at": published_at,
            "summary": summary
        })

    print(f"📥 Hackaday RSS 抓取完成，取得 {len(articles)} 篇文章")
    return articles


def fetch_venturebeat_articles(limit: int = 3) -> list[dict]:
    print("📡 正在從 VentureBeat RSS 抓取最新新聞...")
    feed_url = "https://venturebeat.com/feed/"
    response = requests.get(feed_url, headers=headers, timeout=10)

    try:
        soup = BeautifulSoup(response.content, 'xml')
    except FeatureNotFound:
        warnings.filterwarnings('ignore', category=XMLParsedAsHTMLWarning)
        soup = BeautifulSoup(response.content, 'html.parser')

    items = soup.find_all('item')

    articles = []
    for item in items[:limit]:
        title = item.title.get_text(strip=True) if item.title else ""
        # VentureBeat RSS 使用 guid 作為 URL
        guid_elem = item.find('guid')
        url = guid_elem.get_text(strip=True) if guid_elem else ""

        # VentureBeat RSS 使用 pubdate (全小寫)
        pub_date_elem = item.find('pubdate')
        published_at = parse_date_string(pub_date_elem.get_text(strip=True)) if pub_date_elem else ""

        # 獲取摘要
        description_elem = item.find('description')
        if description_elem:
            summary = BeautifulSoup(description_elem.get_text(strip=True), 'html.parser').get_text(separator=' ', strip=True)[:400]
        else:
            summary = ""

        articles.append({
            "source": "VentureBeat",
            "title": title,
            "url": url,
            "published_at": published_at,
            "summary": summary
        })

    print(f"📥 VentureBeat RSS 抓取完成，取得 {len(articles)} 篇文章")
    return articles


# 如果更新太近，僅更新時間戳而不重新抓取內容與呼叫 API
if OUTPUT_FILE.exists():
    try:
        existing_data = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
        prev_ts = existing_data.get("timestamp")
        if prev_ts:
            prev_time = datetime.fromisoformat(prev_ts)
            now_taipei = datetime.now(TZ)
            elapsed = (now_taipei - prev_time).total_seconds() / 60
            if elapsed < SCRAPE_MINUTES_THRESHOLD:
                existing_data["timestamp"] = now_taipei.isoformat()
                existing_data["date"] = now_taipei.strftime("%Y-%m-%d")
                OUTPUT_FILE.write_text(json.dumps(existing_data, indent=2, ensure_ascii=False), encoding="utf-8")
                print(f"⏱ 更新間隔小於 {SCRAPE_MINUTES_THRESHOLD} 分鐘，僅更新時間戳。")
                print(f"📁 已更新 {OUTPUT_FILE} 的時間，保留現有文章內容。")
                raise SystemExit(0)
    except SystemExit:
        raise
    except Exception as e:
        print(f"⚠️ 讀取先前數據失敗，將執行完整爬蟲：{e}")

sources = []
sources.extend(fetch_technews_articles(10))
sources.extend(fetch_theverge_articles(10))
sources.extend(fetch_hackaday_articles(10))
sources.extend(fetch_venturebeat_articles(10))
print(f"📥 抓取完成！共取得 {len(sources)} 篇新聞。")

raw_news_data = ""
for idx, article in enumerate(sources, 1):
    raw_news_data += (
        f"新聞 {idx}:\n"
        f"source: {article['source']}\n"
        f"title: {article['title']}\n"
        f"url: {article['url']}\n"
        f"published_at: {article['published_at']}\n"
        f"summary: {article['summary']}\n"
        f"---\n"
    )

print("🧠 正在呼叫 Gemini 進行深度分析...\n")

# 檢查是否跳過 AI 調用（本地測試用）
SKIP_AI = os.getenv("SKIP_AI", "false").lower() == "true"

if SKIP_AI:
    print("⚡ SKIP_AI 模式：跳過 AI 調用，直接輸出基本資訊")
    structured_data = []
    for article in sources:
        structured_data.append({
            "title": article["title"],
            "url": article["url"],
            "source": article["source"],
            "published_at": article["published_at"],
            "summary": article["summary"],
            "keywords": [],
            "category": "Other",
            "rd_relevance": "Low",
            "impact": "Low",
            "why_it_matters": "",
            "action_suggestion": ""
        })
else:
    # 3. 呼叫 AI (Prompt 加上要求參考內文)
    prompt = f"""
    你是一位資深的硬體與嵌入式系統研發總監。請閱讀以下來自多個科技來源的最新新聞資料，內容包含標題、來源、時間和摘要。
    請從「硬體研發、晶片設計、供應鏈變化、AI 終端應用」的角度，深入評估這些新聞對我們團隊的價值。

    請絕對遵守以下規則：
    1. 只輸出純 JSON 格式的陣列（Array），不要有 Markdown 標記，不要多餘文字。
    2. JSON 陣列中的每個物件必須包含以下 key：
       - "title": 新聞標題
       - "url": 新聞連結
       - "source": 資料來源
       - "published_at": 發布時間（盡量輸出 ISO 8601）
       - "summary": 根據原始摘要整理出的 1-2 句概要
       - "keywords": 3~5 個關鍵詞
       - "category": 類別 (AI/Hardware/Chip/Edge/Software/Other)
       - "rd_relevance": 研發關聯度 (High/Medium/Low)
       - "impact": 對我們團隊的整體影響程度 (High/Medium/Low)
       - "why_it_matters": 這則新聞對研發團隊最重要的意義
       - "action_suggestion": 具體行動建議 (例如：需追蹤技術路線、評估供應鏈風險)

    以下是今天的新聞資料：
    {raw_news_data}
    """

    try:
        ai_response = model.generate_content(prompt)
        clean_text = ai_response.text.strip().removeprefix("```json").removesuffix("```").strip()
        structured_data = json.loads(clean_text)
    except Exception as e:
        print(f"❌ AI 調用失敗：{e}")
        # 如果 AI 失敗，fallback 到基本資訊
        structured_data = []
        for article in sources:
            structured_data.append({
                "title": article["title"],
                "url": article["url"],
                "source": article["source"],
                "published_at": article["published_at"],
                "summary": article["summary"],
                "keywords": [],
                "category": "Other",
                "rd_relevance": "Low",
                "impact": "Low",
                "why_it_matters": "",
                "action_suggestion": ""
            })

print("✅ 數據處理完成！結果如下：")
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
