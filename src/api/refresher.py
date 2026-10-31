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
from datetime import datetime, timezone

from src.openaq import find_key

log = logging.getLogger("airware.refresher")
# What the last attempts did, shown by /api/health so problems on a server are visible.
STATUS: dict = {"bundle_checked_at": None, "bundle_installed_at": None, "bundle_error": None,
                "readings_at": None, "readings_error": None}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sync_bundle() -> bool:
    from src.live_bundle import sync
    STATUS["bundle_checked_at"] = _now()
    try:
        installed = sync()
    except Exception as exc:
        STATUS["bundle_error"] = f"{type(exc).__name__}: {exc}"
        log.warning("bundle sync failed: %s", STATUS["bundle_error"])
        return False
    STATUS["bundle_error"] = None
    if installed:
        STATUS["bundle_installed_at"] = STATUS["bundle_checked_at"]
    return installed


def refresh_once(svc) -> dict:
    """One tick. Returns what happened, for logs and tests."""
    done = {"bundle": False, "nowcast": False, "reloaded": False}
    if svc.source != "live":
        return done
    if os.getenv("LIVE_BUNDLE_URL"):
        done["bundle"] = _sync_bundle()
    if find_key():
        try:
            from src.nowcast import refresh_signals
            refresh_signals()
            done["nowcast"] = True
            STATUS["readings_at"], STATUS["readings_error"] = _now(), None
        except Exception as exc:
            STATUS["readings_error"] = f"{type(exc).__name__}: {exc}"
            log.warning("readings refresh failed: %s", exc)
    done["reloaded"] = svc.reload_air()
    return done


def prepare() -> bool:
    """At startup, before the models load: fetch the latest daily bundle if one is configured."""
    if not os.getenv("LIVE_BUNDLE_URL"):
        return False
    return _sync_bundle()


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
