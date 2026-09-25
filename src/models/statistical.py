"""Classical forecasters: ARIMA, SARIMA and Holt-Winters (statsmodels).

Each returns ``(forecast, description)`` where ``forecast`` is a length-``horizon``
array in the same space as ``train`` and ``description`` records the chosen config.

Why SARIMA uses weekly seasonality + Fourier terms
--------------------------------------------------
The dominant cycle in AQI is annual (~365 days), but a SARIMA with m=365 needs a
365-lag seasonal polynomial: fitting is extremely slow and numerically fragile on
~2,000 points. The standard remedy is used instead: SARIMA with weekly seasonality
(m=7) plus K pairs of annual Fourier terms as exogenous regressors
(regression with SARIMA errors).
"""
from __future__ import annotations

import functools
import itertools
import warnings

import numpy as np
import pandas as pd
from statsmodels.tools.sm_exceptions import ConvergenceWarning
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX

from src.preprocessing import stationarity_report

FOURIER_K = 3
ANNUAL = 365.25


def _silenced(fn):
    """Suppress statsmodels' convergence/frequency chatter during grid searches."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        with warnings.catch_warnings():
            for cat in (ConvergenceWarning, UserWarning, RuntimeWarning, FutureWarning):
                warnings.simplefilter("ignore", cat)
            return fn(*args, **kwargs)
    return wrapper


def _trend_for(d: int) -> str:
    return "c" if d == 0 else "n"


def select_arima_order(train: pd.Series, d: int, max_p: int = 3, max_q: int = 3):
    """Grid-search (p, q) by AIC for a fixed differencing order ``d``."""
    best = (np.inf, None)
    for p, q in itertools.product(range(max_p + 1), range(max_q + 1)):
        try:
            res = ARIMA(train.to_numpy(), order=(p, d, q), trend=_trend_for(d)).fit()
        except Exception:
            continue
        if res.mle_retvals and not res.mle_retvals.get("converged", True):
            continue
        if res.aic < best[0]:
            best = (res.aic, (p, d, q))
    if best[1] is None:
        raise RuntimeError("No ARIMA order converged")
    return best[1]


@_silenced
def arima_forecast(train: pd.Series, horizon: int):
    d = stationarity_report(train)["recommended_d"]
    order = select_arima_order(train, d)
    res = ARIMA(train.to_numpy(), order=order, trend=_trend_for(d)).fit()
    return res.forecast(horizon), f"ARIMA{order}"


def fourier_terms(index: pd.DatetimeIndex, k: int = FOURIER_K, period: float = ANNUAL) -> pd.DataFrame:
    t = (index - pd.Timestamp("2015-01-01")).days.to_numpy()
    cols = {}
    for i in range(1, k + 1):
        cols[f"sin{i}"] = np.sin(2 * np.pi * i * t / period)
        cols[f"cos{i}"] = np.cos(2 * np.pi * i * t / period)
    return pd.DataFrame(cols, index=index)


@_silenced
def sarima_forecast(train: pd.Series, horizon: int):
    d = stationarity_report(train)["recommended_d"]
    order = select_arima_order(train, d, max_p=2, max_q=2)
    future_idx = pd.date_range(train.index[-1] + pd.Timedelta(days=1), periods=horizon, freq="D")
    x_train, x_future = fourier_terms(train.index), fourier_terms(future_idx)

    best = (np.inf, None, None)
    for P, Q in [(1, 1), (1, 0), (0, 1)]:
        seasonal = (P, 0, Q, 7)
        try:
            res = SARIMAX(train.to_numpy(), exog=x_train.to_numpy(), order=order,
                          seasonal_order=seasonal, trend=_trend_for(d)).fit(disp=False)
        except Exception:
            continue
        if res.aic < best[0]:
            best = (res.aic, seasonal, res)
    if best[2] is None:
        raise RuntimeError("No SARIMA configuration could be fitted")
    _, seasonal, res = best
    fc = res.forecast(horizon, exog=x_future.to_numpy())
    return fc, f"SARIMA{order}x{seasonal} + {FOURIER_K} annual Fourier pairs"


@_silenced
def holt_winters_forecast(train: pd.Series, horizon: int):
    """Additive damped-trend Holt-Winters; seasonal period 365 vs 7 chosen by AIC."""
    y = train.to_numpy()
    best = (np.inf, None, None)
    for m in (365, 7):
        if len(y) < 2 * m:
            continue
        try:
            res = ExponentialSmoothing(y, trend="add", damped_trend=True, seasonal="add",
                                       seasonal_periods=m,
                                       initialization_method="heuristic").fit(optimized=True)
        except Exception:
            continue
        if res.aic < best[0]:
            best = (res.aic, m, res)
    if best[2] is None:
        raise RuntimeError("Holt-Winters failed for every seasonal period")
    _, m, res = best
    return res.forecast(horizon), f"Holt-Winters (add. damped trend, add. seasonal m={m})"
