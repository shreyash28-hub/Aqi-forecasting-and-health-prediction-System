"""XGBoost on lag / rolling-window / calendar features, forecast recursively."""
from __future__ import annotations

import numpy as np
import pandas as pd
from xgboost import XGBRegressor

LAGS = [1, 2, 3, 4, 5, 6, 7, 14, 21, 28]
ROLL_WINDOWS = [7, 14, 30]
SEED = 42


def make_features(y: pd.Series) -> pd.DataFrame:
    """Features for predicting ``y[t]`` using only values up to ``t-1``."""
    X = pd.DataFrame(index=y.index)
    for lag in LAGS:
        X[f"lag_{lag}"] = y.shift(lag)
    past = y.shift(1)
    for w in ROLL_WINDOWS:
        X[f"roll_mean_{w}"] = past.rolling(w).mean()
        X[f"roll_std_{w}"] = past.rolling(w).std()
    X["diff_1"] = past.diff()
    doy = y.index.dayofyear
    X["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    X["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    X["dow"] = y.index.dayofweek
    X["month"] = y.index.month
    return X


def xgboost_forecast(train: pd.Series, horizon: int):
    X = make_features(train)
    ok = X.notna().all(axis=1)
    model = XGBRegressor(n_estimators=400, learning_rate=0.03, max_depth=4, subsample=0.8,
                         colsample_bytree=0.8, min_child_weight=5, random_state=SEED,
                         n_jobs=1)  # single thread: results depend on thread count otherwise
    model.fit(X[ok], train[ok])

    # Recursive multi-step: append each prediction and rebuild features for the next day.
    history = train.copy()
    preds = []
    for _ in range(horizon):
        next_day = history.index[-1] + pd.Timedelta(days=1)
        extended = pd.concat([history, pd.Series([np.nan], index=[next_day])])
        x_next = make_features(extended).iloc[[-1]]
        yhat = float(model.predict(x_next)[0])
        preds.append(yhat)
        history = pd.concat([history, pd.Series([yhat], index=[next_day])])
    return np.array(preds), (f"XGBoost recursive ({len(X.columns)} features: lags "
                             f"{LAGS[0]}-{LAGS[-1]}, rolling {ROLL_WINDOWS}, calendar)")
