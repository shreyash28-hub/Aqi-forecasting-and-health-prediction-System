"""Tests for the signed-in endpoints (/api/me), against an in-memory fake of Supabase.

The fake mimics Supabase Auth (/auth/v1/user) and the PostgREST calls the backend
makes, including Row Level Security: every row is filtered by the caller's user id,
so the tests also check that one user can't see or change another user's data.
Run: python -m pytest tests -q
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import httpx
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.supabase_client import SupabaseClient

ALICE, BOB = str(uuid.uuid4()), str(uuid.uuid4())
TOKENS = {"token-alice": ALICE, "token-bob": BOB}
PROFILE = {"age": 67, "gender": "M", "condition": "COPD", "smoker": False, "occupation": "Retired",
           "area_type": "Industrial", "mask_usage": "No", "outdoor_hours": 3.0, "bmi": 27.5,
           "exercise_hours": 1.0, "family_history": True}


class FakeSupabase:
    def __init__(self):
        self.reset()

    def reset(self):
        self.tables = {"profiles": [], "saved_forecasts": [], "risk_predictions": []}
        self.fail_risk_insert = False
        self.auth_calls = 0

    @staticmethod
    def _rls_denied():
        return httpx.Response(403, json={"code": "42501", "message": "new row violates row-level security policy"})

    def handler(self, request: httpx.Request) -> httpx.Response:
        auth = request.headers.get("Authorization", "")
        token = auth.removeprefix("Bearer ").strip()
        uid = TOKENS.get(token)
        path, params = request.url.path, request.url.params

        if path == "/auth/v1/user":
            self.auth_calls += 1
            return httpx.Response(200, json={"id": uid, "email": f"{token}@example.com"}) if uid \
                else httpx.Response(401, json={"message": "invalid JWT"})
        if uid is None:
            return httpx.Response(401, json={"message": "JWT expired"})

        table = path.removeprefix("/rest/v1/")
        rows = self.tables[table]
        own = [r for r in rows if r["user_id"] == uid]                       # RLS: owner only
        for key, value in params.items():
            if value.startswith("eq."):
                own = [r for r in own if str(r.get(key)) == value[3:]]

        if request.method == "GET":
            out = [dict(r) for r in own]
            if table == "saved_forecasts":
                for r in out:
                    r["risk_predictions"] = [p for p in self.tables["risk_predictions"]
                                             if p["forecast_id"] == r["id"] and p["user_id"] == uid]
                out.sort(key=lambda r: r["generated_at"], reverse=True)
            if "limit" in params:
                out = out[: int(params["limit"])]
            return httpx.Response(200, json=out)

        if request.method == "DELETE":
            ids = {r["id"] for r in own}
            self.tables[table] = [r for r in rows if r.get("id") not in ids]
            if table == "saved_forecasts":   # ON DELETE CASCADE
                self.tables["risk_predictions"] = [p for p in self.tables["risk_predictions"] if p["forecast_id"] not in ids]
            return httpx.Response(200, json=own)

        body = json.loads(request.content)
        new = body if isinstance(body, list) else [body]
        now = datetime.now(timezone.utc).isoformat()
        if any(r.get("user_id") != uid for r in new):
            return self._rls_denied()
        if table == "profiles":                                              # upsert on user_id
            self.tables["profiles"] = [r for r in rows if r["user_id"] != uid]
            row = {**new[0], "updated_at": now}
            self.tables["profiles"].append(row)
            return httpx.Response(201, json=[row])
        if table == "risk_predictions":
            if self.fail_risk_insert:
                return httpx.Response(400, json={"message": "simulated failure"})
            mine = {f["id"] for f in self.tables["saved_forecasts"] if f["user_id"] == uid}
            if any(r["forecast_id"] not in mine for r in new):
                return self._rls_denied()
        out = [{"id": str(uuid.uuid4()), "generated_at": now, **r} for r in new]
        rows.extend(out)
        return httpx.Response(201, json=out)


FAKE = FakeSupabase()


@pytest.fixture(scope="module")
def client():
    app.state.supabase = SupabaseClient("https://fake.supabase.co", "anon-key",
                                        transport=httpx.MockTransport(FAKE.handler))
    with TestClient(app) as c:
        yield c
    del app.state.supabase


@pytest.fixture(autouse=True)
def fresh_store(client):
    FAKE.reset()
    app.state.supabase._users.clear()   # token cache, so each test starts signed out


def auth(token="token-alice"):
    return {"Authorization": f"Bearer {token}"}


def save_profile(client, token="token-alice", **extra):
    return client.put("/api/me/profile", json={**PROFILE, "city": "delhi", **extra}, headers=auth(token))


def test_requires_sign_in(client):
    assert client.get("/api/me/profile").status_code == 401
    assert client.get("/api/me/profile", headers=auth("bad-token")).status_code == 401
    assert client.post("/api/me/risk", json={}).status_code == 401


def test_profile_roundtrip(client):
    assert client.get("/api/me/profile", headers=auth()).status_code == 404
    r = save_profile(client)
    assert r.status_code == 200, r.text
    assert r.json()["city"] == "Delhi"                      # canonical city name stored
    got = client.get("/api/me/profile", headers=auth()).json()
    assert got["condition"] == "COPD" and got["outdoor_hours"] == 3.0 and got["updated_at"]
    # Saving again replaces, it doesn't duplicate.
    save_profile(client, age=68)
    assert client.get("/api/me/profile", headers=auth()).json()["age"] == 68
    assert len(FAKE.tables["profiles"]) == 1


def test_profile_validation(client):
    bad = {k: v for k, v in PROFILE.items() if k != "outdoor_hours"}
    assert client.put("/api/me/profile", json=bad, headers=auth()).status_code == 422
    assert save_profile(client, city="Atlantis").status_code == 422
    assert save_profile(client, mask_usage="Always").status_code == 422


def test_prediction_needs_profile(client):
    assert client.post("/api/me/risk", json={"horizon": 7}, headers=auth("token-bob")).status_code == 409


def test_prediction_saves_history_and_matches_public_endpoint(client):
    save_profile(client)
    r = client.post("/api/me/risk", json={"horizon": 7}, headers=auth())   # city from the profile
    assert r.status_code == 200, r.text
    run = r.json()
    assert run["city"] == "Delhi" and len(run["days"]) == 7 and run["forecast_id"]

    public = client.post("/api/risk/predict", json={"city": "Delhi", "horizon": 7, "profile": PROFILE}).json()
    assert [d["risk_level"] for d in run["days"]] == [d["risk_level"] for d in public["days"]]
    assert [d["risk_score"] for d in run["days"]] == [d["risk_score"] for d in public["days"]]

    assert len(FAKE.tables["saved_forecasts"]) == 1 and len(FAKE.tables["risk_predictions"]) == 7
    stored = FAKE.tables["risk_predictions"][0]
    assert stored["input_snapshot_json"]["profile"]["condition"] == "COPD"
    assert stored["model_used"]["feature_set"] == "aqi_pm25_no2"

    history = client.get("/api/me/history", headers=auth()).json()
    assert len(history) == 1 and history[0]["forecast_id"] == run["forecast_id"]
    assert history[0]["summary"] == run["summary"]

    detail = client.get(f"/api/me/history/{run['forecast_id']}", headers=auth()).json()
    assert [d["date"] for d in detail["days"]] == [d["date"] for d in run["days"]]
    assert [d["score_level"] for d in detail["days"]] == [d["score_level"] for d in run["days"]]
    assert detail["days"][0]["aqi"] == run["days"][0]["aqi"]
    assert detail["models"]["forecast"]["AQI"] == "SARIMA"


def test_city_override_and_30_day_run(client):
    save_profile(client)
    run = client.post("/api/me/risk", json={"city": "Chennai", "horizon": 30}, headers=auth()).json()
    assert run["city"] == "Chennai" and len(run["days"]) == 30


def test_users_cannot_see_each_others_history(client):
    save_profile(client)
    run_id = client.post("/api/me/risk", json={}, headers=auth()).json()["forecast_id"]
    assert client.get("/api/me/history", headers=auth("token-bob")).json() == []
    assert client.get(f"/api/me/history/{run_id}", headers=auth("token-bob")).status_code == 404
    assert client.delete(f"/api/me/history/{run_id}", headers=auth("token-bob")).status_code == 404
    assert client.get(f"/api/me/history/{run_id}", headers=auth()).status_code == 200


def test_delete_run(client):
    save_profile(client)
    run_id = client.post("/api/me/risk", json={}, headers=auth()).json()["forecast_id"]
    assert client.delete(f"/api/me/history/{run_id}", headers=auth()).status_code == 204
    assert client.get(f"/api/me/history/{run_id}", headers=auth()).status_code == 404
    assert FAKE.tables["risk_predictions"] == []            # days removed with the run


def test_failed_save_leaves_no_half_run(client):
    save_profile(client)
    FAKE.fail_risk_insert = True
    r = client.post("/api/me/risk", json={}, headers=auth())
    assert r.status_code >= 400
    assert FAKE.tables["saved_forecasts"] == []


def test_bad_history_id(client):
    assert client.get("/api/me/history/not-a-uuid", headers=auth()).status_code == 422


def test_token_lookups_are_cached(client):
    for _ in range(3):
        client.get("/api/me/profile", headers=auth())
    assert FAKE.auth_calls == 1


def test_accounts_disabled_returns_503(client):
    saved = app.state.supabase
    app.state.supabase = None
    try:
        assert client.get("/api/me/profile", headers=auth()).status_code == 503
        assert client.get("/api/health").json()["accounts_enabled"] is False
    finally:
        app.state.supabase = saved
