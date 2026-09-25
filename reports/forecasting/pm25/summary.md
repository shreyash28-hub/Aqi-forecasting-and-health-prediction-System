# PM2.5 forecasting: evaluation summary

Generated 2026-09-25T18:55:31+00:00. Models fitted on log1p(PM2.5), scored on the original scale (observed days only). Horizon 30 days. Multi-window: 6 non-overlapping 30-day test windows per city, stepping back 120 days from the end (expanding training window); window 0 is the final hold-out. LSTM metrics are the mean of seeds [42, 43, 44].

## Multi-window results (primary)

Best model = lowest mean RMSE across windows. Win = lowest RMSE of all candidates (baselines included) in a window.

| City | Best model | Mean RMSE | Win rate | Beats baseline in | Most frequent window winner | Best baseline (mean RMSE) | Beats baseline |
|---|---|---|---|---|---|---|---|
| Ahmedabad | Holt-Winters | 26.92 | 0% | 50% | LSTM | Naive (last value) (30.08) | yes |
| Bengaluru | SARIMA | 10.53 | 17% | 50% | Holt-Winters | Naive (last value) (11.45) | yes |
| Chennai | Holt-Winters | 25.67 | 17% | 67% | Prophet | Naive (last value) (26.91) | yes |
| Delhi | Prophet | 44.04 | 33% | 83% | SARIMA | Seasonal naive (annual) (67.53) | yes |
| Hyderabad | Holt-Winters | 12.52 | 17% | 50% | ARIMA | Naive (last value) (12.15) | **no** |
| Lucknow | Prophet | 36.04 | 33% | 83% | Prophet | Naive (last value) (50.25) | yes |

### Win rate (share of 6 windows where the model had the lowest RMSE)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 17% | 17% | 0% | 0% | 0% | 0% |
| Seasonal naive (weekly) | 0% | 0% | 17% | 0% | 0% | 0% |
| Seasonal naive (annual) | 0% | 0% | 0% | 17% | 0% | 0% |
| ARIMA | 17% | 17% | 0% | 0% | 33% | 17% |
| SARIMA | 0% | 17% | 17% | 33% | 0% | 33% |
| Holt-Winters | 0% | 33% | 17% | 0% | 17% | 0% |
| LSTM | 33% | 0% | 17% | 0% | 17% | 17% |
| XGBoost | 17% | 17% | 0% | 17% | 17% | 0% |
| Prophet | 17% | 0% | 33% | 33% | 17% | 33% |

### Beat-baseline rate (share of windows beating that window's best baseline)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| ARIMA | 50% | 33% | 50% | 50% | 50% | 50% |
| SARIMA | 33% | 50% | 67% | 67% | 33% | 67% |
| Holt-Winters | 50% | 67% | 67% | 50% | 50% | 50% |
| LSTM | 50% | 17% | 50% | 67% | 17% | 50% |
| XGBoost | 33% | 33% | 33% | 50% | 33% | 50% |
| Prophet | 17% | 33% | 67% | 83% | 33% | 83% |

### Mean RMSE across windows

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 30.08 | 11.45 | 26.91 | 70.37 | 12.15 | 50.25 |
| Seasonal naive (weekly) | 35.85 | 13.84 | 28.85 | 80.94 | 14.62 | 65.51 |
| Seasonal naive (annual) | 42.62 | 17.23 | 42.34 | 67.53 | 15.53 | 54.70 |
| ARIMA | 28.07 | 11.98 | 26.09 | 71.10 | 13.18 | 51.83 |
| SARIMA | 28.35 | 10.53 | 27.76 | 53.18 | 12.96 | 37.70 |
| Holt-Winters | 26.92 | 10.53 | 25.67 | 68.65 | 12.52 | 48.54 |
| LSTM | 34.53 | 11.86 | 26.99 | 48.30 | 16.13 | 40.51 |
| XGBoost | 32.76 | 11.77 | 28.65 | 60.07 | 13.89 | 44.95 |
| Prophet | 42.37 | 12.57 | 25.71 | 44.04 | 13.46 | 36.04 |

### Mean rank across windows (1 = best of all candidates)

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 4.7 | 4.5 | 5.2 | 6.2 | 4.0 | 5.3 |
| Seasonal naive (weekly) | 5.8 | 6.8 | 5.7 | 8.2 | 6.3 | 8.2 |
| Seasonal naive (annual) | 7.2 | 8.0 | 8.8 | 6.7 | 6.3 | 7.2 |
| ARIMA | 4.0 | 4.8 | 4.2 | 5.7 | 4.0 | 5.0 |
| SARIMA | 4.0 | 3.2 | 4.0 | 3.2 | 5.0 | 3.0 |
| Holt-Winters | 3.8 | 2.7 | 3.0 | 5.3 | 3.8 | 4.3 |
| LSTM | 4.3 | 5.0 | 4.8 | 3.2 | 6.2 | 4.3 |
| XGBoost | 4.8 | 4.5 | 5.8 | 4.7 | 4.7 | 5.3 |
| Prophet | 6.3 | 5.5 | 3.5 | 2.0 | 4.7 | 2.3 |

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
| Ahmedabad | 2020-06-02 to 2020-07-01 | XGBoost | 21.04 | 9.38 | 26.2 | Naive (last value) (21.35) | yes |
| Bengaluru | 2020-06-02 to 2020-07-01 | XGBoost | 4.24 | 3.49 | 20.9 | Seasonal naive (weekly) (7.90) | yes |
| Chennai | 2020-06-02 to 2020-07-01 | Holt-Winters | 19.16 | 11.69 | 38.7 | Seasonal naive (weekly) (18.50) | **no** |
| Delhi | 2020-06-02 to 2020-07-01 | XGBoost | 11.28 | 9.33 | 19.4 | Naive (last value) (12.70) | yes |
| Hyderabad | 2020-06-02 to 2020-07-01 | LSTM | 5.79 | 4.48 | 32.4 | Seasonal naive (annual) (9.77) | yes |
| Lucknow | 2020-06-02 to 2020-07-01 | Prophet | 14.36 | 10.91 | 23.7 | Naive (last value) (16.69) | yes |

### RMSE on the final hold-out

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 21.35 | 10.16 | 20.41 | 12.70 | 12.47 | 16.69 |
| Seasonal naive (weekly) | 21.62 | 7.90 | 18.50 | 20.68 | 10.70 | 28.71 |
| Seasonal naive (annual) | 26.87 | 9.16 | 32.13 | 23.58 | 9.77 | 37.35 |
| ARIMA | 23.93 | 4.88 | 19.24 | 12.44 | 13.02 | 22.11 |
| SARIMA | 21.87 | 5.19 | 23.54 | 17.36 | 8.78 | 19.49 |
| Holt-Winters | 21.24 | 6.68 | 19.16 | 16.46 | 9.47 | 16.14 |
| LSTM | 24.92 | 8.58 | 21.20 | 12.57 | 5.79 | 27.46 |
| XGBoost | 21.04 | 4.24 | 24.01 | 11.28 | 8.06 | 22.65 |
| Prophet | 22.99 | 5.61 | 20.44 | 12.51 | 6.29 | 14.36 |

### LSTM seed spread (std of RMSE across seeds, mean over windows)

| City | Mean seed std of RMSE |
|---|---|
| Ahmedabad | 1.07 |
| Bengaluru | 1.02 |
| Chennai | 1.21 |
| Delhi | 5.50 |
| Hyderabad | 0.69 |
| Lucknow | 3.33 |

## Stationarity (final training series)

| City | Span | Days | Interpolated | ADF p | KPSS p | ADF d | ACF@~7 | ACF@~365 (peak lag) | STL strength m=7 / 365 |
|---|---|---|---|---|---|---|---|---|---|
| Delhi | 2015-01-01 to 2020-07-01 | 2009 | 2 | 0.0015 | 0.100 | 0 | 0.76 | 0.56 (367) | 0.12 / 0.80 |
| Bengaluru | 2015-03-20 to 2020-07-01 | 1931 | 68 | 0.0000 | 0.100 | 0 | 0.48 | 0.12 (360) | 0.09 / 0.41 |
| Chennai | 2015-03-23 to 2020-07-01 | 1928 | 36 | 0.0000 | 0.010 | 0 | 0.42 | 0.14 (366) | 0.02 / 0.42 |
| Hyderabad | 2015-03-31 to 2020-07-01 | 1920 | 29 | 0.0024 | 0.010 | 0 | 0.29 | 0.14 (370) | 0.03 / 0.52 |
| Lucknow | 2015-03-20 to 2020-07-01 | 1931 | 24 | 0.0006 | 0.100 | 0 | 0.74 | 0.48 (370) | 0.09 / 0.76 |
| Ahmedabad | 2017-10-10 to 2020-07-01 | 996 | 19 | 0.0001 | 0.010 | 0 | 0.51 | 0.14 (369) | 0.11 / 0.79 |

## Issues log

- None.
