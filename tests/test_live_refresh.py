"""The daily refresh pieces: recent download, merge, bundle, and the API reloading by itself."""
import json
import tarfile
import time

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src import live_bundle, live_data, nowcast, openaq
from src.api import refresher, services
from src.api.main import app


# ------------------------------------------------------------------ recent download

class FakeApi:
    def __init__(self):
        self.calls = []

    def get(self, path, **params):
        self.calls.append((path, params))
        if "/12/" in path:               # an empty answer
            return {"results": []}
        hours = pd.date_range("2026-10-29T00:30:00Z", periods=5, freq="h")
        return {"results": [{"value": 10.0 + i, "parameter": {"units": "ppb"},
                             "period": {"datetimeFrom": {"utc": t.strftime("%Y-%m-%dT%H:%M:%SZ")}}}
                            for i, t in enumerate(hours)]}


def test_fetch_recent_writes_one_file_per_sensor(tmp_path):
    stations = {"Delhi": [{"id": 5, "name": "A", "sensors": {"pm25": {"id": 11, "hours": 1},
                                                              "pm10": {"id": 12, "hours": 1},
                                                              "benzene": {"id": 13, "hours": 1}}}]}
    sp = tmp_path / "stations.json"
    sp.write_text(json.dumps(stations))
    api = FakeApi()
    n = openaq.fetch_recent(days=3, out_dir=tmp_path / "recent", stations_path=sp, api=api)
    assert n == 2 and len(api.calls) == 2                      # benzene is not a kept parameter
    df = pd.read_csv(tmp_path / "recent" / "Delhi" / "5_pm25" / "recent.csv")
    assert list(df.columns) == ["datetime_utc", "value", "units"] and len(df) == 5
    assert (tmp_path / "recent" / "Delhi" / "5_pm10" / "recent.csv").read_text().count("\n") == 1   # header only
    # an empty sensor must not break the daily build
    assert live_data.load_station_hourly(tmp_path / "recent" / "Delhi" / "5_pm10").empty


# ------------------------------------------------------------------ merge into the daily file

def write_sensor(root, city, station, param, values, start):
    folder = root / city / f"{station}_{param}"
    folder.mkdir(parents=True, exist_ok=True)
    stamps = pd.date_range(start, periods=len(values), freq="h")
    pd.DataFrame({"datetime_utc": stamps.strftime("%Y-%m-%dT%H:%M:%SZ"), "value": values,
                  "units": "ppb"}).to_csv(folder / "recent.csv", index=False)


def test_merge_recent_keeps_old_values_and_replaces_with_new(tmp_path):
    raw, out = tmp_path / "recent", tmp_path / "live.csv"
    rng = np.random.default_rng(1)
    hours = 24 * 5
    for p, base in (("pm25", 40), ("pm10", 90), ("no2", 60), ("co", 0.8)):
        write_sensor(raw, "X", "1", p, base + rng.normal(0, 1, hours), "2025-03-01T00:30:00Z")
    old = pd.DataFrame({"City": "X", "Date": pd.to_datetime(["2025-02-27", "2025-03-03"]), "AQI": [77.0, 999.0],
                        "PM2.5": [1.0, 2.0]})
    old.to_csv(out, index=False)
    merged = live_data.merge_recent(raw, ["X"], out).set_index("Date")
    assert merged.loc["2025-02-27", "AQI"] == 77.0                 # untouched older day
    assert merged.loc["2025-03-03", "AQI"] != 999.0                # replaced by the new value
    assert merged.loc["2025-03-03", "PM2.5"] == pytest.approx(40, abs=2)
    # the first day of the window has no 24 h history, so it is not merged
    assert pd.Timestamp("2025-03-01") not in merged.index or np.isnan(merged.loc["2025-03-01", "AQI"])
    assert pd.read_csv(out).shape[0] == len(merged)


# ------------------------------------------------------------------ bundle

def make_root(root):
    (root / "models" / "live" / "aqi").mkdir(parents=True)
    (root / "models" / "live" / "aqi" / "registry.json").write_text('{"v": 1}')
    (root / "data" / "processed").mkdir(parents=True)
    (root / "data" / "processed" / "live_city_day.csv").write_text("City,Date\nX,2026-01-01\n")
    (root / "data" / "processed" / "live_nowcast.json").write_text("{}")
    (root / "models" / "health").mkdir(parents=True)
    (root / "models" / "health" / "secret.txt").write_text("not part of the bundle")


def test_bundle_round_trip_replaces_the_live_folder(tmp_path):
    src, dst = tmp_path / "src", tmp_path / "dst"
    make_root(src)
    bundle = live_bundle.pack(tmp_path / "b.tar.gz", src)
    with tarfile.open(bundle) as t:
        assert not any("health" in n for n in t.getnames())     # only the live files travel
    (dst / "models" / "live" / "aqi").mkdir(parents=True)
    (dst / "models" / "live" / "aqi" / "stale.json").write_text("old")
    done = live_bundle.install(bundle, dst)
    assert set(done) == set(live_bundle.CONTENT)
    assert (dst / "models/live/aqi/registry.json").read_text() == '{"v": 1}'
    assert not (dst / "models/live/aqi/stale.json").exists()    # replaced, not merged
    assert (dst / "data/processed/live_city_day.csv").exists()
    assert list(dst.glob("*.old")) == [] and list(dst.glob("tmp*")) == []


def test_bundle_with_unexpected_paths_is_refused(tmp_path):
    evil = tmp_path / "evil.tar.gz"
    (tmp_path / "f.txt").write_text("x")
    with tarfile.open(evil, "w:gz") as t:
        t.add(tmp_path / "f.txt", arcname="../outside.txt")
    with pytest.raises(ValueError):
        live_bundle.install(evil, tmp_path / "dst")
    with tarfile.open(evil, "w:gz") as t:
        t.add(tmp_path / "f.txt", arcname="src/api/main.py")
    with pytest.raises(ValueError):
        live_bundle.install(evil, tmp_path / "dst")


def test_sync_installs_only_when_the_file_changed(tmp_path, monkeypatch):
    src, dst = tmp_path / "src", tmp_path / "dst"
    make_root(src)
    bundle = live_bundle.pack(tmp_path / "b.tar.gz", src)
    payload, etag = bundle.read_bytes(), {"v": '"a"'}

    class Resp:
        def __init__(self, headers, body=b""):
            self.headers, self.body = headers, body

        def raise_for_status(self):
            pass

        def iter_bytes(self):
            yield self.body

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(live_bundle.httpx, "head", lambda url, **k: Resp({"etag": etag["v"]}))
    monkeypatch.setattr(live_bundle.httpx, "stream", lambda m, url, **k: Resp({}, payload))
    monkeypatch.setattr(live_bundle, "ETAG_PATH", tmp_path / "etag.json")
    dst.mkdir()
    assert live_bundle.sync("http://x/b.tar.gz", dst) is True
    assert (dst / "models/live/aqi/registry.json").exists()
    assert live_bundle.sync("http://x/b.tar.gz", dst) is False   # same ETag: nothing to do
    etag["v"] = '"b"'
    assert live_bundle.sync("http://x/b.tar.gz", dst) is True
    assert live_bundle.sync(None, dst) is False                   # no URL configured


# ------------------------------------------------------------------ the API reloads by itself

@pytest.fixture
def live_client(tmp_path, monkeypatch):
    path = tmp_path / "live_nowcast.json"
    path.write_text("{}")
    monkeypatch.setattr(nowcast, "NOWCAST_PATH", path)
    monkeypatch.setattr(services, "NOWCAST_PATH", path)
    monkeypatch.setattr(services, "RELOAD_CHECK_SECONDS", 0)
    with TestClient(app) as c:
        if c.app.state.models.source != "live":
            pytest.skip("live models not available")
        yield c, path


def test_new_readings_change_the_forecast_without_a_restart(live_client):
    c, path = live_client
    first = c.get("/api/forecast/Delhi?horizon=7").json()
    assert first["readings_as_of"] is None
    day = first["days"][0]["date"]
    path.write_text(json.dumps({"Delhi": {"date": day, "as_of": f"{day}T13:00:00",
                                          "aqi": {"value": 60.0, "hours": 14}}}))
    for _ in range(50):                      # the reload runs in a background thread
        c.get("/api/health")
        again = c.get("/api/forecast/Delhi?horizon=7").json()
        if again["readings_as_of"]:
            break
        time.sleep(0.2)
    assert again["readings_as_of"] == f"{day}T13:00:00"
    assert again["days"][0]["aqi"] < first["days"][0]["aqi"]
    assert c.get("/api/forecast/Chennai?horizon=7").json()["readings_as_of"] is None


def test_a_broken_readings_file_keeps_the_old_forecast(live_client):
    c, path = live_client
    before = c.get("/api/forecast/Delhi?horizon=7").json()["days"][0]["aqi"]
    path.write_text("{ not json")
    svc = c.app.state.models
    assert svc.reload_air() is False and svc.reload_error
    assert c.get("/api/forecast/Delhi?horizon=7").json()["days"][0]["aqi"] == before


def test_refresher_is_off_by_default_and_never_runs_for_history_models(monkeypatch):
    monkeypatch.delenv("LIVE_REFRESH_MINUTES", raising=False)
    assert refresher.interval_seconds() == 0 and refresher.start(object()) is None

    class Svc:
        source = "history"

    assert refresher.refresh_once(Svc()) == {"bundle": False, "nowcast": False, "reloaded": False}


def test_refresher_tick_runs_each_step_and_survives_failures(monkeypatch):
    calls = []
    monkeypatch.setenv("LIVE_BUNDLE_URL", "http://x")
    monkeypatch.setattr(refresher, "find_key", lambda: "key")
    monkeypatch.setattr(live_bundle, "sync", lambda: calls.append("sync") or True)

    def boom(**k):
        calls.append("nowcast")
        raise RuntimeError("OpenAQ down")

    monkeypatch.setattr(nowcast, "refresh_signals", boom)

    class Svc:
        source = "live"

        def reload_air(self):
            calls.append("reload")
            return True

    assert refresher.refresh_once(Svc()) == {"bundle": True, "nowcast": False, "reloaded": True}
    assert calls == ["sync", "nowcast", "reload"]
