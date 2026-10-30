"""Start today's forecast from today's readings so far.

The forecasters work on complete days: their first forecast day is today, but they
only know yesterday and earlier. Today's station readings (hours since midnight IST)
tell us how today is going, so the forecast is nudged towards them:

    r        = log(1 + today so far) - log(1 + forecast for today)
    forecast_k  ->  forecast_k * exp(w * rho**k * r)         k = 0 for today, 1 for tomorrow...
    w        = W_MAX * h / (h + HALF_HOURS)                  h = hours of data so far

The weight grows with the hours available and the effect fades by ``rho`` per day,
so one unusual day cannot move a 30-day forecast. ``W_MAX``, ``HALF_HOURS`` and ``RHO``
were chosen on the first half of a rolling backtest and scored on the second half, which
includes the winter smog season (``scripts/backtest_nowcast.py``, results in
``reports/forecasting/live/nowcast*.md``). On the second half, at a 13:00 cut-off, they cut
the RMSE of today's AQI by about 60% and of the next two days by about 14% and 5%; beyond
that there is no gain, which is why the effect fades quickly.

``python -m src.nowcast`` saves today's signals to ``data/processed/live_nowcast.json``
(``src.refresh_live`` runs it); the API applies them when it loads its forecasts, and
only if the signal's day is one of the forecast days.
"""
from __future__ import annotations

import json
from datetime import datetime

import numpy as np
import pandas as pd

from src.data_loader import CITIES, DATA_DIR
from src.live_data import city_hourly_aqi

NOWCAST_PATH = DATA_DIR / "processed" / "live_nowcast.json"
MIN_HOURS = 6            # fewer hours of today than this: no adjustment
W_MAX = 1.0
HALF_HOURS = 6.0
RHO = 0.7
# Pollutants adjusted alongside the AQI (key in the saved file -> column in the hourly frame).
SIGNALS = {"aqi": None, "pm25": "PM2.5", "no2": "NO2"}


def weight(hours: float, w_max: float = W_MAX, half: float = HALF_HOURS) -> float:
    return w_max * hours / (hours + half)


def partial_mean(hourly: pd.Series, day: pd.Timestamp, until: pd.Timestamp | None = None) -> tuple[float, int]:
    """Mean of the hourly values from midnight of ``day`` up to ``until`` (inclusive), and how many."""
    s = hourly[day: day + pd.Timedelta(hours=23)]
    if until is not None:
        s = s[:until]
    s = s.dropna()
    return (float(s.mean()) if len(s) else float("nan")), len(s)


def adjust_values(forecast: np.ndarray, k0: int, signal: float, hours: float, *, w_max: float = W_MAX,
                  half: float = HALF_HOURS, rho: float = RHO, bias: float = 0.0) -> np.ndarray:
    """Nudge forecast days ``k0`` onwards (k0 = index of the signal's day) towards ``signal``."""
    out = np.array(forecast, dtype=float)
    if not np.isfinite(signal) or not 0 <= k0 < len(out):
        return out
    r = np.log1p(signal) + bias - np.log1p(out[k0])
    k = np.arange(len(out) - k0)
    out[k0:] = np.expm1(np.log1p(out[k0:]) + weight(hours, w_max, half) * rho ** k * r)
    return np.clip(out, 0, None)


def current_signals(cities: list[str] | None = None, now: datetime | None = None) -> dict:
    """Today's-so-far AQI, PM2.5 and NO2 per city, from the latest hourly readings."""
    out = {}
    for city in cities or CITIES:
        aqi_h, conc, _ = city_hourly_aqi(city)
        last = aqi_h.dropna().index.max() if aqi_h.notna().any() else None
        if last is None:
            continue
        day = last.normalize()
        row = {"date": day.date().isoformat(), "as_of": last.isoformat()}
        for key, col in SIGNALS.items():
            series = aqi_h if col is None else conc[col]
            value, n = partial_mean(series, day, last)
            if n >= MIN_HOURS and np.isfinite(value):
                row[key] = {"value": round(value, 2), "hours": n}
        out[city] = row
    return out


def save_signals(signals: dict) -> None:
    NOWCAST_PATH.parent.mkdir(parents=True, exist_ok=True)
    NOWCAST_PATH.write_text(json.dumps(signals, indent=1), encoding="utf-8")


def load_signals() -> dict:
    return json.loads(NOWCAST_PATH.read_text(encoding="utf-8")) if NOWCAST_PATH.exists() else {}


def apply_signals(city: str, air: pd.DataFrame, signals: dict) -> tuple[pd.DataFrame, str | None]:
    """Adjust a city's air forecast (``date``, ``aqi``, ``pm25``, ``no2``) with today's signals.

    Returns the frame and the date of the signal used (None when nothing applied: no
    signal for the city, or its day is not among the forecast days)."""
    sig = signals.get(city)
    if not sig:
        return air, None
    day = pd.Timestamp(sig["date"])
    hits = np.flatnonzero((air["date"].dt.normalize() == day).to_numpy())
    if not len(hits):
        return air, None
    k0, out, used = int(hits[0]), air.copy(), False
    for key in SIGNALS:
        if key in sig and key in out:
            out[key] = adjust_values(out[key].to_numpy(), k0, sig[key]["value"], sig[key]["hours"])
            used = True
    return out, (sig["date"] if used else None)


def main() -> None:
    signals = current_signals()
    save_signals(signals)
    for city, s in signals.items():
        print(f"{city:<10} {s['date']} as of {s['as_of']}: " + ", ".join(
            f"{k} {v['value']:.0f} ({v['hours']} h)" for k, v in s.items() if isinstance(v, dict)))


if __name__ == "__main__":
    main()
