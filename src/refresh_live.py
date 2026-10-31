"""Bring the live forecasts up to date: new station readings in, models refitted.

Steps:
1. ``src.openaq.fetch_recent``: the last few days of hourly readings from the stations in
   ``data/openaq/stations.json`` (~144 requests, a few minutes). Needs only OPENAQ_API_KEY,
   not the full history, so it also runs on a fresh checkout or a server.
2. ``src.live_data --recent``: merge the complete days into ``data/processed/live_city_day.csv``.
3. Optional (``--evaluate``): rerun the live model comparison per target, which may change
   the winning model. Slower; worth doing every few weeks. Needs ``data/Aqi.zip``.
4. ``src.train_final_models --source live``: refit each city's selected model on all the
   data, so forecasts start the day after the latest complete day; then
   ``src.forecast_export`` saves their 30-day forecasts for the API.
5. ``src.nowcast``: save today's readings so far; the API starts today's forecast from them.
6. Optional (``--upload``): pack ``models/live`` and the data into one bundle and upload it
   to Supabase Storage, where a deployed API picks it up (``src.live_bundle``).

Run it once a day (``.github/workflows/refresh-live.yml`` does, on a schedule). A running API
reloads by itself when the files change, so no restart is needed. ``--nowcast-only`` does
steps 1 and 5 only, for an hourly top-up.

Usage::

    python -m src.refresh_live                    # steps 1, 2, 4, 5
    python -m src.refresh_live --upload           # ... and 6
    python -m src.refresh_live --evaluate         # steps 1-5 with the model comparison
    python -m src.refresh_live --nowcast-only     # new readings into today's forecast
    python -m src.refresh_live --skip-download    # reuse data/openaq/recent as it is
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time

from src.data_loader import PROJECT_ROOT, TARGETS


def run(*args: str) -> None:
    print(f"\n$ python {' '.join(args)}", flush=True)
    subprocess.run([sys.executable, "-u", *args], cwd=PROJECT_ROOT, check=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--evaluate", action="store_true", help="rerun the model comparison first")
    ap.add_argument("--skip-download", action="store_true")
    ap.add_argument("--nowcast-only", action="store_true", help="update today's readings only")
    ap.add_argument("--upload", action="store_true", help="upload the result bundle to Supabase Storage")
    args = ap.parse_args()

    t0 = time.perf_counter()
    if args.nowcast_only:
        run("-m", "src.nowcast", *([] if args.skip_download else ["--fetch"]))
        if args.upload:
            run("-m", "src.live_bundle", "upload")
        print(f"\nToday's readings updated in {time.perf_counter() - t0:.0f}s.")
        return
    if not args.skip_download:
        run("-m", "src.nowcast", "--fetch")        # steps 1 and 5 (today's signals use the same download)
    run("-m", "src.live_data", "--recent")
    for target in TARGETS:
        if args.evaluate:
            run("-m", "src.run_forecasting", "--source", "live", "--windows", "5", "--target", target)
        run("-m", "src.train_final_models", "--source", "live", "--target", target)
    run("-m", "src.forecast_export")              # lets the API serve them without the model libraries
    if args.skip_download:
        run("-m", "src.nowcast")                  # signals from the recent files as they are
    if args.upload:
        run("-m", "src.live_bundle", "upload")
    print(f"\nLive forecasts refreshed in {time.perf_counter() - t0:.0f}s.")


if __name__ == "__main__":
    main()
