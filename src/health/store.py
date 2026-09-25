"""Save and load the deployed health-risk models, and turn them into per-day risk.

Layout::

    models/health/registry.json
    models/health/<task>/<feature_set>/metadata.json         features, classes, metrics, versions
    models/health/<task>/<feature_set>/preprocessor.joblib   fitted ColumnTransformer (joblib)
    models/health/<task>/<feature_set>/<estimator file>      Random Forest / MLP: estimator.joblib
                                                             XGBoost: model.ubj (native save_model)

``task`` is ``classification`` (HealthRiskLevel) or ``regression`` (HealthRiskScore).
Two feature sets are deployed: ``aqi_pm25_no2`` (primary) and ``aqi_only`` (fallback,
used when a city has no PM2.5/NO2 forecast).

Reconciling the two models (the "boundary rule")
------------------------------------------------
The classifier and the regressor are trained separately, so near a level boundary
they can disagree (the score, cut at 1.0 / 1.8 / 2.8, implies a neighbouring level).
``predict`` returns:

* ``risk_level``: the classifier's level. It's the model selected for level accuracy
  (weighted F1), so it's the headline.
* ``borderline``: True when the score implies a different level.
* ``risk_range``: e.g. ``"Moderate-High"`` when borderline, else the level itself.
* ``alert_level``: the higher of the two levels. Use this for High/Severe actions
  (hospital map, precautions) so a borderline case is never under-alerted.

Backend usage::

    from src.health.store import load_health_predictor
    from src.model_store import forecast_air
    load_health_predictor().predict(profile, forecast_air("Delhi", 7))
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib.metadata import version

import joblib
import numpy as np
import pandas as pd

from src.data_loader import PROJECT_ROOT
from src.health.data import (AIR_COLUMNS, CATEGORIES, DEPLOY_FEATURE_SETS, FALLBACK_FEATURE_SET,
                             PRIMARY_FEATURE_SET, RISK_LEVELS, score_to_level)

HEALTH_MODELS_DIR = PROJECT_ROOT / "models" / "health"
REGISTRY_PATH = HEALTH_MODELS_DIR / "registry.json"
TASKS = ("classification", "regression")
LIBRARIES = ("scikit-learn", "xgboost", "numpy", "pandas", "joblib")


def _versions() -> dict:
    out = {}
    for lib in LIBRARIES:
        try:
            out[lib] = version(lib)
        except Exception:
            out[lib] = None
    return out


def _model_dir(task: str, feature_set: str):
    return HEALTH_MODELS_DIR / task / feature_set


def save_health_model(task: str, feature_set: str, model_name: str, pipeline, meta: dict) -> dict:
    """Save a fitted ``prep -> est`` pipeline: preprocessor via joblib, estimator natively."""
    out_dir = _model_dir(task, feature_set)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.iterdir():  # never leave a previous winner's files behind
        old.unlink()
    joblib.dump(pipeline.named_steps["prep"], out_dir / "preprocessor.joblib", compress=3)
    est = pipeline.named_steps["est"]
    if model_name == "XGBoost":
        est.save_model(out_dir / "model.ubj")
        est_file = "model.ubj"
    else:
        joblib.dump(est, out_dir / "estimator.joblib", compress=3)
        est_file = "estimator.joblib"
    meta = {"task": task, "feature_set": feature_set, "model": model_name,
            "files": ["preprocessor.joblib", est_file],
            "saved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            **meta, "library_versions": _versions()}
    (out_dir / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def write_registry(metas: list[dict], extra: dict | None = None):
    registry = {"updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "primary_feature_set": PRIMARY_FEATURE_SET, "fallback_feature_set": FALLBACK_FEATURE_SET,
                **(extra or {}), "models": {}}
    for m in metas:
        registry["models"].setdefault(m["task"], {})[m["feature_set"]] = {
            k: m[k] for k in ("model", "target", "files", "selection", "cv", "test", "saved_at")}
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2), encoding="utf-8")


@dataclass
class _LoadedModel:
    meta: dict
    prep: object
    est: object

    @property
    def features(self) -> list[str]:
        return self.meta["features"]["numeric"] + self.meta["features"]["categorical"]

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        return self.prep.transform(X[self.features])


def _load(task: str, feature_set: str) -> _LoadedModel:
    d = _model_dir(task, feature_set)
    meta_path = d / "metadata.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"No saved {task}/{feature_set} model (expected {meta_path}). "
                                "Run: python -m src.health.train")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    prep = joblib.load(d / "preprocessor.joblib")
    if meta["model"] == "XGBoost":
        from xgboost import XGBClassifier, XGBRegressor
        est = XGBClassifier() if task == "classification" else XGBRegressor()
        est.load_model(d / "model.ubj")
    else:
        est = joblib.load(d / "estimator.joblib")
    return _LoadedModel(meta, prep, est)


def reconcile(classifier_idx: np.ndarray, score: np.ndarray) -> pd.DataFrame:
    """Apply the boundary rule (see module docstring) to class indices and scores."""
    score_idx = np.array([RISK_LEVELS.index(v) for v in score_to_level(score)])
    lo, hi = np.minimum(classifier_idx, score_idx), np.maximum(classifier_idx, score_idx)
    levels = np.array(RISK_LEVELS)
    return pd.DataFrame({
        "risk_level": levels[classifier_idx],
        "score_level": levels[score_idx],
        "borderline": classifier_idx != score_idx,
        "risk_range": [str(levels[a]) if a == b else f"{levels[a]}-{levels[b]}" for a, b in zip(lo, hi)],
        "alert_level": levels[hi],
    })


class HealthRiskPredictor:
    """Combines a saved user profile with daily air-quality forecasts to give per-day risk."""

    def __init__(self, models: dict[tuple[str, str], _LoadedModel]):
        self.models = models

    def feature_set_for(self, air: pd.DataFrame) -> str:
        primary_air = {AIR_COLUMNS[c] for c in AIR_COLUMNS}
        have = {AIR_COLUMNS[c] for c in AIR_COLUMNS if c in air and air[c].notna().all()}
        return PRIMARY_FEATURE_SET if primary_air <= have else FALLBACK_FEATURE_SET

    def required_profile_fields(self, feature_set: str = PRIMARY_FEATURE_SET) -> list[str]:
        feats = set()
        for task in TASKS:
            feats |= set(self.models[(task, feature_set)].features)
        return sorted(feats - set(AIR_COLUMNS.values()))

    def build_inputs(self, profile: dict, air: pd.DataFrame, feature_set: str) -> pd.DataFrame:
        """One row per day: the profile repeated, with that day's air values."""
        fields = self.required_profile_fields(feature_set)
        missing = [f for f in fields if profile.get(f) is None]
        if missing:
            raise ValueError(f"Profile is missing fields: {missing}")
        bad = {f: profile[f] for f, allowed in CATEGORIES.items() if f in fields and profile[f] not in allowed}
        if bad:
            raise ValueError(f"Invalid profile values: {bad}; allowed: { {f: CATEGORIES[f] for f in bad} }")
        rows = pd.DataFrame({f: [profile[f]] * len(air) for f in fields})
        for col, feat in AIR_COLUMNS.items():
            if col in air:
                rows[feat] = air[col].to_numpy(dtype=float)
        return rows

    def predict(self, profile: dict, air: pd.DataFrame) -> pd.DataFrame:
        """``air``: DataFrame with ``date``, ``aqi`` and optionally ``pm25``, ``no2``
        (e.g. ``src.model_store.forecast_air``). Uses the pollutant model when both
        pollutant columns are present, otherwise the AQI-only fallback."""
        fs = self.feature_set_for(air)
        X = self.build_inputs(profile, air, fs)
        clf, reg = self.models[("classification", fs)], self.models[("regression", fs)]
        proba = clf.est.predict_proba(clf.transform(X))
        score = np.clip(reg.est.predict(reg.transform(X)), 0, None)
        out = pd.DataFrame({"date": air["date"].to_numpy()})
        for col in AIR_COLUMNS:
            if col in air:
                out[col] = air[col].to_numpy()
        rec = reconcile(proba.argmax(axis=1), score)
        out["risk_level"] = rec["risk_level"].to_numpy()
        out["confidence"] = proba.max(axis=1)
        for i, c in enumerate(clf.meta["classes"]):
            out[f"p_{c.lower()}"] = proba[:, i]
        out["risk_score"] = score
        for c in ("score_level", "borderline", "risk_range", "alert_level"):
            out[c] = rec[c].to_numpy()
        out["feature_set"] = fs
        return out


def load_health_predictor() -> HealthRiskPredictor:
    models = {(task, fs): _load(task, fs) for task in TASKS for fs in DEPLOY_FEATURE_SETS}
    for (task, fs), m in models.items():
        if task == "classification" and m.meta["classes"] != RISK_LEVELS:
            raise ValueError(f"Unexpected class order in saved {fs} classifier: {m.meta['classes']}")
    return HealthRiskPredictor(models)
