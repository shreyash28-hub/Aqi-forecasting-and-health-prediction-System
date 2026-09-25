"""Stationarity diagnostics, seasonal-period check, transforms and train/test split."""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.stattools import acf, adfuller, kpss

TEST_DAYS = 30


def adf_test(s: pd.Series) -> dict:
    with warnings.catch_warnings():  # statsmodels 0.15 FutureWarning about the return type
        warnings.simplefilter("ignore", FutureWarning)
        stat, p, lags, nobs, crit, _ = adfuller(s.dropna(), autolag="AIC")
    return {"adf_stat": stat, "adf_p": p, "adf_lags": lags, "adf_crit_5": crit["5%"]}


def kpss_test(s: pd.Series) -> dict:
    with warnings.catch_warnings():  # KPSS warns when p is outside its lookup table
        warnings.simplefilter("ignore")
        stat, p, _, _ = kpss(s.dropna(), regression="c", nlags="auto")
    return {"kpss_stat": stat, "kpss_p": p}


def stationarity_report(s: pd.Series, alpha: float = 0.05) -> dict:
    """ADF (H0: unit root) + KPSS (H0: stationary) on the level and first difference.

    ``d`` is the recommended differencing order: 0 if ADF rejects a unit root on the
    level series, otherwise 1 (the first difference is checked to confirm).
    """
    level = {**adf_test(s), **kpss_test(s)}
    diff = {f"diff_{k}": v for k, v in {**adf_test(s.diff()), **kpss_test(s.diff())}.items()}
    adf_stationary = level["adf_p"] < alpha
    kpss_stationary = level["kpss_p"] > alpha
    return {
        **level, **diff,
        "adf_says_stationary": adf_stationary,
        "kpss_says_stationary": kpss_stationary,
        "recommended_d": 0 if adf_stationary else 1,
    }


def dominant_seasonal_period(s: pd.Series, candidates=(7, 30, 182, 365), window: int = 5) -> dict:
    """ACF of the detrended series at candidate lags (best value within +/- ``window`` days).

    The trend is removed with a centred 365-day moving average, which averages out
    the annual cycle itself, so the annual seasonality survives in the residual.
    """
    detrended = s - s.rolling(365, center=True, min_periods=180).mean()
    nlags = min(max(candidates) + window, len(s) // 2)
    r = acf(detrended.dropna(), nlags=nlags, fft=True)
    out = {}
    for lag in candidates:
        if lag + window <= nlags:
            lo, hi = max(1, lag - window), lag + window
            best = int(np.argmax(r[lo:hi + 1])) + lo
            out[f"acf_{lag}"] = float(r[best])
            out[f"acf_{lag}_peak_lag"] = best
    return out


def seasonal_strength(s: pd.Series, period: int) -> float:
    """STL seasonal strength F_s = max(0, 1 - Var(R) / Var(S + R)) (Hyndman & Athanasopoulos).

    ~0 = no seasonality at this period, ~1 = seasonality dominates the remainder.
    """
    res = STL(s.dropna().to_numpy(), period=period, robust=True).fit()
    return float(max(0.0, 1 - np.var(res.resid) / np.var(res.seasonal + res.resid)))


def train_test_split(df: pd.DataFrame, test_days: int = TEST_DAYS):
    """Chronological split: everything except the final ``test_days`` rows is train."""
    return df.iloc[:-test_days], df.iloc[-test_days:]


# AQI is strictly positive and right-skewed; models are fitted on log1p(AQI).
def to_model_space(s: pd.Series) -> pd.Series:
    return np.log1p(s)


def from_model_space(s):
    return np.expm1(s)
