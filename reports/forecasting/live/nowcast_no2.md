# Starting the forecast from today's readings: NO2 backtest

Rolling one-day-ahead backtest on the live data (2025-12-16 to 2026-10-22, 296 origin days x 6 cities), ARIMA with the 2015-2020 seasonal prior as the base forecaster. Grid search on origins before 2026-05-25 (mean RMSE over days 1-7) preferred `{'w_max': 1.0, 'half': 6.0, 'rho': 0.5}`; the deployed settings are `{'w_max': 1.0, 'half': 6.0, 'rho': 0.7}` (the same for AQI, PM2.5 and NO2; slightly gentler on later days). Scores below are on the later half (the winter smog season is in it), RMSE per forecast day, plain vs nudged with the readings up to the cut-off hour. Day +1 is today: more than half of today's own hours are already known at the cut-off, so that row measures how well they are used; days +2 onwards show how far the correction carries.

### Cut-off 10:00 IST (882 forecasts)

| Day | +1 | +2 | +3 | +4 | +5 | +6 | +7 |
|---|---|---|---|---|---|---|---|
| Plain | 2.7 | 3.2 | 3.4 | 3.7 | 3.8 | 3.9 | 4.0 |
| Nudged | 1.8 | 3.1 | 3.3 | 3.5 | 3.7 | 3.8 | 3.9 |
| Change | -34% | -3% | -3% | -4% | -2% | -2% | -1% |

### Cut-off 13:00 IST (888 forecasts)

| Day | +1 | +2 | +3 | +4 | +5 | +6 | +7 |
|---|---|---|---|---|---|---|---|
| Plain | 2.7 | 3.2 | 3.4 | 3.7 | 3.7 | 3.9 | 4.0 |
| Nudged | 1.6 | 3.0 | 3.3 | 3.5 | 3.7 | 3.8 | 3.9 |
| Change | -42% | -6% | -5% | -5% | -2% | -3% | -1% |

### Cut-off 18:00 IST (888 forecasts)

| Day | +1 | +2 | +3 | +4 | +5 | +6 | +7 |
|---|---|---|---|---|---|---|---|
| Plain | 2.7 | 3.2 | 3.4 | 3.7 | 3.7 | 3.9 | 4.0 |
| Nudged | 1.3 | 2.9 | 3.2 | 3.4 | 3.6 | 3.8 | 3.9 |
| Change | -52% | -11% | -6% | -7% | -3% | -3% | -2% |

### Per city, cut-off 13:00, day +1 and days +1 to +3 (RMSE plain -> nudged)

| City | Day +1 | Days +1 to +3 |
|---|---|---|
| Delhi | 4.5 -> 2.7 | 5.2 -> 4.3 |
| Bengaluru | 2.3 -> 2.0 | 2.7 -> 2.6 |
| Chennai | 0.8 -> 0.4 | 1.1 -> 0.9 |
| Hyderabad | 0.9 -> 0.5 | 1.1 -> 0.9 |
| Lucknow | 1.1 -> 0.5 | 1.4 -> 1.2 |
| Ahmedabad | 4.0 -> 1.8 | 4.5 -> 3.6 |
