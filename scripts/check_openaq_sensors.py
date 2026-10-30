"""Which pollutant sensors are live today at the stations near our six cities, and since when?

Follow-up to ``check_openaq_coverage.py``: OpenAQ's yearly summaries lag, and a station
that reports today may only report some pollutants (e.g. CO and O3 but not PM2.5). This
reads every sensor's first and last timestamp at the stations active since 2026-09-01.

Read-only; needs ``OPENAQ_API_KEY`` in ``.env``. Writes ``reports/openaq_sensors.json``
and ``reports/openaq_sensors.md``.

Usage::

    venv\\Scripts\\python scripts\\check_openaq_sensors.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_openaq_coverage import CITIES, PARAMS, ROOT, Client, load_key  # noqa: E402

LIVE_SINCE = "2026-09-01"   # a sensor is "live" if its last reading is after this


def main() -> None:
    api = Client(load_key())
    coverage = json.loads((ROOT / "reports" / "openaq_coverage.json").read_text(encoding="utf-8"))
    out: dict = {}
    for city in CITIES:
        stations = [s for s in coverage[city]["stations"] if s["last"] >= LIVE_SINCE]
        print(f"{city}: {len(stations)} active stations", flush=True)
        rows = []
        for st in stations:
            loc = api.get(f"/locations/{st['id']}")["results"][0]
            for s in loc.get("sensors", []):
                param = (s.get("parameter") or {}).get("name")
                if param not in PARAMS:
                    continue
                detail = api.get(f"/sensors/{s['id']}")["results"][0]
                time.sleep(0.8)                     # stay under OpenAQ's per-minute limit
                rows.append({
                    "station_id": st["id"], "station": st["name"], "provider": st["provider"],
                    "sensor_id": s["id"], "parameter": param,
                    "first": ((detail.get("datetimeFirst") or {}).get("utc") or "")[:10],
                    "last": ((detail.get("datetimeLast") or {}).get("utc") or "")[:10],
                    "observed_hours": (detail.get("coverage") or {}).get("observedCount"),
                })
        out[city] = rows

    (ROOT / "reports" / "openaq_sensors.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    lines = ["# OpenAQ: pollutant sensors live now (last reading after " + LIVE_SINCE + ")", "",
             "Per city and pollutant: number of live sensors, and the earliest start date among them.", "",
             "| City | " + " | ".join(PARAMS) + " |", "|---|" + "---|" * len(PARAMS)]
    for city, rows in out.items():
        cells = []
        for p in PARAMS:
            live = [r for r in rows if r["parameter"] == p and r["last"] >= LIVE_SINCE]
            cells.append(f"{len(live)} (from {min(r['first'] for r in live)})" if live else "0")
        lines.append(f"| {city} | " + " | ".join(cells) + " |")
    (ROOT / "reports" / "openaq_sensors.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
