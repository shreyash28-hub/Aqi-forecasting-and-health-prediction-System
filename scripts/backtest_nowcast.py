"""Does starting the forecast from today's readings so far lower the error?

Rolling backtest on the live data: for every day D after the first ``TRAIN_DAYS``, the
model sees the days up to D-1 (statsmodels ``append``, no refit), forecasts D..D+6, and
the forecast is nudged with D's readings up to a cut-off hour (``src.nowcast``). Errors
are compared with the plain forecast for horizons 1 to 7 days.

ARIMA (fitted once, on the first ``TRAIN_DAYS``, with the 2015-2020 seasonal prior)
stands in for the deployed models: the nudge only uses a model's output, so what is
measured is how much of the first-day error today's readings remove. Settings are
tuned on the first half of the test days and scored on the second half.

Usage::

    python scripts/backtest_nowcast.py [--target AQI]
Writes reports/forecasting/live/nowcast.md
"""
from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data_loader import CITIES  # noqa: E402
from src.live_data import city_hourly_aqi, load_live_cities  # noqa: E402
from src.models.statistical import fit_arima  # noqa: E402
from src.nowcast import HALF_HOURS, RHO, W_MAX, adjust_values, partial_mean  # noqa: E402
from src.preprocessing import profile_at, to_model_space  # noqa: E402
from src.run_forecasting import load_profiles  # noqa: E402

TRAIN_DAYS = 300
HORIZON = 7
CUTOFFS = (10, 13, 18)      # IST hour of the day the signal is taken
GRID = {"w_max": (0.5, 0.8, 1.0), "half": (3.0, 6.0, 12.0), "rho": (0.3, 0.5, 0.7, 0.85, 0.92)}
OUT = ROOT / "reports" / "forecasting" / "live" / "nowcast.md"


def collect(city: str, target: str) -> pd.DataFrame:
    """One row per (origin day, cutoff): forecasts and actuals for 7 days, and the signal."""
    frame = load_live_cities([city], target)[city]
    profile = load_profiles([city], target)[city]
    y = to_model_space(frame["value"]) - profile_at(profile, frame.index)
    res, _ = fit_arima(y.iloc[:TRAIN_DAYS])
    aqi_h, conc, _ = city_hourly_aqi(city)
    hourly = aqi_h if target == "AQI" else conc[target]
    actual = frame["value"].where(~frame["is_interpolated"])
    rows = []
    for t in range(TRAIN_DAYS, len(frame) - HORIZON):
        res = res.append(y.iloc[t - 1:t].to_numpy(), refit=False) if t > TRAIN_DAYS else res
        day = frame.index[t]
        dates = pd.date_range(day, periods=HORIZON)
        fc = np.expm1(np.asarray(res.forecast(HORIZON)) + profile_at(profile, dates))
        act = actual.iloc[t:t + HORIZON].to_numpy()
        for c in CUTOFFS:
            value, n = partial_mean(hourly, day, day + pd.Timedelta(hours=c))
            if n >= 6:
                rows.append({"city": city, "day": day, "cutoff": c, "signal": value, "hours": n,
                             "fc": fc, "act": act})
    return pd.DataFrame(rows)


def score(df: pd.DataFrame, **params) -> np.ndarray:
    """Mean squared error per horizon (days 1-7), over rows with an observed actual."""
    se, cnt = np.zeros(HORIZON), np.zeros(HORIZON)
    for r in df.itertuples():
        adj = adjust_values(r.fc, 0, r.signal, r.hours, **params) if params else r.fc
        ok = np.isfinite(r.act)
        se[ok] += (adj - r.act)[ok] ** 2
        cnt[ok] += 1
    return se / np.maximum(cnt, 1)


def rmse(mse: np.ndarray) -> np.ndarray:
    return np.sqrt(mse)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--target", default="AQI", choices=["AQI", "PM2.5", "NO2"])
    args = ap.parse_args()
    data = pd.concat([collect(c, args.target) for c in CITIES], ignore_index=True)
    days = np.sort(data["day"].unique())
    split = days[len(days) // 2]
    tune, test = data[data["day"] < split], data[data["day"] >= split]
    print(f"{len(days)} origin days; tune < {pd.Timestamp(split).date()} <= test")

    best, best_score = None, np.inf
    for w, h, rho in itertools.product(*GRID.values()):
        s = score(tune, w_max=w, half=h, rho=rho).mean()   # tune on all 7 days
        if s < best_score:
            best, best_score = {"w_max": w, "half": h, "rho": rho}, s
    deployed = {"w_max": W_MAX, "half": HALF_HOURS, "rho": RHO}
    print("best settings:", best, "| deployed:", deployed)

    L = [f"# Starting the forecast from today's readings: {args.target} backtest", "",
         f"Rolling one-day-ahead backtest on the live data ({pd.Timestamp(days[0]).date()} to "
         f"{pd.Timestamp(days[-1]).date()}, {len(days)} origin days x {len(CITIES)} cities), ARIMA with the "
         f"2015-2020 seasonal prior as the base forecaster. Grid search on origins before "
         f"{pd.Timestamp(split).date()} (mean RMSE over days 1-7) preferred `{best}`; the deployed settings are "
         f"`{deployed}` (the same for AQI, PM2.5 and NO2; slightly gentler on later days). Scores below are on "
         f"the later half (the winter smog season is in it), RMSE per forecast day, plain vs nudged with "
         f"the readings up to the cut-off hour. Day +1 is today: more than half of today's own hours are "
         f"already known at the cut-off, so that row measures how well they are used; days +2 onwards show "
         f"how far the correction carries.", ""]
    for c in CUTOFFS:
        sub = test[test["cutoff"] == c]
        plain, nudged = rmse(score(sub)), rmse(score(sub, **deployed))
        L += [f"### Cut-off {c}:00 IST ({len(sub)} forecasts)", "",
              "| Day | " + " | ".join(f"+{k + 1}" for k in range(HORIZON)) + " |", "|---|" + "---|" * HORIZON,
              "| Plain | " + " | ".join(f"{v:.1f}" for v in plain) + " |",
              "| Nudged | " + " | ".join(f"{v:.1f}" for v in nudged) + " |",
              "| Change | " + " | ".join(f"{100 * (n / p - 1):+.0f}%" for n, p in zip(nudged, plain)) + " |", ""]
    L += ["### Per city, cut-off 13:00, day +1 and days +1 to +3 (RMSE plain -> nudged)", "",
          "| City | Day +1 | Days +1 to +3 |", "|---|---|---|"]
    for city in CITIES:
        sub = test[(test["cutoff"] == 13) & (test["city"] == city)]
        p, n = rmse(score(sub)), rmse(score(sub, **deployed))
        L.append(f"| {city} | {p[0]:.1f} -> {n[0]:.1f} | {p[:3].mean():.1f} -> {n[:3].mean():.1f} |")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out = OUT if args.target == "AQI" else OUT.with_name(f"nowcast_{args.target.lower().replace('.', '')}.md")
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
