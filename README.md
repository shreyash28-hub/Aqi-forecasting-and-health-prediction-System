# AQI Forecasting Driven Health Prediction System

See `CLAUDE.md` for full project context.

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
```

## AQI forecasting pipeline

```bash
python -m src.data_loader        # sanity-check the cleaned per-city series
python -m src.run_forecasting    # 6 cities x 6 windows x all models, parallel (~10 min on CPU)
python -m src.run_forecasting --cities Delhi Lucknow --models ARIMA Prophet --windows 2
```

`city_day.csv` (and `city_hour.csv`, used to recompute Ahmedabad's AQI without CO) are
extracted from `data/Aqi.zip` automatically on first use.

Evaluation: every model is scored on 6 non-overlapping 30-day test windows per city
(rolling origin, 120 days apart; window 0 = the final 30 days) against three naive
baselines. The LSTM is averaged over seeds 42, 43 and 44.

| Path | Contents |
|---|---|
| `src/data_loader.py` | Load `city_day.csv`, filter to 6 cities, interpolate short gaps |
| `src/aqi.py` | CPCB AQI sub-indices; recompute daily AQI from hourly data (used for Ahmedabad without CO) |
| `src/preprocessing.py` | ADF/KPSS, ACF + STL seasonality checks, log transform, rolling-origin splits |
| `src/evaluation.py` | RMSE / MSE / MAE / MAPE |
| `src/models/` | Baselines, ARIMA/SARIMA/Holt-Winters, XGBoost, LSTM (PyTorch), Prophet |
| `src/run_forecasting.py` | Runs everything, writes `reports/forecasting/` and `reports/figures/` |

Outputs: `metrics.csv` (per window), `multiwindow_summary.csv` (win rates, mean metrics),
`lstm_seed_runs.csv`, `leaderboard.json`, `forecasts.csv` and `stationarity.csv`, plus the
generated `summary.md`. The written analysis is in `reports/forecasting/findings.md`.
