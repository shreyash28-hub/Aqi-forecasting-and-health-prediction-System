# Health models on forecast inputs: backtest

300 held-out profiles × 749 city-days from the forecasting evaluation's rolling-origin windows (Ahmedabad 114, Bengaluru 180, Chennai 95, Delhi 180, Hyderabad 180). Air inputs are each city's selected forecasting model for AQI, PM2.5 and NO2. Reference: the all-pollutant model fed measured values (a proxy for the true risk of those days). All health models are fitted on the training split only.

| Feature set | Air inputs | Score RMSE vs ref. | Score MAE vs ref. | Level agreement | High/Severe caught (alert level) | False High/Severe alerts |
|---|---|---|---|---|---|---|
| `aqi_only` | forecast | 0.592 | 0.361 | 68.5% | 69.0% | 4.6% |
| `aqi_only` | actual | 0.297 | 0.182 | 85.4% | 87.1% | 1.0% |
| `aqi_pm25_no2` | forecast | 0.496 | 0.300 | 73.3% | 79.9% | 5.5% |
| `aqi_pm25_no2` | actual | 0.141 | 0.099 | 93.6% | 98.3% | 2.4% |

### By city (forecast inputs)

| City | `aqi_only` RMSE | `aqi_only` level agr. | `aqi_pm25_no2` RMSE | `aqi_pm25_no2` level agr. |
|---|---|---|---|---|
| Ahmedabad | 0.734 | 50.8% | 0.532 | 59.3% |
| Bengaluru | 0.248 | 79.5% | 0.220 | 82.4% |
| Chennai | 0.366 | 74.4% | 0.369 | 78.3% |
| Delhi | 0.956 | 56.3% | 0.818 | 62.8% |
| Hyderabad | 0.266 | 77.8% | 0.234 | 80.9% |
