# AQI Forecasting Driven Health Prediction System

This file gives Claude Code full context on this project. Read it before doing any work here.

## What this project is

A full-stack website with two linked prediction pipelines:
1. **AQI forecasting** — time-series models forecast air quality 7 and 30 days ahead for Indian cities.
2. **Personalized health-risk prediction** — the forecasted AQI + a user's saved health profile feed ML models that predict health risk (classification: risk level, regression: risk score).

Plus two supporting features: a hospital-enquiry map (contact info only, no booking) shown when risk is high, and a light-NLP recommendation assistant (LLM to be added later).

**This is being built for a graded academic course** ("Time Series and Analysis Project") with three phases:
- Phase 1 — Synopsis: 28 Sept – 9 Oct 2026 (8 marks) — **DONE**. EDA + planning only, no code/models. Delivered as a PPTX.
- Phase 2 — Mid-Sem: 19 – 30 Oct 2026 (10 marks) — classical time-series models (ARIMA/SARIMA/Holt-Winters/decomposition), evaluated with RMSE/MAE/MAPE.
- Phase 3 — Final: 16 – 27 Nov 2026 (12 marks) — ML/DL models (LSTM, XGBoost, Prophet) + comparative analysis.

**Important scope note:** the official course rubric only covers the AQI time-series forecasting piece. The health-prediction, hospital-map, and full-stack website are the user's own extension of the project beyond what's graded — build them, but don't assume course deadlines apply to them.

**Health dataset: in use, with a specific disclosure rule — read this before touching the health pipeline.**
The health pipeline uses `synthetic_person_health.csv` (real AQI values joined to synthetic person profiles via a documented formula). This was briefly paused, then resumed on 2026-09-25 after the user's teacher approved proceeding. The user's explicit instruction on how to handle this:
- Use the dataset fully in the actual build — data pipeline, model training, everything downstream.
- Do NOT foreground its synthetic nature anywhere in the product UI or in any presentation/report material — no banner, no callout, no "this data is synthetic" messaging visible to end users or graders. The existing "estimated risk / decision support, not a medical diagnosis" disclaimer is what's user-facing, and that's sufficient.
- DO keep one plain, factual note near where the dataset is loaded/documented in code (e.g. a comment or short docstring in the data-loading module) stating it's a constructed dataset — real AQI joined to synthetic profiles. This is a minimal, out-of-the-way disclosure and is non-negotiable: never claim or imply this data is genuine real-world records if directly asked.
- Do not generate a *new* synthetic dataset as a substitute without being asked — use the existing one.

## End-user flow

1. User signs in via Supabase Auth.
2. User selects/detects their city — current + forecasted AQI for that city is **public**, no login needed.
3. User fills a health profile **once** (age, gender, pre-existing condition, smoker, optionally BMI/exercise/mask usage/occupation/area type). Saved to Supabase, reused automatically on later visits — never re-entered.
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

### Health prediction: `synthetic_person_health.csv` — in use
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

## Working conventions for this repo

- Follow the finalized tech stack above — ask before introducing a different framework/library.
- Any time-series or ML code should report the metrics listed above, and forecasting models must be compared against a naive baseline.
- `synthetic_person_health.csv` is in active use for the health pipeline. Keep its disclosure at the code/documentation level only (see the note near the top of this file) — never surface "synthetic" in the product UI or presentation materials, but never deny or misrepresent it as real data if asked directly.
- The `synopsis` folder (Phase 1 deliverable — PPTX + EDA script) is finished coursework; don't modify it as part of the website build unless asked.
