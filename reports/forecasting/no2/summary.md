# NO2 forecasting: evaluation summary

Generated 2026-09-25T19:07:04+00:00. Models fitted on log1p(NO2), scored on the original scale (observed days only). Horizon 30 days. Multi-window: 6 non-overlapping 30-day test windows per city, stepping back 120 days from the end (expanding training window); window 0 is the final hold-out. LSTM metrics are the mean of seeds [42, 43, 44].

## Multi-window results (primary)

Best model = lowest mean RMSE across windows. Win = lowest RMSE of all candidates (baselines included) in a window.

| City | Best model | Mean RMSE | Win rate | Beats baseline in | Most frequent window winner | Best baseline (mean RMSE) | Beats baseline |
|---|---|---|---|---|---|---|---|
| Ahmedabad | SARIMA | 36.66 | 60% | 60% | SARIMA | Naive (last value) (34.78) | **no** |
| Bengaluru | LSTM | 6.64 | 0% | 67% | SARIMA | Seasonal naive (weekly) (9.14) | yes |
| Chennai | SARIMA | 4.41 | 33% | 67% | SARIMA | Naive (last value) (4.66) | yes |
| Delhi | Prophet | 8.73 | 50% | 83% | Prophet | Naive (last value) (13.20) | yes |
| Hyderabad | XGBoost | 6.58 | 50% | 67% | XGBoost | Seasonal naive (weekly) (7.95) | yes |
| Lucknow | Prophet | 12.32 | 17% | 50% | ARIMA | Seasonal naive (annual) (14.62) | yes |

### Win rate (share of 6 windows where the model had the lowest RMSE)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 40% | 17% | 0% | 0% | 0% | 0% |
| Seasonal naive (weekly) | 0% | 0% | 0% | 0% | 0% | 0% |
| Seasonal naive (annual) | 0% | 0% | 33% | 0% | 0% | 0% |
| ARIMA | 0% | 17% | 17% | 17% | 17% | 33% |
| SARIMA | 60% | 33% | 33% | 0% | 17% | 17% |
| Holt-Winters | 0% | 0% | 0% | 0% | 0% | 17% |
| LSTM | 0% | 0% | 0% | 0% | 17% | 0% |
| XGBoost | 0% | 17% | 17% | 33% | 50% | 17% |
| Prophet | 0% | 17% | 0% | 50% | 0% | 17% |

### Beat-baseline rate (share of windows beating that window's best baseline)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| ARIMA | 40% | 50% | 67% | 33% | 17% | 50% |
| SARIMA | 60% | 67% | 67% | 67% | 33% | 50% |
| Holt-Winters | 40% | 33% | 50% | 17% | 33% | 33% |
| LSTM | 60% | 67% | 17% | 50% | 50% | 33% |
| XGBoost | 20% | 67% | 33% | 50% | 67% | 50% |
| Prophet | 40% | 67% | 33% | 83% | 33% | 50% |

### Mean RMSE across windows

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 34.78 | 10.57 | 4.66 | 13.20 | 8.58 | 16.29 |
| Seasonal naive (weekly) | 49.18 | 9.14 | 5.71 | 14.30 | 7.95 | 17.26 |
| Seasonal naive (annual) | 81.98 | 10.67 | 6.00 | 14.85 | 13.46 | 14.62 |
| ARIMA | 40.92 | 7.55 | 4.62 | 12.84 | 8.17 | 15.77 |
| SARIMA | 36.66 | 6.90 | 4.41 | 10.60 | 8.71 | 12.48 |
| Holt-Winters | 37.33 | 8.91 | 4.72 | 12.52 | 8.41 | 15.60 |
| LSTM | 47.25 | 6.64 | 4.90 | 10.31 | 8.96 | 15.44 |
| XGBoost | 45.22 | 7.82 | 5.14 | 11.88 | 6.58 | 13.93 |
| Prophet | 45.38 | 6.93 | 6.43 | 8.73 | 9.28 | 12.32 |

### Mean rank across windows (1 = best of all candidates)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 4.0 | 6.2 | 4.8 | 5.8 | 5.5 | 5.5 |
| Seasonal naive (weekly) | 7.2 | 6.5 | 7.0 | 7.0 | 4.0 | 6.8 |
| Seasonal naive (annual) | 7.6 | 6.8 | 6.2 | 6.5 | 8.0 | 6.7 |
| ARIMA | 4.0 | 5.0 | 3.7 | 5.7 | 4.3 | 4.0 |
| SARIMA | 2.2 | 3.7 | 2.3 | 4.3 | 4.7 | 3.8 |
| Holt-Winters | 4.0 | 5.3 | 4.2 | 4.8 | 5.0 | 4.3 |
| LSTM | 5.4 | 3.5 | 5.2 | 4.7 | 5.0 | 5.5 |
| XGBoost | 5.2 | 3.7 | 5.5 | 4.0 | 2.8 | 4.2 |
| Prophet | 5.4 | 4.3 | 6.2 | 2.2 | 5.7 | 4.2 |

### Test windows

| City | Window 0 | Window 1 | Window 2 | Window 3 | Window 4 | Window 5 |
|---|---|---|---|---|---|---|
| Ahmedabad | w0: 2020-06-02 to 2020-07-01 | w1: 2020-02-03 to 2020-03-03 | w2: 2019-10-06 to 2019-11-04 | w3: 2019-06-08 to 2019-07-07 | w4: 2019-02-08 to 2019-03-09 |
| Bengaluru | w0: 2020-06-02 to 2020-07-01 | w1: 2020-02-03 to 2020-03-03 | w2: 2019-10-06 to 2019-11-04 | w3: 2019-06-08 to 2019-07-07 | w4: 2019-02-08 to 2019-03-09 | w5: 2018-10-11 to 2018-11-09 |
| Chennai | w0: 2020-06-02 to 2020-07-01 | w1: 2020-02-03 to 2020-03-03 | w2: 2019-10-06 to 2019-11-04 | w3: 2019-06-08 to 2019-07-07 | w4: 2019-02-08 to 2019-03-09 | w5: 2018-10-11 to 2018-11-09 |
| Delhi | w0: 2020-06-02 to 2020-07-01 | w1: 2020-02-03 to 2020-03-03 | w2: 2019-10-06 to 2019-11-04 | w3: 2019-06-08 to 2019-07-07 | w4: 2019-02-08 to 2019-03-09 | w5: 2018-10-11 to 2018-11-09 |
| Hyderabad | w0: 2020-06-02 to 2020-07-01 | w1: 2020-02-03 to 2020-03-03 | w2: 2019-10-06 to 2019-11-04 | w3: 2019-06-08 to 2019-07-07 | w4: 2019-02-08 to 2019-03-09 | w5: 2018-10-11 to 2018-11-09 |
| Lucknow | w0: 2020-06-02 to 2020-07-01 | w1: 2020-02-03 to 2020-03-03 | w2: 2019-10-06 to 2019-11-04 | w3: 2019-06-08 to 2019-07-07 | w4: 2019-02-08 to 2019-03-09 | w5: 2018-10-11 to 2018-11-09 |

## Final 30-day hold-out only (window 0, kept for comparison)

| City | Window | Best model | RMSE | MAE | MAPE % | Best baseline (RMSE) | Beats baseline |
|---|---|---|---|---|---|---|---|
| Ahmedabad | 2020-06-02 to 2020-07-01 | SARIMA | 12.40 | 9.15 | 29.6 | Naive (last value) (12.93) | yes |
| Bengaluru | 2020-06-02 to 2020-07-01 | SARIMA | 2.19 | 1.79 | 13.6 | Seasonal naive (weekly) (3.64) | yes |
| Chennai | 2020-06-02 to 2020-07-01 | SARIMA | 2.39 | 2.08 | 18.7 | Naive (last value) (2.95) | yes |
| Delhi | 2020-06-02 to 2020-07-01 | Prophet | 3.75 | 3.22 | 14.4 | Naive (last value) (4.96) | yes |
| Hyderabad | 2020-06-02 to 2020-07-01 | XGBoost | 3.12 | 2.59 | 12.3 | Seasonal naive (weekly) (5.26) | yes |
| Lucknow | 2020-06-02 to 2020-07-01 | SARIMA | 5.07 | 4.21 | 33.1 | Naive (last value) (5.13) | yes |

### RMSE on the final hold-out

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 12.93 | 4.63 | 2.95 | 4.96 | 9.21 | 5.13 |
| Seasonal naive (weekly) | 15.51 | 3.64 | 3.49 | 9.07 | 5.26 | 6.30 |
| Seasonal naive (annual) | 118.39 | 8.01 | 10.23 | 16.49 | 7.73 | 10.47 |
| ARIMA | 14.55 | 3.00 | 2.45 | 7.84 | 6.35 | 5.28 |
| SARIMA | 12.40 | 2.19 | 2.39 | 12.82 | 6.46 | 5.07 |
| Holt-Winters | 14.29 | 3.52 | 3.06 | 5.22 | 9.25 | 5.09 |
| LSTM | 12.54 | 2.34 | 2.51 | 6.13 | 3.35 | 5.35 |
| XGBoost | 15.26 | 2.52 | 3.50 | 8.91 | 3.12 | 5.59 |
| Prophet | 12.78 | 3.28 | 2.78 | 3.75 | 10.02 | 5.12 |

### LSTM seed spread (std of RMSE across seeds, mean over windows)

| City | Mean seed std of RMSE |
|---|---|
| Ahmedabad | 0.96 |
| Bengaluru | 0.48 |
| Chennai | 0.11 |
| Delhi | 1.01 |
| Hyderabad | 0.50 |
| Lucknow | 1.36 |

## Stationarity (final training series)

| City | Span | Days | Interpolated | ADF p | KPSS p | ADF d | ACF@~7 | ACF@~365 (peak lag) | STL strength m=7 / 365 |
|---|---|---|---|---|---|---|---|---|---|
| Delhi | 2015-01-01 to 2020-07-01 | 2009 | 2 | 0.0071 | 0.010 | 0 | 0.65 | 0.21 (362) | 0.11 / 0.48 |
| Bengaluru | 2015-01-01 to 2020-07-01 | 2009 | 6 | 0.0009 | 0.048 | 0 | 0.65 | 0.25 (370) | 0.09 / 0.50 |
| Chennai | 2015-01-01 to 2020-07-01 | 2009 | 36 | 0.0000 | 0.092 | 0 | 0.54 | 0.03 (370) | 0.10 / 0.05 |
| Hyderabad | 2015-01-04 to 2020-07-01 | 2006 | 28 | 0.0009 | 0.010 | 0 | 0.78 | 0.31 (369) | 0.03 / 0.28 |
| Lucknow | 2015-01-01 to 2020-07-01 | 2009 | 24 | 0.0063 | 0.010 | 0 | 0.73 | 0.34 (364) | 0.03 / 0.45 |
| Ahmedabad | 2017-10-25 to 2020-07-01 | 981 | 11 | 0.0005 | 0.040 | 0 | 0.78 | 0.07 (364) | 0.09 / 0.76 |

## Issues log

- None.
