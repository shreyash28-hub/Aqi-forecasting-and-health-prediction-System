"""OpenAQ v3 client and the recent-readings download used by the daily refresh.

``scripts/download_openaq.py`` fetches the full history (months of hourly data); this
module fetches only the last few days for the stations already picked in
``data/openaq/stations.json`` (committed, so a fresh checkout or server can refresh):
one request per sensor, saved as ``data/openaq/recent/<City>/<station>_<param>/recent.csv``
in the same format as the monthly files. A refresh run is then ~144 requests.

The API key is read from ``OPENAQ_API_KEY`` (environment, or the git-ignored ``.env``).
"""
from __future__ import annotations

import csv
import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://api.openaq.org/v3"
CITIES = {  # city centre (lat, lon)
    "Delhi": (28.6139, 77.2090), "Bengaluru": (12.9716, 77.5946), "Chennai": (13.0827, 80.2707),
    "Hyderabad": (17.3850, 78.4867), "Lucknow": (26.8467, 80.9462), "Ahmedabad": (23.0225, 72.5714),
}
STATIONS_PATH = ROOT / "data" / "openaq" / "stations.json"
RECENT_DIR = ROOT / "data" / "openaq" / "recent"
PARAMS = ["pm25", "pm10", "no2", "nox", "so2", "co", "o3", "nh3"]   # parameters kept from a station


class OpenAQError(RuntimeError):
    pass


def find_key() -> str | None:
    key = os.getenv("OPENAQ_API_KEY")
    env = ROOT / ".env"
    if not key and env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("OPENAQ_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
    return key or None


def load_key() -> str:
    key = find_key()
    if not key:
        raise OpenAQError("No OPENAQ_API_KEY found. Add it to .env or the environment.")
    return key


class Client:
    def __init__(self, key: str, pause: float = 0.25):
        self.http = httpx.Client(headers={"X-API-Key": key}, timeout=30)
        self.pause = pause

    def get(self, path: str, **params):
        for attempt in range(8):
            try:
                r = self.http.get(f"{BASE}{path}", params=params)
            except (httpx.ConnectError, httpx.ReadTimeout):   # brief network hiccup: retry
                time.sleep(3 * (attempt + 1))
                continue
            if r.status_code == 429:           # rate limited: wait and retry
                time.sleep(float(r.headers.get("x-ratelimit-reset", 5)) + 1)
                continue
            if r.status_code >= 500 or r.status_code == 408:   # OpenAQ hiccup: wait and retry
                time.sleep(5 * (attempt + 1))
                continue
            if r.status_code in (401, 403):
                raise OpenAQError(f"OpenAQ rejected the API key ({r.status_code}). Check OPENAQ_API_KEY.")
            r.raise_for_status()
            time.sleep(self.pause)
            return r.json()
        raise OpenAQError(f"OpenAQ did not answer {path} (rate limit or server errors)")


def fetch_hours(api: Client, sensor_id: int, start: datetime, end: datetime) -> list[tuple[str, float, str]]:
    """Hourly readings of one sensor between two UTC datetimes: (datetime_utc, value, units)."""
    rows, page = [], 1
    while True:
        res = api.get(f"/sensors/{sensor_id}/hours", datetime_from=start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                      datetime_to=end.strftime("%Y-%m-%dT%H:%M:%SZ"), limit=1000, page=page)["results"]
        for r in res:
            stamp = ((r.get("period") or {}).get("datetimeFrom") or {}).get("utc")
            if stamp is not None and r.get("value") is not None:
                rows.append((stamp, r["value"], (r.get("parameter") or {}).get("units", "")))
        if len(res) < 1000:
            return rows
        page += 1


def fetch_recent(days: int = 6, out_dir: Path = RECENT_DIR, stations_path: Path = STATIONS_PATH,
                 api: Client | None = None, progress=None) -> int:
    """Download the last ``days`` days of hourly readings for every picked station sensor.

    Returns the number of sensors saved. A sensor that fails after retries is skipped
    (and reported through ``progress``) rather than stopping the run."""
    api = api or Client(load_key(), pause=0.5)
    stations = json.loads(stations_path.read_text(encoding="utf-8"))
    end = datetime.now(timezone.utc) + timedelta(hours=1)
    start = end - timedelta(days=days)
    saved = 0
    for city, sts in stations.items():
        for st in sts:
            for param, sensor in st["sensors"].items():
                if param not in PARAMS:
                    continue
                try:
                    rows = fetch_hours(api, sensor["id"], start, end)
                except (OpenAQError, httpx.HTTPError) as exc:
                    if progress:
                        progress(f"skipped {city} {st['name']} {param}: {exc}")
                    continue
                folder = out_dir / city / f"{st['id']}_{param}"
                folder.mkdir(parents=True, exist_ok=True)
                with (folder / "recent.csv").open("w", newline="", encoding="utf-8") as f:
                    w = csv.writer(f)
                    w.writerow(["datetime_utc", "value", "units"])
                    w.writerows(rows)
                saved += 1
    return saved
