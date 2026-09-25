"""End-to-end AQI forecasting evaluation.

For each city: load + clean the daily AQI series, run stationarity / seasonality
diagnostics, then evaluate every model on several non-overlapping 30-day test
windows (rolling origin, expanding training window). Window 0 is the final
30 days (the original single hold-out); the others step back 120 days at a time
so they cover different seasons. Forecasts are scored on observed days only.

The LSTM is run once per seed in ``LSTM_SEEDS`` and its metrics averaged.

Usage::

    python -m src.run_forecasting                      # AQI: all cities, all models
    python -m src.run_forecasting --target PM2.5       # same evaluation for a pollutant
    python -m src.run_forecasting --cities Delhi --models ARIMA XGBoost --windows 2

Outputs (``reports/forecasting/`` for AQI, ``reports/forecasting/<pm25|no2>/`` for pollutants):
    stationarity.csv         ADF/KPSS + ACF/STL seasonal diagnostics per city
    metrics.csv              one row per (city, window, model): RMSE/MSE/MAE/MAPE, config
    multiwindow_summary.csv  one row per (city, model): mean metrics, win rate, mean rank
    lstm_seed_runs.csv       per-seed LSTM metrics behind the averaged LSTM rows
    leaderboard.json         per-city final-hold-out and multi-window rankings
    forecasts.csv            per-day actuals and forecasts for every window
    summary.md               generated tables and issues log
and one final-hold-out plot per city in ``reports/figures/`` (``reports/figures/<slug>/``
for pollutants).
"""
from __future__ import annotations

import argparse
import importlib
import json
import math
import os
import time
import traceback
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.data_loader import (AQI_EXCLUDED_POLLUTANTS, CITIES, PROJECT_ROOT, TARGETS,  # noqa: E402
                             load_all_cities)
from src.evaluation import forecast_metrics  # noqa: E402
from src.models.baselines import BASELINES  # noqa: E402
from src.preprocessing import (N_WINDOWS, TEST_DAYS, WINDOW_STEP,  # noqa: E402
                               dominant_seasonal_period, from_model_space, rolling_origin_splits,
                               seasonal_strength, stationarity_report, to_model_space)

OUT_DIR = PROJECT_ROOT / "reports" / "forecasting"
FIG_DIR = PROJECT_ROOT / "reports" / "figures"
UNITS = {"AQI": "AQI", "PM2.5": "PM2.5 (µg/m³)", "NO2": "NO2 (µg/m³)"}


def out_dir(target: str = "AQI"):
    """AQI keeps the original location; pollutants get a subfolder."""
    return OUT_DIR if target == "AQI" else OUT_DIR / TARGETS[target]


def fig_dir(target: str = "AQI"):
    return FIG_DIR if target == "AQI" else FIG_DIR / TARGETS[target]
METRIC_KEYS = ["rmse", "mse", "mae", "mape"]

# name -> (module in src.models, function, seeds or None). Resolved lazily inside
# worker processes so a broken optional dependency only knocks out its own model.
MODELS = {
    "ARIMA": ("statistical", "arima_forecast", None),
    "SARIMA": ("statistical", "sarima_forecast", None),
    "Holt-Winters": ("statistical", "holt_winters_forecast", None),
    "LSTM": ("deep_models", "lstm_forecast", "LSTM_SEEDS"),
    "XGBoost": ("ml_models", "xgboost_forecast", None),
    "Prophet": ("prophet_model", "prophet_forecast", None),
}


def _resolve(name):
    module, fn, seeds_attr = MODELS[name]
    mod = importlib.import_module(f"src.models.{module}")
    return getattr(mod, fn), (getattr(mod, seeds_attr) if seeds_attr else None)


def _to_aqi(yhat_log) -> np.ndarray:
    yhat = np.clip(from_model_space(np.asarray(yhat_log, dtype=float)), 0, None)
    if not np.all(np.isfinite(yhat)):
        raise ValueError("forecast contains non-finite values")
    return yhat


# --------------------------------------------------------------------------- diagnostics

def diagnose(city: str, df: pd.DataFrame, train: pd.DataFrame, target: str = "AQI") -> dict:
    log_train = to_model_space(train["value"])
    row = {
        "city": city,
        "start": df.index.min().date().isoformat(),
        "end": df.index.max().date().isoformat(),
        "n_days": len(df),
        "n_interpolated": int(df["is_interpolated"].sum()),
        "n_train": len(train),
        "target": target,
        "aqi_excludes": ",".join(AQI_EXCLUDED_POLLUTANTS.get(city, ())) if target == "AQI" else "",
    }
    row.update({f"raw_{k}": v for k, v in stationarity_report(train["value"]).items()})
    row.update({f"log_{k}": v for k, v in stationarity_report(log_train).items()})
    row.update(dominant_seasonal_period(train["value"]))
    for m in (7, 365):
        row[f"stl_strength_{m}"] = seasonal_strength(log_train, m)
    return row


# --------------------------------------------------------------------------- evaluation

def evaluate_window(city: str, window: int, train: pd.DataFrame, test: pd.DataFrame,
                    model_names: list[str]):
    """Fit every baseline + model on ``train`` and score on ``test``. Runs in a worker."""
    horizon = len(test)
    y_train = to_model_space(train["value"])
    observed = ~test["is_interpolated"].to_numpy()
    meta = {"city": city, "window": window,
            "test_start": test.index[0].date().isoformat(),
            "test_end": test.index[-1].date().isoformat(), "n_train": len(train)}

    rows, seed_rows = [], []
    preds = {"date": test.index, "city": city, "window": window,
             "actual": test["value"].to_numpy(), "observed": observed}
    candidates = [(n, "baseline") for n in BASELINES] + [(n, "model") for n in model_names]
    for name, kind in candidates:
        t0 = time.perf_counter()
        extra = {}
        try:
            if kind == "baseline":
                fn, seeds = BASELINES[name], None
            else:
                fn, seeds = _resolve(name)
            if seeds is None:
                out = fn(y_train, horizon)
                yhat_log, config = out if isinstance(out, tuple) else (out, name)
                yhat = _to_aqi(yhat_log)
                metrics = forecast_metrics(test["value"], yhat, mask=observed)
            else:
                # Seeded model: one run per seed, metrics averaged across runs.
                runs, forecasts = [], []
                for seed in seeds:
                    yhat_log, config = fn(y_train, horizon, seed=seed)
                    yhat = _to_aqi(yhat_log)
                    m = forecast_metrics(test["value"], yhat, mask=observed)
                    runs.append(m)
                    forecasts.append(yhat)
                    seed_rows.append({**meta, "model": name, "seed": seed, **m, "config": config})
                metrics = {k: float(np.mean([r[k] for r in runs])) for k in METRIC_KEYS}
                metrics["n_scored"] = runs[0]["n_scored"]
                extra = {"rmse_seed_std": float(np.std([r["rmse"] for r in runs])),
                         "n_runs": len(runs)}
                config = config.rsplit(", seed=", 1)[0] + f", mean of seeds {list(seeds)}"
                yhat = np.mean(forecasts, axis=0)  # for plotting only; metrics are per-run means
            preds[name] = yhat
            error = None
        except Exception as exc:  # record and keep going; one bad model shouldn't kill the run
            metrics, config, error = {}, name, f"{type(exc).__name__}: {exc}"
            traceback.print_exc()
        rows.append({**meta, "model": name, "kind": kind, **metrics, **extra, "config": config,
                     "runtime_s": round(time.perf_counter() - t0, 2), "error": error})
    return rows, seed_rows, pd.DataFrame(preds)


def _worker_init():
    # One thread per worker: avoids oversubscription and keeps LSTM runs bit-identical
    # regardless of how many workers are used.
    os.environ["OMP_NUM_THREADS"] = "1"
    import torch
    torch.set_num_threads(1)


def run_all(data: dict, model_names: list[str], test_days: int, n_windows: int, jobs: int):
    tasks = [(city, w, train, test, model_names)
             for city, df in data.items()
             for w, train, test in rolling_origin_splits(df, test_days, n_windows, WINDOW_STEP)]
    print(f"{len(tasks)} (city, window) tasks on {jobs} worker(s)")
    rows, seed_rows, preds = [], [], []
    with ProcessPoolExecutor(max_workers=jobs, initializer=_worker_init) as pool:
        futures = [pool.submit(evaluate_window, *t) for t in tasks]
        for (city, w, _, test, _), fut in zip(tasks, futures):
            r, s, p = fut.result()
            rows += r
            seed_rows += s
            preds.append(p)
            ok = [x for x in r if x["error"] is None]
            best = min(ok, key=lambda x: x["rmse"])
            failed = [x["model"] for x in r if x["error"]]
            print(f"  {city:<10} w{w} {test.index[0].date()}..{test.index[-1].date()}  "
                  f"best={best['model']} ({best['rmse']:.1f})" + (f"  FAILED: {failed}" if failed else ""))
    return pd.DataFrame(rows), pd.DataFrame(seed_rows), pd.concat(preds, ignore_index=True)


# --------------------------------------------------------------------------- aggregation

def add_window_rankings(metrics: pd.DataFrame) -> pd.DataFrame:
    metrics = metrics.copy()
    keys = ["city", "window"]
    best_base = (metrics[metrics["kind"] == "baseline"].groupby(keys)["rmse"].min()
                 .rename("best_baseline_rmse"))
    metrics = metrics.join(best_base, on=keys)
    is_model = metrics["kind"] == "model"
    metrics["beats_baseline"] = (metrics["rmse"] < metrics["best_baseline_rmse"]).where(is_model)
    metrics["rmse_vs_baseline_pct"] = (100 * (metrics["rmse"] / metrics["best_baseline_rmse"] - 1)).round(1)
    metrics["rank"] = metrics.groupby(keys)["rmse"].rank(method="min")
    metrics["window_winner"] = metrics["rank"] == 1
    return metrics.sort_values(keys + ["rank"])


def summarise_windows(metrics: pd.DataFrame) -> pd.DataFrame:
    ok = metrics[metrics["error"].isna()]
    agg = ok.groupby(["city", "model", "kind"]).agg(
        n_windows=("window", "nunique"),
        mean_rmse=("rmse", "mean"), std_rmse=("rmse", "std"),
        mean_mae=("mae", "mean"), mean_mape=("mape", "mean"),
        mean_rank=("rank", "mean"),
        wins=("window_winner", "sum"),
        beat_baseline_windows=("beats_baseline", lambda s: s.fillna(False).astype(bool).sum()),
    ).reset_index()
    total = metrics.groupby("city")["window"].nunique().rename("windows_total")
    agg = agg.join(total, on="city")
    agg["win_rate"] = agg["wins"] / agg["windows_total"]
    agg["beat_baseline_rate"] = (agg["beat_baseline_windows"] / agg["windows_total"]).where(agg["kind"] == "model")
    best_base = agg[agg["kind"] == "baseline"].groupby("city")["mean_rmse"].min().rename("best_baseline_mean_rmse")
    agg = agg.join(best_base, on="city")
    return agg.sort_values(["city", "mean_rmse"]).reset_index(drop=True)


def _clean(v):
    if isinstance(v, (np.floating, float)):
        return None if math.isnan(v) else float(v)
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, np.bool_):
        return bool(v)
    return v


def build_leaderboard(metrics: pd.DataFrame, summary: pd.DataFrame, test_days: int,
                      target: str = "AQI") -> dict:
    board = {
        "task": f"{TARGETS[target]}_forecast",
        "target": target,
        "horizon_days": test_days,
        "selection_metric": "rmse",
        "multi_window_selection": "lowest mean RMSE across windows",
        "n_windows": int(metrics["window"].nunique()),
        "window_step_days": WINDOW_STEP,
        "lstm_seeds": list(_resolve("LSTM")[1]) if "LSTM" in set(metrics["model"]) else None,
        "aqi_excluded_pollutants": ({c: list(p) for c, p in AQI_EXCLUDED_POLLUTANTS.items()}
                                    if target == "AQI" else {}),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "cities": {},
    }
    for city in metrics["city"].unique():
        m = metrics[metrics["city"] == city]
        final = m[(m["window"] == 0) & m["error"].isna()].sort_values("rmse")
        fin_models = final[final["kind"] == "model"]
        fin_base = final[final["kind"] == "baseline"].iloc[0]
        s = summary[summary["city"] == city]
        s_models = s[s["kind"] == "model"]
        s_base = s[s["kind"] == "baseline"].iloc[0]
        freq = m[m["window_winner"] & m["error"].isna()]["model"].value_counts()
        board["cities"][city] = {
            "final_holdout": {
                "test_start": final["test_start"].iloc[0], "test_end": final["test_end"].iloc[0],
                "best_model": fin_models.iloc[0]["model"] if len(fin_models) else None,
                "best_model_beats_baseline": bool(fin_models.iloc[0]["rmse"] < fin_base["rmse"]) if len(fin_models) else None,
                "best_baseline": fin_base["model"],
                "ranking": [{k: _clean(r[k]) for k in ["model", "kind", *METRIC_KEYS, "config"]}
                            | {"rank": int(r["rank"])} for _, r in final.iterrows()],
            },
            "multi_window": {
                "windows": [{"window": int(w), "test_start": g["test_start"].iloc[0], "test_end": g["test_end"].iloc[0]}
                            for w, g in m.groupby("window")],
                "best_model": s_models.iloc[0]["model"] if len(s_models) else None,
                "best_model_beats_baseline": bool(s_models.iloc[0]["mean_rmse"] < s_base["mean_rmse"]) if len(s_models) else None,
                "best_baseline": s_base["model"],
                "most_frequent_window_winner": freq.index[0] if len(freq) else None,
                "ranking": [{k: _clean(r[k]) for k in ["model", "kind", "mean_rmse", "std_rmse", "mean_mae",
                                                       "mean_mape", "mean_rank", "win_rate",
                                                       "beat_baseline_rate", "n_windows"]}
                            for _, r in s.iterrows()],
            },
            "failed": m[m["error"].notna()][["window", "model", "error"]].to_dict("records"),
        }
    return board


def leaderboard_nan_paths(obj, path="") -> list[str]:
    """Metric fields that ended up null/NaN (beat_baseline_rate is legitimately null for baselines)."""
    bad = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if v is None and k in {"rmse", "mse", "mae", "mape", "mean_rmse", "mean_mae", "mean_mape",
                                   "mean_rank", "win_rate", "best_model"}:
                bad.append(f"{path}.{k}")
            bad += leaderboard_nan_paths(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            bad += leaderboard_nan_paths(v, f"{path}[{i}]")
    elif isinstance(obj, float) and math.isnan(obj):
        bad.append(path)
    return bad


# --------------------------------------------------------------------------- reporting

def plot_final_window(city: str, df: pd.DataFrame, preds: pd.DataFrame, metrics: pd.DataFrame,
                      target: str = "AQI"):
    fig, ax = plt.subplots(figsize=(11, 4.5))
    context = df["value"].iloc[-120:]
    ax.plot(context.index, context.values, color="black", lw=1.4, label=f"Actual {target}")
    ranked = metrics[(metrics["city"] == city) & (metrics["window"] == 0)
                     & metrics["error"].isna()].sort_values("rmse")
    best_base = ranked[ranked["kind"] == "baseline"].iloc[0]["model"]
    for name in ranked[ranked["kind"] == "model"]["model"].tolist() + [best_base]:
        rmse = ranked.set_index("model").loc[name, "rmse"]
        style = dict(ls="--", color="grey") if name == best_base else {}
        ax.plot(preds["date"], preds[name], lw=1.2, label=f"{name} (RMSE {rmse:.1f})", **style)
    ax.axvline(preds["date"].iloc[0], color="grey", lw=0.8, ls=":")
    suffix = " (AQI recomputed without CO)" if target == "AQI" and city in AQI_EXCLUDED_POLLUTANTS else ""
    ax.set_title(f"{city}: final 30-day hold-out {target} forecasts{suffix}")
    ax.set_ylabel(UNITS[target])
    ax.legend(fontsize=8, ncol=2, loc="upper left")
    fig.tight_layout()
    fig.savefig(fig_dir(target) / f"forecast_{city.lower()}.png", dpi=120)
    plt.close(fig)


def _md_table(header: list[str], rows: list[list[str]]) -> list[str]:
    return ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)] + \
           ["| " + " | ".join(r) + " |" for r in rows]


def _matrix(df: pd.DataFrame, value: str, fmt, order: list[str]) -> list[str]:
    pivot = df.pivot_table(index="model", columns="city", values=value, aggfunc="first")
    pivot = pivot.reindex([m for m in order if m in pivot.index])
    rows = [[model] + ["-" if pd.isna(v) else fmt(v) for v in r] for model, r in pivot.iterrows()]
    return _md_table(["Model", *pivot.columns], rows)


def write_summary(diag, metrics, summary, board, test_days, model_order, target: str = "AQI"):
    n_win = board["n_windows"]
    L = [f"# {target} forecasting: evaluation summary", "",
         f"Generated {board['generated_at']}. Models fitted on log1p({target}), scored on the original scale "
         f"(observed days only). Horizon {test_days} days. "
         f"Multi-window: {n_win} non-overlapping {test_days}-day test windows per city, stepping back "
         f"{WINDOW_STEP} days from the end (expanding training window); window 0 is the final hold-out. "
         f"LSTM metrics are the mean of seeds {board['lstm_seeds']}."
         + (" Ahmedabad AQI is recomputed without CO (see findings.md)." if target == "AQI" else ""), "",
         "## Multi-window results (primary)", "",
         "Best model = lowest mean RMSE across windows. Win = lowest RMSE of all candidates "
         "(baselines included) in a window.", ""]
    rows = []
    for city, c in board["cities"].items():
        mw = c["multi_window"]
        best = next(r for r in mw["ranking"] if r["model"] == mw["best_model"])
        base = next(r for r in mw["ranking"] if r["model"] == mw["best_baseline"])
        rows.append([city, mw["best_model"], f"{best['mean_rmse']:.2f}", f"{best['win_rate']:.0%}",
                     f"{best['beat_baseline_rate']:.0%}", mw["most_frequent_window_winner"],
                     f"{mw['best_baseline']} ({base['mean_rmse']:.2f})",
                     "yes" if mw["best_model_beats_baseline"] else "**no**"])
    L += _md_table(["City", "Best model", "Mean RMSE", "Win rate", "Beats baseline in",
                    "Most frequent window winner", "Best baseline (mean RMSE)", "Beats baseline"], rows)

    order = list(BASELINES) + model_order
    L += ["", f"### Win rate (share of {n_win} windows where the model had the lowest RMSE)", ""]
    L += _matrix(summary, "win_rate", lambda v: f"{v:.0%}", order)
    L += ["", "### Beat-baseline rate (share of windows beating that window's best baseline)", ""]
    L += _matrix(summary[summary["kind"] == "model"], "beat_baseline_rate", lambda v: f"{v:.0%}", model_order)
    L += ["", "### Mean RMSE across windows", ""]
    L += _matrix(summary, "mean_rmse", lambda v: f"{v:.2f}", order)
    L += ["", "### Mean rank across windows (1 = best of all candidates)", ""]
    L += _matrix(summary, "mean_rank", lambda v: f"{v:.1f}", order)

    L += ["", "### Test windows", ""]
    wrows = []
    for city, c in board["cities"].items():
        wrows.append([city] + [f"w{w['window']}: {w['test_start']} to {w['test_end']}"
                               for w in c["multi_window"]["windows"]])
    L += _md_table(["City"] + [f"Window {i}" for i in range(max(len(r) - 1 for r in wrows))], wrows)

    L += ["", "## Final 30-day hold-out only (window 0, kept for comparison)", ""]
    rows = []
    for city, c in board["cities"].items():
        f = c["final_holdout"]
        best = next((r for r in f["ranking"] if r["model"] == f["best_model"]), None)
        base = next(r for r in f["ranking"] if r["model"] == f["best_baseline"])
        rows.append([city, f"{f['test_start']} to {f['test_end']}", best["model"], f"{best['rmse']:.2f}",
                     f"{best['mae']:.2f}", f"{best['mape']:.1f}", f"{base['model']} ({base['rmse']:.2f})",
                     "yes" if f["best_model_beats_baseline"] else "**no**"])
    L += _md_table(["City", "Window", "Best model", "RMSE", "MAE", "MAPE %", "Best baseline (RMSE)",
                    "Beats baseline"], rows)
    L += ["", "### RMSE on the final hold-out", ""]
    L += _matrix(metrics[metrics["window"] == 0], "rmse", lambda v: f"{v:.2f}", order)

    lstm = metrics[(metrics["model"] == "LSTM") & metrics["error"].isna()]
    if len(lstm):
        L += ["", "### LSTM seed spread (std of RMSE across seeds, mean over windows)", ""]
        spread = lstm.groupby("city")["rmse_seed_std"].mean()
        L += _md_table(["City", "Mean seed std of RMSE"], [[c, f"{v:.2f}"] for c, v in spread.items()])

    L += ["", "## Stationarity (final training series)", ""]
    rows = []
    for _, r in diag.iterrows():
        rows.append([r["city"], f"{r['start']} to {r['end']}", str(r["n_days"]), str(r["n_interpolated"]),
                     f"{r['raw_adf_p']:.4f}", f"{r['raw_kpss_p']:.3f}", str(r["raw_recommended_d"]),
                     f"{r.get('acf_7', np.nan):.2f}",
                     f"{r.get('acf_365', np.nan):.2f} ({r.get('acf_365_peak_lag', '-')})",
                     f"{r['stl_strength_7']:.2f} / {r['stl_strength_365']:.2f}"])
    L += _md_table(["City", "Span", "Days", "Interpolated", "ADF p", "KPSS p", "ADF d", "ACF@~7",
                    "ACF@~365 (peak lag)", "STL strength m=7 / 365"], rows)

    L += ["", "## Issues log", ""]
    failed = metrics[metrics["error"].notna()]
    for _, r in failed.iterrows():
        L.append(f"- **{r['city']} / window {r['window']} / {r['model']}** failed: `{r['error']}`")
    never = summary[(summary["kind"] == "model") & (summary["beat_baseline_rate"] == 0)]
    for city, g in never.groupby("city"):
        L.append(f"- {city}: never beat the baseline in any window: {', '.join(g['model'])}")
    if failed.empty and never.empty:
        L.append("- None.")
    (out_dir(target) / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--target", default="AQI", choices=list(TARGETS))
    ap.add_argument("--cities", nargs="+", default=CITIES)
    ap.add_argument("--models", nargs="+", default=list(MODELS), choices=list(MODELS))
    ap.add_argument("--test-days", type=int, default=TEST_DAYS)
    ap.add_argument("--windows", type=int, default=N_WINDOWS)
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 1) - 2))
    args = ap.parse_args()

    target = args.target
    out, figs = out_dir(target), fig_dir(target)
    out.mkdir(parents=True, exist_ok=True)
    figs.mkdir(parents=True, exist_ok=True)

    data = load_all_cities(args.cities, target=target)
    print(f"Target: {target}")
    for city, df in data.items():
        note = (f"  [AQI without {', '.join(AQI_EXCLUDED_POLLUTANTS[city])}]"
                if target == "AQI" and city in AQI_EXCLUDED_POLLUTANTS else "")
        print(f"{city:<10} {df.index.min().date()} -> {df.index.max().date()} ({len(df)} days){note}")
    diag = pd.DataFrame([diagnose(c, df, df.iloc[:-args.test_days], target) for c, df in data.items()])

    t0 = time.perf_counter()
    raw_metrics, seed_runs, preds = run_all(data, args.models, args.test_days, args.windows, args.jobs)
    metrics = add_window_rankings(raw_metrics)
    summary = summarise_windows(metrics)
    board = build_leaderboard(metrics, summary, args.test_days, target)

    diag.to_csv(out / "stationarity.csv", index=False)
    metrics.to_csv(out / "metrics.csv", index=False)
    summary.to_csv(out / "multiwindow_summary.csv", index=False)
    seed_runs.to_csv(out / "lstm_seed_runs.csv", index=False)
    preds.to_csv(out / "forecasts.csv", index=False)
    (out / "leaderboard.json").write_text(json.dumps(board, indent=2, allow_nan=False), encoding="utf-8")
    for city, df in data.items():
        final = preds[(preds["city"] == city) & (preds["window"] == 0)].reset_index(drop=True)
        plot_final_window(city, df, final, metrics, target)
    write_summary(diag, metrics, summary, board, args.test_days, args.models, target)

    bad = leaderboard_nan_paths(board)
    print(f"\nDone in {time.perf_counter() - t0:.0f}s. Failed fits: {int(metrics['error'].notna().sum())}. "
          f"NaN/null metric fields in leaderboard: {len(bad)}" + (f" -> {bad[:10]}" if bad else ""))
    print(f"Wrote results to {out.relative_to(PROJECT_ROOT)} and plots to {figs.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
