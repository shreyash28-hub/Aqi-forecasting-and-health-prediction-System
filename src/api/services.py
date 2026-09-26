"""Model loading and the logic behind the API endpoints.

All saved models are loaded once at startup, and each city's 30-day forecast is
computed once and cached: the models are fixed until they're retrained, so every
request after startup is a slice of a cached frame.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field

import pandas as pd

from src.data_loader import PROJECT_ROOT, TARGETS
from src.health.data import CATEGORIES, PERSON_NUMERIC, load_health_dataset, score_to_level
from src.health.store import HealthRiskPredictor, load_health_predictor
from src.model_store import Forecaster, load_forecaster, saved_cities
from src.preprocessing import TEST_DAYS

MAX_HORIZON = TEST_DAYS
REPORTS = PROJECT_ROOT / "reports"
FORECAST_LEADERBOARDS = {"AQI": REPORTS / "forecasting" / "leaderboard.json",
                         "PM2.5": REPORTS / "forecasting" / "pm25" / "leaderboard.json",
                         "NO2": REPORTS / "forecasting" / "no2" / "leaderboard.json"}
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

    @classmethod
    def load(cls) -> "ModelService":
        t0 = time.perf_counter()
        svc = cls()
        for target in TARGETS:
            for city in saved_cities(target):
                svc.forecasters[(target, city)] = load_forecaster(city, target)
        for city in saved_cities("AQI"):
            df = svc.forecasters[("AQI", city)].forecast(MAX_HORIZON)
            for target in ("PM2.5", "NO2"):
                fc = svc.forecasters.get((target, city))
                if fc is not None:
                    df[TARGETS[target]] = fc.forecast(MAX_HORIZON)[TARGETS[target]].to_numpy()
            svc.forecasts[city] = df
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
        return self.forecasts[city].iloc[:horizon].copy()

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

    def forecast(self, city: str, horizon: int) -> dict:
        city = self.canonical_city(city)
        return {"city": city, "horizon": horizon, "origin_date": self.origin_date(city),
                "models": self.model_info(city), "days": self.forecast_days(self.air_forecast(city, horizon))}

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


def forecast_leaderboard(target: str) -> dict:
    board = _read_json(FORECAST_LEADERBOARDS[target])
    cities = {}
    for city, c in board["cities"].items():
        mw = c["multi_window"]
        deployed = mw["best_model"] if mw["best_model_beats_baseline"] else mw["best_baseline"]
        cities[city] = {"deployed_model": deployed, "best_model": mw["best_model"],
                        "best_model_beats_baseline": mw["best_model_beats_baseline"],
                        "best_baseline": mw["best_baseline"], "windows": mw["windows"],
                        "ranking": mw["ranking"]}
    return {"target": target, "selection": board["multi_window_selection"], "n_windows": board["n_windows"],
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
