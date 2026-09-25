"""API tests. Run: python -m pytest tests -q"""
from __future__ import annotations

import numpy as np
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.data_loader import CITIES
from src.model_store import forecast_air

FULL_PROFILE = {"age": 67, "gender": "M", "condition": "COPD", "smoker": False, "bmi": 27.5,
                "exercise_hours": 1.0, "outdoor_hours": 3.0, "mask_usage": "No",
                "occupation": "Retired", "area_type": "Industrial", "family_history": True}
MINIMAL_PROFILE = {"age": 30, "gender": "F", "condition": "No Condition", "smoker": False,
                   "occupation": "Indoor Worker", "area_type": "Residential", "mask_usage": "Sometimes",
                   "outdoor_hours": 2.0}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:  # runs the lifespan, i.e. loads every model once
        yield c


def test_health(client):
    r = client.get("/api/health").json()
    assert r["status"] == "ok"
    assert r["cities"] == 6 and r["forecasters"] == 18
    assert len(r["health_models"]) == 4


def test_cities(client):
    cities = client.get("/api/cities").json()
    assert sorted(c["city"] for c in cities) == sorted(CITIES)
    assert all(set(c["targets"]) == {"AQI", "PM2.5", "NO2"} for c in cities)


@pytest.mark.parametrize("horizon", [7, 30])
def test_forecast_matches_saved_models(client, horizon):
    r = client.get(f"/api/forecast/Delhi?horizon={horizon}")
    assert r.status_code == 200
    body = r.json()
    assert len(body["days"]) == horizon
    expected = forecast_air("Delhi", horizon)
    got = np.array([d["aqi"] for d in body["days"]])
    assert np.allclose(got, expected["aqi"].round(1), atol=0.051)
    assert body["days"][0]["date"] == "2020-07-02"
    assert {"AQI", "PM2.5", "NO2"} <= set(body["models"])


def test_forecast_city_is_case_insensitive(client):
    assert client.get("/api/forecast/delhi").json()["city"] == "Delhi"


@pytest.mark.parametrize("horizon", [0, 31, -1])
def test_forecast_rejects_bad_horizon(client, horizon):
    assert client.get(f"/api/forecast/Delhi?horizon={horizon}").status_code == 422


def test_forecast_unknown_city(client):
    r = client.get("/api/forecast/Atlantis")
    assert r.status_code == 404 and "Available" in r.json()["detail"]


def test_risk_full_profile(client):
    r = client.post("/api/risk/predict", json={"city": "Delhi", "horizon": 7, "profile": FULL_PROFILE})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["feature_set"] == "aqi_pm25_no2"
    assert body["imputed_fields"] == []
    assert len(body["days"]) == 7
    for d in body["days"]:
        assert abs(sum(d["probabilities"].values()) - 1) < 0.01
        assert d["risk_level"] in ("Low", "Moderate", "High", "Severe")
        assert d["borderline"] == (d["risk_level"] != d["score_level"])
    s = body["summary"]
    assert s["show_hospitals"] == (s["highest_alert_level"] in ("High", "Severe"))
    assert sum(s["days_by_level"].values()) == 7
    assert "not a medical diagnosis" in body["disclaimer"]


def test_risk_minimal_profile_reports_imputed_fields(client):
    body = client.post("/api/risk/predict", json={"city": "Chennai", "profile": MINIMAL_PROFILE}).json()
    assert set(body["imputed_fields"]) == {"bmi", "exercise_hours", "family_history"}
    assert any("typical values" in w for w in body["warnings"])


def test_risk_rises_with_vulnerability(client):
    healthy = client.post("/api/risk/predict", json={"city": "Delhi", "profile": {
        **FULL_PROFILE, "age": 25, "condition": "No Condition", "family_history": False,
        "mask_usage": "Yes", "area_type": "Residential", "occupation": "Indoor Worker"}}).json()
    copd = client.post("/api/risk/predict", json={"city": "Delhi", "profile": FULL_PROFILE}).json()
    assert np.mean([d["risk_score"] for d in copd["days"]]) > np.mean([d["risk_score"] for d in healthy["days"]])


def test_risk_warns_outside_training_range(client):
    body = client.post("/api/risk/predict", json={"city": "Delhi", "profile": {**FULL_PROFILE, "age": 105}}).json()
    assert any("outside the range" in w for w in body["warnings"])


@pytest.mark.parametrize("bad", [
    {"mask_usage": "Always"}, {"age": 0}, {"gender": "X"}, {"bmi": 5}, {"unexpected": 1},
])
def test_risk_rejects_invalid_profile(client, bad):
    r = client.post("/api/risk/predict", json={"city": "Delhi", "profile": {**FULL_PROFILE, **bad}})
    assert r.status_code == 422


def test_risk_requires_core_fields(client):
    r = client.post("/api/risk/predict", json={"city": "Delhi", "profile": {"age": 40, "gender": "M"}})
    assert r.status_code == 422


@pytest.mark.parametrize("field", ["occupation", "area_type", "mask_usage", "outdoor_hours"])
def test_risk_requires_exposure_fields(client, field):
    profile = {k: v for k, v in FULL_PROFILE.items() if k != field}
    r = client.post("/api/risk/predict", json={"city": "Delhi", "profile": profile})
    assert r.status_code == 422 and field in r.text


def test_profile_schema(client):
    s = client.get("/api/profile/schema").json()
    assert s["required"] == ["age", "gender", "condition", "smoker",
                             "occupation", "area_type", "mask_usage", "outdoor_hours"]
    assert "COPD" in s["choices"]["condition"]
    assert set(s["defaults_when_missing"]) == {"bmi", "exercise_hours", "family_history"}
    assert not set(s["required"]) & set(s["defaults_when_missing"])


@pytest.mark.parametrize("target", ["AQI", "PM2.5", "NO2"])
def test_forecast_leaderboard(client, target):
    b = client.get("/api/leaderboard/forecast", params={"target": target}).json()
    assert len(b["cities"]) == 6
    for c in b["cities"].values():
        assert c["ranking"] and c["deployed_model"]


def test_deployed_model_matches_leaderboard(client):
    cities = {c["city"]: c["targets"] for c in client.get("/api/cities").json()}
    for target in ("AQI", "PM2.5", "NO2"):
        board = client.get("/api/leaderboard/forecast", params={"target": target}).json()
        for city, c in board["cities"].items():
            assert cities[city][target] == c["deployed_model"], (target, city)


def test_health_leaderboard(client):
    b = client.get("/api/leaderboard/health").json()
    assert b["tasks"]["classification"]["selected"]["aqi_pm25_no2"] == "MLP"
    only = client.get("/api/leaderboard/health?task=regression").json()
    assert list(only["tasks"]) == ["regression"]
