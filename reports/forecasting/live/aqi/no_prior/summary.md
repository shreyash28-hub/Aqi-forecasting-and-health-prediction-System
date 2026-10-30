# AQI forecasting: evaluation summary

Generated 2026-10-30T13:55:03+00:00. Models fitted on log1p(AQI), scored on the original scale (observed days only). Horizon 30 days. Multi-window: 5 non-overlapping 30-day test windows per city, stepping back 45 days from the end (expanding training window); window 0 is the final hold-out. LSTM metrics are the mean of seeds None. Data: live CPCB station readings via OpenAQ (src/live_data.py).

## Multi-window results (primary)

Best model = lowest mean RMSE across windows. Win = lowest RMSE of all candidates (baselines included) in a window.

| City | Best model | Mean RMSE | Win rate | Beats baseline in | Most frequent window winner | Best baseline (mean RMSE) | Beats baseline |
|---|---|---|---|---|---|---|---|
| Ahmedabad | Prophet | 22.25 | 0% | 40% | Naive (last value) | Naive (last value) (22.35) | yes |
| Bengaluru | Prophet | 19.34 | 40% | 60% | Naive (last value) | Naive (last value) (27.04) | yes |
| Chennai | Holt-Winters | 20.03 | 20% | 20% | Naive (last value) | Naive (last value) (19.50) | **no** |
| Delhi | Prophet | 55.85 | 0% | 20% | XGBoost | Seasonal naive (weekly) (59.61) | yes |
| Hyderabad | Holt-Winters | 11.04 | 20% | 20% | Seasonal naive (annual) | Naive (last value) (10.28) | **no** |
| Lucknow | XGBoost | 24.30 | 20% | 40% | Naive (last value) | Naive (last value) (27.82) | yes |

### Win rate (share of 5 windows where the model had the lowest RMSE)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 40% | 40% | 40% | 20% | 20% | 40% |
| Seasonal naive (weekly) | 0% | 0% | 20% | 20% | 0% | 0% |
| Seasonal naive (annual) | 0% | 0% | 20% | 0% | 20% | 0% |
| ARIMA | 40% | 20% | 0% | 20% | 20% | 20% |
| Holt-Winters | 0% | 0% | 20% | 20% | 20% | 20% |
| XGBoost | 20% | 0% | 0% | 20% | 20% | 20% |
| Prophet | 0% | 40% | 0% | 0% | 0% | 0% |

### Beat-baseline rate (share of windows beating that window's best baseline)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| ARIMA | 40% | 40% | 0% | 20% | 20% | 40% |
| Holt-Winters | 0% | 20% | 20% | 40% | 20% | 40% |
| XGBoost | 20% | 20% | 0% | 20% | 20% | 40% |
| Prophet | 40% | 60% | 0% | 20% | 0% | 20% |

### Mean RMSE across windows

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 22.35 | 27.04 | 19.50 | 63.13 | 10.28 | 27.82 |
| Seasonal naive (weekly) | 27.58 | 27.16 | 21.04 | 59.61 | 15.51 | 32.68 |
| Seasonal naive (annual) | 45.43 | 29.68 | 29.43 | 61.75 | 18.80 | 38.23 |
| ARIMA | 23.36 | 23.90 | 20.09 | 60.31 | 12.92 | 28.79 |
| Holt-Winters | 23.94 | 25.72 | 20.03 | 65.77 | 11.04 | 27.69 |
| XGBoost | 27.41 | 29.16 | 20.75 | 60.69 | 11.36 | 24.30 |
| Prophet | 22.25 | 19.34 | 21.69 | 55.85 | 15.38 | 28.25 |

### Mean rank across windows (1 = best of all candidates)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 2.2 | 3.8 | 2.6 | 3.0 | 1.8 | 3.2 |
| Seasonal naive (weekly) | 5.0 | 4.2 | 4.2 | 4.0 | 5.4 | 5.6 |
| Seasonal naive (annual) | 6.8 | 5.8 | 5.8 | 5.2 | 5.2 | 5.6 |
| ARIMA | 2.8 | 3.2 | 3.4 | 3.0 | 4.2 | 3.6 |
| Holt-Winters | 3.6 | 3.4 | 3.4 | 3.6 | 2.4 | 2.8 |
| XGBoost | 4.2 | 5.2 | 3.8 | 5.2 | 3.6 | 3.0 |
| Prophet | 3.4 | 2.4 | 4.8 | 4.0 | 5.4 | 4.2 |

### Test windows

| City | Window 0 | Window 1 | Window 2 | Window 3 | Window 4 |
|---|---|---|---|---|---|
| Ahmedabad | w0: 2026-09-30 to 2026-10-29 | w1: 2026-08-16 to 2026-09-14 | w2: 2026-07-02 to 2026-07-31 | w3: 2026-05-18 to 2026-06-16 | w4: 2026-04-03 to 2026-05-02 |
| Bengaluru | w0: 2026-09-30 to 2026-10-29 | w1: 2026-08-16 to 2026-09-14 | w2: 2026-07-02 to 2026-07-31 | w3: 2026-05-18 to 2026-06-16 | w4: 2026-04-03 to 2026-05-02 |
| Chennai | w0: 2026-09-30 to 2026-10-29 | w1: 2026-08-16 to 2026-09-14 | w2: 2026-07-02 to 2026-07-31 | w3: 2026-05-18 to 2026-06-16 | w4: 2026-04-03 to 2026-05-02 |
| Delhi | w0: 2026-09-30 to 2026-10-29 | w1: 2026-08-16 to 2026-09-14 | w2: 2026-07-02 to 2026-07-31 | w3: 2026-05-18 to 2026-06-16 | w4: 2026-04-03 to 2026-05-02 |
| Hyderabad | w0: 2026-09-30 to 2026-10-29 | w1: 2026-08-16 to 2026-09-14 | w2: 2026-07-02 to 2026-07-31 | w3: 2026-05-18 to 2026-06-16 | w4: 2026-04-03 to 2026-05-02 |
| Lucknow | w0: 2026-09-30 to 2026-10-29 | w1: 2026-08-16 to 2026-09-14 | w2: 2026-07-02 to 2026-07-31 | w3: 2026-05-18 to 2026-06-16 | w4: 2026-04-03 to 2026-05-02 |

## Final 30-day hold-out only (window 0, kept for comparison)

| City | Window | Best model | RMSE | MAE | MAPE % | Best baseline (RMSE) | Beats baseline |
|---|---|---|---|---|---|---|---|
| Ahmedabad | 2026-09-30 to 2026-10-29 | XGBoost | 28.50 | 21.10 | 14.6 | Seasonal naive (weekly) (38.91) | yes |
| Bengaluru | 2026-09-30 to 2026-10-29 | Holt-Winters | 26.87 | 23.21 | 26.6 | Naive (last value) (26.30) | **no** |
| Chennai | 2026-09-30 to 2026-10-29 | ARIMA | 23.20 | 17.48 | 22.5 | Seasonal naive (weekly) (22.47) | **no** |
| Delhi | 2026-09-30 to 2026-10-29 | XGBoost | 42.91 | 36.82 | 22.3 | Seasonal naive (annual) (70.99) | yes |
| Hyderabad | 2026-09-30 to 2026-10-29 | Holt-Winters | 21.86 | 20.43 | 24.6 | Seasonal naive (annual) (16.35) | **no** |
| Lucknow | 2026-09-30 to 2026-10-29 | Holt-Winters | 28.40 | 22.33 | 24.5 | Naive (last value) (24.27) | **no** |

### RMSE on the final hold-out

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 43.81 | 26.30 | 24.79 | 129.50 | 18.44 | 24.27 |
| Seasonal naive (weekly) | 38.91 | 35.10 | 22.47 | 93.96 | 27.31 | 39.11 |
| Seasonal naive (annual) | 76.65 | 37.07 | 56.00 | 70.99 | 16.35 | 70.84 |
| ARIMA | 49.24 | 32.46 | 23.20 | 112.23 | 23.49 | 33.11 |
| Holt-Winters | 47.10 | 26.87 | 24.89 | 137.66 | 21.86 | 28.40 |
| XGBoost | 28.50 | 32.04 | 29.32 | 42.91 | 22.30 | 29.03 |
| Prophet | 29.05 | 30.78 | 30.07 | 67.57 | 22.81 | 33.85 |

## Stationarity (final training series)

| City | Span | Days | Interpolated | ADF p | KPSS p | ADF d | ACF@~7 | ACF@~365 (peak lag) | STL strength m=7 / 365 |
|---|---|---|---|---|---|---|---|---|---|
| Delhi | 2025-02-20 to 2026-10-29 | 617 | 45 | 0.4460 | 0.044 | 1 | 0.85 | nan (-) | 0.06 / nan |
| Bengaluru | 2025-02-20 to 2026-10-29 | 617 | 46 | 0.0231 | 0.038 | 0 | 0.74 | nan (-) | 0.03 / nan |
| Chennai | 2025-02-20 to 2026-10-29 | 617 | 45 | 0.0265 | 0.100 | 0 | 0.61 | nan (-) | 0.12 / nan |
| Hyderabad | 2025-02-20 to 2026-10-29 | 617 | 45 | 0.1367 | 0.010 | 1 | 0.81 | nan (-) | 0.10 / nan |
| Lucknow | 2025-02-20 to 2026-10-29 | 617 | 44 | 0.2135 | 0.080 | 1 | 0.70 | nan (-) | 0.00 / nan |
| Ahmedabad | 2025-02-20 to 2026-10-29 | 617 | 44 | 0.0155 | 0.075 | 0 | 0.64 | nan (-) | 0.03 / nan |

## Issues log

- Ahmedabad: never beat the baseline in any window: Holt-Winters
- Chennai: never beat the baseline in any window: ARIMA, XGBoost, Prophet
- Hyderabad: never beat the baseline in any window: Prophet
