# Phase 2 tables

## Preprocessing

| City | Start | End | Days | Interpolated days | Interpolated % | Training days (final hold-out) | AQI note |
|---|---|---|---|---|---|---|---|
| Delhi | 2015-01-01 | 2020-07-01 | 2009 | 10 | 0.50 | 1979 |  |
| Bengaluru | 2015-03-21 | 2020-07-01 | 1930 | 20 | 1.00 | 1900 |  |
| Chennai | 2015-03-24 | 2020-07-01 | 1927 | 43 | 2.20 | 1897 |  |
| Hyderabad | 2015-03-31 | 2020-07-01 | 1920 | 40 | 2.10 | 1890 |  |
| Lucknow | 2015-03-21 | 2020-07-01 | 1930 | 37 | 1.90 | 1900 |  |
| Ahmedabad | 2017-10-11 | 2020-07-01 | 995 | 41 | 4.10 | 965 | recomputed without CO |

## Stationarity (log AQI, final hold-out training data)

| City | ADF stat | ADF p | KPSS stat | KPSS p | Diff ADF p | Diff KPSS p | Level verdict | d used |
|---|---|---|---|---|---|---|---|---|
| Delhi | -3.430 | 0.010 | 0.760 | 0.010 | 4.03e-30 | 0.100 | trend-stationary (ADF yes, KPSS no) | 0 |
| Bengaluru | -5.660 | 9.43e-07 | 0.530 | 0.034 | 2.10e-24 | 0.100 | trend-stationary (ADF yes, KPSS no) | 0 |
| Chennai | -4.670 | 9.64e-05 | 3.280 | 0.010 | 7.21e-26 | 0.100 | trend-stationary (ADF yes, KPSS no) | 0 |
| Hyderabad | -3.690 | 0.004 | 1.610 | 0.010 | 1.83e-19 | 0.100 | trend-stationary (ADF yes, KPSS no) | 0 |
| Lucknow | -3.560 | 0.007 | 0.140 | 0.100 | 8.22e-25 | 0.100 | stationary | 0 |
| Ahmedabad | -4.110 | 9.45e-04 | 0.630 | 0.020 | 9.58e-28 | 0.100 | trend-stationary (ADF yes, KPSS no) | 0 |

## Fitted parameters

| City | Model | Configuration | AIC | Coefficients | alpha (level) | beta (trend) | gamma (season) | phi (damping) |
|---|---|---|---|---|---|---|---|---|
| Delhi | ARIMA | ARIMA(2, 0, 2) | -650.50 | const=5.4332, ar.L1=1.4741, ar.L2=-0.4796, ma.L1=-0.597, ma.L2=-0.2243, sigma2=0.0418 |  |  |  |  |
| Delhi | SARIMA | SARIMA(2, 0, 2)x(0, 0, 1, 7) + 3 annual Fourier pairs | -668.80 | intercept=0.2091, ar.L1=1.2886, ar.L2=-0.3271, ma.L1=-0.438, ma.L2=-0.2468, ma.S.L7=-0.0189, sigma2=0.0412 |  |  |  |  |
| Delhi | Holt-Winters | Holt-Winters (add. damped trend, add. seasonal m=7) | -6003.50 |  | 0.94 | 0.00 | 0.01 | 0.80 |
| Bengaluru | ARIMA | ARIMA(2, 0, 1) | 324.20 | const=4.4859, ar.L1=1.4431, ar.L2=-0.4563, ma.L1=-0.8763, sigma2=0.069 |  |  |  |  |
| Bengaluru | SARIMA | SARIMA(2, 0, 1)x(0, 0, 1, 7) + 3 annual Fourier pairs | 332.60 | intercept=0.2296, ar.L1=1.3079, ar.L2=-0.3591, ma.L1=-0.7597, ma.S.L7=0.0, sigma2=0.0695 |  |  |  |  |
| Bengaluru | Holt-Winters | Holt-Winters (add. damped trend, add. seasonal m=7) | -4756.00 |  | 0.46 | 0.00 | 0.06 | 0.95 |
| Chennai | ARIMA | ARIMA(2, 0, 2) | 172.10 | const=4.7036, ar.L1=1.6043, ar.L2=-0.6066, ma.L1=-0.9212, ma.L2=-0.0346, sigma2=0.0637 |  |  |  |  |
| Chennai | SARIMA | SARIMA(2, 0, 2)x(0, 0, 1, 7) + 3 annual Fourier pairs | 208.80 | intercept=0.2572, ar.L1=1.2523, ar.L2=-0.3075, ma.L1=-0.5541, ma.L2=-0.1153, ma.S.L7=-0.0591, sigma2=0.0642 |  |  |  |  |
| Chennai | Holt-Winters | Holt-Winters (add. damped trend, add. seasonal m=7) | -4942.60 |  | 0.73 | 0.00 | 0.01 | 0.95 |
| Hyderabad | ARIMA | ARIMA(3, 0, 1) | -373.80 | const=4.6192, ar.L1=1.591, ar.L2=-0.7298, ar.L3=0.1314, ma.L1=-0.8613, sigma2=0.0477 |  |  |  |  |
| Hyderabad | SARIMA | SARIMA(2, 0, 2)x(0, 0, 1, 7) + 3 annual Fourier pairs | -359.50 | intercept=0.1707, ar.L1=1.1574, ar.L2=-0.1947, ma.L1=-0.4561, ma.L2=-0.2343, ma.S.L7=-0.0468, sigma2=0.049 |  |  |  |  |
| Hyderabad | Holt-Winters | Holt-Winters (add. damped trend, add. seasonal m=7) | -5355.20 |  | 0.70 | 0.00 | 0.03 | 0.94 |
| Lucknow | ARIMA | ARIMA(2, 0, 2) | 133.10 | const=5.2288, ar.L1=1.4094, ar.L2=-0.4169, ma.L1=-0.6676, ma.L2=-0.1371, sigma2=0.0623 |  |  |  |  |
| Lucknow | SARIMA | SARIMA(2, 0, 2)x(0, 0, 1, 7) + 3 annual Fourier pairs | 74.40 | intercept=0.3002, ar.L1=1.2856, ar.L2=-0.343, ma.L1=-0.5795, ma.L2=-0.1423, ma.S.L7=0.0128, sigma2=0.06 |  |  |  |  |
| Lucknow | Holt-Winters | Holt-Winters (add. damped trend, add. seasonal m=7) | -4996.10 |  | 0.70 | 0.00 | 0.02 | 0.94 |
| Ahmedabad | ARIMA | ARIMA(2, 0, 2) | -65.90 | const=4.9605, ar.L1=1.2697, ar.L2=-0.29, ma.L1=-0.4914, ma.L2=-0.2777, sigma2=0.0539 |  |  |  |  |
| Ahmedabad | SARIMA | SARIMA(2, 0, 2)x(0, 0, 1, 7) + 3 annual Fourier pairs | -63.10 | intercept=0.1097, ar.L1=1.2698, ar.L2=-0.292, ma.L1=-0.4643, ma.L2=-0.3226, ma.S.L7=0.0287, sigma2=0.0535 |  |  |  |  |
| Ahmedabad | Holt-Winters | Holt-Winters (add. damped trend, add. seasonal m=7) | -2594.00 |  | 0.67 | 0.00 | 0.06 | 0.99 |

## Residual diagnostics (after a 14-day burn-in)

| City | Model | Residual mean | Residual sd | Ljung-Box p (lag 7) | Ljung-Box p (lag 14) | Jarque-Bera p | Skew | Kurtosis |
|---|---|---|---|---|---|---|---|---|
| Delhi | ARIMA | -0.001 | 0.203 | 0.859 | 0.933 | 4.41e-50 | -0.300 | 4.600 |
| Delhi | SARIMA | 1.00e-04 | 0.202 | 0.272 | 0.483 | 3.33e-47 | -0.260 | 4.500 |
| Delhi | Holt-Winters | -7.00e-04 | 0.216 | 1.24e-25 | 2.16e-22 | 6.99e-53 | -0.110 | 4.700 |
| Bengaluru | ARIMA | -0.002 | 0.262 | 0.967 | 0.279 | 0.000 | 0.440 | 7.900 |
| Bengaluru | SARIMA | 5.00e-04 | 0.262 | 0.800 | 0.108 | 0.000 | 0.580 | 7.800 |
| Bengaluru | Holt-Winters | -7.00e-04 | 0.284 | 1.38e-27 | 1.81e-26 | 0.000 | 0.190 | 8.300 |
| Chennai | ARIMA | -0.006 | 0.252 | 0.487 | 0.016 | 7.30e-156 | 0.400 | 5.900 |
| Chennai | SARIMA | 1.00e-04 | 0.253 | 0.298 | 0.003 | 8.52e-152 | 0.390 | 5.900 |
| Chennai | Holt-Winters | -2.00e-04 | 0.271 | 1.66e-23 | 3.14e-23 | 2.04e-244 | 0.060 | 6.800 |
| Hyderabad | ARIMA | -0.001 | 0.219 | 0.774 | 0.008 | 0.000 | 0.280 | 13.000 |
| Hyderabad | SARIMA | 0.004 | 0.219 | 0.105 | 0.001 | 0.000 | 0.570 | 12.900 |
| Hyderabad | Holt-Winters | -7.00e-04 | 0.241 | 1.02e-38 | 2.17e-39 | 0.000 | -0.180 | 11.000 |
| Lucknow | ARIMA | -2.00e-04 | 0.246 | 0.699 | 0.490 | 2.45e-127 | -0.440 | 5.600 |
| Lucknow | SARIMA | 7.00e-04 | 0.242 | 0.755 | 0.518 | 8.60e-124 | -0.340 | 5.600 |
| Lucknow | Holt-Winters | -0.000 | 0.263 | 4.31e-27 | 2.60e-25 | 1.42e-149 | -0.300 | 5.900 |
| Ahmedabad | ARIMA | -7.00e-04 | 0.231 | 0.218 | 0.541 | 7.94e-41 | 0.360 | 5.000 |
| Ahmedabad | SARIMA | 0.001 | 0.230 | 0.141 | 0.452 | 9.12e-44 | 0.390 | 5.100 |
| Ahmedabad | Holt-Winters | 9.00e-04 | 0.256 | 4.07e-21 | 3.78e-18 | 2.14e-55 | 0.160 | 5.500 |

## Mean RMSE over 6 windows

| model | Delhi | Bengaluru | Chennai | Hyderabad | Lucknow | Ahmedabad |
|---|---|---|---|---|---|---|
| Naive (last value) | 98.9 | 25.9 | 44.6 | 25.9 | 83.2 | 60.7 |
| Seasonal naive (weekly) | 123.2 | 25.5 | 42.9 | 30.9 | 104.1 | 75.2 |
| Seasonal naive (annual) | 102.3 | 28.9 | 60.1 | 31.4 | 87.1 | 84.8 |
| ARIMA | 107.0 | 22.8 | 37.4 | 28.2 | 88.3 | 62.9 |
| SARIMA | 69.2 | 19.3 | 38.0 | 27.7 | 60.0 | 57.9 |
| Holt-Winters | 99.3 | 21.3 | 40.7 | 25.8 | 85.6 | 57.4 |

## Mean MAE over 6 windows

| model | Delhi | Bengaluru | Chennai | Hyderabad | Lucknow | Ahmedabad |
|---|---|---|---|---|---|---|
| Naive (last value) | 82.0 | 23.1 | 34.5 | 20.9 | 69.7 | 51.4 |
| Seasonal naive (weekly) | 103.2 | 21.2 | 32.5 | 26.0 | 87.8 | 60.0 |
| Seasonal naive (annual) | 78.5 | 23.7 | 42.9 | 25.4 | 71.0 | 68.5 |
| ARIMA | 91.1 | 19.1 | 27.5 | 24.8 | 76.6 | 52.9 |
| SARIMA | 55.9 | 15.8 | 30.3 | 23.6 | 48.5 | 50.5 |
| Holt-Winters | 82.7 | 17.8 | 31.1 | 21.2 | 71.4 | 48.2 |

## Mean MAPE % over 6 windows

| model | Delhi | Bengaluru | Chennai | Hyderabad | Lucknow | Ahmedabad |
|---|---|---|---|---|---|---|
| Naive (last value) | 32.3 | 29.1 | 33.9 | 32.2 | 33.2 | 34.4 |
| Seasonal naive (weekly) | 45.2 | 26.0 | 29.9 | 43.7 | 46.9 | 38.6 |
| Seasonal naive (annual) | 40.2 | 27.9 | 42.3 | 37.5 | 47.1 | 50.3 |
| ARIMA | 37.8 | 24.4 | 24.7 | 43.5 | 40.4 | 33.9 |
| SARIMA | 26.2 | 20.0 | 30.1 | 40.1 | 31.1 | 36.1 |
| Holt-Winters | 32.8 | 22.1 | 29.9 | 33.8 | 35.3 | 32.2 |

## Mean MSE over 6 windows

| model | Delhi | Bengaluru | Chennai | Hyderabad | Lucknow | Ahmedabad |
|---|---|---|---|---|---|---|
| Naive (last value) | 14617.1 | 787.3 | 2343.2 | 739.3 | 9141.2 | 4186.8 |
| Seasonal naive (weekly) | 19480.5 | 719.3 | 2108.0 | 1029.6 | 13471.5 | 6306.5 |
| Seasonal naive (annual) | 10950.8 | 969.1 | 4002.8 | 1090.9 | 7887.7 | 7547.6 |
| ARIMA | 16010.1 | 550.6 | 1654.3 | 909.8 | 10132.0 | 4518.6 |
| SARIMA | 5637.9 | 393.7 | 1656.3 | 784.3 | 3787.8 | 3728.2 |
| Holt-Winters | 14617.5 | 510.3 | 1942.6 | 733.2 | 9670.5 | 3733.3 |

## RMSE on the final hold-out (2 Jun - 1 Jul 2020)

| model | Delhi | Bengaluru | Chennai | Hyderabad | Lucknow | Ahmedabad |
|---|---|---|---|---|---|---|
| Naive (last value) | 41.1 | 9.6 | 21.1 | 14.1 | 36.9 | 38.8 |
| Seasonal naive (weekly) | 52.8 | 15.8 | 25.0 | 35.3 | 55.6 | 33.3 |
| Seasonal naive (annual) | 77.9 | 20.5 | 34.5 | 23.9 | 84.5 | 78.9 |
| ARIMA | 35.7 | 18.8 | 28.0 | 35.8 | 45.5 | 42.7 |
| SARIMA | 38.5 | 14.6 | 20.7 | 29.5 | 49.4 | 33.0 |
| Holt-Winters | 41.6 | 8.5 | 21.4 | 16.6 | 35.8 | 38.1 |

## Best classical model vs best baseline

| City | Best classical model | Mean RMSE | Mean MAE | Mean MAPE % | Best baseline | Baseline RMSE | RMSE vs baseline % | Windows beating every baseline |
|---|---|---|---|---|---|---|---|---|
| Ahmedabad | Holt-Winters | 57.44 | 48.17 | 32.20 | Naive (last value) | 60.75 | -5.40 | 4/6 |
| Bengaluru | SARIMA | 19.35 | 15.78 | 20.00 | Seasonal naive (weekly) | 25.55 | -24.30 | 2/6 |
| Chennai | ARIMA | 37.45 | 27.48 | 24.70 | Seasonal naive (weekly) | 42.87 | -12.60 | 4/6 |
| Delhi | SARIMA | 69.21 | 55.88 | 26.20 | Naive (last value) | 98.91 | -30.00 | 4/6 |
| Hyderabad | Holt-Winters | 25.84 | 21.16 | 33.80 | Naive (last value) | 25.88 | -0.20 | 2/6 |
| Lucknow | SARIMA | 60.01 | 48.55 | 31.10 | Naive (last value) | 83.16 | -27.80 | 4/6 |
