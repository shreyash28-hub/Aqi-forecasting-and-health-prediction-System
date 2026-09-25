# AQI forecasting: findings

Companion to the generated `summary.md` (all tables) in this folder.

**What this covers:** classical time-series models (ARIMA, SARIMA, Holt-Winters) and ML/DL
models (XGBoost, LSTM, Prophet) forecasting daily AQI 30 days ahead for six cities (Delhi,
Bengaluru, Chennai, Hyderabad, Lucknow, Ahmedabad). Each is compared against three naive
baselines on six rolling-origin test windows per city.

**Setup:**
- Models are fitted on log1p(AQI) and scored on the AQI scale, counting observed days only.
- Each city gets 6 non-overlapping 30-day test windows, 120 days apart (window 0 = the final
  30 days, 2020-06-02 → 2020-07-01). Each window trains on everything before it.
- A model "beats the baseline" when its RMSE is below the best of the three naive baselines
  on the same window.
- The LSTM is averaged over seeds 42, 43 and 44.
- Ahmedabad's AQI is recomputed without CO (section 1).

---

## 1. Ahmedabad: AQI recomputed without CO

### Evidence that Ahmedabad's CO readings are faulty

| | Ahmedabad | Other five cities |
|---|---|---|
| Median daily CO (mg/m³) | **16.2** | 0.57 – 1.37 (Delhi 1.24) |
| Days with CO > 10 mg/m³ | **45.5%** | 0 – 3.6% |
| Hours where CO is the dominant AQI sub-index | **82%** | 7 – 33% |
| Hours with CO sub-index > 300 ("very poor") | **51%** | 0.2 – 4.6% |
| Effect of dropping CO on median daily AQI | **384 → 129** | −7 to −15 points |
| Days with AQI > 500 caused by CO | **412** | 0 |

Delhi has the worst particulate pollution in the set, yet its median CO is less than a
tenth of Ahmedabad's. Ahmedabad's CO also climbs year by year (median 8 → 29 mg/m³ from
2015 to 2018) and then falls to 3.4 in 2020. That pattern fits sensor drift or a
calibration fault, not real combustion levels.

### Method
`city_day.csv` doesn't document how its AQI was computed, so I rebuilt it from `city_hour.csv`:
1. Take 24-hour rolling means of PM2.5, PM10, NOx, SO2 and NH3, and 8-hour rolling maxima of
   CO and O3.
2. Convert each to a CPCB sub-index. Hourly AQI is the largest sub-index, with at least 3
   sub-indices required, including PM2.5 or PM10.
3. Daily AQI is the mean of that day's hourly AQI.

For Ahmedabad, a single-station city, this reproduces the published AQI on **all 1,334
comparable days within ±1**. The same code with CO excluded therefore gives a faithful
CO-free series. The implementation is in `src/aqi.py` and the switch is
`AQI_EXCLUDED_POLLUTANTS` in `src/data_loader.py`.

### Why only Ahmedabad
In the other cities CO readings sit in normal urban ranges and barely move the index (table
above), so their published AQI is used unchanged. Bengaluru has a small high-CO tail (4.6% of
hours with a CO sub-index above 300); it's worth watching but doesn't change the series.

### Effect
- **The recomputed series:** median 129, max 414, no days above 500. Its annual seasonality
  is clearer (STL strength 0.58 → 0.71).
- **The fake 2020 regime shift is gone.** Q1-2020 → Q2-2020 median was 299 → 117 with CO and
  is 116 → 106 without it.
- **Usable history is unchanged** at 995 days (from 2017-10-11). The 2015–2017 outages hit
  every pollutant, not just CO.

Final hold-out RMSE for Ahmedabad before and after the fix:

| Model | With CO | Without CO |
|---|---|---|
| Prophet | 22.89 | **18.53** |
| LSTM | 195.03 (1 seed) | 29.38 (3-seed mean) |
| SARIMA | 157.36 | 32.98 |
| Seasonal naive (weekly) | 28.32 | 33.32 |
| Holt-Winters | 36.38 | 38.08 |
| Naive (last value) | 32.68 | 38.81 |
| XGBoost | 36.58 | 41.57 |
| ARIMA | 70.74 | 42.66 |
| Seasonal naive (annual) | 314.00 | 78.86 |

The three models that failed badly (SARIMA, LSTM, ARIMA) were reverting toward the inflated
CO-driven level of 400+. That failure is gone.

---

## 2. Multi-window results

### Best model per city (lowest mean RMSE over 6 windows)

| City | Best model | Mean RMSE | vs best baseline | Win rate | Beats baseline in | Final-window winner |
|---|---|---|---|---|---|---|
| Delhi | SARIMA | 69.21 | −30% | 33% | 67% of windows | ARIMA |
| Lucknow | Prophet | 55.90 | −33% | 33% | 67% | Prophet |
| Bengaluru | SARIMA | 19.35 | −24% | 17% | 33% | Holt-Winters |
| Chennai | ARIMA | 37.45 | −13% | 17% | 67% | SARIMA |
| Hyderabad | Prophet | 22.39 | −13% | 33% | 50% | XGBoost |
| Ahmedabad | Holt-Winters | 57.44 | −5% | 17% | 67% | Prophet |

(Win rate = share of windows where the model had the lowest RMSE of all 9 candidates,
baselines included.)

### What the windows show
1. **Every city has a model that beats the naive baselines on average.** On the June 2020
   window alone, Hyderabad had none. The margin is large in the high-pollution, strongly
   seasonal cities (Delhi −30%, Lucknow −33%) and thin in Ahmedabad (−5%).
2. **No model dominates any city.** The highest win rate anywhere is 2 of 6 windows (33%).
   The best-model margins are also often within noise:
   - Delhi: SARIMA 69.21 vs Prophet 69.31
   - Ahmedabad: Holt-Winters 57.44 vs SARIMA 57.88
   - Chennai: ARIMA 37.45 vs LSTM 37.48 vs SARIMA 37.99

   Treat "best model" as "best on this evidence", not a clear victory.
3. **SARIMA is the most consistent model.** It has the best mean rank in 5 of 6 cities
   (Delhi 2.3, Bengaluru 3.3, Chennai 3.3, Lucknow 3.0, Ahmedabad 3.0). The exception is
   Hyderabad, where Prophet ranks 2.7. The annual Fourier terms help most in the
   winter-onset windows, where persistence fails badly.
4. **Winter onset separates models that know about seasons from those that don't.** In Delhi's
   Oct–Nov 2019 window (stubble burning and Diwali), last-value naive scores RMSE 246, ARIMA
   237 and Holt-Winters 245. Models with an annual component score far better: Prophet 105,
   annual seasonal naive 103, SARIMA 126. In the June 2020 window this reverses and
   persistence is hard to beat. That's why a single window was misleading.
5. **The winner changed in 5 of 6 cities** between the final window alone and the 6-window
   view. Only Lucknow (Prophet) kept its winner. A single 30-day hold-out isn't enough to
   pick a production model.
6. **Prophet is high-variance.** In Ahmedabad it wins 2 windows but has the worst mean RMSE of
   any model (88.7). It misses badly in Oct 2018 (RMSE 170, with only 365 training days, so
   the yearly seasonality is fitted on one cycle) and in Oct 2019 (160).
7. **Bengaluru's best model beats the baseline in only 2 of 6 windows.** SARIMA wins on mean
   RMSE by avoiding large misses, not by being usually better. Bengaluru's AQI is low and
   stable enough that persistence is a strong forecast there.

---

## 3. LSTM reproducibility

- **Seeding:** each run seeds torch and numpy and runs single-threaded, because CPU float
  reductions (and so results) depend on thread count. The same seed gives the same forecast:
  seed 42 reproduces the original Delhi RMSE of 32.85.
- **Averaging:** the evaluation runs **seeds 42, 43 and 44** and reports the mean of their
  metrics. Per-seed results are in `lstm_seed_runs.csv`.
- **Seed matters:**

| City | Seed 42 | Seed 43 | Seed 44 | Mean (reported) |
|---|---|---|---|---|
| Delhi | 32.85 | 39.99 | 54.87 | 42.57 |
| Lucknow | 37.91 | 73.49 | 37.23 | 49.54 |
| Bengaluru | 23.80 | 9.33 | 12.99 | 15.37 |

  (Final window.) Averaged over all windows, the seed-to-seed standard deviation of RMSE is
  0.7 (Chennai) to 6.9 (Delhi).
- **The earlier "LSTM wins Delhi" result was a lucky seed.** With the 3-seed mean, the LSTM
  drops from 1st to 7th of 9 on Delhi's final window.
- **XGBoost:** its results also depend on thread count (±0.5–2 RMSE), so it is now pinned to
  a single thread. No winner changed.

---

## 4. Preprocessing results

- **Stationarity:** the ADF test rejects a unit root in every city (p ≤ 0.012), so `d = 0`.
  The KPSS test rejects stationarity in 5 of 6 cities (p ≈ 0.01; Lucknow 0.10). Together
  these say the series has no unit root but moves around a seasonal level. So seasonality
  is modelled explicitly (Fourier terms, seasonal components) rather than differenced away.
- **Seasonal period:** ~365 days, confirmed in every city.
  - The autocorrelation of the detrended series peaks at lags 363–370.
  - STL seasonal strength at m = 365 is 0.20 to 0.75, against ≤ 0.07 at m = 7.
- **Gaps:** gaps of up to 21 days are time-interpolated. After a longer outage, the series
  starts from the most recent clean segment. Interpolated days are never scored.

---

## 5. Remaining limitations

1. **Holt-Winters always selects m = 7.** statsmodels counts each initial seasonal state as a
   parameter, so AIC penalises m = 365 heavily. A true annual Holt-Winters would need
   deseasonalisation first (e.g. STL + ETS).
2. **SARIMA uses m = 7 plus annual Fourier terms, not m = 365.** A 365-lag seasonal ARMA is
   impractically slow and unstable on ~2k points. Fourier regression with SARIMA errors is
   the standard substitute.
3. **Ahmedabad's earliest window trains on only 365 days,** after the 2015–2017 outages.
   Yearly-seasonal models (Prophet especially) are unreliable there.
4. **Six windows is still a small sample.** Differences under ~5% mean RMSE shouldn't be read
   as meaningful. Before the model is wired into the site, the next step is to either
   choose by mean rank with mean RMSE as the tiebreaker, or average the top 2–3 models
   per city.
5. **MAPE is inflated at low AQI** (Bengaluru, Hyderabad). RMSE stays the selection metric.

---

## 6. Original single-window results (before these fixes)

The first run used a single June 2020 hold-out, Ahmedabad's published AQI (CO included), and
one LSTM seed (42). It is kept for comparison. Current final-window results are in
`summary.md`.

| City | Winner | RMSE | Best baseline RMSE | Beat baseline? |
|---|---|---|---|---|
| Delhi | LSTM | 32.85 | 41.06 | yes (lucky seed, see section 3) |
| Ahmedabad | Prophet | 22.89 | 28.32 | yes (on CO-inflated data) |
| Lucknow | Prophet | 32.03 | 36.88 | yes |
| Bengaluru | Holt-Winters | 8.55 | 9.60 | yes |
| Chennai | SARIMA | 20.68 | 21.14 | yes |
| Hyderabad | XGBoost | 15.94 | 14.08 | **no** |

That window (COVID lockdown plus monsoon onset) is atypical. Hold-out AQI was far below the
same weeks in 2019 (Delhi 126 vs 194, Lucknow 96 vs 166), which strongly favoured
persistence. The multi-window evaluation in section 2 is the one to rely on.
