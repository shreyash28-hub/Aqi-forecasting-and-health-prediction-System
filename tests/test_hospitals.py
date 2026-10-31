"""Hospital enquiry endpoint. Overpass is replaced by canned data, so no network is used.

Run: python -m pytest tests/test_hospitals.py -q
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api import hospitals as h

DELHI = h.CITY_CENTRES["Delhi"]
ELEMENTS = [
    {"type": "node", "id": 1, "lat": DELHI[0] + 0.02, "lon": DELHI[1],          # ~2.2 km north
     "tags": {"amenity": "hospital", "name": "Far Hospital", "phone": "011 1111 1111; 011 2222 2222",
              "addr:housenumber": "12", "addr:street": "Ring Road", "addr:city": "New Delhi"}},
    {"type": "way", "id": 2, "center": {"lat": DELHI[0] + 0.005, "lon": DELHI[1]},  # ~0.6 km
     "tags": {"amenity": "hospital", "name": "Near Hospital", "contact:phone": "+91 11 3333 3333",
              "website": "nearhospital.example", "emergency": "yes", "addr:full": "1 Main Road"}},
    {"type": "node", "id": 3, "lat": DELHI[0], "lon": DELHI[1] + 0.001,
     "tags": {"amenity": "hospital"}},                                            # unnamed: dropped
    {"type": "node", "id": 4, "lat": DELHI[0] + 0.005, "lon": DELHI[1],
     "tags": {"healthcare": "hospital", "name": "Near Hospital"}},                # duplicate of way/2
    {"type": "node", "id": 5, "lat": DELHI[0] + 0.001, "lon": DELHI[1],
     "tags": {"amenity": "hospital", "name": "Jayprakash Infotech"}},             # mis-tagged: dropped
]


@pytest.fixture()
def client(monkeypatch):
    calls = []

    def fake_query(lat, lon, radius_m):
        calls.append((lat, lon, radius_m))
        return ELEMENTS

    monkeypatch.setattr(h, "_query_overpass", fake_query)
    monkeypatch.setattr(h, "_cache", {})
    monkeypatch.setattr(h, "_loaded", True)
    monkeypatch.setattr(h, "_stored", {})          # no stored snapshot: these tests exercise Overpass
    monkeypatch.setattr(h, "_save_disk_cache", lambda: None)
    app = FastAPI()
    app.include_router(h.router)
    c = TestClient(app)
    c.calls = calls
    return c


def test_city_lookup_is_parsed_sorted_and_cleaned(client):
    r = client.get("/api/hospitals?city=delhi")
    assert r.status_code == 200
    body = r.json()
    names = [x["name"] for x in body["hospitals"]]
    assert names == ["Near Hospital", "Far Hospital"]             # nearest first; unnamed, duplicate and non-medical dropped
    near, far = body["hospitals"]
    assert near["id"] == "way/2" and near["emergency"] is True
    assert near["website"] == "https://nearhospital.example"
    assert near["address"] == "1 Main Road" and near["phones"] == ["+91 11 3333 3333"]
    assert far["phones"] == ["011 1111 1111", "011 2222 2222"]
    assert far["address"] == "12 Ring Road, New Delhi"
    assert 0.4 < near["distance_km"] < 0.8 and 2.0 < far["distance_km"] < 2.5
    assert far["osm_url"] == "https://www.openstreetmap.org/node/1"
    assert body["radius_km"] == 5 and "OpenStreetMap" in body["source"]


def test_point_lookup_and_cache(client):
    first = client.get("/api/hospitals?lat=28.61391&lon=77.20899&radius_km=3")
    again = client.get("/api/hospitals?lat=28.6139&lon=77.209&radius_km=3")    # same spot after rounding
    assert first.status_code == again.status_code == 200
    assert client.calls == [(28.614, 77.209, 3000)]                          # second request served from cache
    assert first.json()["centre"] == {"lat": 28.614, "lon": 77.209}


@pytest.mark.parametrize("query,status", [
    ("city=Atlantis", 404),
    ("", 422),
    ("lat=28.6", 422),
    ("city=Delhi&radius_km=50", 422),
    ("lat=95&lon=77", 422),
])
def test_bad_requests(client, query, status):
    assert client.get(f"/api/hospitals?{query}").status_code == status


def test_upstream_failure_is_503(monkeypatch):
    def boom(*_):
        raise h.UpstreamError("down")

    monkeypatch.setattr(h, "_query_overpass", boom)
    monkeypatch.setattr(h, "_cache", {})
    monkeypatch.setattr(h, "_loaded", True)
    app = FastAPI()
    app.include_router(h.router)
    r = TestClient(app).get("/api/hospitals?lat=20.0&lon=75.0")      # outside the stored city areas
    assert r.status_code == 503 and "not responding" in r.json()["detail"]
    if h._load_stored().get("cities"):                               # a city search doesn't need Overpass
        assert TestClient(app).get("/api/hospitals?city=Chennai").status_code == 200


def test_disk_cache_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(h, "CACHE_FILE", tmp_path / "hospitals.json")
    monkeypatch.setattr(h, "_cache", {(28.614, 77.209, 5.0): (123.0, [{"name": "X"}])})
    h._save_disk_cache()
    monkeypatch.setattr(h, "_cache", {})
    h._load_disk_cache()
    assert h._cache == {(28.614, 77.209, 5.0): (123.0, [{"name": "X"}])}


# ------------------------------------------------------------------ stored snapshot

def stored_snapshot():
    return {"radius_km": 25, "cities": {"Delhi": {"centre": list(DELHI), "hospitals": [
        {k: v for k, v in r.items() if k != "distance_km"} for r in h.parse(ELEMENTS, *DELHI, limit=None)]}}}


def test_stored_snapshot_answers_without_overpass(monkeypatch):
    monkeypatch.setattr(h, "_stored", stored_snapshot())
    monkeypatch.setattr(h, "_query_overpass", lambda *a: pytest.fail("Overpass must not be called"))
    app = FastAPI()
    app.include_router(h.router)
    body = TestClient(app).get("/api/hospitals?city=Delhi&radius_km=1").json()
    assert [x["name"] for x in body["hospitals"]] == ["Near Hospital"]          # Far Hospital is 2.2 km
    near_me = TestClient(app).get(f"/api/hospitals?lat={DELHI[0] + 0.02}&lon={DELHI[1]}&radius_km=3").json()
    assert near_me["hospitals"][0]["name"] == "Far Hospital" and near_me["hospitals"][0]["distance_km"] < 0.1


def test_outside_the_stored_area_falls_back_to_overpass(monkeypatch):
    monkeypatch.setattr(h, "_stored", stored_snapshot())
    monkeypatch.setattr(h, "_cache", {})
    monkeypatch.setattr(h, "_loaded", True)
    monkeypatch.setattr(h, "_save_disk_cache", lambda: None)
    calls = []
    monkeypatch.setattr(h, "_query_overpass", lambda lat, lon, r: calls.append(lat) or ELEMENTS)
    assert h.from_stored(DELHI[0] + 0.25, DELHI[1], 5) is None                  # ~28 km out
    h.nearby(DELHI[0] + 0.25, DELHI[1], 5)
    assert len(calls) == 1
