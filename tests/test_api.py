from fastapi.testclient import TestClient

from zova.api import app
from zova.fixtures import load_demo


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_validates_and_echoes_without_logging(capsys):
    profile, activities = load_demo()
    payload = {
        "profile": profile.model_dump(mode="json"),
        "activities": [activity.model_dump(mode="json") for activity in activities],
    }
    with TestClient(app) as client:
        response = client.post("/upload", json=payload)
    assert response.status_code == 200
    assert response.json() == {
        "message": "Preferences validated successfully; not stored",
        **payload,
    }
    assert capsys.readouterr().out == ""


def test_upload_rejects_invalid_profile():
    profile, _ = load_demo()
    payload = {"profile": profile.model_dump(mode="json"), "activities": []}
    payload["profile"]["budget"] = "-1"
    with TestClient(app) as client:
        response = client.post("/upload", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "profile", "budget"]


def test_upload_rejects_missing_body():
    with TestClient(app) as client:
        response = client.post("/upload", json={})
    assert response.status_code == 422
