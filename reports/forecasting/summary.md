# AQI forecasting: hold-out evaluation summary

Generated 2026-09-25T15:18:01+00:00. Hold-out = final 30 days per city; models fitted on log1p(AQI), scored on the AQI scale (observed days only). Winner = lowest RMSE.

## Winners

| City | Best model | RMSE | MAE | MAPE % | Best baseline | Baseline RMSE | Beats baseline |
|---|---|---|---|---|---|---|---|
| Ahmedabad | Prophet | 22.89 | 20.98 | 22.6 | Seasonal naive (weekly) | 28.32 | yes |
| Bengaluru | Holt-Winters | 8.55 | 6.99 | 13.9 | Naive (last value) | 9.60 | yes |
| Chennai | SARIMA | 20.68 | 14.85 | 14.2 | Naive (last value) | 21.14 | yes |
| Delhi | LSTM | 32.85 | 25.90 | 21.2 | Naive (last value) | 41.06 | yes |
| Hyderabad | XGBoost | 15.94 | 12.83 | 33.8 | Naive (last value) | 14.08 | **no** |
| Lucknow | Prophet | 32.03 | 21.27 | 18.9 | Naive (last value) | 36.88 | yes |

## RMSE by city and model

| Model | Ahmedabad | Bengaluru | Chennai | Delhi | Hyderabad | Lucknow |
|---|---|---|---|---|---|---|
| Naive (last value) | 32.68 | 9.60 | 21.14 | 41.06 | 14.08 | 36.88 |
| Seasonal naive (weekly) | 28.32 | 15.78 | 25.02 | 52.78 | 35.25 | 55.64 |
| Seasonal naive (annual) | 314.00 | 20.50 | 34.47 | 77.89 | 23.87 | 84.54 |
| ARIMA | 70.74 | 18.79 | 27.98 | 35.72 | 35.84 | 45.54 |
| SARIMA | 157.36 | 14.55 | 20.68 | 38.51 | 29.48 | 49.36 |
| Holt-Winters | 36.38 | 8.55 | 21.43 | 41.61 | 16.58 | 35.75 |
| LSTM | 195.03 | 23.80 | 24.62 | 32.85 | 27.88 | 37.91 |
| XGBoost | 36.58 | 10.10 | 23.03 | 35.98 | 15.94 | 51.04 |
| Prophet | 22.89 | 10.65 | 46.76 | 39.55 | 16.24 | 32.03 |

## Stationarity (training series)

| City | Span | Days | Interpolated | ADF p | KPSS p | ADF d | ACF@~7 | ACF@~365 (peak lag) | STL strength m=7 / 365 |
|---|---|---|---|---|---|---|---|---|---|
| Delhi | 2015-01-01 to 2020-07-01 | 2009 | 10 | 0.0091 | 0.011 | 0 | 0.80 | 0.53 (370) | 0.06 / 0.67 |
| Bengaluru | 2015-03-21 to 2020-07-01 | 1930 | 20 | 0.0000 | 0.010 | 0 | 0.45 | 0.13 (363) | 0.00 / 0.40 |
| Chennai | 2015-03-24 to 2020-07-01 | 1927 | 43 | 0.0000 | 0.010 | 0 | 0.47 | 0.03 (367) | 0.05 / 0.20 |
| Hyderabad | 2015-03-31 to 2020-07-01 | 1920 | 40 | 0.0017 | 0.010 | 0 | 0.42 | 0.11 (363) | 0.05 / 0.50 |
| Lucknow | 2015-03-21 to 2020-07-01 | 1930 | 37 | 0.0116 | 0.100 | 0 | 0.81 | 0.57 (367) | 0.07 / 0.75 |
| Ahmedabad | 2017-10-11 to 2020-07-01 | 995 | 41 | 0.0017 | 0.010 | 0 | 0.40 | 0.07 (360) | 0.00 / 0.58 |

## Issues log

- Ahmedabad: did not beat the best baseline: Holt-Winters, XGBoost, ARIMA, SARIMA, LSTM
- Bengaluru: did not beat the best baseline: XGBoost, Prophet, SARIMA, ARIMA, LSTM
- Chennai: did not beat the best baseline: Holt-Winters, XGBoost, LSTM, ARIMA, Prophet
- Delhi: did not beat the best baseline: Holt-Winters
- Hyderabad: did not beat the best baseline: XGBoost, Prophet, Holt-Winters, LSTM, SARIMA, ARIMA
- Lucknow: did not beat the best baseline: LSTM, ARIMA, SARIMA, XGBoost
