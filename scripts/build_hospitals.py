"""Store the hospitals around each city so the map doesn't depend on Overpass at request time.

Queries OpenStreetMap (Overpass API) once per city for hospitals within
``STORED_RADIUS_KM`` of the city centre and writes ``data/hospitals.json`` (committed;
the API reads it, see ``src/api/hospitals.py``). The public Overpass servers are often
overloaded, so each city is retried across servers with a long timeout; cities that still
fail keep their previous entry. Re-run every month or so to pick up OpenStreetMap edits.

Data: (c) OpenStreetMap contributors, ODbL.

Usage::

    venv/Scripts/python scripts/build_hospitals.py [--cities Delhi Lucknow]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.api.hospitals import (CITY_CENTRES, STORED_FILE, STORED_RADIUS_KM, USER_AGENT,  # noqa: E402
                               parse)

SERVERS = ["https://overpass-api.de/api/interpreter",
           "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
           "https://overpass.kumi.systems/api/interpreter",
           "https://overpass.private.coffee/api/interpreter"]


def fetch(lat: float, lon: float, radius_m: int, rounds: int = 3) -> list[dict]:
    query = (f'[out:json][timeout:180];('
             f'nwr["amenity"="hospital"](around:{radius_m},{lat},{lon});'
             f'nwr["healthcare"="hospital"](around:{radius_m},{lat},{lon}););out center tags;')
    last = None
    for attempt in range(rounds):
        for url in SERVERS:
            try:
                r = httpx.post(url, data={"data": query}, headers={"User-Agent": USER_AGENT}, timeout=200)
                r.raise_for_status()
                data = r.json()
                if data.get("remark", "").startswith("runtime error"):
                    raise ValueError(data["remark"][:120])
                return data.get("elements", [])
            except (httpx.HTTPError, ValueError) as e:
                last = f"{url.split('/')[2]}: {type(e).__name__} {str(e)[:80]}"
                print("   ", last, flush=True)
        time.sleep(30 * (attempt + 1))
    raise RuntimeError(last)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cities", nargs="+", default=list(CITY_CENTRES))
    args = ap.parse_args()
    old = json.loads(STORED_FILE.read_text(encoding="utf-8")) if STORED_FILE.exists() else {}
    cities = old.get("cities", {})
    for city in args.cities:
        lat, lon = CITY_CENTRES[city]
        print(f"{city}: querying Overpass ({STORED_RADIUS_KM} km)...", flush=True)
        try:
            elements = fetch(lat, lon, STORED_RADIUS_KM * 1000)
        except RuntimeError as e:
            print(f"  failed, keeping the previous entry: {e}", flush=True)
            continue
        hospitals = [{k: v for k, v in h.items() if k != "distance_km"} for h in parse(elements, lat, lon, limit=None)]
        cities[city] = {"centre": [lat, lon], "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        "hospitals": hospitals}
        phones = sum(bool(h["phones"]) for h in hospitals)
        print(f"  {len(hospitals)} hospitals ({phones} with a phone number)", flush=True)
    STORED_FILE.write_text(json.dumps({"radius_km": STORED_RADIUS_KM, "source": "(c) OpenStreetMap contributors, ODbL",
                                       "cities": cities}, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"Wrote {STORED_FILE} ({len(cities)} cities)")


if __name__ == "__main__":
    main()
