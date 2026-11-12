# PM2.5 forecasting: evaluation summary

Generated 2026-11-12T03:57:19+00:00. Models fitted on log1p(PM2.5), scored on the original scale (observed days only). Horizon 30 days. Multi-window: 4 30-day test windows per city ending on 2025-11-30, 2025-12-30, 2026-01-29, 2026-02-28 (expanding training window). LSTM metrics are the mean of seeds [42, 43, 44]. Data: live CPCB station readings via OpenAQ (src/live_data.py). Models (not baselines) use the 2015-2020 seasonal prior.

## Multi-window results (primary)

Best model = lowest mean RMSE across windows. Win = lowest RMSE of all candidates (baselines included) in a window.

| City | Best model | Mean RMSE | Win rate | Beats baseline in | Most frequent window winner | Best baseline (mean RMSE) | Beats baseline |
|---|---|---|---|---|---|---|---|
| Ahmedabad | ARIMA | 15.85 | 25% | 50% | XGBoost | Seasonal naive (weekly) (23.45) | yes |
| Bengaluru | XGBoost | 16.03 | 50% | 75% | XGBoost | Seasonal naive (weekly) (20.56) | yes |
| Chennai | Prophet | 20.88 | 25% | 75% | XGBoost | Seasonal naive (weekly) (29.52) | yes |
| Delhi | XGBoost | 63.42 | 25% | 100% | LSTM | Seasonal naive (weekly) (85.43) | yes |
| Hyderabad | XGBoost | 7.83 | 25% | 50% | LSTM | Naive (last value) (9.76) | yes |
| Lucknow | Prophet | 18.79 | 50% | 100% | Prophet | Seasonal naive (weekly) (24.40) | yes |

### Win rate (share of 4 windows where the model had the lowest RMSE)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 25% | 0% | 25% | 0% | 25% | 0% |
| Seasonal naive (weekly) | 0% | 0% | 0% | 0% | 0% | 0% |
| ARIMA | 25% | 0% | 0% | 0% | 25% | 25% |
| SARIMA | 0% | 0% | 0% | 0% | 0% | 0% |
| Holt-Winters | 0% | 25% | 0% | 0% | 0% | 0% |
| LSTM | 0% | 25% | 0% | 50% | 25% | 0% |
| XGBoost | 50% | 50% | 50% | 25% | 25% | 25% |
| Prophet | 0% | 0% | 25% | 25% | 0% | 50% |

### Beat-baseline rate (share of windows beating that window's best baseline)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| ARIMA | 50% | 25% | 75% | 75% | 50% | 75% |
| SARIMA | 50% | 25% | 75% | 50% | 50% | 75% |
| Holt-Winters | 0% | 50% | 0% | 50% | 25% | 0% |
| LSTM | 75% | 25% | 75% | 50% | 25% | 50% |
| XGBoost | 75% | 75% | 75% | 100% | 50% | 75% |
| Prophet | 50% | 50% | 75% | 75% | 25% | 100% |

### Mean RMSE across windows

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 24.60 | 22.68 | 39.17 | 89.91 | 9.76 | 32.44 |
| Seasonal naive (weekly) | 23.45 | 20.56 | 29.52 | 85.43 | 10.27 | 24.40 |
| ARIMA | 15.85 | 18.94 | 24.23 | 70.90 | 8.72 | 23.72 |
| SARIMA | 16.20 | 18.99 | 24.06 | 71.32 | 8.77 | 23.75 |
| Holt-Winters | 26.02 | 20.55 | 40.03 | 76.97 | 9.26 | 33.32 |
| LSTM | 17.34 | 19.11 | 23.33 | 71.81 | 11.56 | 28.08 |
| XGBoost | 21.14 | 16.03 | 23.82 | 63.42 | 7.83 | 21.82 |
| Prophet | 18.70 | 17.00 | 20.88 | 70.70 | 11.89 | 18.79 |

### Mean rank across windows (1 = best of all candidates)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 5.0 | 6.2 | 5.8 | 6.5 | 4.5 | 6.8 |
| Seasonal naive (weekly) | 6.5 | 4.5 | 6.5 | 5.8 | 5.8 | 4.8 |
| ARIMA | 3.0 | 4.2 | 3.8 | 3.2 | 3.2 | 3.2 |
| SARIMA | 3.2 | 4.2 | 3.8 | 4.2 | 3.2 | 3.8 |
| Holt-Winters | 6.5 | 3.8 | 6.5 | 4.8 | 4.5 | 6.8 |
| LSTM | 3.8 | 4.5 | 4.0 | 3.8 | 4.5 | 5.2 |
| XGBoost | 3.8 | 3.5 | 3.0 | 3.0 | 4.0 | 3.5 |
| Prophet | 4.2 | 5.0 | 2.8 | 4.8 | 6.2 | 2.0 |

### Test windows

| City | Window 0 | Window 1 | Window 2 | Window 3 |
|---|---|---|---|---|
| Ahmedabad | w0: 2026-01-30 to 2026-02-28 | w1: 2025-12-31 to 2026-01-29 | w2: 2025-12-01 to 2025-12-30 | w3: 2025-11-01 to 2025-11-30 |
| Bengaluru | w0: 2026-01-30 to 2026-02-28 | w1: 2025-12-31 to 2026-01-29 | w2: 2025-12-01 to 2025-12-30 | w3: 2025-11-01 to 2025-11-30 |
| Chennai | w0: 2026-01-30 to 2026-02-28 | w1: 2025-12-31 to 2026-01-29 | w2: 2025-12-01 to 2025-12-30 | w3: 2025-11-01 to 2025-11-30 |
| Delhi | w0: 2026-01-30 to 2026-02-28 | w1: 2025-12-31 to 2026-01-29 | w2: 2025-12-01 to 2025-12-30 | w3: 2025-11-01 to 2025-11-30 |
| Hyderabad | w0: 2026-01-30 to 2026-02-28 | w1: 2025-12-31 to 2026-01-29 | w2: 2025-12-01 to 2025-12-30 | w3: 2025-11-01 to 2025-11-30 |
| Lucknow | w0: 2026-01-30 to 2026-02-28 | w1: 2025-12-31 to 2026-01-29 | w2: 2025-12-01 to 2025-12-30 | w3: 2025-11-01 to 2025-11-30 |

## Final 30-day hold-out only (window 0, kept for comparison)

| City | Window | Best model | RMSE | MAE | MAPE % | Best baseline (RMSE) | Beats baseline |
|---|---|---|---|---|---|---|---|
| Ahmedabad | 2026-01-30 to 2026-02-28 | XGBoost | 15.36 | 11.76 | 16.4 | Naive (last value) (15.99) | yes |
| Bengaluru | 2026-01-30 to 2026-02-28 | LSTM | 12.72 | 11.27 | 31.6 | Seasonal naive (weekly) (21.06) | yes |
| Chennai | 2026-01-30 to 2026-02-28 | XGBoost | 16.96 | 14.55 | 40.9 | Seasonal naive (weekly) (25.45) | yes |
| Delhi | 2026-01-30 to 2026-02-28 | LSTM | 22.98 | 16.07 | 13.4 | Naive (last value) (30.23) | yes |
| Hyderabad | 2026-01-30 to 2026-02-28 | LSTM | 3.78 | 2.98 | 7.0 | Seasonal naive (weekly) (4.73) | yes |
| Lucknow | 2026-01-30 to 2026-02-28 | ARIMA | 11.15 | 9.47 | 19.5 | Seasonal naive (weekly) (18.42) | yes |

### RMSE on the final hold-out

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 15.99 | 25.89 | 29.40 | 30.23 | 6.26 | 20.40 |
| Seasonal naive (weekly) | 22.25 | 21.06 | 25.45 | 44.58 | 4.73 | 18.42 |
| ARIMA | 17.18 | 13.91 | 18.44 | 24.77 | 4.50 | 11.15 |
| SARIMA | 16.96 | 13.89 | 18.62 | 25.09 | 4.23 | 11.23 |
| Holt-Winters | 21.35 | 27.33 | 31.09 | 24.79 | 5.75 | 25.03 |
| LSTM | 15.58 | 12.72 | 20.06 | 22.98 | 3.78 | 16.08 |
| XGBoost | 15.36 | 14.74 | 16.96 | 25.10 | 4.50 | 11.31 |
| Prophet | 16.09 | 14.03 | 18.86 | 25.16 | 4.25 | 11.77 |

### LSTM seed spread (std of RMSE across seeds, mean over windows)

| City | Mean seed std of RMSE |
|---|---|
| Ahmedabad | 0.91 |
| Bengaluru | 0.23 |
| Chennai | 0.49 |
| Delhi | 0.64 |
| Hyderabad | 0.20 |
| Lucknow | 0.72 |

## Stationarity (final training series)

| City | Span | Days | Interpolated | ADF p | KPSS p | ADF d | ACF@~7 | ACF@~365 (peak lag) | STL strength m=7 / 365 |
|---|---|---|---|---|---|---|---|---|---|
| Delhi | 2025-02-19 to 2026-10-29 | 618 | 43 | 0.5820 | 0.043 | 1 | 0.86 | nan (-) | 0.18 / nan |
| Bengaluru | 2025-02-19 to 2026-10-29 | 618 | 43 | 0.1163 | 0.019 | 1 | 0.79 | nan (-) | 0.02 / nan |
| Chennai | 2025-02-19 to 2026-10-29 | 618 | 45 | 0.1264 | 0.046 | 1 | 0.66 | nan (-) | 0.07 / nan |
| Hyderabad | 2025-02-19 to 2026-10-29 | 618 | 44 | 0.0014 | 0.010 | 0 | 0.66 | nan (-) | 0.09 / nan |
| Lucknow | 2025-02-19 to 2026-10-29 | 618 | 42 | 0.2204 | 0.042 | 1 | 0.71 | nan (-) | 0.07 / nan |
| Ahmedabad | 2025-02-19 to 2026-10-29 | 618 | 42 | 0.0085 | 0.084 | 0 | 0.69 | nan (-) | 0.03 / nan |

## Issues log

- **Ahmedabad / window 0 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 10 but size of corresponding boolean axis is 30`
- **Ahmedabad / window 1 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Ahmedabad / window 2 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Ahmedabad / window 3 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Bengaluru / window 0 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 10 but size of corresponding boolean axis is 30`
- **Bengaluru / window 1 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Bengaluru / window 2 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Bengaluru / window 3 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Chennai / window 0 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 10 but size of corresponding boolean axis is 30`
- **Chennai / window 1 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Chennai / window 2 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Chennai / window 3 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Delhi / window 0 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 10 but size of corresponding boolean axis is 30`
- **Delhi / window 1 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Delhi / window 2 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Delhi / window 3 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Hyderabad / window 0 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 10 but size of corresponding boolean axis is 30`
- **Hyderabad / window 1 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Hyderabad / window 2 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Hyderabad / window 3 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Lucknow / window 0 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 10 but size of corresponding boolean axis is 30`
- **Lucknow / window 1 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Lucknow / window 2 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- **Lucknow / window 3 / Seasonal naive (annual)** failed: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 0 but size of corresponding boolean axis is 30`
- Ahmedabad: never beat the baseline in any window: Holt-Winters
- Chennai: never beat the baseline in any window: Holt-Winters
- Lucknow: never beat the baseline in any window: Holt-Winters
