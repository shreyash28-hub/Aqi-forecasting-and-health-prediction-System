"""Model loading and the logic behind the API endpoints.

All saved models are loaded once at startup, and each city's 30-day forecast is
computed once and cached: the models are fixed until they're retrained, so every
request after startup is a slice of a cached frame.

Which forecasters are served (``source``): the live ones (``models/live/``, trained on
recent station data, forecasting from the latest day) when they exist, otherwise the
2015-2020 ones. ``FORECAST_SOURCE=history|live`` forces one.
"""
from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass, field

import pandas as pd

from src.aqi import floor_to_pollutants
from src.data_loader import PROJECT_ROOT, TARGETS
from src.health.data import CATEGORIES, PERSON_NUMERIC, load_health_dataset, score_to_level
from src.health.store import HealthRiskPredictor, load_health_predictor
from src.forecast_export import EXPORT_PATH, load_export
from src.model_store import Forecaster, load_forecaster, registry_path, saved_cities
from src.nowcast import NOWCAST_PATH, apply_signals, load_signals
from src.preprocessing import TEST_DAYS

MAX_HORIZON = TEST_DAYS
REPORTS = PROJECT_ROOT / "reports"
FORECAST_LEADERBOARDS = {"AQI": REPORTS / "forecasting" / "leaderboard.json",
                         "PM2.5": REPORTS / "forecasting" / "pm25" / "leaderboard.json",
                         "NO2": REPORTS / "forecasting" / "no2" / "leaderboard.json"}
LIVE_LEADERBOARDS = {t: REPORTS / "forecasting" / "live" / slug / "leaderboard.json" for t, slug in TARGETS.items()}


RELOAD_CHECK_SECONDS = 10
OBSERVED_COLUMNS = {"aqi": "AQI", "pm25": "PM2.5", "no2": "NO2"}   # API name -> column in the daily file
_observed_cache: dict = {}


def _num(v) -> float | None:
    return None if v is None or pd.isna(v) else round(float(v), 1)


def _observed_frame() -> pd.DataFrame | None:
    """The live daily data, read again only when the file changes (the daily bundle replaces it)."""
    from src.live_data import OUT_PATH
    if not OUT_PATH.exists():
        return None
    mtime = OUT_PATH.stat().st_mtime_ns
    if _observed_cache.get("mtime") != mtime:
        _observed_cache.update(mtime=mtime, frame=pd.read_csv(OUT_PATH, parse_dates=["Date"]))
    return _observed_cache["frame"]


def air_fingerprint(source: str) -> tuple:
    """Modification times of the files the air forecasts are built from: the model registries
    and, for live models, today's readings. A change means the forecasts are out of date."""
    paths = [registry_path(t, source) for t in TARGETS] + ([NOWCAST_PATH, EXPORT_PATH] if source == "live" else [])
    return tuple(p.stat().st_mtime_ns if p.exists() else 0 for p in paths)


def _forecasts_from_models(source: str) -> tuple[dict, dict]:
    forecasters, forecasts = {}, {}
    for target in TARGETS:
        for city in saved_cities(target, source):
            forecasters[(target, city)] = load_forecaster(city, target, source)
    for city in saved_cities("AQI", source):
        df = forecasters[("AQI", city)].forecast(MAX_HORIZON)
        for target in ("PM2.5", "NO2"):
            fc = forecasters.get((target, city))
            if fc is not None:
                df[TARGETS[target]] = fc.forecast(MAX_HORIZON)[TARGETS[target]].to_numpy()
        forecasts[city] = df
    return forecasters, forecasts


def load_air(source: str) -> tuple[dict, dict, dict]:
    """Each city's 30-day air forecast (adjusted with today's readings for live models) and
    what to show about its models. Returns ``(forecasters, forecasts, readings_as_of)``.

    Live models: from the precomputed export when it matches the saved models (no model
    libraries loaded; see ``src/forecast_export.py``), else from the models themselves."""
    exported = load_export(source) if source == "live" else None
    if source == "live" and not exported and os.getenv("LIVE_EXPORT_ONLY") == "1":
        # A small server (512 MB) can't load the models: serve the export even if it is a day old.
        exported = load_export(source, strict=False)
    forecasters, forecasts = exported if exported else _forecasts_from_models(source)
    readings_as_of = {}
    signals = load_signals() if source == "live" else {}
    for city, df in list(forecasts.items()):
        if source == "live":   # start today from today's readings so far
            df, used = apply_signals(city, df, signals)
            if used:
                readings_as_of[city] = signals[city]["as_of"]
        forecasts[city], _ = floor_to_pollutants(df)   # AQI never below its PM2.5 / NO2 sub-index
    return forecasters, forecasts, readings_as_of


def default_source() -> str:
    forced = os.getenv("FORECAST_SOURCE")
    if forced in ("history", "live"):
        return forced
    return "live" if saved_cities("AQI", "live") else "history"
HEALTH_LEADERBOARD = REPORTS / "health" / "leaderboard.json"
ELEVATED = ("High", "Severe")

# API profile field -> health model feature (and how to convert the value).
PROFILE_FIELDS = {
    "age": "Age", "gender": "Gender", "condition": "PreexistingCondition", "smoker": "Smoker",
    "bmi": "BMI", "exercise_hours": "ExerciseHoursPerWeek", "outdoor_hours": "OutdoorExposureHours",
    "mask_usage": "MaskUsage", "occupation": "Occupation", "area_type": "AreaType",
    "family_history": "FamilyHistoryRespiratory",
}
BOOL_FIELDS = {"smoker", "family_history"}
REQUIRED_PROFILE_FIELDS = ["age", "gender", "condition", "smoker",
                           "occupation", "area_type", "mask_usage", "outdoor_hours"]


def aqi_category(aqi: float) -> str:
    """CPCB AQI category."""
    for upper, name in ((50, "Good"), (100, "Satisfactory"), (200, "Moderate"), (300, "Poor"), (400, "Very Poor")):
        if aqi <= upper:
            return name
    return "Severe"


class UnknownCity(KeyError):
    pass


LEVEL_ORDER = ["Low", "Moderate", "High", "Severe"]


def score_level_of(score: float) -> str:
    """Level implied by a risk score (the dataset's 1.0 / 1.8 / 2.8 cuts)."""
    return str(score_to_level([float(score)]).iloc[0])


def summarize(days: list[dict]) -> dict:
    """Run summary from per-day risk (works for fresh predictions and stored history)."""
    highest = max((d["alert_level"] for d in days), key=LEVEL_ORDER.index)
    return {"highest_alert_level": highest, "show_hospitals": highest in ELEVATED,
            "borderline_days": sum(bool(d["borderline"]) for d in days),
            "days_by_level": {lvl: sum(d["risk_level"] == lvl for d in days) for lvl in LEVEL_ORDER}}


@dataclass
class ModelService:
    forecasters: dict[tuple[str, str], Forecaster] = field(default_factory=dict)
    forecasts: dict[str, pd.DataFrame] = field(default_factory=dict)   # city -> 30-day air forecast
    health: HealthRiskPredictor | None = None
    defaults: dict[str, object] = field(default_factory=dict)          # health feature -> fill value
    training_ranges: dict[str, tuple[float, float]] = field(default_factory=dict)
    startup_seconds: float = 0.0
    source: str = "history"
    readings_as_of: dict[str, str] = field(default_factory=dict)       # city -> latest reading used
    fingerprint: tuple = ()
    last_check: float = 0.0
    reload_error: str | None = None
    _reloading: threading.Lock = field(default_factory=threading.Lock, repr=False)

    @classmethod
    def load(cls, source: str | None = None) -> "ModelService":
        t0 = time.perf_counter()
        svc = cls(source=source or default_source())
        svc.fingerprint = air_fingerprint(svc.source)
        svc.forecasters, svc.forecasts, svc.readings_as_of = load_air(svc.source)
        svc.health = load_health_predictor()

        # Typical values for optional profile fields, and the ranges the model was trained on.
        data = load_health_dataset()
        for feat in PERSON_NUMERIC:
            svc.defaults[feat] = round(float(data[feat].median()), 1)
            svc.training_ranges[feat] = (float(data[feat].min()), float(data[feat].max()))
        for feat in CATEGORIES:
            svc.defaults[feat] = data[feat].mode().iloc[0]
        svc.startup_seconds = round(time.perf_counter() - t0, 2)
        return svc

    # ------------------------------------------------------------------ reloading

    def reload_air(self) -> bool:
        """Rebuild the air forecasts if the model or readings files changed since they were
        loaded. The new tables are built aside and swapped in, so requests never see a
        half-loaded state. Returns True if anything was reloaded."""
        if not self._reloading.acquire(blocking=False):
            return False                       # another reload is already running
        try:
            fingerprint = air_fingerprint(self.source)
            if fingerprint == self.fingerprint:
                return False
            try:
                forecasters, forecasts, readings_as_of = load_air(self.source)
            except Exception as exc:           # half-written files: keep serving the old ones, retry later
                self.reload_error = f"{type(exc).__name__}: {exc}"
                return False
            self.forecasters, self.forecasts, self.readings_as_of = forecasters, forecasts, readings_as_of
            self.fingerprint, self.reload_error = fingerprint, None
            return True
        finally:
            self._reloading.release()

    def maybe_reload(self) -> None:
        """Called on requests: at most every few seconds, check the files and, if they changed,
        reload in the background so the request itself is not delayed."""
        now = time.monotonic()
        if now - self.last_check < RELOAD_CHECK_SECONDS:
            return
        self.last_check = now
        if air_fingerprint(self.source) != self.fingerprint:
            threading.Thread(target=self.reload_air, daemon=True, name="air-reload").start()

    def live_status(self) -> dict:
        from src.api.refresher import STATUS
        from src.forecast_export import ForecastInfo
        any_fc = next(iter(self.forecasters.values()), None)
        return {"served_from": "export" if isinstance(any_fc, ForecastInfo) else "models",
                "origin_dates": sorted({self.origin_date(c) for c in self.forecasts}),
                "readings_as_of": max(self.readings_as_of.values(), default=None),
                "reload_error": self.reload_error, **STATUS}

    # ------------------------------------------------------------------ lookups

    def canonical_city(self, city: str) -> str:
        for name in self.forecasts:
            if name.lower() == city.strip().lower():
                return name
        raise UnknownCity(city)

    def origin_date(self, city: str) -> str:
        return self.forecasters[("AQI", city)].meta["last_train_date"]

    def cities(self) -> list[dict]:
        return [{"city": c, "origin_date": self.origin_date(c),
                 "targets": {t: self.forecasters[(t, c)].model_name for t in TARGETS if (t, c) in self.forecasters}}
                for c in self.forecasts]

    def model_info(self, city: str) -> dict:
        out = {}
        for t in TARGETS:
            fc = self.forecasters.get((t, city))
            if fc is not None:
                out[t] = {"model": fc.model_name, "config": fc.meta["config"],
                          "selection": fc.meta.get("evaluation", {}).get("selection")}
        return out

    # ------------------------------------------------------------------ forecasts

    def air_forecast(self, city: str, horizon: int) -> pd.DataFrame:
        df = self.forecasts[city]
        if self.source == "live":
            # Models a day or two old would otherwise start at a day already past: start today.
            today = pd.Timestamp.now(tz="Asia/Kolkata").tz_localize(None).normalize()
            upcoming = df[df["date"] >= today]
            df = upcoming if len(upcoming) else df
        return df.iloc[:horizon].copy()

    @staticmethod
    def forecast_days(air: pd.DataFrame) -> list[dict]:
        days = []
        for r in air.itertuples(index=False):
            d = {"date": r.date.date(), "aqi": round(float(r.aqi), 1), "aqi_category": aqi_category(r.aqi)}
            for col in ("pm25", "no2"):
                if hasattr(r, col):
                    d[col] = round(float(getattr(r, col)), 1)
            days.append(d)
        return days

    def observed(self, city: str, days: int) -> dict:
        """The last ``days`` complete days of station readings, and today's readings so far.
        Live models only: the 2015-2020 models have no recent observations to show."""
        city = self.canonical_city(city)
        out = {"city": city, "days": [], "today_so_far": None}
        if self.source != "live":
            return out
        df = _observed_frame()
        if df is not None:
            rows = df[df["City"] == city].sort_values("Date").tail(days)
            records = rows.to_dict("records")
            out["days"] = [{"date": r["Date"].date(), **{k: _num(r[col]) for k, col in OBSERVED_COLUMNS.items()}}
                           for r in records]
        sig = load_signals().get(city)
        if sig and "aqi" in sig:
            out["today_so_far"] = {"date": sig["date"], "as_of": sig["as_of"], "hours": sig["aqi"]["hours"],
                                   **{k: (sig[k]["value"] if k in sig else None) for k in OBSERVED_COLUMNS}}
        return out

    def forecast(self, city: str, horizon: int) -> dict:
        city = self.canonical_city(city)
        return {"city": city, "horizon": horizon, "origin_date": self.origin_date(city),
                "models": self.model_info(city), "readings_as_of": self.readings_as_of.get(city),
                "days": self.forecast_days(self.air_forecast(city, horizon))}

    # ------------------------------------------------------------------ risk

    def to_model_profile(self, profile: dict) -> tuple[dict, list[str], list[str]]:
        """API profile -> health feature dict, plus imputed field names and warnings."""
        out, imputed, warnings = {}, [], []
        for api_name, feat in PROFILE_FIELDS.items():
            value = profile.get(api_name)
            if value is None:
                out[feat] = self.defaults[feat]
                imputed.append(api_name)
                continue
            out[feat] = ("Yes" if value else "No") if api_name in BOOL_FIELDS else value
            if feat in self.training_ranges:
                lo, hi = self.training_ranges[feat]
                if not lo <= float(value) <= hi:
                    warnings.append(f"{api_name}={value} is outside the range the model was trained on "
                                    f"({lo:g}-{hi:g}); the estimate is less reliable.")
        return out, imputed, warnings

    def risk(self, city: str, horizon: int, profile: dict) -> dict:
        city = self.canonical_city(city)
        air = self.air_forecast(city, horizon)
        model_profile, imputed, warnings = self.to_model_profile(profile)
        res = self.health.predict(model_profile, air)
        fs = res["feature_set"].iloc[0]
        if imputed:
            warnings.append("Some profile fields were not provided and were filled with typical values: "
                            + ", ".join(imputed) + ". Completing the profile makes the estimate more personal.")

        days = []
        for base, r in zip(self.forecast_days(air), res.itertuples(index=False)):
            days.append({**base,
                         "risk_level": r.risk_level, "confidence": round(float(r.confidence), 3),
                         "probabilities": {lvl: round(float(getattr(r, f"p_{lvl.lower()}")), 3)
                                           for lvl in ("Low", "Moderate", "High", "Severe")},
                         "risk_score": round(float(r.risk_score), 3), "score_level": r.score_level,
                         "borderline": bool(r.borderline), "risk_range": r.risk_range,
                         "alert_level": r.alert_level})
        return {
            "city": city, "horizon": horizon, "origin_date": self.origin_date(city), "feature_set": fs,
            "health_models": {task: self.health.models[(task, fs)].meta["model"]
                              for task in ("classification", "regression")},
            "imputed_fields": imputed, "warnings": warnings,
            "summary": summarize(days),
            "days": days,
        }

    def profile_schema(self) -> dict:
        """What the frontend's profile form needs: fields, allowed values, defaults."""
        inverse = {feat: api for api, feat in PROFILE_FIELDS.items()}
        required = REQUIRED_PROFILE_FIELDS
        return {
            "required": required,
            "choices": {inverse[f]: v for f, v in CATEGORIES.items() if inverse[f] not in BOOL_FIELDS},
            "booleans": sorted(BOOL_FIELDS),
            "numeric_training_ranges": {inverse[f]: {"min": lo, "max": hi} for f, (lo, hi) in self.training_ranges.items()},
            "defaults_when_missing": {inverse[f]: (v == "Yes" if inverse[f] in BOOL_FIELDS else v)
                                      for f, v in self.defaults.items() if inverse[f] not in required},
        }


# ---------------------------------------------------------------------- leaderboards

def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def forecast_leaderboard(target: str, source: str = "history") -> dict:
    board = _read_json((LIVE_LEADERBOARDS if source == "live" else FORECAST_LEADERBOARDS)[target])
    cities = {}
    for city, c in board["cities"].items():
        mw = c["multi_window"]
        deployed = mw["best_model"] if mw["best_model_beats_baseline"] else mw["best_baseline"]
        cities[city] = {"deployed_model": deployed, "best_model": mw["best_model"],
                        "best_model_beats_baseline": mw["best_model_beats_baseline"],
                        "best_baseline": mw["best_baseline"], "windows": mw["windows"],
                        "ranking": mw["ranking"]}
    return {"target": target, "source": source, "selection": board["multi_window_selection"],
            "n_windows": board["n_windows"],
            "horizon_days": board["horizon_days"], "generated_at": board["generated_at"], "cities": cities}


def health_leaderboard() -> dict:
    board = _read_json(HEALTH_LEADERBOARD)
    keep = ("model", "kind", "feature_set", "selected")
    tasks = {}
    for task, t in board["tasks"].items():
        metric = t["selection_metric"]
        tasks[task] = {
            "target": t["target"], "selection_metric": metric, "selected": t["selected"],
            "ranking": [{**{k: r[k] for k in keep},
                         "cv": {k[3:]: v for k, v in r.items() if k.startswith("cv_")},
                         "test": {k[5:]: v for k, v in r.items() if k.startswith("test_")}}
                        for r in t["ranking"]],
        }
    return {"generated_at": board["generated_at"], "primary_feature_set": board["primary_feature_set"],
            "boundary_rule": board["boundary_rule"], "tasks": tasks}
