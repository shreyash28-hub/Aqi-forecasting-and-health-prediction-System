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
python -m src.train_final_models # retrain each city's winner on full history, save to models/aqi/
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
| `src/train_final_models.py` | Retrains each city's multi-window winner on its full history and saves it |
| `src/model_store.py` | Save/load the deployed models; `load_forecaster(city).forecast(7 or 30)` |

Outputs: `metrics.csv` (per window), `multiwindow_summary.csv` (win rates, mean metrics),
`lstm_seed_runs.csv`, `leaderboard.json`, `forecasts.csv` and `stationarity.csv`, plus the
generated `summary.md`. The written analysis is in `reports/forecasting/findings.md`.

### Saved models (`models/aqi/`)

One folder per city with the winning model (lowest mean RMSE over the multi-window
evaluation), retrained on the city's full history, in its native format:
statsmodels results via joblib (ARIMA, SARIMA, Holt-Winters), XGBoost `save_model`
(`.ubj`), PyTorch `state_dict` per seed (LSTM, served as a 3-seed average) and Prophet's
JSON serialization. `metadata.json` holds the config, training span, forecast origin,
evaluation metrics and library versions; `registry.json` indexes all cities.

```python
from src.model_store import load_forecaster
load_forecaster("Delhi").forecast(7)   # DataFrame of date, aqi. No retraining.
```

Pickled statsmodels models are only guaranteed to load with the library versions in
`metadata.json`, so the backend should pin the same versions (see `requirements.txt`).
If a load fails after an upgrade, rerun `python -m src.train_final_models`.

## Pollutant forecasts (PM2.5, NO2)

The same evaluation and deployment pipeline runs for PM2.5 and NO2, which the health
model uses alongside AQI (the only pollutants with usable history in all six cities):

```bash
python -m src.run_forecasting --target PM2.5      # -> reports/forecasting/pm25/
python -m src.run_forecasting --target NO2        # -> reports/forecasting/no2/
python -m src.train_final_models --target PM2.5   # -> models/pm25/
python -m src.train_final_models --target NO2     # -> models/no2/
```

If no model beats the best naive baseline on mean RMSE for a city, the baseline itself is
deployed (currently Hyderabad PM2.5 and Ahmedabad NO2). `forecast_air(city, horizon)`
returns AQI, PM2.5 and NO2 forecasts together.

## Health-risk models

```bash
python -m src.health.train      # train, evaluate, select and save (~3-10 min on CPU)
python -m src.health.backtest   # health models fed real forecasts vs measured air
```

Random Forest, XGBoost and an MLP are trained for the risk level (classification,
selected by weighted F1) and the risk score (regression, selected by RMSE). Selection
uses 5-fold stratified CV on an 80% split; the 20% test split gives the reported
metrics; each winner is then refitted on all rows and saved to `models/health/`
(preprocessor via joblib, estimator via joblib or XGBoost `.ubj`).

Two variants are deployed: **profile + AQI + PM2.5 + NO2** (primary) and **profile + AQI**
(fallback when a pollutant forecast is missing). Results: `reports/health/summary.md`
and `reports/health/forecast_backtest.md`.

```python
from src.model_store import forecast_air
from src.health.store import load_health_predictor
risk = load_health_predictor().predict(profile, forecast_air("Delhi", 7))
```

Per day it returns `risk_level` (classifier, the headline), `confidence` and
`p_low..p_severe`, `risk_score`, and the boundary rule's outputs: `borderline` (the
score implies a neighbouring level), `risk_range` (e.g. `Moderate-High`) and
`alert_level` (the higher level, used for High/Severe actions such as the hospital map).

| Path | Contents |
|---|---|
| `src/health/data.py` | Dataset loading, feature sets, excluded (leaky) columns, category lists |
| `src/health/models.py` | Preprocessing + Random Forest / XGBoost / MLP builders |
| `src/health/train.py` | CV selection, test evaluation, boundary-rule evaluation, final refit and save |
| `src/health/store.py` | Save/load; `HealthRiskPredictor.predict(profile, air_forecast)` |
| `src/health/backtest.py` | Health models on forecast inputs vs measured air |
