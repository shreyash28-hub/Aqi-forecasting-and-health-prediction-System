# NO2 forecasting: evaluation summary

Generated 2026-11-12T03:59:29+00:00. Models fitted on log1p(NO2), scored on the original scale (observed days only). Horizon 30 days. Multi-window: 4 30-day test windows per city ending on 2025-11-30, 2025-12-30, 2026-01-29, 2026-02-28 (expanding training window). LSTM metrics are the mean of seeds [42, 43, 44]. Data: live CPCB station readings via OpenAQ (src/live_data.py). Models (not baselines) use the 2015-2020 seasonal prior.

## Multi-window results (primary)

Best model = lowest mean RMSE across windows. Win = lowest RMSE of all candidates (baselines included) in a window.

| City | Best model | Mean RMSE | Win rate | Beats baseline in | Most frequent window winner | Best baseline (mean RMSE) | Beats baseline |
|---|---|---|---|---|---|---|---|
| Ahmedabad | XGBoost | 16.92 | 50% | 50% | XGBoost | Seasonal naive (weekly) (16.25) | **no** |
| Bengaluru | ARIMA | 7.19 | 0% | 50% | Naive (last value) | Naive (last value) (6.13) | **no** |
| Chennai | LSTM | 1.57 | 25% | 75% | Naive (last value) | Naive (last value) (1.93) | yes |
| Delhi | SARIMA | 7.12 | 75% | 100% | SARIMA | Seasonal naive (weekly) (12.98) | yes |
| Hyderabad | Prophet | 2.05 | 50% | 50% | Prophet | Naive (last value) (2.14) | yes |
| Lucknow | ARIMA | 1.87 | 50% | 75% | ARIMA | Naive (last value) (2.89) | yes |

### Win rate (share of 4 windows where the model had the lowest RMSE)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 0% | 50% | 25% | 0% | 25% | 25% |
| Seasonal naive (weekly) | 25% | 0% | 0% | 0% | 0% | 0% |
| ARIMA | 0% | 0% | 25% | 0% | 0% | 50% |
| SARIMA | 0% | 0% | 0% | 75% | 0% | 0% |
| Holt-Winters | 0% | 0% | 0% | 0% | 25% | 0% |
| LSTM | 25% | 50% | 25% | 25% | 0% | 0% |
| XGBoost | 50% | 0% | 0% | 0% | 0% | 25% |
| Prophet | 0% | 0% | 25% | 0% | 50% | 0% |

### Beat-baseline rate (share of windows beating that window's best baseline)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| ARIMA | 25% | 50% | 75% | 100% | 0% | 75% |
| SARIMA | 25% | 50% | 75% | 100% | 0% | 75% |
| Holt-Winters | 25% | 0% | 50% | 25% | 50% | 25% |
| LSTM | 50% | 50% | 75% | 100% | 0% | 50% |
| XGBoost | 50% | 25% | 75% | 100% | 0% | 75% |
| Prophet | 0% | 25% | 75% | 100% | 50% | 0% |

### Mean RMSE across windows

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 19.91 | 6.13 | 1.93 | 15.47 | 2.14 | 2.89 |
| Seasonal naive (weekly) | 16.25 | 7.81 | 2.27 | 12.98 | 2.18 | 3.02 |
| ARIMA | 20.69 | 7.19 | 1.60 | 8.37 | 2.73 | 1.87 |
| SARIMA | 20.67 | 7.49 | 1.74 | 7.12 | 2.72 | 1.88 |
| Holt-Winters | 21.26 | 8.00 | 2.01 | 13.62 | 2.46 | 2.50 |
| LSTM | 20.38 | 8.23 | 1.57 | 7.35 | 3.12 | 5.74 |
| XGBoost | 16.92 | 7.75 | 2.08 | 8.75 | 3.02 | 2.12 |
| Prophet | 25.67 | 9.08 | 1.75 | 10.12 | 2.05 | 3.86 |

### Mean rank across windows (1 = best of all candidates)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 4.5 | 3.0 | 6.0 | 7.8 | 3.5 | 5.0 |
| Seasonal naive (weekly) | 3.0 | 5.2 | 5.8 | 6.2 | 3.2 | 4.8 |
| ARIMA | 4.2 | 3.5 | 3.0 | 3.0 | 5.8 | 2.0 |
| SARIMA | 4.2 | 4.5 | 4.0 | 1.2 | 4.8 | 3.0 |
| Holt-Winters | 5.0 | 5.8 | 5.8 | 7.0 | 4.5 | 4.2 |
| LSTM | 5.2 | 3.5 | 2.2 | 2.2 | 5.8 | 6.2 |
| XGBoost | 2.5 | 5.0 | 5.2 | 4.0 | 5.8 | 3.5 |
| Prophet | 7.2 | 5.5 | 4.0 | 4.5 | 2.8 | 7.2 |

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
| Ahmedabad | 2026-01-30 to 2026-02-28 | XGBoost | 12.17 | 9.76 | 20.0 | Naive (last value) (14.77) | yes |
| Bengaluru | 2026-01-30 to 2026-02-28 | Holt-Winters | 4.40 | 3.50 | 10.1 | Naive (last value) (3.92) | **no** |
| Chennai | 2026-01-30 to 2026-02-28 | LSTM | 1.58 | 1.43 | 18.6 | Naive (last value) (0.89) | **no** |
| Delhi | 2026-01-30 to 2026-02-28 | SARIMA | 6.21 | 5.29 | 10.7 | Seasonal naive (weekly) (12.05) | yes |
| Hyderabad | 2026-01-30 to 2026-02-28 | Prophet | 1.54 | 1.24 | 10.6 | Seasonal naive (weekly) (1.61) | yes |
| Lucknow | 2026-01-30 to 2026-02-28 | XGBoost | 1.84 | 1.51 | 9.2 | Seasonal naive (weekly) (2.28) | yes |

### RMSE on the final hold-out

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 14.77 | 3.92 | 0.89 | 12.15 | 2.49 | 2.34 |
| Seasonal naive (weekly) | 15.32 | 6.94 | 1.40 | 12.05 | 1.61 | 2.28 |
| ARIMA | 12.73 | 8.20 | 1.64 | 8.06 | 2.41 | 1.88 |
| SARIMA | 12.73 | 8.34 | 1.86 | 6.21 | 2.41 | 1.88 |
| Holt-Winters | 13.60 | 4.40 | 1.63 | 12.67 | 2.68 | 2.30 |
| LSTM | 13.61 | 14.48 | 1.58 | 6.72 | 1.88 | 2.12 |
| XGBoost | 12.17 | 4.53 | 2.34 | 6.30 | 1.89 | 1.84 |
| Prophet | 20.01 | 13.33 | 1.93 | 9.95 | 1.54 | 2.97 |

### LSTM seed spread (std of RMSE across seeds, mean over windows)

| City | Mean seed std of RMSE |
|---|---|
| Ahmedabad | 1.31 |
| Bengaluru | 0.35 |
| Chennai | 0.03 |
| Delhi | 0.15 |
| Hyderabad | 0.38 |
| Lucknow | 0.71 |

## Stationarity (final training series)

| City | Span | Days | Interpolated | ADF p | KPSS p | ADF d | ACF@~7 | ACF@~365 (peak lag) | STL strength m=7 / 365 |
|---|---|---|---|---|---|---|---|---|---|
| Delhi | 2025-02-19 to 2026-10-29 | 618 | 43 | 0.5107 | 0.015 | 1 | 0.85 | nan (-) | 0.13 / nan |
| Bengaluru | 2025-02-19 to 2026-10-29 | 618 | 43 | 0.1416 | 0.078 | 1 | 0.86 | nan (-) | 0.15 / nan |
| Chennai | 2025-02-19 to 2026-10-29 | 618 | 43 | 0.3633 | 0.010 | 1 | 0.56 | nan (-) | 0.10 / nan |
| Hyderabad | 2025-02-19 to 2026-10-29 | 618 | 43 | 0.0013 | 0.010 | 0 | 0.59 | nan (-) | 0.05 / nan |
| Lucknow | 2025-02-19 to 2026-10-29 | 618 | 42 | 0.0024 | 0.090 | 0 | 0.80 | nan (-) | 0.02 / nan |
| Ahmedabad | 2025-02-19 to 2026-10-29 | 618 | 42 | 0.0756 | 0.050 | 1 | 0.74 | nan (-) | 0.08 / nan |

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
- Ahmedabad: never beat the baseline in any window: Prophet
- Bengaluru: never beat the baseline in any window: Holt-Winters
- Hyderabad: never beat the baseline in any window: SARIMA, ARIMA, XGBoost, LSTM
- Lucknow: never beat the baseline in any window: Prophet
