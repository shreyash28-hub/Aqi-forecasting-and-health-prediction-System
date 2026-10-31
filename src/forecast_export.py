"""Precomputed forecasts of the live models, so the API doesn't need the model libraries.

Loading the 18 forecasters needs statsmodels, Prophet, XGBoost and PyTorch: about 350 MB
before any request, too much for a 512 MB server. The models only change once a day, so
the daily refresh writes their 30-day forecasts (and what the API shows about each model)
to ``data/processed/live_forecasts.json``, and the API reads that instead.

The API uses the file only if it matches the saved models (same model and last training
date for every city and target in the registries); otherwise it falls back to loading the
models, so a local retrain without an export still works.

Usage::

    python -m src.forecast_export      # after src.train_final_models --source live
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.data_loader import DATA_DIR, TARGETS
from src.preprocessing import TEST_DAYS

EXPORT_PATH = DATA_DIR / "processed" / "live_forecasts.json"


@dataclass
class ForecastInfo:
    """What the API needs to know about a deployed forecaster, without the model itself."""
    model_name: str
    meta: dict = field(default_factory=dict)


def _registry(target: str, source: str) -> dict:
    from src.model_store import registry_path
    path = registry_path(target, source)
    return json.loads(path.read_text(encoding="utf-8")).get("cities", {}) if path.exists() else {}


def export(source: str = "live", path: Path = EXPORT_PATH) -> dict:
    from src.model_store import forecast_air, load_forecaster, saved_cities
    out = {"source": source, "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "horizon": TEST_DAYS, "cities": {}}
    for city in saved_cities("AQI", source):
        air = forecast_air(city, TEST_DAYS, source)
        models = {}
        for target in TARGETS:
            if city in saved_cities(target, source):
                m = load_forecaster(city, target, source).meta
                models[target] = {"model": m["model"], "config": m["config"],
                                  "last_train_date": m["last_train_date"],
                                  "evaluation": {"selection": m.get("evaluation", {}).get("selection")}}
        out["cities"][city] = {
            "dates": [d.date().isoformat() for d in air["date"]],
            "values": {col: [float(v) for v in air[col]] for col in air.columns if col != "date"},
            "models": models,
        }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out), encoding="utf-8")
    return out


def load_export(source: str = "live", path: Path = EXPORT_PATH, strict: bool = True):
    """``(infos, forecasts)`` from the export file, or None when it is missing, unreadable or
    (``strict``) out of step with the saved models. ``infos`` maps (target, city) to
    ``ForecastInfo``. ``strict=False`` serves the file even if the models moved on: older
    forecasts, but no model libraries loaded (see ``EXPORT_ONLY`` in the API)."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if data.get("source") != source:
        return None
    infos, forecasts = {}, {}
    if strict:
        for target in TARGETS:
            for city, reg in _registry(target, source).items():
                got = data["cities"].get(city, {}).get("models", {}).get(target)
                if not got or got["model"] != reg["model"] or got["last_train_date"] != reg["train_end"]:
                    return None             # the models changed since the export: don't trust it
    for city, c in data.get("cities", {}).items():
        for target, got in c.get("models", {}).items():
            infos[(target, city)] = ForecastInfo(got["model"], got)
    for city, c in data["cities"].items():
        if ("AQI", city) not in infos:
            return None
        df = pd.DataFrame({"date": pd.to_datetime(c["dates"])})
        for col, values in c["values"].items():
            df[col] = values
        forecasts[city] = df
    return infos, forecasts


def inconsistent_days(out: dict, tolerance: float = 1.10) -> dict[str, int]:
    """Days where the PM2.5 forecast alone implies a higher AQI than the AQI forecast. The AQI
    is the highest pollutant sub-index, so this can't happen in reality: if it does, the
    AQI and PM2.5 models disagree (Delhi and Lucknow did on ~29 of 30 days before the
    seasonal prior was scaled and the models' own annual terms switched off)."""
    from src.aqi import sub_index
    bad = {}
    for city, c in out["cities"].items():
        v = c["values"]
        if "pm25" in v:
            si = sub_index(pd.Series(v["pm25"]), "PM2.5").to_numpy()
            n = int((si > tolerance * pd.Series(v["aqi"]).to_numpy()).sum())
            if n:
                bad[city] = n
    return bad


def main() -> None:
    out = export()
    print(f"Wrote {EXPORT_PATH} ({len(out['cities'])} cities, {out['horizon']} days)")
    for city, n in inconsistent_days(out).items():
        print(f"WARNING {city}: on {n} days the PM2.5 forecast implies a higher AQI than the AQI forecast")


if __name__ == "__main__":
    main()
