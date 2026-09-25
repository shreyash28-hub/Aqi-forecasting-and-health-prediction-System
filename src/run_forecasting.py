"""End-to-end AQI forecasting evaluation.

For each city: load + clean the daily AQI series, run stationarity / seasonality
diagnostics, hold out the final 30 days, fit every model on the rest, and score
the 30-day forecast against the hold-out (observed days only).

Usage::

    python -m src.run_forecasting                      # all cities, all models
    python -m src.run_forecasting --cities Delhi --models ARIMA XGBoost

Outputs (``reports/forecasting/``):
    stationarity.csv   ADF/KPSS + ACF seasonal diagnostics per city
    metrics.csv        one row per (city, model): RMSE/MSE/MAE/MAPE, config, runtime
    leaderboard.json   per-city ranking, ready to back the site's leaderboard
    forecasts.csv      hold-out actuals and every model's forecast, per day
    summary.md         generated summary tables and issues log
and one plot per city in ``reports/figures/``.
"""
from __future__ import annotations

import argparse
import importlib
import json
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.data_loader import CITIES, PROJECT_ROOT, load_all_cities  # noqa: E402
from src.evaluation import forecast_metrics  # noqa: E402
from src.models.baselines import BASELINES  # noqa: E402
from src.preprocessing import (TEST_DAYS, dominant_seasonal_period, from_model_space,  # noqa: E402
                               seasonal_strength, stationarity_report, to_model_space, train_test_split)

OUT_DIR = PROJECT_ROOT / "reports" / "forecasting"
FIG_DIR = PROJECT_ROOT / "reports" / "figures"


def _model_registry():
    # Imported lazily so a broken optional dependency only knocks out its own model.
    def lazy(module, fn):
        def run(train, horizon):
            mod = importlib.import_module(f"src.models.{module}")
            return getattr(mod, fn)(train, horizon)
        return run

    return {
        "ARIMA": lazy("statistical", "arima_forecast"),
        "SARIMA": lazy("statistical", "sarima_forecast"),
        "Holt-Winters": lazy("statistical", "holt_winters_forecast"),
        "LSTM": lazy("deep_models", "lstm_forecast"),
        "XGBoost": lazy("ml_models", "xgboost_forecast"),
        "Prophet": lazy("prophet_model", "prophet_forecast"),
    }


def diagnose(city: str, df: pd.DataFrame, train: pd.DataFrame) -> dict:
    log_train = to_model_space(train["aqi"])
    row = {
        "city": city,
        "start": df.index.min().date().isoformat(),
        "end": df.index.max().date().isoformat(),
        "n_days": len(df),
        "n_interpolated": int(df["is_interpolated"].sum()),
        "n_train": len(train),
    }
    row.update({f"raw_{k}": v for k, v in stationarity_report(train["aqi"]).items()})
    row.update({f"log_{k}": v for k, v in stationarity_report(log_train).items()})
    row.update(dominant_seasonal_period(train["aqi"]))
    for m in (7, 365):
        row[f"stl_strength_{m}"] = seasonal_strength(log_train, m)
    return row


def evaluate_city(city: str, df: pd.DataFrame, models: dict, test_days: int):
    train, test = train_test_split(df, test_days)
    y_train = to_model_space(train["aqi"])
    observed = ~test["is_interpolated"].to_numpy()

    rows, preds = [], {"date": test.index, "city": city, "actual": test["aqi"].to_numpy(),
                       "observed": observed}
    candidates = [(n, f, "baseline") for n, f in BASELINES.items()] + \
                 [(n, f, "model") for n, f in models.items()]
    for name, fn, kind in candidates:
        t0 = time.perf_counter()
        try:
            out = fn(y_train, test_days)
            yhat_log, config = out if isinstance(out, tuple) else (out, name)
            yhat = np.clip(from_model_space(np.asarray(yhat_log, dtype=float)), 0, None)
            if not np.all(np.isfinite(yhat)):
                raise ValueError("forecast contains non-finite values")
            metrics, error = forecast_metrics(test["aqi"], yhat, mask=observed), None
            preds[name] = yhat
        except Exception as exc:  # record and keep going; one bad model shouldn't kill the run
            metrics, config, error = {}, name, f"{type(exc).__name__}: {exc}"
            traceback.print_exc()
        runtime = time.perf_counter() - t0
        rows.append({"city": city, "model": name, "kind": kind, **metrics,
                     "config": config, "runtime_s": round(runtime, 2), "error": error})
        status = f"RMSE={metrics['rmse']:.2f}" if metrics else f"FAILED ({error})"
        print(f"  {name:<26} {status:<22} {runtime:6.1f}s")
    return pd.DataFrame(rows), pd.DataFrame(preds)


def add_rankings(metrics: pd.DataFrame) -> pd.DataFrame:
    metrics = metrics.copy()
    best_base = (metrics[metrics["kind"] == "baseline"].groupby("city")["rmse"].min()
                 .rename("best_baseline_rmse"))
    metrics = metrics.join(best_base, on="city")
    metrics["beats_baseline"] = np.where(metrics["kind"] == "model",
                                         metrics["rmse"] < metrics["best_baseline_rmse"], np.nan)
    metrics["rmse_vs_baseline_pct"] = (100 * (metrics["rmse"] / metrics["best_baseline_rmse"] - 1)).round(1)
    metrics["rank"] = metrics.groupby("city")["rmse"].rank(method="min")
    return metrics.sort_values(["city", "rank"])


def build_leaderboard(metrics: pd.DataFrame, test_days: int) -> dict:
    board = {
        "task": "aqi_forecast",
        "horizon_days": test_days,
        "selection_metric": "rmse",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "cities": {},
    }
    for city, g in metrics.groupby("city", sort=False):
        ok = g[g["error"].isna()]
        models = ok[ok["kind"] == "model"]
        base = ok[ok["kind"] == "baseline"].sort_values("rmse").iloc[0]
        best = models.sort_values("rmse").iloc[0] if len(models) else None
        board["cities"][city] = {
            "best_model": None if best is None else best["model"],
            "best_model_beats_baseline": None if best is None else bool(best["rmse"] < base["rmse"]),
            "best_baseline": base["model"],
            "ranking": [
                {k: (None if pd.isna(r[k]) else r[k]) for k in
                 ["model", "kind", "rmse", "mse", "mae", "mape", "config", "runtime_s"]}
                | {"rank": int(r["rank"])}
                for _, r in ok.sort_values("rmse").iterrows()
            ],
            "failed": g[g["error"].notna()][["model", "error"]].to_dict("records"),
        }
    return board


def plot_city(city: str, df: pd.DataFrame, preds: pd.DataFrame, metrics: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(11, 4.5))
    context = df["aqi"].iloc[-120:]
    ax.plot(context.index, context.values, color="black", lw=1.4, label="Actual AQI")
    ranked = metrics[(metrics["city"] == city) & metrics["error"].isna()].sort_values("rmse")
    best_base = ranked[ranked["kind"] == "baseline"].iloc[0]["model"]
    for name in ranked[ranked["kind"] == "model"]["model"].tolist() + [best_base]:
        rmse = ranked.set_index("model").loc[name, "rmse"]
        style = dict(ls="--", color="grey") if name == best_base else {}
        ax.plot(preds["date"], preds[name], lw=1.2, label=f"{name} (RMSE {rmse:.1f})", **style)
    ax.axvline(preds["date"].iloc[0], color="grey", lw=0.8, ls=":")
    ax.set_title(f"{city}: 30-day hold-out forecasts")
    ax.set_ylabel("AQI")
    ax.legend(fontsize=8, ncol=2, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIG_DIR / f"forecast_{city.lower()}.png", dpi=120)
    plt.close(fig)


def write_summary(diag: pd.DataFrame, metrics: pd.DataFrame, board: dict, test_days: int):
    lines = ["# AQI forecasting: hold-out evaluation summary", "",
             f"Generated {board['generated_at']}. Hold-out = final {test_days} days per city; "
             "models fitted on log1p(AQI), scored on the AQI scale (observed days only). "
             "Winner = lowest RMSE.", "",
             "## Winners", "",
             "| City | Best model | RMSE | MAE | MAPE % | Best baseline | Baseline RMSE | Beats baseline |",
             "|---|---|---|---|---|---|---|---|"]
    for city, c in board["cities"].items():
        best = next((r for r in c["ranking"] if r["model"] == c["best_model"]), None)
        base = next(r for r in c["ranking"] if r["model"] == c["best_baseline"])
        if best:
            lines.append(f"| {city} | {best['model']} | {best['rmse']:.2f} | {best['mae']:.2f} | "
                         f"{best['mape']:.1f} | {base['model']} | {base['rmse']:.2f} | "
                         f"{'yes' if c['best_model_beats_baseline'] else '**no**'} |")

    lines += ["", "## RMSE by city and model", ""]
    pivot = metrics.pivot_table(index="model", columns="city", values="rmse")
    order = list(BASELINES) + list(_model_registry())
    pivot = pivot.reindex([m for m in order if m in pivot.index])
    lines.append("| Model | " + " | ".join(pivot.columns) + " |")
    lines.append("|---|" + "---|" * len(pivot.columns))
    for model, r in pivot.iterrows():
        lines.append(f"| {model} | " + " | ".join("-" if pd.isna(v) else f"{v:.2f}" for v in r) + " |")

    lines += ["", "## Stationarity (training series)", "",
              "| City | Span | Days | Interpolated | ADF p | KPSS p | ADF d | ACF@~7 | ACF@~365 (peak lag) | STL strength m=7 / 365 |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in diag.iterrows():
        lines.append(f"| {r['city']} | {r['start']} to {r['end']} | {r['n_days']} | {r['n_interpolated']} | "
                     f"{r['raw_adf_p']:.4f} | {r['raw_kpss_p']:.3f} | {r['raw_recommended_d']} | "
                     f"{r.get('acf_7', np.nan):.2f} | {r.get('acf_365', np.nan):.2f} "
                     f"({r.get('acf_365_peak_lag', '-')}) | "
                     f"{r['stl_strength_7']:.2f} / {r['stl_strength_365']:.2f} |")

    lines += ["", "## Issues log", ""]
    failed = metrics[metrics["error"].notna()]
    for _, r in failed.iterrows():
        lines.append(f"- **{r['city']} / {r['model']}** failed: `{r['error']}`")
    losers = metrics[(metrics["kind"] == "model") & (metrics["beats_baseline"] == False)]  # noqa: E712
    for city, g in losers.groupby("city"):
        lines.append(f"- {city}: did not beat the best baseline: {', '.join(g['model'])}")
    if failed.empty and losers.empty:
        lines.append("- None.")
    (OUT_DIR / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    registry = _model_registry()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cities", nargs="+", default=CITIES)
    ap.add_argument("--models", nargs="+", default=list(registry), choices=list(registry))
    ap.add_argument("--test-days", type=int, default=TEST_DAYS)
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    models = {m: registry[m] for m in args.models}

    data = load_all_cities(args.cities)
    diag_rows, metric_frames, pred_frames = [], [], []
    for city, df in data.items():
        print(f"\n=== {city}: {df.index.min().date()} -> {df.index.max().date()} ({len(df)} days) ===")
        train, _ = train_test_split(df, args.test_days)
        diag_rows.append(diagnose(city, df, train))
        m, p = evaluate_city(city, df, models, args.test_days)
        metric_frames.append(m)
        pred_frames.append(p)

    diag = pd.DataFrame(diag_rows)
    metrics = add_rankings(pd.concat(metric_frames, ignore_index=True))
    preds = pd.concat(pred_frames, ignore_index=True)
    board = build_leaderboard(metrics, args.test_days)

    diag.to_csv(OUT_DIR / "stationarity.csv", index=False)
    metrics.to_csv(OUT_DIR / "metrics.csv", index=False)
    preds.to_csv(OUT_DIR / "forecasts.csv", index=False)
    (OUT_DIR / "leaderboard.json").write_text(json.dumps(board, indent=2, default=float), encoding="utf-8")
    for city, df in data.items():
        plot_city(city, df, preds[preds["city"] == city].reset_index(drop=True), metrics)
    write_summary(diag, metrics, board, args.test_days)
    print(f"\nWrote results to {OUT_DIR.relative_to(PROJECT_ROOT)} and plots to "
          f"{FIG_DIR.relative_to(PROJECT_ROOT)}")
    print((OUT_DIR / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
