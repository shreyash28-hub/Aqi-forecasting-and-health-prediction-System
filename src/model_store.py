"""Save and load the deployed per-city AQI forecasters.

Layout::

    models/aqi/registry.json            one entry per city: model, files, metrics
    models/aqi/<city>/metadata.json     everything needed to forecast (see below)
    models/aqi/<city>/<model file(s)>   native format per model type:
        ARIMA / SARIMA / Holt-Winters   model.joblib        (statsmodels results, joblib)
        XGBoost                         model.ubj           (XGBoost native save_model)
        LSTM                            lstm_seed<N>.pt     (PyTorch state_dict, one per seed)
        Prophet                         model.json          (prophet.serialize.model_to_json)

All models work in log1p(AQI) space; ``AQIForecaster.forecast`` returns AQI.
``metadata.json`` records the training span, the forecast origin (last training
date), model hyper-parameters, the recent history the recursive/sequence models
need (XGBoost, LSTM), and library versions, since pickled statsmodels objects are
only guaranteed to load under the same versions.

Backend usage::

    from src.model_store import load_forecaster
    fc = load_forecaster("Delhi")
    fc.forecast(7)     # DataFrame: date, aqi   (days after fc.last_train_date)
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.data_loader import AQI_EXCLUDED_POLLUTANTS, PROJECT_ROOT
from src.preprocessing import TEST_DAYS, from_model_space, to_model_space

MODELS_DIR = PROJECT_ROOT / "models" / "aqi"
REGISTRY_PATH = MODELS_DIR / "registry.json"
STATSMODELS_TYPES = ("ARIMA", "SARIMA", "Holt-Winters")
SUPPORTED = (*STATSMODELS_TYPES, "XGBoost", "LSTM", "Prophet")
LIBRARIES = ("pandas", "numpy", "statsmodels", "xgboost", "torch", "prophet", "scikit-learn", "joblib")


def _city_dir(city: str) -> Path:
    return MODELS_DIR / city.lower()


def _series_payload(s: pd.Series) -> dict:
    return {"dates": [d.date().isoformat() for d in s.index], "values": [float(v) for v in s]}


def _series_from_payload(p: dict) -> pd.Series:
    return pd.Series(p["values"], index=pd.DatetimeIndex(pd.to_datetime(p["dates"]), freq="D"))


def _versions() -> dict:
    out = {}
    for lib in LIBRARIES:
        try:
            out[lib] = version(lib)
        except Exception:
            out[lib] = None
    return out


# --------------------------------------------------------------------------- fit + save

def fit_and_save(city: str, model_name: str, series: pd.DataFrame, eval_info: dict | None = None,
                 max_horizon: int = TEST_DAYS):
    """Fit ``model_name`` on the city's full history and save it.

    Returns ``(metadata, in_memory_forecaster)``; the latter lets callers check that
    the saved files reproduce the freshly trained model exactly.

    ``series`` is the cleaned frame from ``load_city_series`` (``aqi`` column).
    """
    if model_name not in SUPPORTED:
        raise ValueError(f"Unsupported model {model_name!r}; expected one of {SUPPORTED}")
    y = to_model_space(series["aqi"])
    out_dir = _city_dir(city)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.iterdir():  # never leave a previous winner's files behind
        old.unlink()

    params: dict = {}
    if model_name == "ARIMA":
        from src.models.statistical import fit_arima
        res, config = fit_arima(y)
        fitted = res
        joblib.dump(res, out_dir / "model.joblib", compress=3)
        files = ["model.joblib"]
    elif model_name == "SARIMA":
        from src.models.statistical import ANNUAL, FOURIER_K, fit_sarima
        res, config = fit_sarima(y)
        fitted = res
        joblib.dump(res, out_dir / "model.joblib", compress=3)
        files = ["model.joblib"]
        params = {"fourier_k": FOURIER_K, "fourier_period": ANNUAL, "fourier_origin": "2015-01-01"}
    elif model_name == "Holt-Winters":
        from src.models.statistical import fit_holt_winters
        res, config = fit_holt_winters(y)
        fitted = res
        joblib.dump(res, out_dir / "model.joblib", compress=3)
        files = ["model.joblib"]
    elif model_name == "XGBoost":
        from src.models.ml_models import MIN_HISTORY, fit_xgboost
        model, config = fit_xgboost(y)
        fitted = model
        model.save_model(out_dir / "model.ubj")
        files = ["model.ubj"]
        params = {"history": _series_payload(y.iloc[-MIN_HISTORY:])}
    elif model_name == "LSTM":
        import torch
        from src.models.deep_models import HIDDEN, LOOKBACK, LSTM_SEEDS, fit_lstm
        files, scalers, fitted = [], {}, []
        for seed in LSTM_SEEDS:
            model, scaler, config = fit_lstm(y, max_horizon, seed)
            name = f"lstm_seed{seed}.pt"
            torch.save(model.state_dict(), out_dir / name)
            fitted.append(model)
            files.append(name)
            scalers[str(seed)] = scaler
        config = config.rsplit(", seed=", 1)[0] + f", ensemble of seeds {list(LSTM_SEEDS)}"
        params = {"seeds": list(LSTM_SEEDS), "scalers": scalers, "hidden": HIDDEN,
                  "lookback": LOOKBACK, "n_features": 3, "horizon": max_horizon,
                  "history": _series_payload(y.iloc[-LOOKBACK:])}
    else:  # Prophet
        from src.models.prophet_model import fit_prophet  # first: quietens prophet's import logging
        from prophet.serialize import model_to_json
        model, config = fit_prophet(y)
        fitted = model
        (out_dir / "model.json").write_text(model_to_json(model), encoding="utf-8")
        files = ["model.json"]

    meta = {
        "city": city,
        "model": model_name,
        "config": config,
        "files": files,
        "transform": "log1p",
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "train_start": series.index[0].date().isoformat(),
        "train_end": series.index[-1].date().isoformat(),
        "last_train_date": series.index[-1].date().isoformat(),
        "n_train": len(series),
        "max_horizon": max_horizon,
        "aqi_excluded_pollutants": list(AQI_EXCLUDED_POLLUTANTS.get(city, ())),
        "evaluation": eval_info or {},
        "params": params,
        "library_versions": _versions(),
    }
    (out_dir / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta, AQIForecaster(city, model_name, meta, fitted)


def write_registry(metas: list[dict]):
    registry = {"task": "aqi_forecast", "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "cities": {}}
    if REGISTRY_PATH.exists():  # keep cities not retrained in this run
        registry["cities"] = json.loads(REGISTRY_PATH.read_text(encoding="utf-8")).get("cities", {})
    for m in metas:
        registry["cities"][m["city"]] = {
            "model": m["model"], "config": m["config"],
            "dir": _city_dir(m["city"]).relative_to(PROJECT_ROOT).as_posix(),
            "files": m["files"], "trained_at": m["trained_at"],
            "train_start": m["train_start"], "train_end": m["train_end"],
            "max_horizon": m["max_horizon"], "evaluation": m["evaluation"],
        }
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2), encoding="utf-8")


# --------------------------------------------------------------------------- load + forecast

@dataclass
class AQIForecaster:
    city: str
    model_name: str
    meta: dict
    model: object  # statsmodels results / XGBRegressor / list of LSTM modules / Prophet

    @property
    def last_train_date(self) -> pd.Timestamp:
        return pd.Timestamp(self.meta["last_train_date"])

    def forecast(self, horizon: int = 7) -> pd.DataFrame:
        """AQI for the ``horizon`` days after ``last_train_date``."""
        if not 1 <= horizon <= self.meta["max_horizon"]:
            raise ValueError(f"horizon must be 1..{self.meta['max_horizon']}")
        p = self.meta["params"]
        if self.model_name in ("ARIMA", "Holt-Winters"):
            yhat = np.asarray(self.model.forecast(horizon))
        elif self.model_name == "SARIMA":
            from src.models.statistical import predict_sarima
            yhat = predict_sarima(self.model, self.last_train_date, horizon)
        elif self.model_name == "XGBoost":
            from src.models.ml_models import predict_xgboost
            yhat = predict_xgboost(self.model, _series_from_payload(p["history"]), horizon)
        elif self.model_name == "LSTM":
            from src.models.deep_models import predict_lstm
            history = _series_from_payload(p["history"])
            runs = [predict_lstm(m, p["scalers"][str(s)], history) for s, m in zip(p["seeds"], self.model)]
            yhat = np.mean(runs, axis=0)[:horizon]
        else:
            from src.models.prophet_model import predict_prophet
            yhat = predict_prophet(self.model, horizon)
        dates = pd.date_range(self.last_train_date + pd.Timedelta(days=1), periods=horizon, freq="D")
        aqi = np.clip(from_model_space(np.asarray(yhat, dtype=float)), 0, None)
        return pd.DataFrame({"date": dates, "aqi": aqi})


def load_forecaster(city: str) -> AQIForecaster:
    """Load a saved city model; no retraining."""
    d = _city_dir(city)
    meta_path = d / "metadata.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"No saved model for {city!r} (expected {meta_path}). "
                                "Run: python -m src.train_final_models")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    name = meta["model"]
    if name in STATSMODELS_TYPES:
        model = joblib.load(d / "model.joblib")
    elif name == "XGBoost":
        from xgboost import XGBRegressor
        model = XGBRegressor()
        model.load_model(d / "model.ubj")
    elif name == "LSTM":
        import torch
        from src.models.deep_models import LSTMForecaster
        p = meta["params"]
        model = []
        for f in meta["files"]:
            net = LSTMForecaster(p["horizon"], n_features=p["n_features"], hidden=p["hidden"])
            net.load_state_dict(torch.load(d / f, weights_only=True))
            net.eval()
            model.append(net)
    elif name == "Prophet":
        import src.models.prophet_model  # noqa: F401  (quietens prophet's import logging)
        from prophet.serialize import model_from_json
        model = model_from_json((d / "model.json").read_text(encoding="utf-8"))
    else:
        raise ValueError(f"Unknown model type {name!r} in {meta_path}")
    return AQIForecaster(city, name, meta, model)


def saved_cities() -> list[str]:
    if not REGISTRY_PATH.exists():
        return []
    return list(json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))["cities"])
