"""Facebook Prophet with yearly + weekly seasonality."""
from __future__ import annotations

import logging

import pandas as pd

# Prophet logs an error at import when plotly (only used for its interactive plots) is absent.
logging.getLogger("prophet.plot").disabled = True
from prophet import Prophet  # noqa: E402



def fit_prophet(train: pd.Series):
    """Returns ``(model, config)``."""
    # cmdstanpy (re)configures its INFO handler lazily on first use, so a level set at
    # import time doesn't stick; disabling the logger does.
    logging.getLogger("cmdstanpy").disabled = True
    logging.getLogger("prophet").setLevel(logging.WARNING)
    df = pd.DataFrame({"ds": train.index, "y": train.to_numpy()})
    model = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False,
                    seasonality_mode="additive", changepoint_prior_scale=0.05)
    model.fit(df)
    return model, "Prophet (yearly + weekly, additive)"


def predict_prophet(model: Prophet, horizon: int):
    future = model.make_future_dataframe(periods=horizon, freq="D", include_history=False)
    return model.predict(future)["yhat"].to_numpy()


def prophet_forecast(train: pd.Series, horizon: int):
    model, config = fit_prophet(train)
    return predict_prophet(model, horizon), config
