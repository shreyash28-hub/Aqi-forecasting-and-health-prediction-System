"""Background refresh of the live forecasts while the API runs.

Off unless ``LIVE_REFRESH_MINUTES`` is set (so tests and a plain ``uvicorn`` never touch
the network). Every tick, in a daemon thread:

1. ``LIVE_BUNDLE_URL`` set: download the daily-refreshed models and data if they changed
   (``src.live_bundle.sync``; produced by the scheduled job in ``.github/workflows``).
2. An OpenAQ key available (``OPENAQ_API_KEY``): fetch the last hours of station readings
   and save today's signals (``src.nowcast.refresh_signals``), about 144 requests.
3. Reload the forecasts if either changed anything (``ModelService.reload_air``).

A failing step is logged and skipped; the API keeps serving what it has.
"""
from __future__ import annotations

import logging
import os
import threading

from src.openaq import find_key

log = logging.getLogger("airware.refresher")


def refresh_once(svc) -> dict:
    """One tick. Returns what happened, for logs and tests."""
    done = {"bundle": False, "nowcast": False, "reloaded": False}
    if svc.source != "live":
        return done
    if os.getenv("LIVE_BUNDLE_URL"):
        try:
            from src.live_bundle import sync
            done["bundle"] = sync()
        except Exception as exc:
            log.warning("bundle sync failed: %s", exc)
    if find_key():
        try:
            from src.nowcast import refresh_signals
            refresh_signals()
            done["nowcast"] = True
        except Exception as exc:
            log.warning("readings refresh failed: %s", exc)
    done["reloaded"] = svc.reload_air()
    return done


def prepare() -> bool:
    """At startup, before the models load: fetch the latest daily bundle if one is configured."""
    if not os.getenv("LIVE_BUNDLE_URL"):
        return False
    try:
        from src.live_bundle import sync
        return sync()
    except Exception as exc:
        log.warning("bundle sync at startup failed, using the files in the repository: %s", exc)
        return False


def interval_seconds() -> float:
    try:
        return max(0.0, float(os.getenv("LIVE_REFRESH_MINUTES", "0"))) * 60
    except ValueError:
        return 0.0


def start(svc) -> threading.Event | None:
    """Start the loop if enabled; returns the event that stops it."""
    every = interval_seconds()
    if not every:
        return None
    stop = threading.Event()

    def loop() -> None:
        while True:
            done = refresh_once(svc)
            log.info("live refresh: %s", done)
            if stop.wait(every):
                return

    threading.Thread(target=loop, daemon=True, name="live-refresh").start()
    return stop
