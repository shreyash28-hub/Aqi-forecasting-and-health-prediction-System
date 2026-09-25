# AQI forecasting: evaluation summary

Generated 2026-09-25T17:44:20+00:00. Models fitted on log1p(AQI), scored on the AQI scale (observed days only). Horizon 30 days. Multi-window: 6 non-overlapping 30-day test windows per city, stepping back 120 days from the end (expanding training window); window 0 is the final hold-out. LSTM metrics are the mean of seeds [42, 43, 44]. Ahmedabad AQI is recomputed without CO (see findings.md).

## Multi-window results (primary)

Best model = lowest mean RMSE across windows. Win = lowest RMSE of all candidates (baselines included) in a window.

| City | Best model | Mean RMSE | Win rate | Beats baseline in | Most frequent window winner | Best baseline (mean RMSE) | Beats baseline |
|---|---|---|---|---|---|---|---|
| Ahmedabad | Holt-Winters | 57.44 | 17% | 67% | Prophet | Naive (last value) (60.75) | yes |
| Bengaluru | SARIMA | 19.35 | 17% | 33% | Naive (last value) | Seasonal naive (weekly) (25.55) | yes |
| Chennai | ARIMA | 37.45 | 17% | 67% | SARIMA | Seasonal naive (weekly) (42.87) | yes |
| Delhi | SARIMA | 69.21 | 33% | 67% | SARIMA | Naive (last value) (98.91) | yes |
| Hyderabad | Prophet | 22.39 | 33% | 50% | Prophet | Naive (last value) (25.88) | yes |
| Lucknow | Prophet | 55.90 | 33% | 67% | Prophet | Naive (last value) (83.16) | yes |

### Win rate (share of 6 windows where the model had the lowest RMSE)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 0% | 33% | 0% | 17% | 17% | 0% |
| Seasonal naive (weekly) | 0% | 0% | 0% | 0% | 0% | 0% |
| Seasonal naive (annual) | 17% | 17% | 0% | 17% | 17% | 0% |
| ARIMA | 17% | 17% | 17% | 17% | 0% | 17% |
| SARIMA | 17% | 17% | 33% | 33% | 0% | 33% |
| Holt-Winters | 17% | 17% | 17% | 0% | 17% | 0% |
| LSTM | 0% | 0% | 0% | 0% | 0% | 17% |
| XGBoost | 0% | 0% | 17% | 0% | 17% | 0% |
| Prophet | 33% | 0% | 17% | 17% | 33% | 33% |

### Beat-baseline rate (share of windows beating that window's best baseline)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| ARIMA | 17% | 33% | 67% | 33% | 50% | 33% |
| SARIMA | 50% | 33% | 67% | 67% | 33% | 67% |
| Holt-Winters | 67% | 33% | 33% | 17% | 33% | 33% |
| LSTM | 33% | 33% | 33% | 33% | 17% | 33% |
| XGBoost | 33% | 17% | 33% | 33% | 33% | 17% |
| Prophet | 50% | 17% | 33% | 50% | 50% | 67% |

### Mean RMSE across windows

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 60.75 | 25.86 | 44.61 | 98.91 | 25.88 | 83.16 |
| Seasonal naive (weekly) | 75.16 | 25.55 | 42.87 | 123.22 | 30.89 | 104.06 |
| Seasonal naive (annual) | 84.78 | 28.94 | 60.12 | 102.29 | 31.43 | 87.07 |
| ARIMA | 62.87 | 22.83 | 37.45 | 106.95 | 28.22 | 88.27 |
| SARIMA | 57.88 | 19.35 | 37.99 | 69.21 | 27.69 | 60.01 |
| Holt-Winters | 57.44 | 21.31 | 40.73 | 99.26 | 25.84 | 85.57 |
| LSTM | 75.70 | 20.92 | 37.48 | 81.65 | 33.99 | 57.98 |
| XGBoost | 62.87 | 27.74 | 38.22 | 86.12 | 23.26 | 69.76 |
| Prophet | 88.70 | 26.72 | 41.14 | 69.31 | 22.39 | 55.90 |

### Mean rank across windows (1 = best of all candidates)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 5.0 | 4.5 | 6.0 | 4.7 | 4.5 | 4.3 |
| Seasonal naive (weekly) | 6.3 | 6.3 | 5.2 | 8.5 | 6.0 | 8.2 |
| Seasonal naive (annual) | 7.0 | 7.3 | 8.7 | 6.7 | 6.7 | 7.3 |
| ARIMA | 5.0 | 4.3 | 3.7 | 5.5 | 4.5 | 4.8 |
| SARIMA | 3.0 | 3.3 | 3.3 | 2.3 | 5.2 | 3.0 |
| Holt-Winters | 3.7 | 4.0 | 5.0 | 4.8 | 4.5 | 4.5 |
| LSTM | 4.8 | 4.2 | 4.0 | 4.5 | 7.0 | 4.0 |
| XGBoost | 4.7 | 4.8 | 4.3 | 4.5 | 4.0 | 5.5 |
| Prophet | 5.5 | 6.2 | 4.8 | 3.5 | 2.7 | 3.3 |

### Test windows

| City | Window 0 | Window 1 | Window 2 | Window 3 | Window 4 | Window 5 |
|---|---|---|---|---|---|---|
| Ahmedabad | w0: 2020-06-02 to 2020-07-01 | w1: 2020-02-03 to 2020-03-03 | w2: 2019-10-06 to 2019-11-04 | w3: 2019-06-08 to 2019-07-07 | w4: 2019-02-08 to 2019-03-09 | w5: 2018-10-11 to 2018-11-09 |
| Bengaluru | w0: 2020-06-02 to 2020-07-01 | w1: 2020-02-03 to 2020-03-03 | w2: 2019-10-06 to 2019-11-04 | w3: 2019-06-08 to 2019-07-07 | w4: 2019-02-08 to 2019-03-09 | w5: 2018-10-11 to 2018-11-09 |
| Chennai | w0: 2020-06-02 to 2020-07-01 | w1: 2020-02-03 to 2020-03-03 | w2: 2019-10-06 to 2019-11-04 | w3: 2019-06-08 to 2019-07-07 | w4: 2019-02-08 to 2019-03-09 | w5: 2018-10-11 to 2018-11-09 |
| Delhi | w0: 2020-06-02 to 2020-07-01 | w1: 2020-02-03 to 2020-03-03 | w2: 2019-10-06 to 2019-11-04 | w3: 2019-06-08 to 2019-07-07 | w4: 2019-02-08 to 2019-03-09 | w5: 2018-10-11 to 2018-11-09 |
| Hyderabad | w0: 2020-06-02 to 2020-07-01 | w1: 2020-02-03 to 2020-03-03 | w2: 2019-10-06 to 2019-11-04 | w3: 2019-06-08 to 2019-07-07 | w4: 2019-02-08 to 2019-03-09 | w5: 2018-10-11 to 2018-11-09 |
| Lucknow | w0: 2020-06-02 to 2020-07-01 | w1: 2020-02-03 to 2020-03-03 | w2: 2019-10-06 to 2019-11-04 | w3: 2019-06-08 to 2019-07-07 | w4: 2019-02-08 to 2019-03-09 | w5: 2018-10-11 to 2018-11-09 |

## Final 30-day hold-out only (window 0, kept for comparison)

| City | Window | Best model | RMSE | MAE | MAPE % | Best baseline (RMSE) | Beats baseline |
|---|---|---|---|---|---|---|---|
| Ahmedabad | 2020-06-02 to 2020-07-01 | Prophet | 18.53 | 15.62 | 17.4 | Seasonal naive (weekly) (33.32) | yes |
| Bengaluru | 2020-06-02 to 2020-07-01 | Holt-Winters | 8.55 | 6.99 | 13.9 | Naive (last value) (9.60) | yes |
| Chennai | 2020-06-02 to 2020-07-01 | SARIMA | 20.68 | 14.85 | 14.2 | Naive (last value) (21.14) | yes |
| Delhi | 2020-06-02 to 2020-07-01 | ARIMA | 35.72 | 28.37 | 25.7 | Naive (last value) (41.06) | yes |
| Hyderabad | 2020-06-02 to 2020-07-01 | XGBoost | 15.33 | 12.38 | 32.3 | Naive (last value) (14.08) | **no** |
| Lucknow | 2020-06-02 to 2020-07-01 | Prophet | 32.03 | 21.27 | 18.9 | Naive (last value) (36.88) | yes |

### RMSE on the final hold-out

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 38.81 | 9.60 | 21.14 | 41.06 | 14.08 | 36.88 |
| Seasonal naive (weekly) | 33.32 | 15.78 | 25.02 | 52.78 | 35.25 | 55.64 |
| Seasonal naive (annual) | 78.86 | 20.50 | 34.47 | 77.89 | 23.87 | 84.54 |
| ARIMA | 42.66 | 18.79 | 27.98 | 35.72 | 35.84 | 45.54 |
| SARIMA | 32.98 | 14.55 | 20.68 | 38.51 | 29.48 | 49.36 |
| Holt-Winters | 38.08 | 8.55 | 21.43 | 41.61 | 16.58 | 35.75 |
| LSTM | 29.38 | 15.37 | 24.38 | 42.57 | 26.98 | 49.54 |
| XGBoost | 41.57 | 10.60 | 23.57 | 38.12 | 15.33 | 52.03 |
| Prophet | 18.53 | 10.65 | 46.76 | 39.55 | 16.24 | 32.03 |

### LSTM seed spread (std of RMSE across seeds, mean over windows)

| City | Mean seed std of RMSE |
|---|---|
| Ahmedabad | 1.98 |
| Bengaluru | 2.55 |
| Chennai | 0.65 |
| Delhi | 6.90 |
| Hyderabad | 2.87 |
| Lucknow | 5.81 |

## Stationarity (final training series)

| City | Span | Days | Interpolated | ADF p | KPSS p | ADF d | ACF@~7 | ACF@~365 (peak lag) | STL strength m=7 / 365 |
|---|---|---|---|---|---|---|---|---|---|
| Delhi | 2015-01-01 to 2020-07-01 | 2009 | 10 | 0.0091 | 0.011 | 0 | 0.80 | 0.53 (370) | 0.06 / 0.67 |
| Bengaluru | 2015-03-21 to 2020-07-01 | 1930 | 20 | 0.0000 | 0.010 | 0 | 0.45 | 0.13 (363) | 0.00 / 0.40 |
| Chennai | 2015-03-24 to 2020-07-01 | 1927 | 43 | 0.0000 | 0.010 | 0 | 0.47 | 0.03 (367) | 0.05 / 0.20 |
| Hyderabad | 2015-03-31 to 2020-07-01 | 1920 | 40 | 0.0017 | 0.010 | 0 | 0.42 | 0.11 (363) | 0.05 / 0.50 |
| Lucknow | 2015-03-21 to 2020-07-01 | 1930 | 37 | 0.0116 | 0.100 | 0 | 0.81 | 0.57 (367) | 0.07 / 0.75 |
| Ahmedabad | 2017-10-11 to 2020-07-01 | 995 | 41 | 0.0000 | 0.010 | 0 | 0.57 | 0.11 (368) | 0.06 / 0.71 |

## Issues log

- None.
