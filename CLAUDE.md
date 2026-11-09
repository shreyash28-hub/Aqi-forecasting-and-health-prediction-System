# AQI Forecasting Driven Health Prediction System

This file gives Claude Code full context on this project. Read it before doing any work here.

## What this project is

A full-stack website with two linked prediction pipelines:
1. **AQI forecasting** — time-series models forecast air quality 7 and 30 days ahead for Indian cities.
2. **Personalized health-risk prediction** — the forecasted AQI + a user's saved health profile feed ML models that predict health risk (classification: risk level, regression: risk score).

Plus two supporting features: a hospital-enquiry map (contact info only, no booking) shown when risk is high, and a light-NLP recommendation assistant (LLM to be added later).

**This is being built for a graded academic course** ("Time Series and Analysis Project") with three phases:
- Phase 1 — Synopsis: 28 Sept – 9 Oct 2026 (8 marks) — **DONE**. EDA + planning only, no code/models. Delivered as a PPTX.
- Phase 2 — Mid-Sem: 19 – 30 Oct 2026 (10 marks) — classical time-series models (ARIMA/SARIMA/Holt-Winters/decomposition), evaluated with RMSE/MAE/MAPE. **DONE** (marked complete 2026-11-09; the deck restyle idea was dropped).
- Phase 3 — Final: 16 – 27 Nov 2026 (12 marks) — ML/DL models (LSTM, XGBoost, Prophet) + comparative analysis.

**Important scope note:** the official course rubric only covers the AQI time-series forecasting piece. The health-prediction, hospital-map, and full-stack website are the user's own extension of the project beyond what's graded — build them, but don't assume course deadlines apply to them.

**Health dataset: in use, with a specific disclosure rule — read this before touching the health pipeline.**
The health pipeline uses `person_health.csv` (real AQI values joined to synthetic person profiles via a documented formula). This was briefly paused, then resumed on 2026-09-25 after the user's teacher approved proceeding. The user's explicit instruction on how to handle this:
- Use the dataset fully in the actual build — data pipeline, model training, everything downstream.
- Do NOT foreground its synthetic nature anywhere in the product UI or in any presentation/report material — no banner, no callout, no "this data is synthetic" messaging visible to end users or graders. The existing "estimated risk / decision support, not a medical diagnosis" disclaimer is what's user-facing, and that's sufficient.
- DO keep one plain, factual note near where the dataset is loaded/documented in code (e.g. a comment or short docstring in the data-loading module) stating it's a constructed dataset — real AQI joined to synthetic profiles. This is a minimal, out-of-the-way disclosure and is non-negotiable: never claim or imply this data is genuine real-world records if directly asked.
- Do not generate a *new* synthetic dataset as a substitute without being asked — use the existing one.

## End-user flow

1. User signs in via Supabase Auth.
2. User selects/detects their city — current + forecasted AQI for that city is **public**, no login needed.
3. User fills a health profile **once** (required: age, gender, pre-existing condition, smoker, occupation, area type, mask usage, outdoor hours per day; optional: BMI, exercise hours, family history of respiratory disease). Saved to Supabase, reused automatically on later visits — never re-entered.
4. Backend combines the saved profile with the forecasted AQI/pollutants for the selected horizon (7-day / 30-day).
5. Health models return a risk level (Low/Moderate/High/Severe) from classification, a risk score from regression, and per-class confidence — not just a bare label.
6. Result shown day-by-day following the forecast curve (e.g. "Tue: Moderate, Fri: High").
7. Each prediction run is saved to the user's history so they can look back.
8. If risk is High/Severe: nearby hospitals appear on a map with contact details (enquiry only — no booking), and the assistant surfaces relevant precautions.
9. UI must clearly label results as estimated decision support, not a medical diagnosis.

## Models and metrics

**AQI forecasting** (best by lowest RMSE on a 30-day hold-out; also report MSE/MAE/MAPE; must beat a naive baseline):
- ARIMA, SARIMA
- Holt-Winters exponential smoothing
- Seasonal decomposition (additive/multiplicative) — used for diagnosis, feeds preprocessing decisions
- LSTM and variants
- XGBoost on lag features, other ensembles
- Facebook Prophet (if it suits the data's missingness)

**Health classification:**
- Random Forest, XGBoost, deep learning (MLP)
- Target: `HealthRiskLevel` (Low/Moderate/High/Severe)
- Best by weighted F1; also report accuracy/precision/recall; watch per-class recall — classes are imbalanced

**Health regression:**
- Random Forest, XGBoost, deep learning (MLP)
- Target: `HealthRiskScore` (primary); `HospitalVisitsLastYear` available as a secondary target
- Best by RMSE; also report MSE/MAE/R²

Model selection is automatic (best model by metric), shown on a leaderboard on the site.

## Tech stack (finalized — do not deviate without asking)

**Frontend:** Next.js, React + TypeScript, Tailwind CSS, shadcn/ui, Motion (Framer Motion), ECharts, Lucide React, Leaflet (OpenStreetMap) for the hospital map, Overpass API for hospital data.

**Backend:** FastAPI, Python.

**Database & Auth:** Supabase, PostgreSQL, Supabase Auth + Row Level Security.

**ML:** scikit-learn, XGBoost.

**Time series:** statsmodels, Prophet.

**Deployment:** Vercel (frontend), Render or Railway (FastAPI backend).

**Maps:** free, no API key — OpenStreetMap tiles via Leaflet, hospital name/address/phone/website via the Overpass API. "Enquire" means show contact details only.

**Assistant:** light NLP for now — intent matching + a curated precautions knowledge base personalized with the user's AQI/risk. LLM API can be swapped in later.

## Data access model (public vs. auth-gated)

**Public, no login:** current/forecasted AQI per city, model leaderboard, hospital locations/contact details, general assistant precaution content.

**Auth-gated with Row Level Security (`auth.uid() = user_id`):**
- `profiles` — user_id, age, gender, condition, smoker, bmi, occupation, area_type, mask_usage, exercise_hours, family_history, updated_at
- `saved_forecasts` — id, user_id, city, generated_at, horizon, model_used, forecast_json
- `risk_predictions` — id, user_id, forecast_id, predicted_at, city, date_of_prediction, risk_level, risk_score, model_used, input_snapshot_json

**Public tables (no user column, no RLS needed):**
- `aqi_forecasts_cache` — city, generated_at, model_used, horizon, forecast_json
- `model_leaderboard` — task, model_name, metrics_json, trained_at

Hospitals are not stored in Supabase — fetched live from Overpass per map view (add caching later if needed).

This schema is a sketch — refine exact column types/indexes/RLS policy syntax during the actual build.

## Datasets

### AQI forecasting: `city_day.csv` (from `Aqi.zip`, real CPCB data via Kaggle)
- ~29,500 rows, 26 cities, 2015-01-01 to 2020-07-01.
- Columns: City, Date, PM2.5, PM10, NO, NO2, NOx, NH3, CO, SO2, O3, Benzene, Toluene, Xylene, AQI, AQI_Bucket.
- Use only the 6 well-covered cities: Delhi, Bengaluru, Chennai, Hyderabad, Lucknow, Ahmedabad (1,300–2,000 days each). Exclude cities under ~300 days (Aizawl, Kochi, Shillong, etc.).
- Missing values: ~16% AQI, ~38% PM10 overall (varies a lot by city — e.g. Delhi ~0.5% missing AQI vs. Ahmedabad ~33.6%). Interpolate short gaps; per-city median fill only where a complete row was needed for a join.
- Data ends mid-2020 — forecasts will start from there. Not flagged in the product UI; user is handling this directly with their instructor.

### Health prediction: `person_health.csv` (renamed from `synthetic_person_health.csv` on 2026-10-30; same data) — in use
- 7,500 rows, 28 columns, zero missing values.
- **Real** AQI/pollutant values (AQI, PM2_5, PM10, NO2, SO2, O3) sampled from actual `city_day.csv` rows by real city + real date.
- **Synthetic** person and risk label: PersonID, Name, Age, Gender, City, Date, Occupation, AreaType, IncomeLevel, PreexistingCondition (No Condition/Asthma/COPD/HeartDisease/Diabetes/Hypertension), FamilyHistoryRespiratory, Smoker, BMI, BMICategory, ExerciseHoursPerWeek, OutdoorExposureHours, MaskUsage, YearsLivedInCity, VulnerabilityScore, HealthRiskScore, HealthRiskLevel, HospitalVisitsLastYear.
- Built because no public dataset links person-level health (age, conditions) to city+date air quality. Target built from: a vulnerability multiplier (age, condition, smoking, family history, BMI, exercise) × an effective-exposure term (real AQI/PM2.5/NO2 adjusted by outdoor exposure hours, mask usage, area type), plus noise, bucketed into 4 risk bands. `HospitalVisitsLastYear` derived via Poisson sampling scaled by risk level and income-based healthcare access.
- Sanity-checked: risk climbs from AQI ~86 (Low) to AQI ~515 (Severe); mask use lowers mean risk score (1.98 → 1.29); industrial areas score higher than residential (2.05 vs 1.56); hospital visits rise from 0.39/yr (Low) to 3.70/yr (Severe).
- `Gender` and `YearsLivedInCity` are not wired into the risk formula (demographic detail only). `IncomeLevel` affects only `HospitalVisitsLastYear`, not `HealthRiskScore`.
- **Disclosure rule (see the note near the top of this file):** don't foreground this dataset's synthetic nature in the UI or presentation materials; do keep a plain factual note in code/data-loading docs; never claim it's genuine real-world data if directly asked.

### Datasets considered and rejected
- `air_quality_health_impact_data.csv` (5,811 rows) — real correlation (~0.61) but no city/date/age, so no personalization possible. Kept only as a fallback reference, not used for training.
- `Air_quality_data.csv` (18,265 rows) — rejected, values are effectively random (no seasonality, no city variation, AQI uncorrelated with PM2.5).
- `air_quality_health_dataset.csv` (88,489 rows) — rejected, non-Indian cities, nonsensical random dates (2020–2262), zero correlation between hospital admissions and AQI.
- WHO-SAGE India — rejected, wrong time period, no city/date link to AQI, access-gated.

## Key decisions log

- User profile: saved to Supabase, reused every visit, never re-entered.
- Temperature/humidity/wind: not used anywhere (were only in the rejected health-impact file).
- Hospital "enquire": contact details only, never booking.
- 2020 AQI data cutoff: not flagged on the site; user is handling this with their instructor separately — don't add a caveat about it unless asked.
- Health model features: AQI, PM2_5, PM10, NO2, SO2, O3 + the person-level columns above. No weather variables.
- **2026-09-25: synthetic health dataset briefly paused, then resumed the same day after the user's teacher approved proceeding with it. In active use per the disclosure rule above.**
- 2026-09-25: Ahmedabad AQI is recomputed from `city_hour.csv` **without CO** (faulty CO sensor: median 16 mg/m³ vs ~1 elsewhere, drove AQI to 2,049). Other cities use published AQI. Evidence in `reports/forecasting/findings.md`; switch is `AQI_EXCLUDED_POLLUTANTS` in `src/data_loader.py`.
- 2026-09-25: AQI model selection uses 6 rolling-origin 30-day windows per city (lowest mean RMSE), not just the final June 2020 hold-out. LSTM metrics are averaged over seeds 42/43/44.
- 2026-09-25: Deployed AQI models live in `models/aqi/<city>/` (winner retrained on full history, native save formats, `registry.json` index). Backend should load them with `src.model_store.load_forecaster(city).forecast(horizon)`, not retrain. Regenerate with `python -m src.train_final_models` after re-running the evaluation.
- 2026-09-26: PM2.5 and NO2 are now forecast per city (same multi-window pipeline, `--target`), saved under `models/pm25/` and `models/no2/`. When no model beats the naive baseline on mean RMSE, the baseline is deployed (Hyderabad PM2.5, Ahmedabad NO2). PM10/SO2/O3 aren't forecast: too little data in several cities, and they don't improve the health model.
- 2026-09-26: Health models deployed in two variants: profile + AQI + PM2.5 + NO2 (primary) and profile + AQI (fallback). MLP selected for both tasks in both variants. Boundary rule: classifier level is the headline; when the score implies a different level the day is `borderline`, shown as a range, and `alert_level` (the higher level) drives High/Severe actions. Backtest on real forecast inputs: primary beats fallback, but air-forecast error is now the main source of health-risk error.
- 2026-09-25: Health models first trained (`python -m src.health.train`). `VulnerabilityScore` and `HospitalVisitsLastYear` are excluded as target leakage. The model needs `OutdoorExposureHours`, which is not yet in the `profiles` schema sketch above: add an `outdoor_hours` column when building the database. Load with `src.health.store.load_health_predictor()`.
- 2026-09-26: FastAPI backend started in `src/api/` (public endpoints: cities, forecast, risk prediction, profile schema, leaderboards; tests in `tests/`). Profile exposure fields (occupation, area type, mask usage, outdoor hours) are **required**: filling them with typical values made a 67-year-old COPD patient Low instead of Moderate. BMI, exercise and family history stay optional (filled with typical values, reported in `imputed_fields`).
- 2026-09-26: Supabase schema written (`supabase/migrations/0001_init.sql`, setup steps in `supabase/README.md`). Refinements to the sketch above: `profiles` gets `outdoor_hours` and the same required/optional fields as the API; `risk_predictions` has one row per forecast day plus confidence, probabilities, borderline, risk_range and alert_level; history tables are append-only. The public tables (`aqi_forecasts_cache`, `model_leaderboard`) **do** get RLS, with a public read-only policy, because without RLS the public anon key could write to them; only the backend's service role writes.
- 2026-09-26: Supabase connected (project ref `oopbjwhsauqmoqgheljm`; URL and anon key in the git-ignored `.env`). Signed-in endpoints in `src/api/me.py`: profile get/save, prediction run saved to history, history list/detail/delete. The backend verifies the user's access token with Supabase Auth and makes every table call **with the user's own token**, so RLS applies; the service-role key is not needed for user data. Tests use an in-memory Supabase fake that emulates RLS (`tests/test_me.py`); `scripts/check_accounts_live.py` is the user-run live check.
- 2026-09-26: **Frontend design agreed (no code yet; wait for the user's go-ahead before coding).** Site name: **Airware**. Full spec in `docs/frontend_design.md`; approved visual reference `docs/design/airware_overview_mockup.html`. Key points: data-first dashboard (IQAir/Windy style), not a Lovable-style landing page; avoid "AI template" tells (giant centred gradient headline, glow blobs, gradient text, pill badges); IBM Plex Sans + Plex Mono numbers; neutral greys + one deep-teal brand colour; CPCB AQI colours reserved for data; light + dark with a header toggle; full-width fluid layout to 1840 px. The user's screen is 1920×1080 with Windows scaling (~1280 CSS px), so every page must be checked at 1280, 1536 and 1920 px with no half-empty rows.
- 2026-09-26: **Landing page added to the design** (mockup approved, `docs/design/airware_landing_mockup.html`). Routes: `/` landing page, `/dashboard` the approved Overview, plus `/sign-in`, `/profile`, `/risk`, `/history`, `/models`. Same visual language as the dashboard. Coding waits for the user's go-ahead. A partly-created `frontend/` folder exists from an interrupted `create-next-app` run: check it and redo or clean it when coding starts, and don't commit it before then.
- 2026-10-06: **Signed-in pages and Models built** (`/sign-in`, `/profile`, `/risk`, `/history`, `/history/[id]`, `/models`). The browser uses Supabase only for sign-in; all data goes through the FastAPI `/api/me/*` endpoints with the user's token. `/risk` reuses the latest saved run and only calculates (and saves) a new one when there is none or the profile changed since, so visits don't flood history. The hospital map is still to come; High/Severe runs show a callout in its place.
- 2026-10-30: **Hospital enquiry map built.** Backend `GET /api/hospitals?city=|lat=&lon=&radius_km=` (`src/api/hospitals.py`, public) queries Overpass for `amenity`/`healthcare=hospital`, keeps named places, drops clearly non-medical names, sorts by distance and caches results for a week in memory and in the git-ignored `data/cache/hospitals.json` (a fresh Overpass query takes 30-70 s). Frontend: plain Leaflet (no react-leaflet) with OSM tiles, CSS pins (red = emergency department), list with phone/website/directions; public page `/hospitals?city=` and a panel on My risk when `show_hospitals` is true. Contact details only, with an "in an emergency call 112 / 108" note. 9 tests in `tests/test_hospitals.py` (Overpass mocked).
- 2026-10-30: **Live data, step 1 done: daily AQI from OpenAQ.** `scripts/download_openaq.py` saves hourly readings from 24 CPCB stations (4 per city, picked from `reports/openaq_sensors.json`) for Feb 2025 to today under the git-ignored `data/openaq/raw/` (resumable; re-run to fetch new data). `src/live_data.py` (`python -m src.live_data`) builds `data/processed/live_city_day.csv`: IST days, station mean per hour, `src.aqi.hourly_aqi`, at least 16 hours per day. OpenAQ labels CPCB gases "ppb" but they are CPCB units (µg/m³, CO mg/m³), so no conversion. Cleaning: negatives, stuck runs (12 h), PM2.5 > PM10 hours, and station-days far above the other stations (Chennai Manali O3 pinned at 500). NO2 sub-index uses NO2 (no NOx sensors); CO kept for Ahmedabad (live CO sensors are normal). Spot-checks: Delhi 20/21 Oct 2025 346/362 vs CPCB 345/351; above ~450 our values run higher (CPCB caps at 500, we extend the top band like `city_day.csv`). Next: retrain on this data, forecast from today.
- 2026-10-30: **Live data, step 2 done: the site forecasts from today.** Live models in `models/live/<aqi|pm25|no2>/` (results in `reports/forecasting/live/`), trained on Feb 2025 to yesterday with `python -m src.run_forecasting --source live --target T` then `python -m src.train_final_models --source live --target T`. Evaluation: 5 windows stepping back 45 days (the live series is too short for 6 x 120). Models (not baselines) use a **seasonal prior**: the city's average annual shape from 2015-2020 (`historic_profile` in `src/preprocessing.py`, log space) is subtracted before fitting and added back to forecasts; stored in `metadata.json` `params.seasonal_prior`. It cut mean RMSE ~6% overall and roughly halved some October errors (Ahmedabad ARIMA 49 to 21); `--no-prior` reruns the comparison without it (`reports/forecasting/live/aqi/no_prior/`). Every city's live AQI and PM2.5 winner beats the naive baseline; Lucknow NO2 deploys the naive baseline. The API serves the live set when `models/live/aqi/registry.json` exists (`FORECAST_SOURCE=history|live` forces one); `/api/leaderboard/forecast` takes `source=` (default: the served set). The 2015-2020 coursework models and reports are unchanged. Daily update: `python -m src.refresh_live` (download, rebuild, refit; `--evaluate` reruns the comparison), then restart the API. My risk recalculates when the city's forecast origin moved on.
- 2026-10-30: **Today's forecast starts from today's readings (`src/nowcast.py`).** The models only see complete days, so day one of the forecast ignored how today was going (Delhi showed AQI 256 when the stations read about 107 by 13:00). `python -m src.nowcast` saves each city's AQI, PM2.5 and NO2 so far today to `data/processed/live_nowcast.json`; the API applies them at startup (`apply_signals`): forecast_k is multiplied by exp(w x rho^k x r) in log space, r = today-so-far vs forecast, w = hours/(hours+6), rho = 0.7, so the effect fades in a few days. Backtest (`scripts/backtest_nowcast.py`, `reports/forecasting/live/nowcast*.md`, ARIMA stand-in, second half incl. winter): at a 13:00 cut-off today's AQI RMSE falls ~57%, day 2 ~12%, day 3 ~5%, nothing beyond; PM2.5 and NO2 gain similarly. Day-one gain is partly because over half of today's hours are already known. `/api/forecast` returns `readings_as_of`; the dashboard shows "Today updated with readings to HH:MM". `python -m src.refresh_live --nowcast-only` updates it during the day; restart the API afterwards. The dashboard AQI is on India's CPCB scale, which reads higher than the US-style AQI Google shows (PM2.5 100 µg/m3 is about 174 US, about 230 CPCB).
- 2026-10-30: **Daily refresh for a deployed site built (not yet deployed).** `python -m src.refresh_live` now needs only an OpenAQ key and `data/openaq/stations.json` (committed): `src/openaq.py` downloads the last 6 days of hourly readings (~144 requests) to the git-ignored `data/openaq/recent/`, `src.live_data --recent` merges the complete days into `data/processed/live_city_day.csv` (values identical to the full download on overlapping days), the live models are refitted (~90 s total), and today's signals are saved. The seasonal prior is cached in `models/live/seasonal_profiles.json` so the job doesn't need the Kaggle zip. Retrained models (~25 MB) are NOT committed daily: `src/live_bundle.py` packs `models/live` plus the daily data and nowcast into `live_bundle.tar.gz`, uploaded to a public Supabase Storage bucket by `.github/workflows/refresh-live.yml` (06:00 IST; secrets OPENAQ_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY; variable LIVE_BUNDLE_URL). The API downloads the bundle at startup and, when `LIVE_REFRESH_MINUTES` is set, every N minutes (`src/api/refresher.py`, also fetches new readings for the nowcast); `ModelService.maybe_reload` reloads forecasts in the background when the registries or nowcast file change, so no restart is needed (checked on requests, every 10 s; a bad file keeps the old forecast). `requirements.lock.txt` pins the library versions that pickled models need: the job and the API must install from it. Setup steps in `docs/live_refresh.md`. Only the model comparison (`--evaluate`, needs `data/Aqi.zip`) stays manual.
- 2026-10-31: **Deployment prepared for Render (API) + Vercel (site)**; steps in `docs/deployment.md`, Blueprint `render.yaml` (Singapore, free plan, Python 3.12.5, installs `requirements.lock.txt`). The API used ~490 MB (torch, Prophet, statsmodels, XGBoost for the 18 forecasters), too close to Render's 512 MB, so the daily refresh now also writes `data/processed/live_forecasts.json` (`python -m src.forecast_export`, in the bundle) and the API serves those precomputed 30-day forecasts: ~170 MB, starts in ~1.5 s, none of those libraries imported. It falls back to loading the models only if the export is missing or doesn't match the registries (model and train_end per city and target). `src/preprocessing.py` imports statsmodels lazily for the same reason. The scheduled refresh ran by itself on 2026-10-31 (models trained to 30 Oct).
- 2026-10-31: **Deployed.** Site: https://aqi-forecasting-and-health-predicti.vercel.app (Vercel, root `frontend`, env NEXT_PUBLIC_API_URL / NEXT_PUBLIC_SUPABASE_URL / NEXT_PUBLIC_SUPABASE_ANON_KEY). API: https://airware-api.onrender.com (Render Blueprint `render.yaml`, free plan, Singapore; ALLOWED_ORIGINS = the Vercel URL + localhost:3000). Supabase Auth Site URL / redirect URLs point at the Vercel URL. Fixes found while deploying: the bundle install renamed `models/live`, which Render's filesystem refuses (EXDEV), so `src/live_bundle.install` now swaps files one by one with registries last; forecasts start at today even if the models are a day old (`ModelService.air_forecast`, a 30-day request may return 29 days); `/api/health` has a `live` section (served_from, origin dates, last bundle/readings refresh and errors), the first place to look when something is off.
- 2026-10-31: **Forecast page built** (`/forecast?city=`, `frontend/src/components/forecast/forecast-view.tsx`): week-by-week summary (average AQI, worst day, Poor-or-worse days), "How reliable is this?" (deployed model per target, typical error = mean RMSE over the live test windows, gain over the naive baseline, from `/api/leaderboard/forecast`), AQI chart with the last 30 measured days running into the 30-day forecast plus today's readings so far (`TrendChart`, one axis, measured solid / forecast dashed / today a diamond, CPCB bands), PM2.5 and NO2 charts with India's 24-hour standards (60 and 80 µg/m³) as reference lines, and a day-by-day table in two halves. New public endpoint `GET /api/observed/{city}?days=` returns the measured daily AQI/PM2.5/NO2 from `live_city_day.csv` and `today_so_far` from the nowcast signals (empty for the 2015-2020 models).
- 2026-10-31: **Live models: seasonal prior scaled per city, no double annual terms.** Old setup: SARIMA's 3 annual Fourier pairs and Prophet's yearly seasonality re-fitted the annual cycle on top of the 2015-2020 prior from <2 years of data, and the full-strength prior didn't match cities whose seasonality changed. Result: Delhi's and Lucknow's AQI and PM2.5 forecasts contradicted each other on 29/30 and 28/30 days (PM2.5 sub-index above the AQI; Lucknow AQI forecast 56 vs 148 measured in Nov 2025, PM2.5 114 vs 72). Now `fit_prior_scale` (src/preprocessing.py) scales the prior by the slope of y ~ a + c*t + b*prior on the training data (clipped 0-1.5; e.g. Lucknow AQI 0.68, Delhi 1.18, Hyderabad PM2.5 0.28), stored as `params.prior_scale`; SARIMA/Prophet get `annual=False` when a prior is used (`OWN_ANNUAL` in run_forecasting). Apr-Oct test-window RMSE moved slightly (AQI/PM2.5 a little worse, NO2 a little better; every city still beats the naive baseline) but those windows contain no winter; all 6 cities now have 0/30 inconsistent days, checked by `inconsistent_days` in `src/forecast_export.py` (prints a warning on export). 2015-2020 coursework models unchanged (no prior there).
- 2026-10-31: **Hospital map no longer depends on Overpass at request time.** The public Overpass servers were overloaded (all timed out or 504'd, including from Render), so the deployed map failed. `scripts/build_hospitals.py` stores every named hospital within 25 km of each city centre in `data/hospitals.json` (committed, ~1.4 MB, (c) OpenStreetMap contributors / ODbL; Delhi 854, Bengaluru 1,135, Chennai 844, Hyderabad 1,040, Lucknow 267, Ahmedabad 788; Lucknow has almost no phone numbers in OSM). `/api/hospitals` answers from it in ~0.2 s whenever the search circle lies inside a stored area (city searches and "use my location" in the city); only searches elsewhere go to Overpass. Re-run the script every month or so.
- 2026-10-31: **Mid-sem (Phase 2) deliverables built.** Guidelines: Milestone 2 PDF (evaluation 19 Oct - 7 Nov; rubric: relevance of algorithms 3, synchronization of design and implementation 3, implementation and demonstration 3, presentation clarity 1). `python -m src.phase2` (after `src.run_forecasting`) writes `reports/phase2/`: preprocessing and stationarity tables, decomposition and ACF/PACF plots, ARIMA AIC grids, fitted parameters, residual diagnostics (Ljung-Box, Jarque-Bera), hold-out forecast plots, RMSE/MSE/MAE/MAPE for ARIMA/SARIMA/Holt-Winters vs the 3 naive baselines, and `observations.md`. It refits the models with the project's own `src.models.statistical` functions (asserts the AIC grid matches `fit_arima`). Result: the best classical model beats the naive forecast in all 6 cities (SARIMA Delhi/Lucknow/Bengaluru, ARIMA Chennai, Holt-Winters Ahmedabad and Hyderabad, the latter only by 0.2%); Holt-Winters fails Ljung-Box everywhere and AIC picks m = 7 for it in every city. Presentation: 8 slides, `docs/phase2/AQI_Forecasting_Phase2_MidSem.pptx`, built by `docs/phase2/build_deck.js` (pptxgenjs; data from `docs/phase2/deck_data.py`; it post-processes chart XML because pptxgenjs writes blank points and per-series dashes that PowerPoint refuses to open). Demo: `notebooks/02_classical_models.ipynb` (one city end to end; needs nbformat/nbclient/ipykernel only to re-execute it).
- 2026-11-09: **Phase 2 complete.** The interview guide and the health Q&A sheet (`docs/interview/`, `docs/health_system_qa.*`) are the user's private prep notes: git-ignored, never to be committed or pushed. The repo is public and still tracks `docs/` and `reports/`; hiding them (make the repo private, or rewrite history) is postponed by the user. If redone, keep `reports/**/leaderboard.json` tracked (the API and the daily refresh read them).
- 2026-09-26: **Live 2026 data deferred until after the frontend** (user's decision). The site must eventually show today's AQI and forecast from today, never by relabelling 2020 dates. Options found: Open-Meteo air-quality API (free, no key; CAMS model estimates; all 6 cities; history from ~Sep 2022 plus a 5-day forecast; reads low for India, e.g. Bengaluru PM2.5 4.5 vs ~20-40 at stations) versus station data via OpenAQ (free API key; CPCB stations; consistent with the training data) or data.gov.in (official, current only). Recommended: OpenAQ (optionally with Open-Meteo filling gaps), a daily refresh job, and retraining on recent data with the naive-baseline check. Coursework evaluation stays on the 2015-2020 data.
- 2026-10-05: **Frontend build started** in `frontend/` (Next.js 16 App Router, React 19, Tailwind v4, shadcn/ui "base-nova" style (Base UI primitives, not Radix), Motion, ECharts 6 with tree-shaken imports, Lucide). Done: theme (IBM Plex fonts, design tokens, light/dark toggle with no-flash init script), both headers, landing page (`/`) and dashboard (`/dashboard?city=&h=`), wired to the live FastAPI API; placeholder pages for `/forecast`, `/risk`, `/history`, `/models`, `/sign-in`. Next.js 16 bundles its own docs at `frontend/node_modules/next/dist/docs/`: read them before using Next APIs. Wide breakpoint is 1700 px (`--breakpoint-wide: 106.25rem`, must be in rem to sort after `lg`). Verify layouts with headless Edge screenshots at 1280/1536/1920 px when the browser pane is in use by the user.

## Working conventions for this repo

- Follow the finalized tech stack above — ask before introducing a different framework/library.
- Any time-series or ML code should report the metrics listed above, and forecasting models must be compared against a naive baseline.
- `person_health.csv` is in active use for the health pipeline. Keep its disclosure at the code/documentation level only (see the note near the top of this file) — never surface "synthetic" in the product UI or presentation materials, but never deny or misrepresent it as real data if asked directly.
- After every completed task, update the progress report: edit the CONTENT section of `docs/progress/build_progress.js` (status table, work done, results, remaining work, change log, last-updated date) and run `node docs/progress/build_progress.js` to regenerate `docs/Project_Progress.docx`. It may be shared, so it follows the dataset disclosure rule (no "synthetic" wording).
- The `synopsis` folder (Phase 1 deliverable — PPTX + EDA script) is finished coursework; don't modify it as part of the website build unless asked.
