"""Cleaning and daily AQI for the live OpenAQ station data (src/live_data.py)."""
import numpy as np
import pandas as pd
import pytest

from src import live_data


def write_sensor(root, city, station, param, values, start="2025-03-01T00:30:00Z"):
    """Hourly readings as download_openaq.py saves them (UTC stamps, CPCB units)."""
    folder = root / city / f"{station}_{param}"
    folder.mkdir(parents=True, exist_ok=True)
    stamps = pd.date_range(start, periods=len(values), freq="h")
    pd.DataFrame({"datetime_utc": stamps.strftime("%Y-%m-%dT%H:%M:%SZ"), "value": values,
                  "units": "ppb"}).to_csv(folder / "2025-03.csv", index=False)


@pytest.fixture
def raw(tmp_path, monkeypatch):
    monkeypatch.setattr(live_data, "RAW_DIR", tmp_path)
    return tmp_path


def test_stuck_runs_are_dropped_short_repeats_kept():
    s = pd.Series([5.0] * 12 + [1.0, 2.0, 2.0, 3.0])
    out = live_data._drop_stuck(s)
    assert out[:12].isna().all() and out[12:].notna().all()


def test_stamps_move_to_indian_time_and_bad_values_go(raw):
    write_sensor(raw, "X", "1", "pm25", [10.0, -3.0, 2000.0] + list(range(20, 41)))
    s = live_data.load_station_hourly(raw / "X" / "1_pm25")
    assert s.index[0] == pd.Timestamp("2025-03-01 06:00")      # 00:30 UTC + 5:30
    assert np.isnan(s.iloc[1]) and np.isnan(s.iloc[2])          # negative and above the cap


def test_pm25_above_pm10_drops_both(raw):
    write_sensor(raw, "X", "1", "pm25", [50.0, 90.0, 30.0] + list(range(1, 22)))
    write_sensor(raw, "X", "1", "pm10", [80.0, 60.0, 40.0] + list(range(30, 51)))
    df = live_data.load_station("X", "1")
    assert df.iloc[1][["PM2.5", "PM10"]].isna().all()
    assert df.iloc[0][["PM2.5", "PM10"]].notna().all()


def test_station_far_above_the_others_is_dropped_for_that_day():
    idx = pd.date_range("2025-03-01", periods=48, freq="h")
    normal = pd.Series(np.r_[np.full(24, 30.0), np.full(24, 30.0)], index=idx)
    pinned = pd.Series(np.r_[np.full(24, 32.0), np.full(24, 500.0)], index=idx)
    out = live_data._drop_outlier_days({"a": normal, "b": normal * 1.1, "c": pinned}, "O3")
    assert out["c"][:24].notna().all() and out["c"][24:].isna().all()
    assert out["a"].notna().all()


def test_city_daily_needs_16_hours_and_uses_no2_for_the_aqi(raw):
    hours = 24 * 3
    rng = np.random.default_rng(0)
    for st in ("1", "2"):
        write_sensor(raw, "X", st, "pm25", 40 + rng.normal(0, 3, hours))
        write_sensor(raw, "X", st, "pm10", 90 + rng.normal(0, 5, hours))
        write_sensor(raw, "X", st, "no2", 200 + rng.normal(0, 5, hours))   # NO2 drives the AQI here
        write_sensor(raw, "X", st, "co", 0.8 + rng.normal(0, 0.05, hours))
    daily = live_data.city_daily("X").set_index("Date")
    # Readings run 06:00 IST on 1 Mar to 05:00 on 4 Mar: the first and last days are too short.
    assert daily["AQI"].isna()[["2025-03-01", "2025-03-04"]].all()
    # NO2 200 ug/m3 -> sub-index 220 (180-280 band), above PM2.5 (~67) and PM10 (~90)
    assert daily.loc[["2025-03-02", "2025-03-03"], "AQI"].between(212, 228).all()


def test_historic_profile_is_centred_and_follows_the_season():
    from src.preprocessing import historic_profile, profile_at
    idx = pd.date_range("2015-01-01", "2019-12-31", freq="D")
    winter_high = np.log1p(150 + 100 * np.cos(2 * np.pi * (idx.dayofyear - 1) / 365.25))
    prof = historic_profile(pd.Series(winter_high, index=idx))
    assert len(prof) == 366 and abs(prof.mean()) < 1e-9
    jan, jul = profile_at(prof, pd.DatetimeIndex(["2026-01-01", "2026-07-01"]))
    assert jan > 0.5 > -0.5 > jul


def test_live_model_with_prior_round_trips(tmp_path, monkeypatch):
    from src import model_store
    from src.preprocessing import to_model_space
    monkeypatch.setattr(model_store, "MODELS_ROOT", tmp_path)
    idx = pd.date_range("2025-03-01", periods=200, freq="D")
    series = pd.DataFrame({"value": 100 + 10 * np.sin(np.arange(200) / 3), "is_interpolated": False}, index=idx)
    prof = np.linspace(-0.3, 0.3, 366)
    meta, fitted = model_store.fit_and_save("X", "Holt-Winters", series, source="live", profile=prof)
    assert (tmp_path / "live" / "aqi" / "x" / "metadata.json").exists()
    assert "seasonal prior" in meta["config"] and len(meta["params"]["seasonal_prior"]) == 366
    loaded = model_store.load_forecaster("X", source="live").forecast(7)
    assert loaded["date"].iloc[0] == pd.Timestamp("2025-09-17")
    assert np.allclose(loaded["aqi"], fitted.forecast(7)["aqi"])
    # Without the prior added back the forecast would be lower (the profile is positive in Sep).
    raw = np.expm1(np.asarray(fitted.model.forecast(7)))
    assert (loaded["aqi"].to_numpy() > raw).all()
    # Naive baselines never get the prior.
    meta_b, _ = model_store.fit_and_save("Y", "Naive (last value)", series, source="live", profile=prof)
    assert "seasonal_prior" not in meta_b["params"]
    assert to_model_space(series["value"]).iloc[-1] == pytest.approx(meta_b["params"]["history"]["values"][-1])
