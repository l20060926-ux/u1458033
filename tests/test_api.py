from copy import deepcopy

import app as app_module


def setup_function():
    app_module.jobs = deepcopy(app_module.SEED_JOBS)
    app_module.applications.clear()


def test_health_and_search_filters():
    client = app_module.app.test_client()
    assert client.get("/api/health").json["status"] == "ok"
    data = client.get("/api/jobs?q=咖啡店&no_experience=true").json
    assert data["count"] == 1
    assert data["jobs"][0]["company"] == "日光咖啡"
    assert client.get("/api/jobs?quick_tag=high_pay&sort=pay_desc").json["jobs"][0]["pay_per_hour"] == 250
    assert client.get("/api/jobs?quick_tag=short_term").json["count"] >= 1


def test_create_rejects_pay_below_floor():
    client = app_module.app.test_client()
    payload = dict(title="新工作", company="店家", location="台北", category="餐飲服務", pay_per_hour=189, hours=8, schedule="週末", no_experience=True)
    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 400
    assert "低於" in response.json["error"]


def test_apply_complete_and_not_found():
    client = app_module.app.test_client()
    applied = client.patch("/api/jobs/1/apply", json={"applicant": "小明", "available_note": "下週可開始"})
    assert applied.status_code == 200 and applied.json["status"] == "applied"
    completed = client.patch("/api/jobs/1/complete")
    assert completed.json["total_income"] == 9600
    assert client.get("/api/jobs/999").status_code == 404
    assert client.patch("/api/jobs/999/apply").status_code == 404


def test_quick_tip_external_api_fallback(monkeypatch):
    def fail(*args, **kwargs):
        raise app_module.requests.Timeout("offline")
    monkeypatch.setattr(app_module.requests, "get", fail)
    response = app_module.app.test_client().get("/api/quick-tip")
    assert response.status_code == 200
    assert response.json["source"] == "fallback"
    assert response.json["tip"]
