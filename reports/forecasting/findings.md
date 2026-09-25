# AQI forecasting: findings from the first evaluation run

Companion to the generated `summary.md` (tables) in this folder. Setup: six cities, final
30 days (2020-06-02 → 2020-07-01) held out, models fitted on log1p(AQI), scored on the AQI
scale. Baselines: last value, weekly seasonal naive, annual seasonal naive; the bar each model
must clear is the **best** of the three for that city.

## Winners per city

| City | Winner | RMSE | Best baseline (RMSE) | Margin | Why it plausibly won |
|---|---|---|---|---|---|
| Delhi | LSTM | 32.85 | Last value (41.06) | −20% | Longest clean history (2,009 days, 10 interpolated), strong annual cycle (STL 0.67). 5 of 6 models beat the baseline here; this is the most reliable result. |
| Lucknow | Prophet | 32.03 | Last value (36.88) | −13% | Strongest annual seasonality of all cities (STL 0.75); Prophet's yearly term followed the June monsoon decline. |
| Bengaluru | Holt-Winters | 8.55 | Last value (9.60) | −11% | Low, stable AQI with little seasonality. Damped-trend HW is basically a smoothed persistence forecast, and that's what this series needs. |
| Chennai | SARIMA | 20.68 | Last value (21.14) | −2% | Effectively a tie. Weakest annual seasonality (STL 0.20). The hold-out mean rose (72 → 103), which the naive forecast couldn't anticipate either. |
| Ahmedabad | Prophet | 22.89 | Weekly naive (28.32) | −19% | Prophet's piecewise trend adapted to the 2020 level drop; see data issue below. |
| Hyderabad | XGBoost (best model) | 15.94 | Last value (14.08) | **+13%** | **No model beat the baseline.** June 2020 AQI (mean 47) fell below anything in the training history; mean-reverting models were pulled back up toward ~100. |

Every model beats the baseline in at least one city, and no model wins in more than two.
On one 30-day window that's what you'd expect when the differences are mostly noise.
**Treat these winners as provisional** (see issue 1).

## Preprocessing results

- **Stationarity:** ADF rejects a unit root in every city (p ≤ 0.012), so `d = 0`. But KPSS
  *also* rejects stationarity in 5 of 6 (p ≈ 0.01; Lucknow p = 0.10). The two tests agree
  once you allow for seasonality: the series has no unit root but moves around a seasonal
  level, so it isn't level-stationary. So ARIMA/SARIMA use `d = 0` and the seasonality is
  modelled explicitly (Fourier terms, seasonal components) rather than differenced away.
- **Seasonal period:** ~365 days, confirmed two ways. The ACF of the detrended series peaks
  at lags 360–370 in every city, and STL seasonal strength at m=365 is 0.20–0.75 versus
  ≤ 0.07 at m=7. Weekly seasonality is negligible.
- **Gaps:** gaps of up to 21 days are time-interpolated. Longer outages cause the series to
  start after the last one. Interpolated days are excluded from scoring (only Ahmedabad has
  any in the hold-out: 2 days).

## Issues encountered

1. **The hold-out window is atypical.** June 2020 falls under the COVID lockdown and the
   monsoon onset. Hold-out AQI is far below the same weeks in 2019 (Delhi 126 vs 194,
   Lucknow 96 vs 166, Ahmedabad 98 vs 396). This rewards persistence (the last-value
   baseline wins 5 of 6 baseline contests) and penalises models that learned "last June"
   or the long-run mean. The annual seasonal naive is the worst baseline everywhere.
   *Recommendation:* add a rolling-origin backtest (e.g. 8–12 successive 30-day windows
   through 2019–2020) before drawing Phase 2/3 conclusions. The single final window can stay
   as the headline hold-out.
2. **Ahmedabad data quality.** Before 2020 its AQI median is 447 and its max is 2,049, well
   above the official CPCB AQI ceiling of 500. On the 93 days with AQI > 1000, the mean CO
   reading is 69 mg/m³, which points to a CO-sensor problem. From April 2020 the level drops
   to ~110. ARIMA (+150%), SARIMA (+456%) and LSTM (+589%) revert toward the inflated
   pre-2020 level and fail badly. Also, the 232- and 340-day outages in 2015–2017 leave only
   995 usable days, so annual seasonality is fitted on about 2.7 cycles. *Options (needs
   your decision):* cap AQI at 500, recompute AQI from sub-indices without CO, or keep
   Ahmedabad with a documented caveat.
3. **Holt-Winters always chose m = 7.** statsmodels counts each initial seasonal state as a
   parameter, so AIC heavily penalises m = 365. In practice this is weekly HW with a damped
   trend. An annual HW would need deseasonalisation first (e.g. STL + ETS). This is a
   candidate improvement for Phase 2.
4. **SARIMA uses m = 7 + annual Fourier terms, not m = 365.** A 365-lag seasonal ARMA is
   impractically slow and numerically unstable on ~2k points. Regression on 3 annual Fourier
   pairs with SARIMA(p,0,q)(P,0,Q)₇ errors is the standard substitute (see the docstring in
   `src/models/statistical.py`).
5. **Convergence:** no model raised an error in any city. Non-converged candidates in the
   ARIMA (p,q) grid are skipped silently. Selected orders were mostly ARIMA(2,0,2).
6. **LSTM variance:** one seed, a small network, and ~1,800 training windows. Early stopping
   ended training at epoch 16–34. Results will shift with the seed; average several seeds
   before trusting a ranking.
7. **MAPE is inflated at low AQI** (e.g. Hyderabad 33.8% on a mean AQI of 47). RMSE is the
   selection metric, as agreed.
