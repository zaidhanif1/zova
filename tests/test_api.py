from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from zova.api import app
from zova.fixtures import load_demo
from zova.models import Itinerary
from zova.planner import validate_plan


def demo_payload():
    profile, activities = load_demo()
    return {
        "profile": profile.model_dump(mode="json"),
        "activities": [activity.model_dump(mode="json") for activity in activities],
    }


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_itinerary_generates_demo_without_logging(capsys):
    payload = demo_payload()
    with TestClient(app) as client:
        response = client.post("/itinerary", json=payload)
    assert response.status_code == 200
    result = response.json()
    assert result["profile"] == payload["profile"]
    assert result["total_cost"] == "55.00"
    assert [a["id"] for a in result["activities"]] == [
        "architecture-walk",
        "thrift-session",
        "food-stop",
        "gallery",
    ]
    assert all(a["source"] == "synthetic fixture" for a in result["activities"])
    plan = Itinerary.model_validate({"activities": result["activities"]})
    profile, _ = load_demo()
    validate_plan(profile, plan)
    assert plan.total_cost <= profile.budget
    assert capsys.readouterr().out == ""


def test_itinerary_preserves_fractional_costs():
    payload = demo_payload()
    payload["activities"] = payload["activities"][:2]
    payload["activities"][0]["cost"] = "20.25"
    payload["activities"][1]["cost"] = "10.10"
    with TestClient(app) as client:
        response = client.post("/itinerary", json=payload)
    assert response.status_code == 200
    assert response.json()["total_cost"] == "30.35"


@pytest.mark.parametrize("empty_candidates", [True, False])
def test_itinerary_empty_or_unaffordable_candidates(empty_candidates):
    payload = demo_payload()
    if empty_candidates:
        payload["activities"] = []
    else:
        payload["profile"]["budget"] = "0.00"
    with TestClient(app) as client:
        response = client.post("/itinerary", json=payload)
    assert response.status_code == 200
    assert response.json()["activities"] == []
    assert response.json()["total_cost"] == "0.00"


def test_itinerary_reduced_budget():
    payload = demo_payload()
    payload["profile"]["budget"] = "30.00"
    with TestClient(app) as client:
        response = client.post("/itinerary", json=payload)
    assert response.status_code == 200
    assert Decimal(response.json()["total_cost"]) <= Decimal("30.00")
    assert [a["id"] for a in response.json()["activities"]] == [
        "architecture-walk",
        "thrift-session",
    ]


def test_itinerary_rejects_invalid_profile():
    payload = demo_payload()
    payload["profile"]["budget"] = "-1"
    with TestClient(app) as client:
        response = client.post("/itinerary", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "profile", "budget"]


def test_itinerary_rejects_invalid_activity():
    payload = demo_payload()
    payload["activities"][0]["schedule"]["start"] = "2026-10-24T09:00:00"
    with TestClient(app) as client:
        response = client.post("/itinerary", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "activities", 0, "schedule", "start"]


def test_itinerary_rejects_missing_body():
    with TestClient(app) as client:
        response = client.post("/itinerary", json={})
    assert response.status_code == 422
