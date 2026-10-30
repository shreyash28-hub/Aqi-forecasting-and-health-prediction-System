"""Download recent hourly CPCB station data from OpenAQ (Feb 2025 to today) for the six cities.

Step 1 of the live-data fix: the 2015-2020 Kaggle data ends on 1 July 2020, while
OpenAQ carries the same CPCB stations live, re-registered on 18 Feb 2025. For each city
it picks the best-covered CPCB stations (``reports/openaq_sensors.json``, from
``check_openaq_sensors.py``) and saves their hourly readings, one CSV per sensor and
month, under ``data/openaq/raw/`` (git-ignored). Hourly data is needed because the CPCB
AQI uses 8-hour maxima for CO and O3 (see ``src/aqi.py``).

Resumable: months saved after they ended are skipped, so the script can simply be
re-run after an interruption, or later to fetch the newest data (the current month,
and a month that was saved while still running, are fetched again). Needs
``OPENAQ_API_KEY`` in ``.env``. ``--keep-stations`` reuses ``data/openaq/stations.json``
so a refresh doesn't switch stations.

Usage::

    venv\\Scripts\\python scripts\\download_openaq.py [--stations-per-city 4]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_openaq_coverage import CITIES, ROOT, Client, load_key  # noqa: E402

START = date(2025, 2, 1)
PARAMS = ["pm25", "pm10", "no2", "nox", "so2", "co", "o3", "nh3"]
KEY_PARAMS = {"pm25", "pm10", "no2", "co", "o3"}      # a station must report all of these
RAW = ROOT / "data" / "openaq" / "raw"
PAUSE = 1.9                                           # OpenAQ allows about 2,000 requests an hour


def months(start: date, end: date):
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def saved_after_month_end(path: Path, y: int, m: int) -> bool:
    """True when the file was written after the month (plus a day for late readings) ended.
    A month saved while it was still running is fetched again."""
    nxt = (y + 1, 1) if m == 12 else (y, m + 1)
    done = datetime(nxt[0], nxt[1], 2, tzinfo=timezone.utc)
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc) >= done


def pick_stations(n: int) -> dict[str, list[dict]]:
    """Best CPCB stations per city: live for every key pollutant, most PM2.5 hours first."""
    sensors = json.loads((ROOT / "reports" / "openaq_sensors.json").read_text(encoding="utf-8"))
    picked = {}
    for city, rows in sensors.items():
        by_station: dict[int, dict] = {}
        for r in rows:
            if r["provider"] != "CPCB" or r["last"] < "2026-09-01" or r["first"] < "2025-01-01":
                continue                                  # only the current CPCB sensors
            st = by_station.setdefault(r["station_id"], {"id": r["station_id"], "name": r["station"], "sensors": {}})
            st["sensors"][r["parameter"]] = {"id": r["sensor_id"], "hours": r["observed_hours"] or 0}
        ok = [s for s in by_station.values() if KEY_PARAMS <= set(s["sensors"])]
        ok.sort(key=lambda s: -s["sensors"]["pm25"]["hours"])
        picked[city] = ok[:n]
    return picked


def fetch_month(api: Client, sensor_id: int, y: int, m: int) -> list[tuple[str, float, str]]:
    nxt = (y + 1, 1) if m == 12 else (y, m + 1)
    rows, page = [], 1
    while True:
        res = api.get(f"/sensors/{sensor_id}/hours", datetime_from=f"{y}-{m:02d}-01T00:00:00Z",
                      datetime_to=f"{nxt[0]}-{nxt[1]:02d}-01T00:00:00Z", limit=1000, page=page)["results"]
        time.sleep(PAUSE)
        for r in res:
            stamp = ((r.get("period") or {}).get("datetimeFrom") or {}).get("utc")
            if stamp is not None and r.get("value") is not None:
                rows.append((stamp, r["value"], (r.get("parameter") or {}).get("units", "")))
        if len(res) < 1000:
            return rows
        page += 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stations-per-city", type=int, default=4)
    ap.add_argument("--keep-stations", action="store_true", help="reuse the stations picked last time")
    args = ap.parse_args()

    api = Client(load_key())
    today = datetime.now(timezone.utc).date()
    saved = RAW.parent / "stations.json"
    if args.keep_stations and saved.exists():
        stations = json.loads(saved.read_text(encoding="utf-8"))
    else:
        stations = pick_stations(args.stations_per_city)
        saved.parent.mkdir(parents=True, exist_ok=True)
        saved.write_text(json.dumps(stations, indent=1), encoding="utf-8")

    jobs = [(city, st, p, s["id"]) for city, sts in stations.items() for st in sts
            for p, s in st["sensors"].items() if p in PARAMS]
    total_months = len(list(months(START, today)))
    print(f"{len(jobs)} sensors at {sum(len(v) for v in stations.values())} stations, "
          f"{total_months} months each", flush=True)
    for city, sts in stations.items():
        print(f"  {city}: " + "; ".join(s["name"] for s in sts), flush=True)

    done = 0
    for city, st, param, sid in jobs:
        folder = RAW / city / f"{st['id']}_{param}"
        folder.mkdir(parents=True, exist_ok=True)
        for y, m in months(START, today):
            out = folder / f"{y}-{m:02d}.csv"
            if out.exists() and saved_after_month_end(out, y, m):
                continue                                  # finished month already saved
            rows = fetch_month(api, sid, y, m)
            with out.open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["datetime_utc", "value", "units"])
                w.writerows(rows)
        done += 1
        print(f"[{done}/{len(jobs)}] {city} · {st['name']} · {param}", flush=True)
    print("Download complete:", RAW)


if __name__ == "__main__":
    main()
