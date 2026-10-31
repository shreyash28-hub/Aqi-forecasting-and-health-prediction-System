"""Exports the numbers the Phase 2 deck charts need to deck_data.json.

Run from the repo root after ``python -m src.phase2``:
    python docs/phase2/deck_data.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_loader import CITIES, load_all_cities  # noqa: E402
from src.preprocessing import TEST_DAYS, to_model_space  # noqa: E402

REP = ROOT / "reports"
data = load_all_cities(CITIES)
delhi = data["Delhi"]["value"]

# Title slide: Delhi monthly mean AQI, 2015-2020
monthly = delhi.resample("MS").mean().dropna()

# ACF of Delhi log AQI (final hold-out training data), lags 1-400
from statsmodels.tsa.stattools import acf  # noqa: E402
y = to_model_space(delhi.iloc[:-TEST_DAYS])
r = acf(y, nlags=400, fft=True)

# Hold-out forecasts for Delhi (window 0) plus the last 30 training days
preds = pd.read_csv(REP / "forecasting" / "forecasts.csv", parse_dates=["date"])
p = preds[(preds.city == "Delhi") & (preds.window == 0)]
hist = delhi.iloc[-TEST_DAYS - 30:-TEST_DAYS]
final = pd.read_csv(REP / "phase2" / "metrics_final_holdout.csv")
fd = final[final.city == "Delhi"].set_index("model")["rmse"]

mean = pd.read_csv(REP / "phase2" / "metrics_mean_6_windows.csv")
best = pd.read_csv(REP / "phase2" / "best_classical_vs_baseline.csv")
diag = pd.read_csv(REP / "phase2" / "residual_diagnostics.csv")
params = pd.read_csv(REP / "phase2" / "parameters.csv")
pre = pd.read_csv(REP / "phase2" / "preprocessing.csv")

# ARIMA AIC evidence per city: the gap to the runner-up order and to the best model without an AR term
aic = {}
for city, g in json.loads((REP / "phase2" / "aic_grids.json").read_text(encoding="utf-8")).items():
    grid = pd.DataFrame(g["aic"]).astype(float)   # columns q, index p (as strings)
    vals = np.sort(grid.to_numpy()[np.isfinite(grid.to_numpy())])
    no_ar = grid.loc["0"].dropna().min() if "0" in grid.index else grid.loc[0].dropna().min()
    aic[city] = {"runner_up": round(float(vals[1] - vals[0]), 1), "no_ar": round(float(no_ar - vals[0]), 0)}

out = {
    "aic": aic,
    "monthly": {"labels": [d.strftime("%b %y") for d in monthly.index], "values": monthly.round(1).tolist()},
    "acf": {"lags": list(range(1, 401)), "values": np.round(r[1:], 3).tolist()},
    "delhi_holdout": {
        "labels": [d.strftime("%d %b") for d in hist.index] + [d.strftime("%d %b") for d in p.date],
        "n_hist": len(hist),
        "actual": hist.round(1).tolist() + p.actual.round(1).tolist(),
        "forecasts": {m: p[m].round(1).tolist() for m in ["Naive (last value)", "ARIMA", "SARIMA", "Holt-Winters"]},
        "rmse": fd.round(1).to_dict(),
    },
    "mean_rmse": mean.round(2).to_dict(orient="records"),
    "best": best.to_dict(orient="records"),
    "lb_pass": {m: int((g["Ljung-Box p (lag 14)"] > 0.05).sum()) for m, g in diag.groupby("Model")},
    "kurtosis": [float(diag.Kurtosis.min()), float(diag.Kurtosis.max())],
    "params": params.fillna("").to_dict(orient="records"),
    "total_days": int(pre.Days.sum()),
}
path = Path(__file__).with_name("deck_data.json")
path.write_text(json.dumps(out, indent=1), encoding="utf-8")
print("wrote", path)
