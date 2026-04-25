# 🔧 設置指南 | Setup Guide

## 前置要求

- Python 3.9+
- Git & GitHub (含 GitHub Pages 啟用)
- Google Gemini API Key

---

## 📋 本地設置

### 1️⃣ 安裝依賴

```bash
pip install requests google-generativeai
```

### 2️⃣ 設定 API Key

在終端機執行爬蟲前，設定環境變數：

**Mac/Linux (Bash/Zsh):**
```bash
export GEMINI_API_KEY="your-api-key-here"
```

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your-api-key-here"
```

或在 `.env` 檔案中設定（建議加入 `.gitignore`）：
```
GEMINI_API_KEY=your-api-key-here
```

### 3️⃣ 本地測試爬蟲

```bash
python daily_scraper.py
```

#### 🔧 本地測試模式 (跳過 AI 調用)

開發時不想消耗 API 額度，可以設定環境變數跳過 AI 分析：

**Mac/Linux (Bash/Zsh):**
```bash
export SKIP_AI=true
python daily_scraper.py
# 或單行執行：SKIP_AI=true python daily_scraper.py
```

**Windows (PowerShell):**
```powershell
$env:SKIP_AI="true"
python daily_scraper.py
```

#### 🤖 使用 Antigravity 進行自動測試

如果你正在使用 Antigravity AI 助理，你可以直接用自然語言請它幫你測試。Antigravity 會自動處理 Windows PowerShell 等不同環境的指令語法差異（像是處理麻煩的 `$env:VAR`）：

- **一般執行：** 請輸入「幫我執行測試腳本」或「跑 daily_scraper.py」。
- **無 AI 模式：** 請輸入「幫我用 SKIP_AI 模式執行爬蟲」。
- **帶入密鑰測試：** 請輸入「先幫我設定好 GEMINI_API_KEY 再跑測試」。

Antigravity 會自動在背景打好正確的指令並執行。

✅ SKIP_AI 模式會：
- 跳過 Gemini AI 調用
- 直接輸出基本新聞資訊（標題、URL、來源、摘要）
- 其他欄位（關鍵詞、類別、影響度等）設為預設值
- **仍然保存 JSON 文件**供 HTML 頁面測試使用
- 適合快速測試爬蟲功能和網頁顯示

✅ 正常模式成功後會看到：
- 終端機輸出 JSON 格式結果
- `docs/daily_news.json` 被生成

### 4️⃣ 本地查看 GitHub Pages

**Mac/Linux (Bash/Zsh):**
```bash
cd docs && python -m http.server 8080
```

**Windows (PowerShell):**
```powershell
cd docs; python -m http.server 8080
```

然後訪問 `http://localhost:8080` 查看頁面

---

## 🚀 GitHub 自動化設置

### 1️⃣ 啟用 GitHub Pages

1. 進入 Repository Settings → Pages
2. 選擇 "Source" 為 `main` 分支
3. 選擇資料夾為 `/docs`

### 2️⃣ 設定 GitHub Secret

1. Repository Settings → Secrets and variables → Actions
2. 新增 Secret:
   - 名稱: `GEMINI_API_KEY`
   - 值: 妳的 API Key

### 3️⃣ 驗證 Workflow

1. 進入 Actions 分頁
2. 選擇 "📡 Daily Tech News Scraper"
3. 點擊 "Run workflow" → "Run workflow" 手動觸發

✅ 成功後：
- CI/CD 會執行 Python 腳本
- 更新 `docs/daily_news.json`
- GitHub Pages 自動更新展示

---

## 📅 排程設置

Workflow 預設：
- ⏰ 每天 **UTC 8:00** (台灣時間下午 4 點) 執行
- 🔄 可在 `.github/workflows/daily_scrape.yml` 修改 cron 時間

修改範例（每天 00:00 UTC）：
```yaml
schedule:
  - cron: '0 0 * * *'
```

---

## 📊 GitHub Pages 訪問

設置完成後，妳的頁面會在：
```
https://你的-github-username.github.io/daily-tech-tracker
```

或如果開啟了自訂域名，使用妳的自訂域名。

---

## 🐛 常見問題

### Q1: 執行爬蟲後沒有生成 `daily_news.json`?
**A:** 檢查 `GEMINI_API_KEY` 是否正確設定

### Q2: GitHub Actions 執行失敗?
**A:** 
1. 檢查 Secrets 中的 `GEMINI_API_KEY` 是否正確
2. 檢查 `.github/workflows/daily_scrape.yml` 語法
3. 查看 Actions 日誌詳細錯誤訊息

### Q3: GitHub Pages 沒有更新?
**A:**
1. 確認 Pages 設置中資料夾選擇為 `/docs`
2. 確認 `docs/daily_news.json` 已被推送到 main 分支
3. 若超過 1 分鐘仍未更新，手動重新觸發 Workflow

---

## 🎯 下一步改進

- [ ] 添加數據查詢 API
- [ ] 支持多個新聞源（Reddit, Product Hunt 等）
- [ ] 建立數據庫存儲歷史記錄
- [ ] 添加郵件通知功能
- [ ] Web Dashboard 查看統計分析

---

有問題？歡迎提 Issue 或 PR！🙌
