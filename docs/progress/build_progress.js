// Generates docs/Project_Progress.docx: work done, work remaining, key results.
// Update the CONTENT section below after every task, then run:
//     node docs/progress/build_progress.js
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, HeadingLevel,
  AlignmentType, WidthType, ShadingType, BorderStyle, LevelFormat, Footer, PageNumber,
} = require("docx");

// =========================================================================== CONTENT

const LAST_UPDATED = "13 November 2026";
const LATEST_COMMIT = "5c69fb6 Run the daily refresh after midnight IST, with a backup run";

const AT_A_GLANCE = [
  // [area, status, note]
  ["AQI forecasting (6 cities)", "Done", "6 models + naive baselines, 6 test windows per city"],
  ["PM2.5 and NO2 forecasting", "Done", "Same pipeline; naive forecast deployed where no model beats it"],
  ["Saved forecasting models", "Done", "18 city forecasters, loadable without retraining"],
  ["Health-risk models", "Done", "Level (F1 0.873) and score (RMSE 0.198); primary + fallback variants"],
  ["FastAPI backend: public endpoints", "Done", "7 endpoints"],
  ["Supabase: database and sign-in", "Done", "Project created, tables and row-level security live and verified"],
  ["Backend: sign-in, saved profile, history", "Done", "5 signed-in endpoints; 41 tests pass in total"],
  ["Live check with a real test user", "Done", "All 8 checks passed against the real Supabase project"],
  ["Frontend design (Airware)", "Done", "Landing page and dashboard designs approved; spec in docs/frontend_design.md"],
  ["Next.js frontend: landing + dashboard", "Done", "Built and connected to the live API; checked at 1280, 1536 and 1920 px"],
  ["Frontend: sign-in, profile, my risk, history, models", "Done", "Built on the live API; sign-in flow to be tested by you with a real account"],
  ["Frontend: forecast page", "Done", "Measured 30 days into the 30-day forecast for AQI, PM2.5 and NO2; weekly summary; reliability; day-by-day table"],
  ["Hospital map", "Done", "Leaflet + OpenStreetMap; nearby hospitals with phone, address, directions; shown at High/Severe risk"],
  ["Live 2026 data: station download + daily AQI", "Done", "24 CPCB stations (4 per city), Feb 2025 to today; daily AQI matches CPCB bulletins"],
  ["Live 2026 data: retrain + forecast from today", "Done", "18 live models (6 cities x AQI, PM2.5, NO2); the site now forecasts from today; daily refresh command"],
  ["Live data: today's readings in the forecast", "Done", "Today's and the next days' forecast adjusted with station readings so far; backtested"],
  ["Live data: automatic daily refresh", "Done", "GitHub Actions job runs daily at 02:37 IST (backup run 04:37 IST); the live API downloads the new bundle by itself"],
  ["Air-quality assistant", "Built, needs API key", "Chat on My risk, answers from the forecast and the saved profile; switched on once the API key is added"],
  ["Deployment", "Done", "Live site on Vercel, API on Render (free plan); daily models and hourly readings update by themselves"],
  ["Project report (4 evaluation criteria)", "Done", "15-page Word report in docs/Project_Report.docx; fill in title-page details"],
  ["Course mid-sem submission (Phase 2)", "Complete", "Completed: 8-slide deck, analysis (reports/phase2) and demo notebook"],
  ["Course final submission (16-27 Nov)", "Results ready", "Presentation still to prepare (report content can be reused)"],
];

const DONE = [
  {
    title: "AQI forecasting pipeline",
    items: [
      "Data loading for Delhi, Bengaluru, Chennai, Hyderabad, Lucknow and Ahmedabad (CPCB data, 2015-2020); gaps up to 21 days interpolated.",
      "Diagnostics: ADF and KPSS stationarity tests (no differencing needed), seasonal period confirmed at ~365 days (ACF peaks at lags 363-370, STL seasonal strength).",
      "Models: ARIMA, SARIMA (weekly + annual Fourier terms), Holt-Winters, LSTM, XGBoost on lag features, Prophet; compared with three naive baselines.",
      "Evaluation on 6 non-overlapping 30-day test windows per city (RMSE, MSE, MAE, MAPE); winner = lowest mean RMSE.",
      "Ahmedabad fix: its CO sensor readings were faulty (median 16 mg/m3 vs about 1 elsewhere, AQI up to 2,049), so its AQI is recomputed from hourly data without CO. The method reproduces the published values exactly when CO is included.",
      "LSTM results averaged over seeds 42, 43 and 44 (a single seed gave a misleadingly good Delhi result).",
    ],
  },
  {
    title: "Pollutant forecasting (PM2.5, NO2)",
    items: [
      "Same evaluation for PM2.5 and NO2, the only pollutants with usable history in all six cities.",
      "Where no model beats the naive forecast on mean RMSE, the naive forecast itself is deployed (Hyderabad PM2.5, Ahmedabad NO2).",
    ],
  },
  {
    title: "Saved forecasting models",
    items: [
      "Each city's winner retrained on its full history and saved in its native format (joblib, XGBoost .ubj, PyTorch state_dict, Prophet JSON), with metadata and a registry.",
      "Verified: reloaded models reproduce the in-memory forecasts exactly.",
    ],
  },
  {
    title: "Health-risk models",
    items: [
      "Random Forest, XGBoost and MLP compared for risk level (weighted F1) and risk score (RMSE), with 5-fold cross-validation and a held-out 20% test set.",
      "MLP selected for both tasks. Primary model uses the profile plus AQI, PM2.5 and NO2; an AQI-only model is the automatic fallback.",
      "Boundary rule: the classifier's level is the headline; days where the score implies a neighbouring level are flagged borderline and shown as a range; the higher level drives High/Severe alerts.",
      "Backtest on real historical forecasts: the pollutant model beats the AQI-only model (73.3% vs 68.5% level agreement with the reference).",
    ],
  },
  {
    title: "FastAPI backend (public part)",
    items: [
      "Endpoints: /api/health, /api/cities, /api/forecast/{city}, /api/risk/predict, /api/profile/schema, /api/leaderboard/forecast, /api/leaderboard/health.",
      "All models load once at startup (~20 s); requests after that take well under a second.",
      "Profile validation: occupation, area type, mask usage and outdoor hours are required (defaulting them understated risk); BMI, exercise and family history are optional.",
      "29 automated tests pass.",
    ],
  },
  {
    title: "Supabase and user accounts",
    items: [
      "Supabase project created (Mumbai region); database script run; checks confirmed public tables are readable, private tables are blocked without sign-in, and the public key can't write.",
      "Signed-in endpoints: GET/PUT /api/me/profile, POST /api/me/risk (runs a prediction with the saved profile and saves it to history), GET /api/me/history, GET/DELETE /api/me/history/{id}.",
      "Each database call is made with the user's own sign-in token, so row-level security keeps every user's profile and history private, even inside the backend.",
      "12 new tests using an in-memory stand-in for Supabase that enforces the same per-user rules (41 tests pass in total); the real sign-in service correctly rejects invalid tokens.",
      "Live end-to-end check with a real test user passed all 8 steps: save and read profile, run a prediction, list and read history, hidden without sign-in, delete, confirm deletion.",
      "SQL script supabase/migrations/0001_init.sql: profiles, saved_forecasts, risk_predictions, aqi_forecasts_cache, model_leaderboard.",
      "Row-level security: users only see and change their own profile and history; history can't be edited; public tables are read-only except for the backend.",
      "Step-by-step setup guide (supabase/README.md) and .env.example; real keys stay in a git-ignored .env.",
    ],
  },
];

DONE.push({
  title: "Frontend design (Airware)",
  items: [
    "Site named Airware. Stack confirmed: Next.js, React + TypeScript, Tailwind CSS, shadcn/ui, Motion, ECharts, Lucide React, Leaflet + OpenStreetMap, Overpass API.",
    "Design direction: a data-first dashboard (like IQAir or Windy) using the full screen width, with IBM Plex fonts, neutral colours, one deep-teal brand colour, and the official CPCB colours reserved for air-quality data.",
    "Approved overview page: city tabs, tomorrow's AQI with the CPCB scale and health advice, interactive forecast chart, pollutants, day-by-day health risk, precautions, and an all-cities comparison table.",
    "Approved landing page: hero with a live dashboard preview, city AQI strip, a two-person example showing why personal risk matters, how it works, features, model results, data and AQI scale, privacy, FAQ and footer.",
    "Site structure: landing page at /, dashboard at /dashboard, plus sign-in, profile wizard, my risk, history and models pages.",
    "Light and dark themes with a toggle; layout checked at 1280, 1536 and 1920 px wide (the user's laptop at 150%, 125% and 100% scaling).",
    "Spec saved in docs/frontend_design.md with the approved preview in docs/design/.",
  ],
});

DONE.push({
  title: "Project report",
  items: [
    "15-page Word report (docs/Project_Report.docx) structured around the four evaluation criteria: review of existing systems and feasibility, objectives and methodology, relevance of algorithms, and synchronisation of design and implementation.",
    "Includes 11 figures (architecture, methodology, data overview, Ahmedabad sensor fix, STL decomposition, evaluation windows, model comparison, forecasts, health results, dashboard design) and 9 tables, all from the project's actual results, plus 15 references.",
    "A cleaned dataset export (data/processed/city_day_clean.csv) was also produced on request.",
  ],
});

DONE.push({
  title: "Hospital enquiry map",
  items: [
    "New public endpoint /api/hospitals finds hospitals near a city centre or the user's location using OpenStreetMap (Overpass API): name, distance, address, phone numbers, website and whether it has an emergency department.",
    "Results are cleaned (unnamed, duplicate and clearly non-medical entries removed), sorted nearest first and cached for a week, because a fresh lookup can take 30-70 seconds.",
    "Website: a Leaflet map with OpenStreetMap tiles and a list of hospitals with tap-to-call phone numbers, website and directions links; 3, 5 or 10 km radius and an optional 'use my location'.",
    "Shown on its own Hospitals page and automatically on My risk when risk reaches High or Severe. Contact details only (no booking), with a reminder to call 112 or 108 in an emergency.",
    "9 new automated tests (50 in total); type check, lint and production build pass; checked at 1280, 1536 and 1920 px in light and dark.",
  ],
});

DONE.push({
  title: "Frontend: sign-in, profile, my risk, history and models",
  items: [
    "Sign in and create account (email and password through Supabase); new accounts confirm by email and go straight to the profile form.",
    "Health profile: a 3-step form (about you, daily exposure, optional health details) saved once and reused; it can be edited at any time.",
    "My risk: the user's own day-by-day risk for 7 or 30 days in any of the six cities, with confidence, borderline ranges, a risk-score chart, the AQI forecast, precautions and a High/Severe callout.",
    "Each new estimate is saved to History, where past runs can be opened in full or deleted; the page reuses the latest run unless the profile changed, so visits don't create duplicates.",
    "Models page: leaderboards for AQI, PM2.5 and NO2 forecasting per city (gain over the naive forecast, all metrics, test windows) and for the health models (classification, regression, recall by risk level, borderline-day statistics).",
    "Type check, lint and production build pass; layouts checked at 1280, 1536 and 1920 px in light and dark.",
  ],
});

DONE.push({
  title: "Air-quality assistant",
  items: [
    "Chat panel on My risk: signed-in users ask about the air, their own risk and precautions, in English or Hindi; suggested questions to start.",
    "Answers come from the site's own data through five tools: the city forecast, recent measurements, the user's own risk estimate, a curated precautions list and nearby hospitals. The model is told never to give numbers it did not get from these.",
    "Safety: messages describing an emergency (can't breathe, chest pain) get a fixed reply with 112 / 108 and the nearest hospitals without calling the model; no diagnosis, medicines or doses; every answer is labelled as decision support.",
    "Limits: signed-in users only, 30 questions per user per day, nothing stored on the server; the question and the profile details needed to answer it go to the model provider.",
    "12 automated tests with a fake model client (no API cost).",
  ],
});

DONE.push({
  title: "Delhi's live AQI model switched to XGBoost",
  items: [
    "Compared every model over 10 test windows (the usual 6 recent ones plus 4 covering last winter, since the regular live comparison never reached winter). For Delhi, XGBoost's mean error is 62 against ARIMA's 65, and in winter alone 72 against 88, clearly better where it mattered.",
    "Retrained and deployed for Delhi only; the other 5 cities and PM2.5/NO2 are unchanged pending a decision on the rest. The public leaderboard's Delhi entry now matches what is actually running, instead of the recent-only comparison.",
  ],
});

DONE.push({
  title: "AQI/PM2.5/NO2 consistency: the fix is now applied in the right order",
  items: [
    "The AQI floor (next entry below) was being applied after today's real-time reading adjustment (nowcast), so a live reading correcting only one pollutant could be silently overridden by a stale forecast for another. Reordered: the raw model forecasts are made consistent with each other first, then the nowcast adjusts from there using real station data, which is allowed to stand even if it only touches one pollutant for a day or two.",
    "Found this testing Delhi's new XGBoost deployment; it is a real fix for all 6 cities, not specific to Delhi.",
  ],
});

DONE.push({
  title: "AQI and PM2.5 forecasts made consistent",
  items: [
    "India's AQI is the largest pollutant sub-index, so a day's AQI can never be below what its PM2.5 or NO2 implies. The AQI and pollutant forecasts come from separate models and could disagree; the site now raises each day's AQI to at least that level before showing it or using it for health risk.",
    "On the live forecasts of 12 Nov this corrects Delhi on 27 of 29 days (by about 25 AQI points on average) and Lucknow on 7; the other four cities were already consistent.",
  ],
});

DONE.push({
  title: "Winter test of the live models",
  items: [
    "Ran the live models on last winter (four 30-day windows, Nov 2025 to Feb 2026), which the regular Apr-Oct test windows never covered. Report: reports/forecasting/live/winter.md.",
    "PM2.5 holds up (beats the naive forecast in all 6 cities). AQI beats it in only 3 of 6 cities in winter (Delhi, Ahmedabad and Bengaluru fall short), and errors roughly double (Delhi 51 to 89).",
    "Choosing models over all nine windows instead of Apr-Oct would change the AQI model in 5 of 6 cities. The 2015-2020 seasonal prior cuts the best model's winter error by about 11%.",
  ],
});

DONE.push({
  title: "Mid-sem (Phase 2) deliverables",
  items: [
    "Phase 2 analysis (python -m src.phase2, results in reports/phase2): preprocessing summary, ADF and KPSS tests, decomposition, ACF/PACF plots, ARIMA AIC grids, fitted parameters, residual diagnostics (Ljung-Box, Jarque-Bera), hold-out forecast plots and RMSE/MSE/MAE/MAPE tables for ARIMA, SARIMA and Holt-Winters against three naive baselines, plus written interim observations.",
    "Result: the best classical model beats the best naive forecast in all six cities on mean RMSE over six 30-day windows (SARIMA in Delhi -30%, Lucknow -28%, Bengaluru -24%; ARIMA in Chennai -13%; Holt-Winters in Ahmedabad -5% and Hyderabad -0.2%).",
    "Assumption checks: ARIMA and SARIMA leave white-noise residuals in 4 of 6 cities; Holt-Winters in none (no autoregressive term). The runner-up ARIMA order is always within 2 AIC points of the best, while models without an AR term are 185-888 points worse.",
    "8-slide presentation (docs/phase2/AQI_Forecasting_Phase2_MidSem.pptx, built by docs/phase2/build_deck.js) with speaker notes, covering every Milestone 2 rubric item, including a plan-to-implementation table.",
    "Demo notebook notebooks/02_classical_models.ipynb: one city end to end with the project's own code (switch city with CITY).",
  ],
});

DONE.push({
  title: "Frontend: landing page and dashboard",
  items: [
    "Next.js app in frontend/ with React + TypeScript, Tailwind CSS, shadcn/ui, Motion, ECharts and Lucide icons, following the approved Airware design.",
    "Landing page: hero with a live dashboard preview, city AQI strip, two-person risk comparison computed live by the models, how it works, features, model results from the leaderboard, AQI scale, privacy and FAQ.",
    "Dashboard: city tabs, tomorrow's AQI on the CPCB scale with health advice, 7/30-day forecast chart, pollutant trends, 7-day risk for an example profile, precautions and an all-cities table; city and horizon are kept in the page address.",
    "Light and dark themes with a toggle; layouts checked at 1280, 1536 and 1920 px; type check, lint and production build all pass.",
  ],
});

const AQI_RESULTS = [
  // [city, deployed AQI model, mean RMSE, best baseline mean RMSE, improvement]
  ["Delhi", "SARIMA", "69.21", "98.91", "-30%"],
  ["Lucknow", "Prophet", "55.90", "83.16", "-33%"],
  ["Bengaluru", "SARIMA", "19.35", "25.55", "-24%"],
  ["Chennai", "ARIMA", "37.45", "42.87", "-13%"],
  ["Hyderabad", "Prophet", "22.39", "25.88", "-13%"],
  ["Ahmedabad", "Holt-Winters", "57.44", "60.75", "-5%"],
];

const POLLUTANT_MODELS = [
  // [city, PM2.5 model, NO2 model]
  ["Delhi", "Prophet", "Prophet"],
  ["Lucknow", "Prophet", "Prophet"],
  ["Bengaluru", "SARIMA", "LSTM"],
  ["Chennai", "Holt-Winters", "SARIMA"],
  ["Hyderabad", "Naive (last value)", "XGBoost"],
  ["Ahmedabad", "Holt-Winters", "Naive (last value)"],
];

const HEALTH_RESULTS = [
  // [variant, level F1, level accuracy, recall L/M/H/S, score RMSE, score R2]
  ["Profile + AQI + PM2.5 + NO2 (primary)", "0.873", "0.873", "92% / 79% / 88% / 91%", "0.198", "0.986"],
  ["Profile + AQI (fallback)", "0.839", "0.838", "88% / 81% / 74% / 86%", "0.377", "0.948"],
];

const REMAINING = [
  // [task, needs, notes]
  ["Assistant: add billing credit", "You", "The key is in place and the server-side error handling is fixed, but the Anthropic account has no credit yet (a test question returned a credit-balance error); add credit, then a real answer can be checked"],
  ["Live models: decide on the rest", "You + me", "Delhi's AQI is now on the winter-inclusive comparison; Ahmedabad, Bengaluru, Hyderabad and Lucknow's AQI, and most cities' PM2.5/NO2, would also change model - see reports/forecasting/live/selection_all_seasons.md"],
  ["Deployment: keep an eye on it", "You", "Free Render plan sleeps after 15 min idle (first visit ~1 min); open the site once before a demo, or switch to Starter ($7/month)"],
  ["Frontend redesign", "Your references", "Current look judged too generic; waiting for website references to restyle the real site"],
  ["Final report/presentation (16-27 Nov)", "You + me", "LSTM, XGBoost, Prophet and the comparison"],
];

const ACTIONS_FOR_YOU = [
  "Push the latest commit to GitHub (git push origin main) so the hospital map and live-data work are in the repository.",
  "Share the website references for the redesign.",
  "Test the signed-in pages with a real account: create an account, confirm the email, fill in the profile, check My risk, then History (open and delete a run).",
  "Try the site locally: start the API, then run npm run dev in frontend/ and open http://localhost:3000.",
  "Fill in the title-page details in docs/Project_Report.docx before submitting it.",
];

const IMPROVEMENTS = [
  "Most of the remaining health-risk error comes from the air-quality forecasts (especially Delhi and Ahmedabad); better forecasting is the biggest accuracy lever.",
  "Holt-Winters always selects weekly seasonality; a proper annual version needs deseasonalising first.",
  "No single forecasting model dominates; averaging the top 2-3 models per city could make forecasts more stable.",
];

const CHANGE_LOG = [
  // newest first: [date, summary]
  ["13 Nov 2026", "Delhi's live AQI model switched to XGBoost after comparing all models on 10 windows including last winter; found and fixed a real bug in the process (the AQI/pollutant consistency floor could override a same-day real-reading correction, fixed for all cities, not just Delhi)."],
  ["12 Nov 2026", "Daily refresh moved to 02:37 IST with a backup run at 04:37 IST: GitHub had been starting the 06:00 run around midday, so mornings used day-old models."],
  ["12 Nov 2026", "AQI forecasts can no longer fall below what the PM2.5 or NO2 forecast implies (fixes Delhi on 27 of 29 days and Lucknow on 7 in the live forecasts)."],
  ["12 Nov 2026", "Air-quality assistant built (chat on My risk, grounded in the forecast and the saved profile, with an emergency short-cut and a daily limit); it switches on when the API key is added. Winter test of the live models: PM2.5 holds up, AQI needs model choices that include winter."],
  ["9 Nov 2026", "Phase 2 (mid-sem) marked complete. The final (Phase 3) is next: LSTM, XGBoost and Prophet compared with the classical models."],
  ["31 Oct 2026", "Mid-sem (Phase 2) deliverables built: analysis and figures for the classical models (reports/phase2), an 8-slide presentation with speaker notes, and a demo notebook. A classical model beats the naive forecast in all six cities."],
  ["31 Oct 2026", "Lucknow and Delhi forecasts fixed: their AQI and PM2.5 forecasts contradicted each other (Lucknow AQI 56 against 148 measured last November). The models now scale the 2015-2020 seasonal pattern to each city's recent data and no longer fit the yearly cycle twice; every city's forecasts are now consistent."],
  ["31 Oct 2026", "Hospital map made reliable: hospitals within 25 km of each city are stored with the site (5,000+ in total), so the map loads in a fraction of a second instead of depending on the often-overloaded OpenStreetMap lookup service."],
  ["31 Oct 2026", "Forecast page built: for each city, the last 30 measured days running into the 30-day forecast for AQI, PM2.5 and NO2, a week-by-week summary, how reliable each forecast is, and a day-by-day table."],
  ["31 Oct 2026", "Site deployed: https://aqi-forecasting-and-health-predicti.vercel.app (Vercel) with the API on Render. Fixed while deploying: the model download on the server, and forecasts now always start at today."],
  ["31 Oct 2026", "Deployment prepared: Render Blueprint (render.yaml) and step-by-step guide. The API now serves the daily job's precomputed forecasts, cutting its memory from about 490 MB to 170 MB and startup from 11 s to 1.5 s. The scheduled daily refresh ran on its own this morning."],
  ["30 Oct 2026", "Daily refresh switched on: Supabase bucket and GitHub secrets set up, first workflow run succeeded, bundle (26 MB, models trained to 29 Oct) verified by downloading it."],
  ["30 Oct 2026", "Daily refresh built for the deployed site: a scheduled GitHub Actions job fetches the last days of readings, retrains the 18 live models and publishes them; the API downloads them and reloads by itself, no restart or redeploy. Setup steps in docs/live_refresh.md; switched on when the site is deployed."],
  ["30 Oct 2026", "Today's forecast now starts from the readings so far today (Delhi showed 256 when stations read about 107): in the winter-season backtest it cuts today's AQI error by about 57% and the next two days by 12% and 5%. Dashboard shows when the readings were last updated."],
  ["30 Oct 2026", "Forecasting models retrained on Feb 2025 to 29 Oct 2026 station data, using the 2015-2020 seasonal pattern as a guide; best model beats the naive baseline for every city's AQI and PM2.5 (Lucknow NO2 keeps the baseline). The site now forecasts from today; the 2015-2020 coursework results are unchanged."],
  ["30 Oct 2026", "Live data: hourly readings from 24 CPCB stations downloaded from OpenAQ (Feb 2025 to today) and turned into daily AQI per city (src/live_data.py), with faulty-sensor cleaning; spot-checks match CPCB bulletins (Delhi 20 Oct 2025: 346 vs 345)."],
  ["30 Oct 2026", "Hospital enquiry map built: /hospitals page and a panel on My risk at High/Severe risk; OpenAQ coverage check started for live data."],
  ["8 Oct 2026", "Project working guide written (22 pages, theory and technical): docs/Project_Working_Guide.docx."],
  ["7 Oct 2026", "Precautions now follow the selected day's risk (tomorrow by default) instead of the week's highest level; day cards are clickable."],
  ["6 Oct 2026", "Risk score now shown out of 100 (each risk level fills a quarter of the scale)."],
  ["6 Oct 2026", "Sign-in, profile form, My risk, History and Models pages built."],
  ["5 Oct 2026", "Frontend started: landing page and dashboard built on the live API, light and dark themes."],
  ["5 Oct 2026", "Project report written (15 pages, 11 figures, 9 tables); cleaned dataset exported to CSV."],
  ["26 Sep 2026", "Landing page design approved and saved; site structure set; live 2026 data scheduled after the frontend."],
  ["26 Sep 2026", "Frontend design approved: Airware data-first dashboard, light and dark themes; spec and preview saved."],
  ["26 Sep 2026", "Live accounts check passed (8/8) with a real test user; all commits pushed to GitHub."],
  ["26 Sep 2026", "Supabase connected: signed-in endpoints for profile, prediction runs and history; 41 tests."],
  ["26 Sep 2026", "Supabase schema, row-level security and setup guide; this progress report created."],
  ["26 Sep 2026", "FastAPI backend public endpoints with 29 tests; exposure fields made required."],
  ["26 Sep 2026", "PM2.5/NO2 forecasting, two-variant health models, boundary rule, forecast backtest."],
  ["25-26 Sep 2026", "Health-risk models trained and saved; per-city forecasting models saved."],
  ["25 Sep 2026", "AQI forecasting pipeline; Ahmedabad CO fix; multi-window evaluation; seeded LSTM."],
];

// =========================================================================== LAYOUT

const FONT = "Calibri";
const ACCENT = "1F4E79";
const PAGE_W = 11906, MARGIN = 1134;          // A4, 2 cm margins
const CONTENT_W = PAGE_W - 2 * MARGIN;        // 9638 DXA
const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const borders = { top: border, bottom: border, left: border, right: border };
const STATUS_FILL = { "Done": "E2EFDA", "Results ready": "E2EFDA", "Waiting on you": "FFF2CC", "Not started": "F2F2F2" };

const text = (t, opts = {}) => new TextRun({ text: t, font: FONT, ...opts });
const para = (t, opts = {}) => new Paragraph({ spacing: { after: 120 }, children: [text(t, opts)] });
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [text(t)] });
const h2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [text(t)] });
const bullet = (t) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [text(t)] });

function table(header, rows, widths, fillFor) {
  const cell = (value, w, opts = {}) => new TableCell({
    borders, width: { size: w, type: WidthType.DXA },
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    shading: opts.fill ? { fill: opts.fill, type: ShadingType.CLEAR, color: "auto" } : undefined,
    children: [new Paragraph({ children: [text(value, { bold: !!opts.bold, color: opts.color, size: 19 })] })],
  });
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({ tableHeader: true, children: header.map((h, i) => cell(h, widths[i], { bold: true, fill: ACCENT, color: "FFFFFF" })) }),
      ...rows.map((r) => new TableRow({ children: r.map((v, i) => cell(v, widths[i], { fill: fillFor ? fillFor(r, i) : undefined })) })),
    ],
  });
}

const children = [
  new Paragraph({ alignment: AlignmentType.LEFT, spacing: { after: 60 },
    children: [text("AQI Forecasting & Health Risk Prediction System", { bold: true, size: 40, color: ACCENT })] }),
  new Paragraph({ spacing: { after: 60 }, children: [text("Project progress report", { size: 28, color: "595959" })] }),
  new Paragraph({ spacing: { after: 240 }, border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: ACCENT, space: 4 } },
    children: [text(`Last updated: ${LAST_UPDATED}    |    Latest commit: ${LATEST_COMMIT}`, { size: 18, color: "595959" })] }),

  h1("1. Status at a glance"),
  table(["Area", "Status", "Notes"], AT_A_GLANCE, [3400, 1600, 4638],
    (r, i) => (i === 1 ? STATUS_FILL[r[1]] : undefined)),

  h1("2. Actions needed from you"),
  ...ACTIONS_FOR_YOU.map(bullet),

  h1("3. Work completed"),
  ...DONE.flatMap((s) => [h2(s.title), ...s.items.map(bullet)]),

  h1("4. Key results"),
  h2("AQI forecasting: deployed model per city"),
  para("Mean RMSE over 6 test windows, compared with the best naive baseline (lower is better)."),
  table(["City", "Deployed model", "Mean RMSE", "Best baseline", "Change"], AQI_RESULTS, [1900, 2300, 1800, 1900, 1738]),
  h2("PM2.5 and NO2: deployed model per city"),
  table(["City", "PM2.5 model", "NO2 model"], POLLUTANT_MODELS, [2638, 3500, 3500]),
  h2("Health-risk models (held-out test set, MLP)"),
  table(["Variant", "Level F1", "Accuracy", "Recall Low / Mod / High / Severe", "Score RMSE", "Score R²"],
    HEALTH_RESULTS, [2900, 1000, 1100, 2438, 1100, 1100]),
  para("Results are estimated risk for decision support, not a medical diagnosis.", { italics: true, color: "595959" }),

  h1("5. Work remaining"),
  table(["Task", "Needs", "Notes"], REMAINING, [3300, 1600, 4738]),

  h1("6. Known limitations and improvements"),
  ...IMPROVEMENTS.map(bullet),

  h1("7. Change log"),
  table(["Date", "What changed"], CHANGE_LOG, [1900, 7738]),
];

const doc = new Document({
  creator: "Project team",
  title: "Project progress report",
  styles: {
    default: { document: { run: { font: FONT, size: 21 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, font: FONT, color: ACCENT }, paragraph: { spacing: { before: 320, after: 140 }, outlineLevel: 0, keepNext: true, keepLines: true } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: FONT, color: "2E75B6" }, paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 1, keepNext: true, keepLines: true } },
    ],
  },
  numbering: { config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
    alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: 16838 }, margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [text("Page ", { size: 16, color: "808080" }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "808080", font: FONT })] })] }) },
    children,
  }],
});

const out = path.join(__dirname, "..", "Project_Progress.docx");
Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(out, buf); console.log("Wrote", out); });
