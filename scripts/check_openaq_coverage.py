"""How much 2015-2026 station data does OpenAQ have for our six cities?

Read-only: it only calls OpenAQ's public API (v3) and writes a summary. For each city it
finds the monitoring stations within 25 km of the city centre, looks up each pollutant
sensor's yearly coverage, and prints, per city / pollutant / year, the percentage of hours
with data at the best-covered single station (the safest reading of "usable": stations are not
merged).

Needs a free OpenAQ API key (register at https://explore.openaq.org/register) in the
git-ignored ``.env`` as ``OPENAQ_API_KEY=...``. Never put the key in chat or in git.

Usage::

    venv\\Scripts\\python scripts\\check_openaq_coverage.py

Writes ``reports/openaq_coverage.json`` (raw findings) and ``reports/openaq_coverage.md``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.openaq import CITIES, ROOT, Client, OpenAQError, load_key  # noqa: E402,F401  (shared with the daily refresh)

PARAMS = ["pm25", "pm10", "no2", "so2", "co", "o3"]
YEARS = list(range(2015, 2027))


def year_of(item: dict) -> int | None:
    period = item.get("period") or {}
    stamp = ((period.get("datetimeFrom") or {}).get("utc")
             or (item.get("coverage") or {}).get("datetimeFrom", {}).get("utc") or "")
    return int(stamp[:4]) if stamp[:4].isdigit() else None


def main() -> None:
    api = Client(load_key())
    findings: dict = {}
    for city, (lat, lon) in CITIES.items():
        locs = api.get("/locations", coordinates=f"{lat},{lon}", radius=25000, limit=1000)["results"]
        print(f"{city}: {len(locs)} stations within 25 km", flush=True)
        best: dict[str, dict[int, int]] = {p: {} for p in PARAMS}
        stations = []
        for loc in locs:
            sensors = [s for s in loc.get("sensors", []) if (s.get("parameter") or {}).get("name") in PARAMS]
            first = (loc.get("datetimeFirst") or {}).get("utc", "")[:10]
            last = (loc.get("datetimeLast") or {}).get("utc", "")[:10]
            stations.append({"id": loc["id"], "name": loc.get("name"), "provider": (loc.get("provider") or {}).get("name"),
                             "first": first, "last": last, "parameters": sorted({s["parameter"]["name"] for s in sensors})})
            if not last or last < "2020-07-01":      # no data after our dataset ends: nothing to add
                continue
            for s in sensors:
                param = s["parameter"]["name"]
                rows = api.get(f"/sensors/{s['id']}/years", limit=50)["results"]
                for row in rows:
                    y = year_of(row)
                    pct = (row.get("coverage") or {}).get("percentComplete")
                    if y and pct is not None:
                        best[param][y] = max(best[param].get(y, 0), round(float(pct)))
        findings[city] = {"stations": stations, "pct_hours_best_station": best}

    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    (out / "openaq_coverage.json").write_text(json.dumps(findings, indent=1), encoding="utf-8")

    lines = ["# OpenAQ coverage (% of hours with data at the best-covered station, per year)", ""]
    for city, f in findings.items():
        lines += [f"## {city}", "", "| Pollutant | " + " | ".join(str(y) for y in YEARS) + " |",
                  "|---|" + "---|" * len(YEARS)]
        for p in PARAMS:
            lines.append(f"| {p} | " + " | ".join(str(f["pct_hours_best_station"][p].get(y, 0)) for y in YEARS) + " |")
        lines.append("")
    (out / "openaq_coverage.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print("Saved reports/openaq_coverage.md and .json")


if __name__ == "__main__":
    main()
