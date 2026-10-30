# Starting the forecast from today's readings: AQI backtest

Rolling one-day-ahead backtest on the live data (2025-12-17 to 2026-10-22, 288 origin days x 6 cities), ARIMA with the 2015-2020 seasonal prior as the base forecaster. Grid search on origins before 2026-05-24 (mean RMSE over days 1-7) preferred `{'w_max': 1.0, 'half': 3.0, 'rho': 0.92}`; the deployed settings are `{'w_max': 1.0, 'half': 6.0, 'rho': 0.7}` (the same for AQI, PM2.5 and NO2; slightly gentler on later days). Scores below are on the later half (the winter smog season is in it), RMSE per forecast day, plain vs nudged with the readings up to the cut-off hour. Day +1 is today: more than half of today's own hours are already known at the cut-off, so that row measures how well they are used; days +2 onwards show how far the correction carries.

### Cut-off 10:00 IST (858 forecasts)

| Day | +1 | +2 | +3 | +4 | +5 | +6 | +7 |
|---|---|---|---|---|---|---|---|
| Plain | 16.7 | 22.6 | 24.6 | 25.6 | 26.2 | 26.5 | 26.5 |
| Nudged | 8.6 | 20.4 | 23.7 | 25.3 | 25.9 | 26.4 | 26.5 |
| Change | -48% | -10% | -4% | -1% | -1% | -0% | -0% |

### Cut-off 13:00 IST (858 forecasts)

| Day | +1 | +2 | +3 | +4 | +5 | +6 | +7 |
|---|---|---|---|---|---|---|---|
| Plain | 16.7 | 22.6 | 24.6 | 25.6 | 26.2 | 26.5 | 26.5 |
| Nudged | 7.3 | 19.9 | 23.5 | 25.2 | 25.8 | 26.4 | 26.5 |
| Change | -57% | -12% | -5% | -1% | -1% | -0% | -0% |

### Cut-off 18:00 IST (864 forecasts)

| Day | +1 | +2 | +3 | +4 | +5 | +6 | +7 |
|---|---|---|---|---|---|---|---|
| Plain | 16.7 | 22.6 | 24.6 | 25.6 | 26.2 | 26.4 | 26.4 |
| Nudged | 5.1 | 19.0 | 23.1 | 25.0 | 25.7 | 26.3 | 26.4 |
| Change | -69% | -16% | -6% | -2% | -2% | -1% | -0% |

### Per city, cut-off 13:00, day +1 and days +1 to +3 (RMSE plain -> nudged)

| City | Day +1 | Days +1 to +3 |
|---|---|---|
| Delhi | 30.6 -> 13.1 | 39.5 -> 31.4 |
| Bengaluru | 11.8 -> 4.9 | 15.6 -> 12.3 |
| Chennai | 13.1 -> 5.6 | 15.9 -> 12.5 |
| Hyderabad | 6.3 -> 2.6 | 7.4 -> 5.8 |
| Lucknow | 13.0 -> 6.2 | 16.3 -> 13.0 |
| Ahmedabad | 14.6 -> 6.5 | 18.8 -> 14.7 |
