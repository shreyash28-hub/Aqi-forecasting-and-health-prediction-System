"""Does the pollutant health model still help when its inputs are *forecasts*?

The health models are evaluated on measured air values. In production they receive
forecasts, and PM2.5/NO2 forecasts carry their own error. This backtest replays the
rolling-origin windows of the forecasting evaluation:

* For every city and window, take the forecast of each city's selected model
  (multi-window winner) for AQI, PM2.5 and NO2 from the evaluation's forecasts.csv.
* Pair every forecast day with held-out profiles (the health test split).
* Predict risk with the ``aqi_only`` and ``aqi_pm25_no2`` models, fed forecasts.

The true risk for those real days is unknown, so the reference is a proxy: the most
accurate model available (``full``: all five pollutants, CV R² ~0.98) fed the
*measured* air values of that day. All models here are fitted on the health training
split only, so the test profiles are unseen.

Usage::

    python -m src.health.backtest       # needs AQI, PM2.5 and NO2 evaluations to have run
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from src.data_loader import PROJECT_ROOT, TARGETS, load_raw
from src.health.data import (CLS_TARGET, FALLBACK_FEATURE_SET, PRIMARY_FEATURE_SET, REG_TARGET,
                             RISK_LEVELS, load_health_dataset)
from src.health.models import SEED
from src.health.store import reconcile
from src.health.train import TEST_SIZE, fit
from src.run_forecasting import out_dir

OUT = PROJECT_ROOT / "reports" / "health"
N_PROFILES = 300
ORACLE_SET = "full"
AIR = {"AQI": "AQI", "PM2.5": "PM2_5", "NO2": "NO2"}  # forecast target -> health feature


def winner_forecasts(target: str) -> pd.DataFrame:
    """Per city/window/day: actual and the city's deployed model's forecast for ``target``."""
    board = json.loads((out_dir(target) / "leaderboard.json").read_text(encoding="utf-8"))
    fc = pd.read_csv(out_dir(target) / "forecasts.csv", parse_dates=["date"])
    parts = []
    for city, c in board["cities"].items():
        g = fc[fc["city"] == city]
        mw = c["multi_window"]  # same choice as train_final_models: baseline if no model beats it
        deployed = mw["best_model"] if mw["best_model_beats_baseline"] else mw["best_baseline"]
        parts.append(pd.DataFrame({"city": city, "window": g["window"], "date": g["date"],
                                   f"{target}_actual": g["actual"],
                                   f"{target}_forecast": g[deployed]}))
    return pd.concat(parts, ignore_index=True)


def main():
    df = load_health_dataset()
    y_cls = df[CLS_TARGET].map({lvl: i for i, lvl in enumerate(RISK_LEVELS)}).to_numpy()
    y_reg = df[REG_TARGET].to_numpy(dtype=float)
    idx_tr, idx_te = train_test_split(np.arange(len(df)), test_size=TEST_SIZE, stratify=y_cls, random_state=SEED)
    tr = df.iloc[idx_tr]
    models = {(task, fs): fit(task, name, fs, tr, (y_cls if task == "classification" else y_reg)[idx_tr])
              for fs, name in [(FALLBACK_FEATURE_SET, "MLP"), (PRIMARY_FEATURE_SET, "MLP"), (ORACLE_SET, "MLP")]
              for task in ("classification", "regression")}

    # Air: forecasts for AQI/PM2.5/NO2; measured values for all oracle pollutants.
    air = winner_forecasts("AQI")
    for t in ("PM2.5", "NO2"):
        air = air.merge(winner_forecasts(t), on=["city", "window", "date"], how="inner")
    raw = load_raw()[["City", "Date", "PM10", "SO2", "O3"]].rename(columns={"City": "city", "Date": "date"})
    air = air.merge(raw, on=["city", "date"], how="left")
    air = air.dropna(subset=[c for c in air.columns if c.endswith(("_actual", "_forecast"))] + ["PM10", "SO2", "O3"])

    profiles = (df.iloc[idx_te].sample(N_PROFILES, random_state=SEED).reset_index(drop=True)
                .drop(columns=["City", "Date", "AQI", "PM2_5", "PM10", "NO2", "SO2", "O3"]))
    rows = profiles.merge(air, how="cross")
    for fc_target, feat in AIR.items():
        rows[f"{feat}__actual"] = rows[f"{fc_target}_actual"]
        rows[f"{feat}__forecast"] = rows[f"{fc_target}_forecast"]

    def run(fs, source):
        X = rows.copy()
        for feat in AIR.values():
            X[feat] = X[f"{feat}__{source}"]
        clf = models[("classification", fs)].predict(X).astype(int)
        score = np.clip(models[("regression", fs)].predict(X), 0, None)
        return clf, score

    ref_clf, ref_score = run(ORACLE_SET, "actual")
    ref_elev = ref_clf >= RISK_LEVELS.index("High")
    results = []
    for fs in (FALLBACK_FEATURE_SET, PRIMARY_FEATURE_SET):
        for source in ("forecast", "actual"):
            clf, score = run(fs, source)
            alert = np.array([RISK_LEVELS.index(v) for v in reconcile(clf, score)["alert_level"]])
            results.append({
                "feature_set": fs, "air_inputs": source,
                "score_rmse_vs_reference": float(np.sqrt(np.mean((score - ref_score) ** 2))),
                "score_mae_vs_reference": float(np.mean(np.abs(score - ref_score))),
                "level_agreement_with_reference": float((clf == ref_clf).mean()),
                "high_severe_caught_by_alert_level": float((alert >= 2)[ref_elev].mean()),
                "false_high_severe_alert_rate": float((alert >= 2)[~ref_elev].mean()),
            })
    res = pd.DataFrame(results)
    per_city = []
    for city, g in rows.groupby("city"):
        idx = g.index.to_numpy()
        for fs in (FALLBACK_FEATURE_SET, PRIMARY_FEATURE_SET):
            clf, score = run(fs, "forecast")
            per_city.append({"city": city, "feature_set": fs,
                             "score_rmse_vs_reference": float(np.sqrt(np.mean((score[idx] - ref_score[idx]) ** 2))),
                             "level_agreement_with_reference": float((clf[idx] == ref_clf[idx]).mean())})
    per_city = pd.DataFrame(per_city)

    res.to_csv(OUT / "forecast_backtest.csv", index=False)
    per_city.to_csv(OUT / "forecast_backtest_by_city.csv", index=False)
    n_days = air.groupby("city").size()
    L = ["# Health models on forecast inputs: backtest", "",
         f"{N_PROFILES} held-out profiles × {len(air)} city-days from the forecasting evaluation's "
         f"rolling-origin windows ({', '.join(f'{c} {n}' for c, n in n_days.items())}). Air inputs are "
         "each city's selected forecasting model for AQI, PM2.5 and NO2. Reference: the all-pollutant "
         "model fed measured values (a proxy for the true risk of those days). All health models are "
         "fitted on the training split only.", "",
         "| Feature set | Air inputs | Score RMSE vs ref. | Score MAE vs ref. | Level agreement | "
         "High/Severe caught (alert level) | False High/Severe alerts |",
         "|---|---|---|---|---|---|---|"]
    for _, r in res.iterrows():
        L.append(f"| `{r.feature_set}` | {r.air_inputs} | {r.score_rmse_vs_reference:.3f} | "
                 f"{r.score_mae_vs_reference:.3f} | {r.level_agreement_with_reference:.1%} | "
                 f"{r.high_severe_caught_by_alert_level:.1%} | {r.false_high_severe_alert_rate:.1%} |")
    L += ["", "### By city (forecast inputs)", "", "| City | " + " | ".join(
        f"`{fs}` RMSE | `{fs}` level agr." for fs in (FALLBACK_FEATURE_SET, PRIMARY_FEATURE_SET)) + " |",
          "|---|---|---|---|---|"]
    for city, g in per_city.groupby("city"):
        g = g.set_index("feature_set")
        L.append(f"| {city} | " + " | ".join(
            f"{g.loc[fs, 'score_rmse_vs_reference']:.3f} | {g.loc[fs, 'level_agreement_with_reference']:.1%}"
            for fs in (FALLBACK_FEATURE_SET, PRIMARY_FEATURE_SET)) + " |")
    (OUT / "forecast_backtest.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(res.round(3).to_string(index=False))
    print(per_city.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
