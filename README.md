# 小雞打工 App（Chick Gig App）

以「快速找到打工」為核心，為高中剛畢業生整理免經驗、暑期短期、彈性班與清楚薪資資訊。首頁免登入即可搜尋、快篩和查看職缺，應徵只需暱稱與可上班時間。

## 本機啟動

需要 Python 3.12。Windows PowerShell：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

瀏覽 <http://127.0.0.1:5000>。

## API

| 方法 | 路徑 | 用途 |
|---|---|---|
| GET | `/api/health` | 健康檢查 |
| GET | `/api/jobs` | 搜尋、分類、免經驗、時薪、快篩與排序；支援 `q`/`keyword`、`category`、`no_experience=true`、`min_pay`、`quick_tag=high_pay\|short_term\|flexible`、`sort=newest\|pay_desc` |
| GET | `/api/jobs/<id>` | 職缺完整資料 |
| POST | `/api/jobs` | 新增職缺；時薪低於 NT$190 會拒絕 |
| PATCH | `/api/jobs/<id>/apply` | 快速應徵，JSON 可傳 `applicant`、`available_note` |
| PATCH | `/api/jobs/<id>/complete` | 完成職缺並計算預估收入 |
| DELETE | `/api/jobs/<id>` | 刪除職缺 |
| GET | `/api/quick-tip` | 求職提醒；外部 API 失敗時使用備援文字 |
| POST | `/api/reset` | 重置示範職缺與應徵資料 |

職缺與應徵資料目前保存在 Python 記憶體中，重啟或 Vercel Serverless 冷啟動可能重置，且不同執行個體不共享資料。正式服務請將資料改存 PostgreSQL、Supabase 等外部資料庫。

## 測試

```powershell
python -m pip install -r requirements.txt pytest
python -m pytest -q
```

## GitHub 與 Vercel 部署

1. 在 GitHub 建立空白 Repository，將 Repository HTTPS 或 SSH URL 加為 `origin`，再推送 `main`：

   ```powershell
   git remote add origin <你的 Repository URL>
   git push -u origin main
   ```

2. 在 Vercel 選擇 **Add New → Project**，匯入該 GitHub Repository。Vercel 會使用根目錄 `vercel.json` 的 Python Runtime 設定。
3. 按 **Deploy**，完成後用 Vercel 提供的網址檢查首頁與 `/api/health`。

本專案目前沒有需要設定的秘密值。未來若有 API Key，請放在 Vercel Project Settings → Environment Variables，不要提交 `.env`。
