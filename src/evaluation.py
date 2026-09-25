"""Forecast accuracy metrics (computed on the original AQI scale)."""
from __future__ import annotations

import numpy as np


def forecast_metrics(y_true, y_pred, mask=None) -> dict:
    """RMSE, MSE, MAE and MAPE (%). ``mask`` selects which points to score."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    if mask is not None:
        mask = np.asarray(mask, dtype=bool)
        y_true, y_pred = y_true[mask], y_pred[mask]
    err = y_pred - y_true
    mse = float(np.mean(err ** 2))
    return {
        "rmse": float(np.sqrt(mse)),
        "mse": mse,
        "mae": float(np.mean(np.abs(err))),
        "mape": float(np.mean(np.abs(err) / np.abs(y_true)) * 100),
        "n_scored": int(len(y_true)),
    }
