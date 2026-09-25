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
python -m src.run_forecasting    # all 6 cities x all models (~3 min on CPU)
python -m src.run_forecasting --cities Delhi Lucknow --models ARIMA Prophet
```

`city_day.csv` is extracted from `data/Aqi.zip` automatically on first use.

| Path | Contents |
|---|---|
| `src/data_loader.py` | Load `city_day.csv`, filter to 6 cities, interpolate short gaps |
| `src/preprocessing.py` | ADF/KPSS, ACF + STL seasonality checks, log transform, train/test split |
| `src/evaluation.py` | RMSE / MSE / MAE / MAPE |
| `src/models/` | Baselines, ARIMA/SARIMA/Holt-Winters, XGBoost, LSTM (PyTorch), Prophet |
| `src/run_forecasting.py` | Runs everything, writes `reports/forecasting/` and `reports/figures/` |

Outputs: `metrics.csv`, `leaderboard.json`, `forecasts.csv` and `stationarity.csv`, plus the
generated `summary.md`. The written analysis is in `reports/forecasting/findings.md`.
