"""Bring the live forecasts up to date: new station readings in, models refitted.

Steps:
1. ``scripts/download_openaq.py --keep-stations``: fetch readings since the last run.
2. ``src.live_data``: rebuild the daily AQI / PM2.5 / NO2 per city.
3. Optional (``--evaluate``): rerun the live model comparison for each target, which
   may change the winning model. Slower; worth doing every few weeks.
4. ``src.train_final_models --source live``: refit each city's selected model on all
   the data, so forecasts start the day after the latest complete day.
5. ``src.nowcast``: save today's readings so far; the API uses them to start today's
   forecast from where the day actually is.

Today's readings change by the hour. ``--nowcast-only`` redoes just steps 1 and 5 (a
couple of minutes) and is the one to run during the day.

Run it once a day (e.g. Windows Task Scheduler, or a cron job after deployment) and
restart the API afterwards: it loads the models at startup.

Usage::

    python -m src.refresh_live                    # steps 1, 2, 4
    python -m src.refresh_live --evaluate         # steps 1-4
    python -m src.refresh_live --skip-download    # rebuild and refit only
    python -m src.refresh_live --nowcast-only     # new readings into today's forecast
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
    ap.add_argument("--nowcast-only", action="store_true", help="download and update today's readings only")
    args = ap.parse_args()

    t0 = time.perf_counter()
    if not args.skip_download:
        run("scripts/download_openaq.py", "--keep-stations")
    if args.nowcast_only:
        run("-m", "src.nowcast")
        print(f"\nToday's readings updated in {time.perf_counter() - t0:.0f}s. Restart the API to serve them.")
        return
    run("-m", "src.live_data")
    for target in TARGETS:
        if args.evaluate:
            run("-m", "src.run_forecasting", "--source", "live", "--windows", "5", "--target", target)
        run("-m", "src.train_final_models", "--source", "live", "--target", target)
    run("-m", "src.nowcast")
    print(f"\nLive forecasts refreshed in {time.perf_counter() - t0:.0f}s. Restart the API to serve them.")


if __name__ == "__main__":
    main()
