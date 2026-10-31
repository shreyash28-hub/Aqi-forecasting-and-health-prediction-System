"""Nearby hospitals from OpenStreetMap (Overpass API), for the enquiry map.

Contact details only: Airware never books appointments. Hospitals are not stored in
the database. For the six cities they come from ``data/hospitals.json``, a snapshot of
OpenStreetMap within ``STORED_RADIUS_KM`` of each city centre built by
``scripts/build_hospitals.py``: the public Overpass servers are often overloaded (a query
takes 30-70 s, or times out), so the map must not depend on them. A request outside the
stored areas goes to Overpass live, cached for a week (in memory and in
``data/cache/hospitals.json``).
"""
from __future__ import annotations

import json
import math
import threading
import time
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["hospitals"])

# Same city centres as the rest of the site (latitude, longitude).
CITY_CENTRES: dict[str, tuple[float, float]] = {
    "Delhi": (28.6139, 77.2090), "Bengaluru": (12.9716, 77.5946), "Chennai": (13.0827, 80.2707),
    "Hyderabad": (17.3850, 78.4867), "Lucknow": (26.8467, 80.9462), "Ahmedabad": (23.0225, 72.5714),
}
OVERPASS_URLS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
USER_AGENT = "Airware/0.1 (student air-quality project; hospital enquiry map)"
CACHE_SECONDS = 7 * 24 * 3600
CACHE_FILE = Path(__file__).resolve().parents[2] / "data" / "cache" / "hospitals.json"
STORED_FILE = Path(__file__).resolve().parents[2] / "data" / "hospitals.json"
STORED_RADIUS_KM = 25
MAX_RESULTS = 80
# OpenStreetMap is edited by anyone; drop entries whose name is clearly not a medical place.
NOT_MEDICAL = ("infotech", "technolog", "software", "solutions", "builders", "real estate", "consultancy")


class Hospital(BaseModel):
    id: str                      # OpenStreetMap element, e.g. "way/123"
    name: str
    lat: float
    lon: float
    distance_km: float
    address: str | None = None
    phones: list[str] = []
    website: str | None = None
    emergency: bool = False
    osm_url: str


class HospitalsResponse(BaseModel):
    centre: dict[str, float]
    radius_km: float
    source: str
    hospitals: list[Hospital]


class UpstreamError(Exception):
    """Overpass could not be reached or returned an error."""


_cache: dict[tuple, tuple[float, list[dict]]] = {}
_lock = threading.Lock()
_loaded = False


def _load_disk_cache() -> None:
    """Results survive restarts, because a fresh Overpass query is slow (30-70 s)."""
    global _loaded
    _loaded = True
    try:
        raw = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        for k, (stamp, items) in raw.items():
            lat, lon, radius = (float(x) for x in k.split(","))
            _cache[(lat, lon, radius)] = (stamp, items)
    except (OSError, ValueError):
        pass


def _save_disk_cache() -> None:
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {f"{lat},{lon},{radius}": v for (lat, lon, radius), v in _cache.items()}
        CACHE_FILE.write_text(json.dumps(data), encoding="utf-8")
    except OSError:
        pass                                   # caching is best-effort


def _query_overpass(lat: float, lon: float, radius_m: int) -> list[dict]:
    """Raw Overpass elements for hospitals within ``radius_m`` (tries a mirror if the main server fails)."""
    query = (f'[out:json][timeout:40];('
             f'nwr["amenity"="hospital"](around:{radius_m},{lat},{lon});'
             f'nwr["healthcare"="hospital"](around:{radius_m},{lat},{lon}););out center tags;')
    last: Exception | None = None
    for url in OVERPASS_URLS:
        try:
            r = httpx.post(url, data={"data": query}, headers={"User-Agent": USER_AGENT}, timeout=60)
            r.raise_for_status()
            return r.json().get("elements", [])
        except (httpx.HTTPError, ValueError) as e:
            last = e
    raise UpstreamError(str(last))


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle (haversine) distance."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 6371.0 * 2 * math.asin(math.sqrt(a))


def _address(tags: dict) -> str | None:
    if tags.get("addr:full"):
        return tags["addr:full"]
    street = " ".join(x for x in (tags.get("addr:housenumber"), tags.get("addr:street")) if x)
    parts = [street, tags.get("addr:suburb") or tags.get("addr:neighbourhood"),
             tags.get("addr:city"), tags.get("addr:postcode")]
    text = ", ".join(p for p in parts if p)
    return text or None


def _phones(tags: dict) -> list[str]:
    raw = [tags.get(k) for k in ("phone", "contact:phone", "contact:mobile", "mobile")]
    out: list[str] = []
    for value in filter(None, raw):
        for p in value.replace(",", ";").split(";"):
            p = p.strip()
            if p and p not in out:
                out.append(p)
    return out


def _website(tags: dict) -> str | None:
    url = tags.get("website") or tags.get("contact:website")
    if not url:
        return None
    return url if url.startswith(("http://", "https://")) else f"https://{url}"


def parse(elements: list[dict], lat: float, lon: float, limit: int | None = MAX_RESULTS) -> list[dict]:
    """Named hospitals with contact details, nearest first. Duplicates (same name and spot) are dropped."""
    seen, out = set(), []
    for e in elements:
        tags = e.get("tags") or {}
        name = (tags.get("name") or tags.get("name:en") or "").strip()
        point = (e.get("lat"), e.get("lon")) if "lat" in e else ((e.get("center") or {}).get("lat"), (e.get("center") or {}).get("lon"))
        if not name or point[0] is None:
            continue                                  # unnamed places can't be enquired about
        if any(word in name.lower() for word in NOT_MEDICAL):
            continue
        key = (name.lower(), round(point[0], 3), round(point[1], 3))
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "id": f"{e['type']}/{e['id']}", "name": name, "lat": point[0], "lon": point[1],
            "distance_km": round(_distance_km(lat, lon, point[0], point[1]), 2),
            "address": _address(tags), "phones": _phones(tags), "website": _website(tags),
            "emergency": tags.get("emergency") == "yes",
            "osm_url": f"https://www.openstreetmap.org/{e['type']}/{e['id']}",
        })
    out.sort(key=lambda h: h["distance_km"])
    return out[:limit]


_stored: dict | None = None


def _load_stored() -> dict:
    global _stored
    if _stored is None:
        try:
            _stored = json.loads(STORED_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _stored = {}
    return _stored


def from_stored(lat: float, lon: float, radius_km: float) -> list[dict] | None:
    """Hospitals from the stored snapshot, if the whole search circle lies inside one city's
    stored area; None otherwise (the caller then asks Overpass)."""
    stored = _load_stored()
    for c in stored.get("cities", {}).values():
        clat, clon = c["centre"]
        if _distance_km(lat, lon, clat, clon) + radius_km <= stored.get("radius_km", 0):
            out = []
            for h in c["hospitals"]:
                d = _distance_km(lat, lon, h["lat"], h["lon"])
                if d <= radius_km:
                    out.append({**h, "distance_km": round(d, 2)})
            out.sort(key=lambda h: h["distance_km"])
            return out[:MAX_RESULTS]
    return None


def nearby(lat: float, lon: float, radius_km: float) -> list[dict]:
    """Cached lookup. Coordinates are rounded to about 100 m, so nearby requests share a result."""
    lat, lon = round(lat, 3), round(lon, 3)
    stored = from_stored(lat, lon, radius_km)
    if stored is not None:
        return stored
    key = (lat, lon, radius_km)
    now = time.time()
    with _lock:
        if not _loaded:
            _load_disk_cache()
        hit = _cache.get(key)
        if hit and now - hit[0] < CACHE_SECONDS:
            return hit[1]
    result = parse(_query_overpass(lat, lon, int(radius_km * 1000)), lat, lon)
    with _lock:
        _cache[key] = (now, result)
        _save_disk_cache()
    return result


@router.get("/hospitals", response_model=HospitalsResponse)
def hospitals(city: str | None = Query(None, description="One of the six cities; used when lat/lon are not given"),
              lat: float | None = Query(None, ge=-90, le=90),
              lon: float | None = Query(None, ge=-180, le=180),
              radius_km: float = Query(5, ge=1, le=15)):
    """Hospitals near a city centre or a point, with phone, address and website. Enquiry only: no booking."""
    if lat is None or lon is None:
        if lat is not None or lon is not None:
            raise HTTPException(422, "Give both lat and lon, or a city")
        match = next((c for c in CITY_CENTRES if city and c.lower() == city.lower()), None)
        if match is None:
            raise HTTPException(404 if city else 422,
                                f"Unknown city {city!r}. Available: {sorted(CITY_CENTRES)}" if city else "Give a city or lat/lon")
        lat, lon = CITY_CENTRES[match]
    try:
        found = nearby(lat, lon, radius_km)
    except UpstreamError:
        raise HTTPException(503, "The hospital directory (OpenStreetMap) is not responding. Try again in a minute.")
    return {"centre": {"lat": round(lat, 3), "lon": round(lon, 3)}, "radius_km": radius_km,
            "source": "OpenStreetMap contributors", "hospitals": found}
