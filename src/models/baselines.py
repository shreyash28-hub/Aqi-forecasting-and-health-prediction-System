"""Naive baselines every forecaster has to beat.

All forecasters in ``src.models`` share one signature:
``fn(train: pd.Series, horizon: int) -> np.ndarray`` of length ``horizon``,
with ``train`` a daily series (already in model space, i.e. log1p AQI).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def naive_last(train: pd.Series, horizon: int) -> np.ndarray:
    """Repeat the last observed value."""
    return np.repeat(train.iloc[-1], horizon)


def _seasonal_naive(train: pd.Series, horizon: int, m: int) -> np.ndarray:
    last_season = train.iloc[-m:].to_numpy()
    return np.resize(last_season, horizon) if horizon > m else last_season[:horizon]


def seasonal_naive_weekly(train: pd.Series, horizon: int) -> np.ndarray:
    """Same weekday last week."""
    return _seasonal_naive(train, horizon, 7)


def seasonal_naive_annual(train: pd.Series, horizon: int) -> np.ndarray:
    """Same calendar day one year (365 days) earlier."""
    return train.iloc[-365:-365 + horizon].to_numpy()


BASELINES = {
    "Naive (last value)": naive_last,
    "Seasonal naive (weekly)": seasonal_naive_weekly,
    "Seasonal naive (annual)": seasonal_naive_annual,
}
