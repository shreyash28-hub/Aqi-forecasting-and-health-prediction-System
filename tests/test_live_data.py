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


def test_nudge_moves_today_most_and_fades():
    from src.nowcast import adjust_values
    fc = np.full(7, 200.0)
    out = adjust_values(fc, 0, signal=100.0, hours=14)
    assert out[0] < 150 and out[0] < out[1] < out[6] < 200      # largest fall today, then fading
    assert np.allclose(adjust_values(fc, 0, 200.0, 14), fc)      # no gap, no change
    assert np.allclose(adjust_values(fc, 3, 100.0, 14)[:3], 200)  # days before the signal's day stay
    assert np.allclose(adjust_values(fc, 0, float("nan"), 14), fc)
    few = adjust_values(fc, 0, 100.0, hours=2)
    assert few[0] > out[0]                                       # fewer hours known, smaller nudge


def test_partial_mean_and_signal_dates():
    from src.nowcast import apply_signals, partial_mean
    idx = pd.date_range("2026-10-30", periods=48, freq="h")
    s = pd.Series(np.r_[np.arange(24, dtype=float), np.full(24, 99.0)], index=idx)
    value, n = partial_mean(s, pd.Timestamp("2026-10-30"), pd.Timestamp("2026-10-30 09:00"))
    assert n == 10 and value == pytest.approx(4.5)
    air = pd.DataFrame({"date": pd.date_range("2026-10-30", periods=5), "aqi": 200.0, "pm25": 90.0, "no2": 30.0})
    sig = {"X": {"date": "2026-10-30", "as_of": "2026-10-30T13:00:00", "aqi": {"value": 100.0, "hours": 14}}}
    out, used = apply_signals("X", air, sig)
    assert used == "2026-10-30" and out["aqi"].iloc[0] < 150 and (out["pm25"] == 90).all()
    out, used = apply_signals("X", air, {"X": {**sig["X"], "date": "2026-11-20"}})   # not a forecast day
    assert used is None and out["aqi"].equals(air["aqi"])
    assert apply_signals("Y", air, sig)[1] is None


def test_sarima_with_prior_has_no_annual_terms_and_round_trips(tmp_path, monkeypatch):
    from src import model_store
    monkeypatch.setattr(model_store, "MODELS_ROOT", tmp_path)
    monkeypatch.setattr(model_store, "MODELS_DIR", tmp_path / "aqi")   # the 2015-2020 models' folder
    idx = pd.date_range("2025-03-01", periods=150, freq="D")
    rng = np.random.default_rng(3)
    series = pd.DataFrame({"value": 90 + 8 * np.sin(np.arange(150) / 2) + rng.normal(0, 3, 150),
                           "is_interpolated": False}, index=idx)
    prof = np.linspace(-0.2, 0.2, 366)
    meta, fitted = model_store.fit_and_save("X", "SARIMA", series, source="live", profile=prof)
    assert "Fourier" not in meta["config"] and meta["params"]["annual"] is False
    assert fitted.model.model.exog is None          # the prior is the only annual term
    loaded = model_store.load_forecaster("X", source="live").forecast(10)
    assert np.allclose(loaded["aqi"], fitted.forecast(10)["aqi"])
    # without a prior (2015-2020 models) the Fourier pairs stay
    meta_h, _ = model_store.fit_and_save("Y", "SARIMA", series)
    assert "Fourier" in meta_h["config"] and "annual" not in meta_h["params"]


# ---------------------------------------------------------------------------- test windows

def _daily(start="2025-02-19", end="2026-11-12"):
    idx = pd.date_range(start, end, freq="D")
    return pd.DataFrame({"value": np.arange(len(idx), dtype=float), "is_interpolated": False}, index=idx)


def test_window_splits_add_winter_after_rolling_windows():
    from src.run_forecasting import LIVE_STEP, LIVE_WINTER_ENDS, window_splits
    df = _daily()
    wins = list(window_splits(df, 30, 6, LIVE_STEP, extra_window_ends=list(LIVE_WINTER_ENDS)))
    assert [w for w, _, _ in wins] == list(range(10))
    ends = [te.index[-1].date().isoformat() for _, _, te in wins]
    assert ends[0] == "2026-11-12" and ends[6:] == sorted(LIVE_WINTER_ENDS, reverse=True)
    for _, train, test in wins:                       # each window trains only on earlier days
        assert len(test) == 30 and train.index[-1] < test.index[0]


def test_window_splits_skip_a_winter_window_overlapping_a_rolling_one():
    from src.run_forecasting import window_splits
    df = _daily(start="2025-01-01", end="2026-03-15") # the rolling window covers Feb 14 - Mar 15
    wins = list(window_splits(df, 30, 1, 45, extra_window_ends=["2026-02-28", "2026-01-29"]))
    ends = [te.index[-1].date().isoformat() for _, _, te in wins]
    assert ends == ["2026-03-15", "2026-01-29"]       # 2026-02-28 overlaps it and is skipped


def test_summary_ignores_candidates_missing_windows():
    from src.run_forecasting import add_window_rankings, summarise_windows
    rows = []
    for w in range(4):
        hard = w >= 2                                 # windows 2-3 are hard (winter); annual naive can't run there
        rows += [{"city": "X", "window": w, "model": "Model", "kind": "model", "rmse": 60.0 if hard else 20.0, "error": None},
                 {"city": "X", "window": w, "model": "Naive", "kind": "baseline", "rmse": 70.0 if hard else 25.0, "error": None},
                 {"city": "X", "window": w, "model": "Annual naive", "kind": "baseline",
                  "rmse": None if hard else 10.0, "error": "too short" if hard else None}]
    s = summarise_windows(add_window_rankings(pd.DataFrame(rows).assign(mae=1.0, mape=1.0)))
    assert s.iloc[0]["model"] == "Model"              # complete candidates rank first
    assert s.iloc[0]["best_baseline_mean_rmse"] == 47.5   # Naive's mean, not Annual naive's easy-window 10.0
    assert bool(s.set_index("model").loc["Annual naive", "incomplete"])
