# Starting the forecast from today's readings: PM2.5 backtest

Rolling one-day-ahead backtest on the live data (2025-12-16 to 2026-10-22, 296 origin days x 6 cities), ARIMA with the 2015-2020 seasonal prior as the base forecaster. Grid search on origins before 2026-05-25 (mean RMSE over days 1-7) preferred `{'w_max': 1.0, 'half': 6.0, 'rho': 0.7}`; the deployed settings are `{'w_max': 1.0, 'half': 6.0, 'rho': 0.7}` (the same for AQI, PM2.5 and NO2; slightly gentler on later days). Scores below are on the later half (the winter smog season is in it), RMSE per forecast day, plain vs nudged with the readings up to the cut-off hour. Day +1 is today: more than half of today's own hours are already known at the cut-off, so that row measures how well they are used; days +2 onwards show how far the correction carries.

### Cut-off 10:00 IST (880 forecasts)

| Day | +1 | +2 | +3 | +4 | +5 | +6 | +7 |
|---|---|---|---|---|---|---|---|
| Plain | 8.0 | 9.6 | 10.5 | 10.8 | 10.9 | 11.1 | 11.0 |
| Nudged | 4.8 | 9.2 | 10.3 | 10.8 | 11.0 | 11.2 | 11.1 |
| Change | -40% | -4% | -2% | +0% | +0% | +1% | +1% |

### Cut-off 13:00 IST (886 forecasts)

| Day | +1 | +2 | +3 | +4 | +5 | +6 | +7 |
|---|---|---|---|---|---|---|---|
| Plain | 8.0 | 9.6 | 10.5 | 10.8 | 10.9 | 11.1 | 11.0 |
| Nudged | 4.0 | 9.0 | 10.1 | 10.7 | 10.9 | 11.1 | 11.1 |
| Change | -50% | -6% | -3% | -1% | -0% | +0% | +1% |

### Cut-off 18:00 IST (888 forecasts)

| Day | +1 | +2 | +3 | +4 | +5 | +6 | +7 |
|---|---|---|---|---|---|---|---|
| Plain | 8.0 | 9.6 | 10.4 | 10.8 | 10.9 | 11.1 | 11.0 |
| Nudged | 3.1 | 8.6 | 10.0 | 10.6 | 10.8 | 11.1 | 11.1 |
| Change | -61% | -10% | -5% | -2% | -1% | -0% | +0% |

### Per city, cut-off 13:00, day +1 and days +1 to +3 (RMSE plain -> nudged)

| City | Day +1 | Days +1 to +3 |
|---|---|---|
| Delhi | 12.4 -> 5.9 | 14.8 -> 12.2 |
| Bengaluru | 5.9 -> 3.4 | 7.4 -> 6.2 |
| Chennai | 6.1 -> 3.8 | 7.3 -> 6.2 |
| Hyderabad | 3.4 -> 2.2 | 4.4 -> 3.8 |
| Lucknow | 7.6 -> 3.9 | 9.2 -> 7.5 |
| Ahmedabad | 9.1 -> 4.0 | 9.5 -> 7.7 |
