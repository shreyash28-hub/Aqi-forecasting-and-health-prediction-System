"""Retrain each city's winning model on its full history and save it for the backend.

Winners come from the multi-window evaluation (``leaderboard.json`` of that target,
``multi_window.best_model`` = lowest mean RMSE across windows). If that model does not
beat the best naive baseline on mean RMSE, the baseline is deployed instead. Run
``python -m src.run_forecasting --target <T>`` first. Each saved model is reloaded from disk and its
forecast checked against the in-memory model before the run is considered successful.

Usage::

    python -m src.train_final_models                          # AQI, all cities in the leaderboard
    python -m src.train_final_models --target PM2.5           # pollutant models
    python -m src.train_final_models --cities Delhi
    python -m src.train_final_models --cities Delhi --model Prophet   # override the winner
    python -m src.train_final_models --source live --target AQI       # live models (models/live/)

For ``--source live`` run ``python -m src.run_forecasting --source live --target <T>``
first; the live models are refitted on all the live data with the same 2015-2020
seasonal prior the evaluation used.
"""
from __future__ import annotations

import argparse
import json
import time

import numpy as np

from src.data_loader import TARGETS
from src.model_store import SOURCES, SUPPORTED, fit_and_save, load_forecaster, write_registry
from src.preprocessing import TEST_DAYS
from src.run_forecasting import load_data, load_profiles, out_dir


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--target", default="AQI", choices=list(TARGETS))
    ap.add_argument("--cities", nargs="+")
    ap.add_argument("--model", choices=SUPPORTED, help="override the leaderboard winner")
    ap.add_argument("--source", default="history", choices=SOURCES)
    args = ap.parse_args()

    target, col, source = args.target, TARGETS[args.target], args.source
    board = json.loads((out_dir(target, source) / "leaderboard.json").read_text(encoding="utf-8"))
    cities = args.cities or list(board["cities"])
    data = load_data(cities, target, source)
    profiles = load_profiles(cities, target) if board.get("seasonal_prior") else {}

    metas = []
    for city in cities:
        mw = board["cities"][city]["multi_window"]
        if args.model:
            model_name, selection = args.model, "manual override"
        elif mw["best_model_beats_baseline"]:
            model_name, selection = mw["best_model"], "lowest mean RMSE over multi-window evaluation"
        else:
            model_name = mw["best_baseline"]
            selection = (f"naive baseline: best model ({mw['best_model']}) did not beat it on mean RMSE "
                         "over the multi-window evaluation")
        row = next((r for r in mw["ranking"] if r["model"] == model_name), {})
        eval_info = {"selection": selection,
                     "n_windows": board["n_windows"], "horizon_days": board["horizon_days"],
                     **{k: row.get(k) for k in ("mean_rmse", "std_rmse", "mean_mae", "mean_mape",
                                                "mean_rank", "win_rate", "beat_baseline_rate")},
                     "best_baseline": mw["best_baseline"],
                     "best_baseline_mean_rmse": next(r["mean_rmse"] for r in mw["ranking"]
                                                     if r["model"] == mw["best_baseline"])}

        t0 = time.perf_counter()
        meta, in_memory = fit_and_save(city, model_name, data[city], eval_info, target=target,
                                       source=source, profile=profiles.get(city))
        fit_s = time.perf_counter() - t0

        # Round trip: the model loaded from disk must reproduce the freshly trained one,
        # and a 7-day forecast must be the prefix of the 30-day one.
        fc = load_forecaster(city, target, source)
        f30 = fc.forecast(TEST_DAYS)
        expected = in_memory.forecast(TEST_DAYS)
        f7 = fc.forecast(7)
        assert np.allclose(f30[col], expected[col], rtol=1e-6, atol=1e-6), (
            f"{city}: loaded model does not reproduce the trained model")
        assert np.allclose(f7[col], f30[col].iloc[:7]), f"{city}: 7-day != first 7 of 30-day"
        assert np.isfinite(f30[col]).all(), f"{city}: non-finite forecast"
        metas.append(meta)
        print(f"{city:<10} {model_name:<13} trained on {meta['train_start']}..{meta['train_end']} "
              f"({meta['n_train']} days) in {fit_s:5.1f}s  ->  "
              f"next 7 days {target}: {', '.join(f'{v:.0f}' for v in f7[col])}")

    write_registry(metas, target, source)
    where = f"models/live/{col}/" if source == "live" else f"models/{col}/"
    print(f"\nSaved {len(metas)} {target} model(s) under {where} and updated its registry.json")


if __name__ == "__main__":
    main()
