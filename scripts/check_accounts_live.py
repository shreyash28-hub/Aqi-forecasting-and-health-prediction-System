"""End-to-end check of the signed-in API against the real Supabase project.

Signs in as a TEST user (you type the email/password; nothing is stored), then:
save profile -> run a prediction -> read history -> read the run -> delete the run.
It runs the API in-process, so no server needs to be running.

Create the test user first: Supabase dashboard -> Authentication -> Users ->
Add user -> Create new user (tick "Auto Confirm User").

Usage::

    venv\\Scripts\\python scripts\\check_accounts_live.py

Note: this OVERWRITES the test user's saved profile. Use a dedicated test account.
"""
from __future__ import annotations

import getpass
import os
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient  # noqa: E402

from src.api.main import app  # noqa: E402  (also loads .env)

TEST_PROFILE = {"age": 45, "gender": "F", "condition": "Asthma", "smoker": False, "occupation": "Indoor Worker",
                "area_type": "Residential", "mask_usage": "Sometimes", "outdoor_hours": 2.0, "city": "Delhi"}


def step(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f": {detail}" if detail else ""))
    if not ok:
        sys.exit(1)


def main():
    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        sys.exit("SUPABASE_URL / SUPABASE_ANON_KEY missing from .env")
    email = input("Test user email: ").strip()
    password = getpass.getpass("Test user password (hidden): ")
    r = httpx.post(f"{url}/auth/v1/token", params={"grant_type": "password"}, headers={"apikey": key},
                   json={"email": email, "password": password}, timeout=15)
    if r.status_code != 200:
        sys.exit(f"Sign-in failed ({r.status_code}): {r.json().get('msg') or r.json().get('error_description') or r.text}")
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    print("Signed in. Running checks...\n")

    with TestClient(app) as c:
        r = c.put("/api/me/profile", json=TEST_PROFILE, headers=headers)
        step("save profile", r.status_code == 200, r.text[:200] if r.status_code != 200 else "")
        r = c.get("/api/me/profile", headers=headers)
        step("read profile back", r.status_code == 200 and r.json()["condition"] == "Asthma")

        r = c.post("/api/me/risk", json={"horizon": 7}, headers=headers)
        step("run prediction (saved to history)", r.status_code == 200, r.text[:200] if r.status_code != 200 else "")
        run = r.json()
        print("        " + ", ".join(f"{d['date'][5:]}: {d['risk_range']}" for d in run["days"]))

        r = c.get("/api/me/history", headers=headers)
        step("history lists the run", r.status_code == 200 and any(h["forecast_id"] == run["forecast_id"] for h in r.json()))
        r = c.get(f"/api/me/history/{run['forecast_id']}", headers=headers)
        step("read the run back", r.status_code == 200 and len(r.json()["days"]) == 7)

        r = c.get(f"/api/me/history/{run['forecast_id']}")
        step("run hidden without sign-in", r.status_code == 401)

        r = c.delete(f"/api/me/history/{run['forecast_id']}", headers=headers)
        step("delete the test run", r.status_code == 204)
        r = c.get(f"/api/me/history/{run['forecast_id']}", headers=headers)
        step("run is gone", r.status_code == 404)
    print("\nAll live checks passed. (The test profile was kept; delete it in the dashboard if you like.)")


if __name__ == "__main__":
    main()
