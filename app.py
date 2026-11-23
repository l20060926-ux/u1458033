"""小雞打工 App：以記憶體資料展示無狀態部署模式。"""
from copy import deepcopy
from datetime import datetime, timezone

import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# 示範資料存在記憶體；Vercel 函式重啟後會重置。正式使用請改接外部資料庫。
SEED_JOBS = [
    dict(id=1, title="暑期咖啡店外場夥伴", company="日光咖啡", location="台北市大安區", category="餐飲服務", pay_per_hour=200, hours=48, schedule="平日 10:00–16:00，可排 3 天", no_experience=True, tags=["暑期短期", "免經驗", "彈性"], description="協助點餐、送餐與整理桌面，提供完整新人訓練。", created_at="2026-11-20T09:00:00+00:00", status="open"),
    dict(id=2, title="週末市集活動工讀生", company="好日子市集", location="新北市板橋區", category="活動展場", pay_per_hour=220, hours=16, schedule="週六日 09:00–17:00", no_experience=True, tags=["週末", "高時薪 200+", "免經驗"], description="協助攤位報到、動線引導與簡易場佈。", created_at="2026-11-22T09:00:00+00:00", status="open"),
    dict(id=3, title="暑期營隊活動助理", company="小樹學習營", location="台中市西區", category="暑期短期", pay_per_hour=210, hours=40, schedule="7 月起，週一至週五 08:30–16:30", no_experience=True, tags=["暑期短期", "免經驗"], description="陪伴國小學員參與活動，需親切、有耐心。", created_at="2026-11-21T09:00:00+00:00", status="open"),
    dict(id=4, title="書店上架與門市支援", company="拾頁書店", location="台南市中西區", category="行政協助", pay_per_hour=195, hours=24, schedule="每週排班 3 天，13:00–19:00", no_experience=True, tags=["彈性", "免經驗"], description="整理新書、協助顧客找書與維持門市整潔。", created_at="2026-11-19T09:00:00+00:00", status="open"),
    dict(id=5, title="國中數學伴讀夥伴", company="暖暖課後班", location="高雄市左營區", category="家教伴讀", pay_per_hour=250, hours=12, schedule="平日 17:00–19:00，可選 2–3 天", no_experience=False, tags=["高時薪 200+", "彈性"], description="陪伴國中生複習數學，需能清楚說明基礎觀念。", created_at="2026-11-18T09:00:00+00:00", status="open"),
    dict(id=6, title="早午餐店內場新手", company="好好早午餐", location="桃園市中壢區", category="餐飲服務", pay_per_hour=200, hours=32, schedule="週末或平日早班 07:00–13:00", no_experience=True, tags=["週末", "免經驗", "彈性"], description="協助備料與簡單出餐，無經驗可，供員工餐。", created_at="2026-11-17T09:00:00+00:00", status="open"),
]
jobs = deepcopy(SEED_JOBS)
applications = []
QUICK_TIP = "面試前確認時薪、排班與工作內容；先告知可信任的家人工作地點，遇到要求先繳費或交出證件正本請提高警覺。"
CATEGORIES = ["全部", "暑期短期", "餐飲服務", "活動展場", "行政協助", "家教伴讀"]


def error(message, status=400):
    return jsonify({"error": message}), status


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "service": "chick-gig"})


@app.get("/api/jobs")
def list_jobs():
    result = list(jobs)
    args = request.args
    q = (args.get("q") or args.get("keyword") or "").strip().casefold()
    if q:
        result = [j for j in result if q in " ".join([j["title"], j["company"], j["location"], j["schedule"], j["category"]]).casefold()]
    category = args.get("category", "全部")
    if category and category != "全部":
        result = [j for j in result if j["category"] == category or (category == "暑期短期" and "暑期短期" in j["tags"])]
    if args.get("no_experience", "").lower() == "true":
        result = [j for j in result if j["no_experience"]]
    try:
        min_pay = int(args.get("min_pay", 0))
        if min_pay < 0:
            return error("最低時薪不可小於 0")
    except ValueError:
        return error("min_pay 必須是數字")
    result = [j for j in result if j["pay_per_hour"] >= min_pay]
    tag = args.get("quick_tag", "")
    if tag == "high_pay":
        result = [j for j in result if j["pay_per_hour"] >= 200]
    elif tag == "short_term":
        result = [j for j in result if "暑期短期" in j["tags"]]
    elif tag == "flexible":
        result = [j for j in result if "彈性" in j["tags"] or "週末" in j["tags"]]
    elif tag == "weekend":
        result = [j for j in result if "週末" in j["tags"]]
    elif tag:
        return error("不支援的 quick_tag")
    result.sort(key=lambda j: (j["created_at"], j["id"]), reverse=True)
    if args.get("sort") == "pay_desc":
        result.sort(key=lambda j: (j["pay_per_hour"], j["created_at"]), reverse=True)
    elif args.get("sort", "newest") != "newest":
        return error("sort 僅支援 newest 或 pay_desc")
    return jsonify({"jobs": result, "count": len(result), "categories": CATEGORIES,
                    "popular_searches": ["暑期短期", "週末", "咖啡店"],
                    "quick_tags": ["免經驗", "暑期短期", "高時薪 200+", "週末/彈性"]})


@app.get("/api/jobs/<int:job_id>")
def get_job(job_id):
    job = next((j for j in jobs if j["id"] == job_id), None)
    return (jsonify(job), 200) if job else error("找不到此職缺", 404)


@app.post("/api/jobs")
def create_job():
    data = request.get_json(silent=True) or {}
    required = ["title", "company", "location", "category", "pay_per_hour", "hours", "schedule", "no_experience"]
    missing = [key for key in required if key not in data or data[key] in (None, "")]
    if missing:
        return error("缺少必填欄位：" + ", ".join(missing))
    try:
        pay, hours = int(data["pay_per_hour"]), float(data["hours"])
    except (TypeError, ValueError):
        return error("時薪與工時必須是有效數字")
    if pay < 190:
        return error("時薪不可低於示範基本工資門檻 NT$190")
    if pay > 10000 or hours <= 0 or hours > 1000:
        return error("時薪或工時超出合理範圍")
    if not isinstance(data["no_experience"], bool):
        return error("no_experience 必須是布林值")
    job = {**{key: data[key] for key in required}, "id": max((j["id"] for j in jobs), default=0) + 1,
           "pay_per_hour": pay, "hours": hours, "tags": data.get("tags", []),
           "description": data.get("description", ""), "created_at": datetime.now(timezone.utc).isoformat(), "status": "open"}
    jobs.append(job)
    return jsonify(job), 201


@app.patch("/api/jobs/<int:job_id>/apply")
def apply_job(job_id):
    job = next((j for j in jobs if j["id"] == job_id), None)
    if not job:
        return error("找不到此職缺", 404)
    if job["status"] != "open":
        return error("此職缺目前無法應徵", 409)
    data = request.get_json(silent=True) or {}
    applicant = str(data.get("applicant", "同學")).strip()
    note = str(data.get("available_note", "近期可開始，時間可再討論")).strip()
    if not applicant or len(applicant) > 30:
        return error("暱稱需為 1 至 30 個字")
    if len(note) > 200:
        return error("備註最多 200 字")
    job.update(status="applied", applicant=applicant, available_note=note)
    applications.append({"job_id": job_id, "applicant": applicant, "available_note": note})
    return jsonify(job)


@app.patch("/api/jobs/<int:job_id>/complete")
def complete_job(job_id):
    job = next((j for j in jobs if j["id"] == job_id), None)
    if not job:
        return error("找不到此職缺", 404)
    job.update(status="completed", total_income=round(job["pay_per_hour"] * job["hours"], 2))
    return jsonify(job)


@app.delete("/api/jobs/<int:job_id>")
def delete_job(job_id):
    job = next((j for j in jobs if j["id"] == job_id), None)
    if not job:
        return error("找不到此職缺", 404)
    jobs.remove(job)
    return jsonify({"deleted": True, "id": job_id})


@app.get("/api/quick-tip")
def quick_tip():
    try:
        response = requests.get("https://api.adviceslip.com/advice", timeout=5)
        response.raise_for_status()
        external = response.json().get("slip", {}).get("advice")
        if not isinstance(external, str) or not external.strip():
            raise ValueError("外部 API 未提供建議")
        return jsonify({"tip": QUICK_TIP, "extra_tip": external, "source": "external"})
    except (requests.RequestException, ValueError, TypeError, KeyError):
        return jsonify({"tip": QUICK_TIP, "extra_tip": "面試時確認薪資算法與休息時間，錄取後保留班表與出勤紀錄。", "source": "fallback"})


@app.post("/api/reset")
def reset_demo_data():
    global jobs
    jobs = deepcopy(SEED_JOBS)
    applications.clear()
    return jsonify({"status": "reset", "count": len(jobs)})


if __name__ == "__main__":
    app.run(debug=True)
