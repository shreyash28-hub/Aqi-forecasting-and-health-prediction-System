// Builds docs/Project_Working_Guide.docx: how the whole project works (theory + technical).
// Run from the repo root:   node docs/guide/build_guide.js
// Then open in Word and update the table of contents (right-click, Update field).
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, HeadingLevel, AlignmentType,
  WidthType, ShadingType, BorderStyle, LevelFormat, Footer, Header, PageNumber, ImageRun,
  TableOfContents,
} = require("../progress/node_modules/docx");

const ROOT = path.join(__dirname, "..", "..");
const FIG = path.join(ROOT, "docs", "report", "figures");
const FONT = "Calibri", MONO = "Consolas";
const PAGE_W = 11906, MARGIN = 1247, CONTENT_W = PAGE_W - 2 * MARGIN;   // A4, ~2.2 cm margins
const INK = "1F2933", BRAND = "0B6E74", SOFT = "E4F1F2", GREY = "F3F4F6";
const line = { style: BorderStyle.SINGLE, size: 4, color: "B8BEC8" };
const borders = { top: line, bottom: line, left: line, right: line };

// ------------------------------------------------------------------ helpers
let figN = 0, tabN = 0;
function runs(text, base = {}) {          // **bold** and `code` inline markup
  return text.split(/(\*\*[^*]+\*\*|`[^`]+`)/).filter(Boolean).map((s) => {
    if (s.startsWith("**")) return new TextRun({ text: s.slice(2, -2), bold: true, font: FONT, ...base });
    if (s.startsWith("`")) return new TextRun({ text: s.slice(1, -1), font: MONO, size: (base.size || 22) - 2, ...base, color: "9A3412" });
    return new TextRun({ text: s, font: FONT, ...base });
  });
}
const P = (t) => new Paragraph({ spacing: { after: 110, line: 276 }, children: runs(t) });
const BREAK = /^(3|5|6|9)\./;
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: BREAK.test(t), keepNext: true, children: [new TextRun({ text: t, font: FONT })] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text: t, font: FONT })] });
const H3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun({ text: t, font: FONT })] });
const B = (t) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 50, line: 270 }, children: runs(t) });
const N = (t, ref = "numbers") => new Paragraph({ numbering: { reference: ref, level: 0 }, spacing: { after: 50, line: 270 }, children: runs(t) });
const caption = (t) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 200 }, children: runs(t, { italics: true, size: 19, color: "5A6270" }) });

/** Shaded "key idea" box, one cell wide. */
function callout(title, text) {
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [CONTENT_W],
    rows: [new TableRow({ children: [new TableCell({
      width: { size: CONTENT_W, type: WidthType.DXA },
      borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE },
                 left: { style: BorderStyle.SINGLE, size: 24, color: BRAND } },
      shading: { fill: SOFT, type: ShadingType.CLEAR, color: "auto" },
      margins: { top: 90, bottom: 90, left: 180, right: 160 },
      children: [new Paragraph({ spacing: { after: 40 }, children: runs(title, { bold: true, color: BRAND }) }),
                 ...(Array.isArray(text) ? text : [text]).map((t) => new Paragraph({ spacing: { after: 40, line: 264 }, children: runs(t, { size: 21 }) }))],
    })] })],
  });
}
const gap = () => new Paragraph({ spacing: { after: 100 }, children: [] });

/** Monospace block for formulas, commands and file trees. */
function code(lines) {
  return lines.map((l, i) => new Paragraph({
    spacing: { after: 0, line: 252 }, keepNext: i < lines.length - 1,
    shading: { fill: GREY, type: ShadingType.CLEAR, color: "auto" }, indent: { left: 120, right: 120 },
    children: [new TextRun({ text: l || " ", font: MONO, size: 19 })],
  })).concat([gap()]);
}

function pngSize(file) { const b = fs.readFileSync(file); return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) }; }
function figure(file, text, width = 520) {
  figN += 1;
  const { w, h } = pngSize(file);
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120 }, children: [
      new ImageRun({ type: "png", data: fs.readFileSync(file), transformation: { width, height: Math.round(width * h / w) },
        altText: { title: `Figure ${figN}`, description: text, name: `fig${figN}` } })] }),
    caption(`Figure ${figN}: ${text}`),
  ];
}
function table(header, rows, widths, title) {
  tabN += 1;
  const total = widths.reduce((a, b) => a + b, 0);
  const w = widths.map((x) => Math.round(x * CONTENT_W / total));
  w[w.length - 1] += CONTENT_W - w.reduce((a, b) => a + b, 0);
  const cell = (v, i, head) => new TableCell({
    borders, width: { size: w[i], type: WidthType.DXA }, margins: { top: 55, bottom: 55, left: 95, right: 95 },
    shading: head ? { fill: BRAND, type: ShadingType.CLEAR, color: "auto" } : undefined,
    children: [new Paragraph({ children: runs(String(v), head ? { size: 19, bold: true, color: "FFFFFF" } : { size: 19 }) })],
  });
  return [
    new Paragraph({ keepNext: true, spacing: { before: 160, after: 70 }, children: runs(`Table ${tabN}: ${title}`, { italics: true, size: 19, color: "5A6270" }) }),
    new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: w,
      rows: [new TableRow({ tableHeader: true, cantSplit: true, children: header.map((h, i) => cell(h, i, true)) }),
             ...rows.map((r) => new TableRow({ cantSplit: true, children: r.map((v, i) => cell(v, i, false)) }))] }),
    gap(),
  ];
}
const fig = (n) => path.join(FIG, n);
const rep = (n) => path.join(ROOT, "reports", "figures", n);

// ------------------------------------------------------------------ title page
const center = (t, o = {}) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 }, children: [new TextRun({ text: t, font: FONT, ...o })] });
const titlePage = [
  new Paragraph({ spacing: { before: 2600 }, children: [] }),
  center("AIRWARE", { size: 28, bold: true, color: BRAND, characterSpacing: 120 }),
  center("AQI Forecasting Driven Health Prediction System", { size: 52, bold: true, color: INK }),
  new Paragraph({ spacing: { after: 300 }, border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: BRAND, space: 12 } }, children: [] }),
  center("How the whole project works", { size: 34, color: INK }),
  center("Theory and technical guide", { size: 26, color: "5A6270" }),
  new Paragraph({ spacing: { before: 1800 }, children: [] }),
  center("Data  ·  Time-series forecasting  ·  Health-risk models  ·  FastAPI  ·  Supabase  ·  Next.js", { size: 22, color: "5A6270" }),
  new Paragraph({ spacing: { before: 2400 }, children: [] }),
  center("Course: Time Series and Analysis Project", { size: 22 }),
  center("Team: Shreyash Singh (S24CSEU1290)  ·  Bhoomi Singh (S24CSEU0886)  ·  Vansh Mittal (S24CSEU1950)", { size: 22 }),
  center("Mentor: Madhuri Gupta", { size: 22 }),
  center("First prepared October 2026  ·  Updated 17 November 2026", { size: 22 }),
];

// ------------------------------------------------------------------ content
const body = [];
const add = (...x) => body.push(...x.flat());

// ============================================================ 1
add(H1("1. What the project does"));
add(P("Airware answers two questions for people in Indian cities. First: **how clean will the air be over the next 7 or 30 days?** Second: **what does that air mean for my own health?** The first question is a time-series forecasting problem. The second is a prediction problem that combines the forecast with a person's saved health profile."));
add(H2("1.1 The two linked pipelines"));
add(table(["Pipeline", "Input", "Output", "Main techniques"], [
  ["AQI forecasting", "Daily AQI, PM2.5 and NO2 for six cities: 2015 to mid-2020 for the course comparison, and live station data from February 2025 to today for the website", "Daily AQI, PM2.5 and NO2 for the next 7 or 30 days, starting today", "ARIMA, SARIMA, Holt-Winters, Prophet, XGBoost, LSTM, compared with naive baselines"],
  ["Health-risk prediction", "A person's profile plus the forecast AQI, PM2.5 and NO2 for each day", "Risk level (Low to Severe), risk score, confidence, borderline flag", "Random Forest, XGBoost, MLP (neural network), selected by cross-validation"],
], [1.3, 2.2, 2.2, 2.6], "The two pipelines"));
add(P("Two supporting features sit around them: a **hospital map** that shows contact details (never booking) when risk is High or Severe, and **precautions** matched to the risk level. A conversational assistant was built and then postponed (section 13)."));
add(H2("1.2 The user's journey"));
add(N("The visitor opens the site. Current and forecast AQI for any of the six cities is **public**, with no login.", "journey"));
add(N("The user signs in (Supabase Auth) and fills a health profile **once**: age, gender, health condition, smoking, occupation, area type, mask use and hours outdoors are required. BMI, exercise hours and family history are optional.", "journey"));
add(N("The backend combines the saved profile with the forecast for the chosen city and horizon.", "journey"));
add(N("The health models return, for each day, a risk level, a risk score, a confidence and a borderline flag. The page shows this day by day, following the forecast curve.", "journey"));
add(N("Every estimate is saved to the user's history. If risk reaches High or Severe, the page warns the user and shows nearby hospitals on a map with their phone numbers and addresses.", "journey"));
add(N("Every result is labelled as an estimate for decision support, not a medical diagnosis.", "journey"));
add(gap());
add(callout("Scope note", "The course rubric covers the AQI time-series forecasting part. The health prediction, hospital map and website are an extension built on top of it, so the forecasting part is documented in the most depth here."));
add(H2("1.3 Team and responsibilities"));
add(P("The work is split so that each person owns a complete part of the system and can explain it on their own. The three parts meet at the API: the models Bhoomi built are the ones the backend refits every night, and the pages Vansh built get all their data from it."));
add(table(["Member", "Owns", "Main files"], [
  ["**Shreyash Singh** (S24CSEU1290)", "**Backend, data pipeline, evaluation and testing.** The FastAPI service and all 15 endpoints; live station data from OpenAQ and the daily AQI calculation; the Supabase database, sign-in and row-level security; the nightly refresh job and the model bundle; same-day correction and the AQI consistency floor; deployment on Render and keeping it awake. **Model evaluation and selection:** rolling-origin test windows, naive baselines, metrics, the winter test and the rule for switching models. **Testing:** the 84 automated tests and the live checks.", "`src/api/`, `src/openaq.py`, `src/live_data.py`, `src/aqi.py`, `src/nowcast.py`, `src/refresh_live.py`, `src/live_bundle.py`, `src/forecast_export.py`, `src/run_forecasting.py`, `src/evaluation.py`, `scripts/selection_report.py`, `supabase/`, `tests/`, `.github/workflows/`"],
  ["**Bhoomi Singh** (S24CSEU0886)", "**Data preparation and time-series models.** Exploring and cleaning the 2015-2020 CPCB data, gap filling, the Ahmedabad CO correction, stationarity tests and STL decomposition; building the six forecasting models (ARIMA, SARIMA, Holt-Winters, LSTM, XGBoost, Prophet), the naive baselines and the seasonal prior; the Phase 2 analysis, deck and notebook.", "`src/data_loader.py`, `src/preprocessing.py`, `src/models/`, `src/train_final_models.py`, `src/model_store.py`, `src/phase2.py`, `notebooks/`"],
  ["**Vansh Mittal** (S24CSEU1950)", "**Website and health-risk models.** The Next.js site: design, landing page, dashboard, forecast, My risk, history and models pages, charts and the hospital map; deployment on Vercel. The health dataset preparation, the Random Forest, XGBoost and MLP models and the boundary rule. The project report and presentation.", "`frontend/`, `src/health/`, `docs/report/`"],
], [1.5, 4.4, 2.6], "Who owns what"));
add(callout("How the parts connect", "Bhoomi's models produce the forecasts; Shreyash's evaluation decides which model each city uses and his nightly job retrains it; the API serves the forecasts and runs Vansh's health models on them; Vansh's pages show the result."));

// ============================================================ 2
add(H1("2. System architecture"));
add(P("The system has three columns: data sources on the left, model training and the nightly refresh in the middle, and the serving side (API, website, database) on the right. The browser never talks to the models or the database directly, except for one thing: signing in with Supabase."));
add(figure(fig("fig_architecture_live.png"), "Overall architecture: data sources, training and nightly refresh, and the serving side.", 560));
add(table(["Layer", "Technology", "Responsibility"], [
  ["Frontend", "Next.js 16, React 19, TypeScript, Tailwind CSS, shadcn/ui, Motion, ECharts, Leaflet, Lucide; hosted on Vercel", "Pages, charts, the hospital map, light and dark themes. Calls the API and signs users in."],
  ["Backend API", "FastAPI (Python); hosted on Render", "Serves forecasts, measured data, risk estimates, hospitals and leaderboards; checks sign-in tokens; saves history; applies today's readings to the forecast."],
  ["Models", "statsmodels, Prophet, XGBoost, PyTorch (LSTM), scikit-learn", "Forecast AQI, PM2.5 and NO2 (18 forecasters: 6 cities x 3 targets); predict health risk."],
  ["Live data and automation", "OpenAQ API, GitHub Actions, Supabase Storage", "Downloads new station readings every night, refits all 18 forecasters and publishes them as one bundle that the API picks up by itself."],
  ["Database and auth", "Supabase (PostgreSQL, Supabase Auth, Row Level Security)", "Stores profiles and history privately per user; handles accounts."],
], [1.3, 3, 3.1], "Layers and responsibilities"));
add(H2("2.1 Why this split"));
add(B("**Models are trained offline, never per request.** The nightly job refits the models and saves their 30-day forecasts; the API only reads those, so it answers in well under a second and fits in a small server (section 7.6)."));
add(B("**The API is the only door to user data.** The website sends the user's Supabase token to the API, and the API talks to Supabase with that same token. The database therefore enforces privacy itself (section 8)."));
add(B("**Public and private data are separated.** Forecasts, leaderboards and precautions are public; profiles and history are private."));
add(H2("2.2 Repository map"));
add(...code([
  "src/                   Python: data, models, evaluation, live data, API",
  "  data_loader.py       Loads city_day.csv (2015-2020), builds the daily series",
  "  aqi.py               CPCB AQI calculation, consistency floor",
  "  preprocessing.py     Stationarity tests, STL, test windows, seasonal prior",
  "  models/              ARIMA/SARIMA/Holt-Winters, Prophet, XGBoost, LSTM, baselines",
  "  run_forecasting.py   Rolling-origin comparison and leaderboards",
  "  evaluation.py        Metrics",
  "  train_final_models.py, model_store.py   Retrain winners, save and load them",
  "  openaq.py, live_data.py                 Live station readings -> daily AQI",
  "  nowcast.py           Today's readings applied to the forecast",
  "  refresh_live.py, live_bundle.py, forecast_export.py   Nightly refresh",
  "  health/              Health data, model training, backtest, predictor store",
  "  api/                 FastAPI app (main, services, me, hospitals, refresher, ...)",
  "models/                Saved models: aqi/, pm25/, no2/ (2015-2020), live/, health/",
  "data/hospitals.json    Stored hospital list from OpenStreetMap",
  "reports/               Results, leaderboards and figures (live/ for the live models)",
  "scripts/               One-off tools: downloads, reports, live checks",
  "supabase/              SQL schema and setup guide",
  "frontend/              The Next.js website",
  ".github/workflows/     Nightly refresh and keep-awake jobs",
  "docs/                  Report, progress file, deployment notes, this guide",
  "tests/                 84 automated tests",
]));

// ============================================================ 3
add(H1("3. Data"));
add(H2("3.1 The AQI dataset"));
add(P("The forecasting data is `city_day.csv`, real daily readings from India's Central Pollution Control Board (CPCB) monitoring stations, published through Kaggle. It has about 29,500 rows covering 26 cities from 1 January 2015 to 1 July 2020, with columns for the pollutants (PM2.5, PM10, NO, NO2, NOx, NH3, CO, SO2, O3, benzene, toluene, xylene) and the published AQI and AQI bucket."));
add(P("Only six cities have enough history to forecast well: **Delhi, Bengaluru, Chennai, Hyderabad, Lucknow and Ahmedabad** (1,300 to 2,000 days each). Cities with under about 300 days were excluded."));
add(...figure(fig("fig_aqi_overview.png"), "Daily AQI for the six cities, showing the strong yearly cycle and the difference between cities.", 470));
add(H2("3.2 What AQI means (theory)"));
add(P("The Air Quality Index turns many pollutant concentrations into one number from 0 to 500 that ordinary people can read. CPCB's National AQI works in three steps:"));
add(N("For each pollutant, take its average concentration over the averaging period (24 hours for most pollutants; the 8-hour maximum for CO and O3).", "aqi"));
add(N("Convert each concentration to a **sub-index** by straight-line interpolation between published concentration breakpoints.", "aqi"));
add(N("The day's AQI is the **highest** sub-index. The worst pollutant sets the AQI. CPCB requires at least three pollutants, one of them PM2.5 or PM10.", "aqi"));
add(...code([
  "Sub-index  I = (I_hi - I_lo) / (BP_hi - BP_lo) * (C - BP_lo) + I_lo",
  "AQI        = max( I_PM2.5, I_PM10, I_NO2, I_SO2, I_CO, I_O3, I_NH3, ... )",
]));
add(table(["AQI", "Category", "Meaning for health"], [
  ["0 - 50", "Good", "Minimal impact"],
  ["51 - 100", "Satisfactory", "Minor breathing discomfort for sensitive people"],
  ["101 - 200", "Moderate", "Discomfort for people with lung or heart disease, children and older adults"],
  ["201 - 300", "Poor", "Discomfort for most people on prolonged exposure"],
  ["301 - 400", "Very poor", "Respiratory illness possible on prolonged exposure"],
  ["401 - 500", "Severe", "Affects healthy people and seriously affects those with existing disease"],
], [1, 1.4, 5], "CPCB AQI categories (the colours used on the website)"));
add(callout("Important: what the models forecast", "The forecasting models predict the **daily AQI series directly**, as published by CPCB. They do not forecast every pollutant and rebuild the AQI. PM2.5 and NO2 are forecast separately because the health model uses them as extra inputs."));
add(H2("3.3 Cleaning and missing values"));
add(B("**Interpolation.** Gaps of up to 21 days are filled by interpolating between the neighbouring observed days. Longer gaps stay missing and are ignored when scoring."));
add(B("**Log transform.** Models are fitted on `log1p(AQI)`, which stabilises the spread (high-pollution days vary far more than clean days) and keeps forecasts positive. Forecasts are converted back to the AQI scale before scoring."));
add(B("**Median fill** is used only where a complete row is needed for a join, never for the forecasting series."));
add(P("Missingness varies a lot by city: about 0.5% of Delhi's AQI is missing, against about 34% for Ahmedabad. That is one reason the models are compared city by city."));
add(H2("3.4 The Ahmedabad correction"));
add(P("Ahmedabad's published AQI contained values up to 2,049 on a scale that ends at 500. The cause was its carbon-monoxide sensor. Its median daily CO was **16 mg/m3 against about 1 in the other cities**, and the readings drifted upward for years before falling in 2020, a pattern that fits sensor drift or a calibration fault rather than real pollution. Because AQI takes the maximum sub-index, one faulty sensor made CO the deciding pollutant on most hours."));
add(P("The fix was to rebuild Ahmedabad's AQI from the hourly file (`city_hour.csv`) using the CPCB method **without CO**. The same code reproduces the published values exactly when CO is included, which shows the method is right and CO is the cause. The switch is `AQI_EXCLUDED_POLLUTANTS` in `src/data_loader.py`. The other five cities use the published AQI."));
add(...figure(fig("fig_ahmedabad_co.png"), "Ahmedabad's carbon-monoxide readings compared with other cities, and the AQI before and after the fix.", 470));
add(H2("3.5 The health dataset"));
add(P("Health prediction needs rows that link a person (age, condition, habits) to the air they breathe. No public dataset does this for Indian cities, so the project uses a person-level table of **7,500 records with 28 columns and no missing values**."));
add(B("**Air columns** (AQI, PM2.5, PM10, NO2, SO2, O3) are real CPCB values taken from `city_day.csv` by real city and date."));
add(B("**Person columns** are age, gender, occupation, area type, condition (none, asthma, COPD, heart disease, diabetes, hypertension), family history, smoking, BMI, exercise, outdoor hours and mask use."));
add(B("**The risk label** follows a documented formula: a vulnerability multiplier (age, condition, smoking, family history, BMI, exercise) times an effective-exposure term (the air values adjusted by outdoor hours, mask use and area type), plus noise, cut into four risk bands."));
add(P("This is a constructed dataset: real air-quality values joined to person profiles by a documented formula. It is not a set of clinical records, and results should be read as an illustration of the method rather than medical evidence. This note is kept in the data-loading code (`src/health/data.py`) as well."));
add(P("Sanity checks on the data behave sensibly: average risk rises from AQI near 86 (Low) to near 515 (Severe); mask use lowers risk; industrial areas score higher than residential ones."));
add(H2("3.6 Live data: forecasting from today"));
add(P("The Kaggle data ends on 1 July 2020, so a website built on it alone could only forecast 2020. The live site therefore uses **current readings from the same CPCB stations**, collected through **OpenAQ**, a free public platform that republishes official monitoring data (free API key)."));
add(B("**Stations:** 24 CPCB stations, four per city, chosen because they report all the key pollutants most reliably. The list is fixed in `data/openaq/stations.json`."));
add(B("**History:** hourly readings from February 2025 to today. `scripts/download_openaq.py` downloads the full history once; every night `src/openaq.py` downloads just the last six days."));
add(B("**From hours to days** (`src/live_data.py`): the four stations are averaged hour by hour, the CPCB method (section 3.2) turns the hourly values into an hourly AQI, and a day's AQI is the mean of its hours. A day only counts if **at least 16 hours** were measured, in Indian Standard Time."));
add(B("**Cleaning:** negative values, sensors stuck on the same number for 12 hours, hours where PM2.5 exceeds PM10 (impossible, since PM2.5 is part of PM10) and a station far above the other three in its city are removed before averaging."));
add(B("**Validation:** the daily AQI agrees with CPCB's own bulletins, for example Delhi on 20 and 21 October 2025: 346 and 362 here against 345 and 351 published."));
add(callout("Missing week in January 2026", "OpenAQ has no readings from any station between 11 and 19 January 2026. Every station in every city stops and restarts at the same moment, so the gap is at the data provider, not in the sensors or our code; a re-download confirmed it is still empty. Those days are skipped, never filled in for scoring."));

// ============================================================ 4
add(H1("4. Time-series theory used"));
add(P("A time series is a sequence of values recorded in time order, here one AQI value per day. Forecasting uses the pattern in the past to predict the future. Four ideas matter most."));
add(H2("4.1 Components of a series"));
add(table(["Component", "Meaning", "In daily AQI"], [
  ["Trend", "Slow long-term rise or fall", "Weak; some cities improve slowly"],
  ["Seasonality", "A repeating cycle with a fixed period", "Strong yearly cycle (winter smog, monsoon wash-out) and a weekly one"],
  ["Autocorrelation", "Today's value depends on recent days", "Strong; AQI changes slowly from day to day"],
  ["Noise", "Unpredictable day-to-day variation", "Large, especially in Delhi"],
], [1.3, 3, 3.4], "Components of a time series"));
add(H2("4.2 Stationarity and differencing"));
add(P("Many classical models assume a **stationary** series: its mean and variance do not drift over time. Two tests check this, and they ask opposite questions so that they can confirm each other."));
add(B("**ADF test** (null: the series has a unit root, i.e. is non-stationary). A small p-value means the series is stationary."));
add(B("**KPSS test** (null: the series is stationary). A small p-value means it is not."));
add(P("If a series is not stationary, **differencing** (subtracting yesterday's value) usually fixes it; the number of times is called `d`. For these cities the tests showed the level series is already stationary, so no differencing was needed (`d = 0`)."));
add(H2("4.3 Seasonal decomposition (STL)"));
add(P("STL splits a series into trend, seasonal and remainder parts. It is a **diagnostic**: the strength of the seasonal part confirms how strong the yearly cycle is, and the autocorrelation function (ACF) peaks at lags 363 to 370 days, confirming a period of about **365 days**. This decided which seasonal models to try."));
add(...figure(fig("fig_stl_delhi.png"), "STL decomposition of Delhi's AQI into trend, yearly seasonality and remainder.", 440));
add(H2("4.4 Why a naive baseline"));
add(P("A forecast is only useful if it beats something trivial. Three **naive baselines** are scored on exactly the same test windows."));
add(B("**Naive (last value):** repeat the last observed value for every future day."));
add(B("**Seasonal naive (weekly):** repeat the value from the same weekday last week."));
add(B("**Seasonal naive (annual):** repeat the value from the same day last year."));
add(P("For AQI, the last-value baseline is hard to beat over a few days because the series changes slowly. That is why the project requires a model to beat the **best** of the three baselines before it is deployed."));

// ============================================================ 5
add(H1("5. The forecasting models"));
add(H2("5.1 What each model is (theory) and how it is set up (technical)"));
add(H3("ARIMA"));
add(P("**AutoRegressive Integrated Moving Average.** It predicts the next value from a weighted sum of recent past values (the AR part, order `p`) and recent past forecast errors (the MA part, order `q`), after differencing `d` times. Written ARIMA(p, d, q). **Our set-up:** `d` from the stationarity tests; `p` and `q` from 0 to 3 chosen by lowest AIC (a score that rewards fit and penalises complexity)."));
add(H3("SARIMA"));
add(P("ARIMA plus a seasonal part, written SARIMA(p,d,q)(P,D,Q)m. A true yearly period of 365 makes the model extremely slow and unstable on about 2,000 points, so the standard remedy is used: **weekly seasonality (m = 7) plus three yearly Fourier pairs** as external regressors. Fourier terms are sine and cosine waves of the yearly period; they let the model draw a smooth yearly curve cheaply."));
add(H3("Holt-Winters exponential smoothing"));
add(P("It keeps a running estimate of level, trend and seasonality and updates each with exponentially fading weights, so recent days count more. **Our set-up:** additive damped trend and additive seasonality; the seasonal period (365 or 7) is picked by AIC."));
add(H3("Prophet"));
add(P("Facebook's additive model: `y(t) = trend(t) + seasonality(t) + noise`. The trend is piecewise linear with automatically detected change points, and seasonality uses Fourier series. It copes well with missing days. **Our set-up:** yearly and weekly seasonality, additive mode, change-point prior 0.05."));
add(H3("XGBoost on lag features"));
add(P("A gradient-boosted tree model turns forecasting into ordinary regression: predict today's value from lagged values and calendar features. **Our features:** lags 1 to 7, 14, 21, 28; rolling mean and standard deviation over 7, 14 and 30 days; the 1-day difference; sine and cosine of the day of year; weekday and month. It forecasts **recursively**, feeding each prediction back in as the next day's lag. 400 trees, depth 4, learning rate 0.03."));
add(H3("LSTM"));
add(P("A Long Short-Term Memory network is a recurrent neural network with gates that decide what to remember and what to forget, which lets it learn patterns across many days. **Our set-up:** one LSTM layer of 64 units reads the last **60 days** (each day described by the scaled value plus the sine and cosine of the day of year) and a dropout layer plus a linear layer produce all **30 future days at once** (a direct multi-step forecast, which avoids the error build-up of recursion). Early stopping with up to 150 epochs. Results are averaged over three random seeds (42, 43, 44), because a single seed once gave a misleadingly good Delhi result."));
add(H2("5.2 Evaluation: rolling-origin windows"));
add(P("Testing on one final month is risky: that month might be unusually easy or hard. Instead each city is tested on **six non-overlapping 30-day windows, 120 days apart**. For each window every model is trained only on data before it, then forecasts the 30 days that follow. This mimics real use, where the model always forecasts the future from the past."));
add(...figure(fig("fig_windows.png"), "The six rolling test windows for one city; each trains on everything before it.", 470));
add(H3("Metrics"));
add(...code([
  "RMSE = sqrt( mean( (y - yhat)^2 ) )      punishes large misses; used to pick the winner",
  "MSE  = mean( (y - yhat)^2 )",
  "MAE  = mean( |y - yhat| )                average miss, in AQI points",
  "MAPE = mean( |y - yhat| / y ) * 100      average miss as a percentage",
]));
add(P("The winner for each city is the model with the **lowest mean RMSE across the six windows**. It is deployed only if it also beats the best naive baseline; otherwise the baseline itself is deployed (this happens for Hyderabad PM2.5 and Ahmedabad NO2)."));
add(H2("5.3 Results on the 2015-2020 data (the course comparison)"));
add(table(["City", "Deployed model", "Mean RMSE", "Best baseline RMSE", "Improvement"], [
  ["Delhi", "SARIMA", "69.21", "98.91", "-30%"],
  ["Lucknow", "Prophet", "55.90", "83.16", "-33%"],
  ["Bengaluru", "SARIMA", "19.35", "25.55", "-24%"],
  ["Chennai", "ARIMA", "37.45", "42.87", "-13%"],
  ["Hyderabad", "Prophet", "22.39", "25.88", "-13%"],
  ["Ahmedabad", "Holt-Winters", "57.44", "60.75", "-5%"],
], [1.3, 1.6, 1.2, 1.7, 1.3], "AQI forecasting on 2015-2020: selected model per city (mean over 6 windows of 30 days)"));
add(...figure(fig("fig_model_heatmap.png"), "Mean RMSE of every model in every city. No single model wins everywhere.", 500));
add(P("**Reading the results.** Different cities prefer different models, which is why selection is automatic and per city. Gains over the baseline are large for Delhi and Lucknow (strong seasonal swings) and small for Ahmedabad (noisy, heavily gap-filled data). Errors are largest in Delhi simply because its AQI is highest and most variable."));
add(P("**Classical versus machine learning.** A classical model wins in four cities and Prophet in two. Averaged over all cities, SARIMA ranks best (average rank 3.4), then Prophet (4.3), Holt-Winters (4.4), ARIMA and XGBoost (4.6) and LSTM (4.8). The machine-learning models can be excellent in one city and poor in another: the LSTM is strong in Lucknow but 31% worse than the naive forecast in Hyderabad. This agrees with published comparisons: a classical model with the right seasonal structure is hard to beat, so the safest approach is to compare all of them and pick per city."));
add(H2("5.4 Pollutant forecasts"));
add(P("PM2.5 and NO2 go through the same pipeline, because they have usable history in all six cities and improve the health model. PM10, SO2 and O3 are not forecast: they have too little data in several cities and do not improve the health model."));
add(table(["City", "PM2.5 model", "NO2 model"], [
  ["Delhi", "Prophet", "Prophet"], ["Lucknow", "Prophet", "Prophet"], ["Bengaluru", "SARIMA", "LSTM"],
  ["Chennai", "Holt-Winters", "SARIMA"], ["Hyderabad", "Naive (last value)", "XGBoost"], ["Ahmedabad", "Holt-Winters", "Naive (last value)"],
], [1.4, 2, 2], "Deployed PM2.5 and NO2 models"));
add(H2("5.5 From experiment to deployment"));
add(N("Evaluation picks the winner per city and target (`python -m src.run_forecasting`).", "deploy"));
add(N("`python -m src.train_final_models` retrains each winner on the **full** history and saves it in its native format (joblib, XGBoost `.ubj`, PyTorch `state_dict`, Prophet JSON) under `models/aqi/<city>/`, with a `registry.json` index.", "deploy"));
add(N("Each saved model is reloaded and must reproduce the in-memory forecast exactly before it counts. For the live site, the nightly job then exports every model's 30-day forecast (`src/forecast_export.py`), and the API serves those (section 7.6).", "deploy"));
add(...figure(rep("forecast_delhi.png"), "Example: Delhi's 30-day forecast against the actual values of the final test window.", 460));
add(P("The website uses a second set of models, trained the same way on the live data (section 5.6). The 2015-2020 models above stay unchanged as the course comparison."));

add(H2("5.6 The live models and the winter test"));
add(P("The live series starts in February 2025, so it is much shorter than the 2015-2020 data. Three adjustments make the same pipeline work on it."));
add(B("**Seasonal prior.** Less than two years of data is too little for a model to learn the yearly cycle by itself. Each city's average yearly shape from 2015-2020 is therefore subtracted before fitting and added back to the forecast. Because some cities' seasons have changed since 2020, the shape is **scaled per city** by a regression on the training data (between 0 and 1.5; for example Lucknow 0.68, Delhi 1.18). SARIMA and Prophet then drop their own yearly terms so the cycle is not counted twice."));
add(B("**Test windows.** Six 30-day windows, 45 days apart, from March to November 2026, **plus four fixed winter windows** covering November 2025 to February 2026."));
add(B("**Same rule:** lowest mean RMSE wins and must beat the best naive forecast. A baseline that cannot run in every window (same-date-last-year needs a full year of history, which the winter windows do not have) is not compared on its easier subset."));
add(H3("Why winter was added"));
add(P("The first live comparison used spring-to-autumn windows only. A **winter test** on the four winter windows showed that winter errors roughly doubled, and that in winter the deployed AQI model lost to the naive forecast in three of six cities. Winter is exactly when the forecast matters most in north India, so the models were re-chosen on all ten windows."));
add(H3("The switching rule"));
add(P("One winter of data cannot settle small differences, so a model was only replaced when the evidence was clear:"));
add(B("**Switch** if the current model loses to the naive forecast over all ten windows, or the new winner is **at least 5% better** in mean RMSE **and no worse in winter**."));
add(B("**Keep** the current model otherwise (a near-tie). The near-ties are rechecked in March 2027, when there will be two winters of data."));
add(P("This changed ten of the eighteen choices (Delhi's AQI first, then nine more) and lowered the summed error by 5-8% over all windows and by 10-12% in winter. Four of the old choices had been losing to the naive forecast once winter was counted."));
add(table(["City", "AQI", "PM2.5", "NO2", "AQI error: all windows / winter", "Best naive"], [
  ["Delhi", "XGBoost", "XGBoost", "LSTM (kept)", "62.1 / 72.4", "86.5"],
  ["Lucknow", "SARIMA (kept)", "Prophet", "ARIMA", "35.2 / 44.7", "49.8"],
  ["Ahmedabad", "ARIMA", "ARIMA", "XGBoost", "32.3 / 39.5", "33.4"],
  ["Bengaluru", "ARIMA", "Prophet", "Naive (last value)", "29.2 / 30.1", "30.8"],
  ["Chennai", "XGBoost", "LSTM (kept)", "ARIMA", "33.3 / 46.9", "39.7"],
  ["Hyderabad", "Holt-Winters (kept)", "Holt-Winters", "Prophet", "13.1 / 13.5", "13.7"],
], [1.2, 1.5, 1.4, 1.5, 1.9, 1.1], "Deployed live models (\"kept\" = near-tie, not switched)"));
add(P("Across the 18 live forecasters, nine are machine-learning or deep-learning models, eight are classical and one (Bengaluru NO2) is the naive forecast, because no model beat it there. The full before-and-after comparison is in `reports/forecasting/live/selection_all_seasons.md`."));

add(H2("5.7 Today's readings and the consistency floor"));
add(P("Two corrections are applied every time a forecast is served (`src/nowcast.py`, `src/aqi.py`)."));
add(H3("Same-day correction (nowcast)"));
add(P("The models only see complete days, so on its own the forecast for today ignores how today is actually going (once it said 256 for Delhi while the stations read about 107 by midday). The API therefore compares today's readings so far with the forecast and nudges the first days towards them, in log space:"));
add(...code([
  "r   = log(1 + reading so far) - log(1 + forecast for today)",
  "w   = hours / (hours + 6)            more hours measured -> more weight",
  "F_k = exp( log(1 + F_k) + w * 0.7^k * r ) - 1      k = 0 (today), 1, 2, ...",
]));
add(P("The factor 0.7 per day makes the effect fade over a few days. A backtest at a 13:00 cut-off showed today's AQI error falling by about 57%, tomorrow's by about 12% and the third day's by about 5%."));
add(H3("AQI consistency floor"));
add(P("AQI is the **largest** pollutant sub-index, so the AQI can never be lower than what the PM2.5 or NO2 level implies. The AQI, PM2.5 and NO2 forecasts come from separate models, though, and sometimes disagreed (in Delhi's winter, on most days). The floor raises each day's AQI to at least the sub-index of the PM2.5 and NO2 forecasts."));
add(callout("Getting the order right", [
  "The floor is applied **before** the same-day correction, so the separate models first agree with each other.",
  "It is applied **again after** it, so that real readings that move AQI and PM2.5 by different amounts still give a consistent answer.",
  "In the second pass a pollutant with **no reading yet today while AQI has one** is left out: its value is still only a forecast and must not override an AQI correction based on real measurements.",
  "Two earlier versions each got one part of this wrong; the tests now check every served day.",
]));

// ============================================================ 6
add(H1("6. The health-risk models"));
add(H2("6.1 The task in plain terms"));
add(P("Given a person and one day's air quality, predict how risky that day is for them. Two related questions are answered by two different kinds of model:"));
add(B("**Classification:** which risk **level** (Low, Moderate, High, Severe)? The model also gives a probability for each level, and the highest probability is the **confidence**."));
add(B("**Regression:** what risk **score** (a number)? Levels are just bands cut from this score, so the two answers should agree."));
add(H2("6.2 Inputs"));
add(table(["Group", "Features"], [
  ["Person (numeric)", "Age, BMI, exercise hours per week, outdoor hours per day"],
  ["Person (categories)", "Gender, occupation, area type, health condition, family history, smoker, mask use"],
  ["Air, primary model", "AQI, PM2.5, NO2"],
  ["Air, fallback model", "AQI only"],
], [2, 6], "Health model inputs"));
add(P("Two columns are deliberately **excluded** because they would leak the answer: `VulnerabilityScore` is part of the formula that produced the risk label, and `HospitalVisitsLastYear` is derived from the risk level. A model that saw them would score well and be useless on a new person. City and date are also excluded; the air values already represent them, and keeping them would tie the model to the training cities and dates."));
add(P("Two variants are deployed. The **primary** model uses AQI, PM2.5 and NO2. The **fallback** uses AQI only and is used automatically when pollutant forecasts are not available."));
add(H2("6.3 The three model families"));
add(table(["Model", "How it works", "Our set-up"], [
  ["Random Forest", "Many decision trees, each trained on a random sample; their votes are averaged. Robust and hard to overfit.", "400 trees, minimum leaf size 2"],
  ["XGBoost", "Trees built one after another, each correcting the previous trees' mistakes (gradient boosting).", "500 trees, depth 5, learning rate 0.05, 80% row and column sampling"],
  ["MLP (neural network)", "Layers of simple units; each layer transforms the inputs so the network can learn curved relationships.", "Two hidden layers (64 and 32 units), L2 penalty 0.001, standardised inputs"],
], [1.4, 3.4, 2.6], "Health models compared"));
add(H2("6.4 Training and selection"));
add(B("**80/20 split**, stratified by risk level, so both parts keep the same mix of levels. The 20% test set is touched only for final reporting."));
add(B("**5-fold stratified cross-validation** on the 80% to compare models fairly. Each model is also compared with a **dummy baseline** that always predicts the most common class."));
add(B("**Classification winner:** highest weighted F1. F1 balances precision (how many predicted cases were right) and recall (how many true cases were found). \"Weighted\" averages the per-level F1 by how common each level is. Recall is also checked **per level**, because the classes are imbalanced."));
add(B("**Regression winner:** lowest RMSE; MSE, MAE and R-squared are reported too."));
add(...code([
  "Precision = TP / (TP + FP)        Recall = TP / (TP + FN)",
  "F1 = 2 * Precision * Recall / (Precision + Recall)",
  "R2 = 1 - SSE / SST               (1.0 = perfect, 0 = no better than the mean)",
]));
add(H2("6.5 Results"));
add(table(["Variant", "Level F1", "Level accuracy", "Recall Low / Mod / High / Severe", "Score RMSE", "Score R2"], [
  ["Primary: profile + AQI + PM2.5 + NO2", "0.873", "0.873", "92% / 79% / 88% / 91%", "0.198", "0.986"],
  ["Fallback: profile + AQI", "0.839", "0.838", "88% / 81% / 74% / 86%", "0.377", "0.948"],
], [2.4, 0.9, 1, 2.1, 1, 0.9], "Selected model (MLP) on the held-out test set"));
add(P("The MLP won **both tasks in both variants**. Against the baseline (about 41% accuracy, always guessing the commonest level) the models are far better, and the extra pollutant inputs clearly help (primary beats fallback)."));
add(...figure(fig("fig_health_models.png"), "Health models compared on the test set.", 470));
add(H2("6.6 The boundary rule"));
add(P("The classifier and the regressor can disagree near a level edge: the classifier says Moderate while the score sits just inside High. About **7% of days** are like this. Instead of hiding it, the system uses a clear rule:"));
add(B("The **classifier's level is the headline**."));
add(B("If the score implies a different level, the day is marked **borderline** and shown as a range, for example \"Moderate to High\"."));
add(B("The **higher of the two levels** (the alert level) decides precautions and High/Severe warnings, so the system errs on the side of caution."));
add(P("On the test set, when both models agree the level is right 90% of the time, and on borderline days the true level lies inside the shown range 75% of the time. High and Severe days are caught 96% of the time with the rule, against 95% with the classifier alone, for a false-alert rate of about 4%."));
add(H2("6.7 Backtest on real forecasts"));
add(P("The health models were trained on real observed air values but are used on **forecast** air values, which contain forecast error. A backtest feeds real historical forecasts into the models: the primary variant agrees with the reference level 73.3% of the time against 68.5% for the fallback. The main source of remaining error is now the quality of the air forecast, not the health model."));
add(H2("6.8 The 0 to 100 score on the website"));
add(P("The raw risk score has no upper limit (the data reaches about 18), which is hard for users to read. The website maps it to **0 to 100** so that each level fills a quarter of the scale. The mapping is display only; stored and API values stay raw."));
add(table(["Level", "Score out of 100", "Raw score"], [
  ["Low", "0 - 25", "0 - 1.0"], ["Moderate", "25 - 50", "1.0 - 1.8"], ["High", "50 - 75", "1.8 - 2.8"], ["Severe", "75 - 100", "2.8 and above (6+ shows as 100)"],
], [1.5, 2, 3], "Score mapping (piecewise linear)"));

// ============================================================ 7
add(H1("7. The backend (FastAPI)"));
add(P("FastAPI is a Python web framework. Each endpoint is a function; request and response shapes are declared as types, and FastAPI validates them automatically and generates interactive documentation at `/docs`."));
add(H2("7.1 Files"));
add(table(["File", "Role"], [
  ["`src/api/main.py`", "Creates the app, allows cross-origin requests from the website, defines the public endpoints"],
  ["`src/api/services.py`", "`ModelService`: loads all models at startup; forecast, risk and leaderboard logic"],
  ["`src/api/schemas.py`", "Request and response definitions with validation (for example, required profile fields)"],
  ["`src/api/me.py`", "Signed-in endpoints: profile, saved runs, history"],
  ["`src/api/hospitals.py`", "Hospital search: stored list first, OpenStreetMap's Overpass service only outside it"],
  ["`src/api/refresher.py`", "Downloads the nightly model bundle and today's readings every hour while the API runs"],
  ["`src/api/supabase_client.py`", "Small client for Supabase's auth and table API"],
], [2.2, 5.2], "Backend files"));
add(H2("7.2 Endpoints"));
add(table(["Endpoint", "Auth", "What it does"], [
  ["`GET /api/health`", "Public", "Is the service up; which forecasts it serves, their date, and the last refresh and any error (the first place to look when something is off)"],
  ["`GET /api/cities`", "Public", "Cities, forecast start date, deployed model per target"],
  ["`GET /api/forecast/{city}?horizon=7|30`", "Public", "Daily AQI, PM2.5, NO2 forecast from today, with the time of the latest reading used"],
  ["`GET /api/observed/{city}?days=`", "Public", "Measured daily AQI, PM2.5, NO2 for recent days, and today so far"],
  ["`GET /api/hospitals?city=` or `?lat=&lon=`", "Public", "Named hospitals near a city or a location, nearest first, with contact details"],
  ["`POST /api/risk/predict`", "Public", "Risk for a profile sent in the request (not saved); used for the example profiles"],
  ["`GET /api/profile/schema`", "Public", "Describes the profile fields"],
  ["`GET /api/leaderboard/forecast?target=`", "Public", "Forecast model ranking per city (AQI, PM2.5, NO2)"],
  ["`GET /api/leaderboard/health`", "Public", "Health model ranking and boundary-rule statistics"],
  ["`GET`, `PUT /api/me/profile`", "Signed in", "Read or save the user's profile (404 if none yet)"],
  ["`POST /api/me/risk`", "Signed in", "Predict with the saved profile and save the run to history"],
  ["`GET /api/me/history`", "Signed in", "List the user's past runs, newest first"],
  ["`GET`, `DELETE /api/me/history/{id}`", "Signed in", "Open or delete one run"],
], [3, 1, 3.4], "API endpoints"));
add(H2("7.3 What happens in one risk request"));
add(N("Take the city's cached 30-day forecast and cut it to 7 or 30 days.", "risk"));
add(N("Validate the profile. Required fields must be present. Missing optional fields (BMI, exercise, family history) are filled with typical values and listed in `imputed_fields`. Values far outside the training range produce a warning.", "risk"));
add(N("For each day, build the model input from the profile and that day's AQI, PM2.5 and NO2. If the pollutant forecasts are missing, switch to the AQI-only fallback model.", "risk"));
add(N("Run the classifier (level and per-level probabilities) and the regressor (score). Apply the boundary rule to set `borderline`, `risk_range` and `alert_level`.", "risk"));
add(N("Add the run summary: highest alert level, days per level, borderline days and `show_hospitals`.", "risk"));
add(callout("Why exposure fields are required", "Filling the exposure fields (occupation, area type, mask use, outdoor hours) with typical values once turned a 67-year-old COPD patient from Moderate into Low. They change the answer too much to guess, so the form requires them."));
add(H2("7.4 Sign-in and privacy in the backend"));
add(N("The browser sends the user's Supabase access token as `Authorization: Bearer <token>`.", "auth"));
add(N("The API asks Supabase Auth who owns the token. Invalid or expired tokens get a 401.", "auth"));
add(N("Every table call is then made **with the user's own token**, so Supabase's row-level security (section 8) applies. Even a bug in the API could not read another user's rows. The powerful service-role key is not used for user data and is never placed in the frontend.", "auth"));
add(H2("7.5 Testing"));
add(P("**84 automated tests** (`pytest`, folder `tests/`) run in about 40 seconds. They cover:"));
add(B("**Endpoints and validation:** every public and signed-in endpoint, bad inputs (unknown city, wrong horizon, missing profile fields) and the error codes."));
add(B("**Forecast correctness:** what the API serves must equal what the saved models produce, after today's readings and the floor are applied; and no served day may have a PM2.5 or NO2 level implying a higher AQI than the one shown."));
add(B("**Live refresh:** new readings or a new model bundle change the forecast without a restart, and a broken file keeps the old forecast."));
add(B("**Model selection:** the test windows (including the winter ones) and the rule that a candidate missing windows is not compared unfairly."));
add(B("**Privacy:** signed-in tests use an in-memory stand-in for Supabase that enforces the same per-user rules, so one user can never read another's data."));
add(B("**Hospitals:** the search and the OpenStreetMap fallback, with the outside service mocked."));
add(P("`scripts/check_accounts_live.py` runs the full signed-in flow against the real Supabase project (8 of 8 checks passed). Every saved model is also reloaded and must reproduce its training-time forecast exactly."));
add(H2("7.6 Nightly refresh and serving"));
add(N("**02:37 IST** (backup run at 04:37 IST): GitHub Actions starts `python -m src.refresh_live`. It downloads the last six days of readings, merges the complete days, refits all 18 forecasters (about 90 seconds), exports their 30-day forecasts and records today's readings so far.", "refresh"));
add(N("Everything is packed into one bundle and uploaded to Supabase Storage. Nothing is committed to git.", "refresh"));
add(N("The API downloads the bundle at startup and checks for a new one every hour, together with fresh readings for today; it reloads in the background without a restart.", "refresh"));
add(N("The API serves the **exported forecasts** rather than loading the models. Loading all 18 models with their libraries took about 490 MB, too close to the server's 512 MB; serving the exported forecasts needs about 170 MB.", "refresh"));
add(callout("Why 02:37 IST", "The job originally ran at 06:00 IST, but GitHub started it five to seven hours late every day, so mornings showed day-old models. Starting soon after midnight (with a backup two hours later) means yesterday is complete and the new forecast is ready before people wake up. Running twice is harmless: the second run re-downloads the same six days."));
add(H2("7.7 Hospitals"));
add(P("The public OpenStreetMap search service (Overpass) was often overloaded and timed out, so `scripts/build_hospitals.py` stores every named hospital within 25 km of each city centre in `data/hospitals.json` (from 267 in Lucknow to 1,135 in Bengaluru). The API answers from this list in about 0.2 seconds and only asks Overpass for searches outside the stored areas. The site shows contact details only (phone, address, website, directions), never booking, with a reminder to call 112 or 108 in an emergency."));

// ============================================================ 8
add(H1("8. The database and sign-in (Supabase)"));
add(P("Supabase provides a PostgreSQL database and an authentication service. The schema is in `supabase/migrations/0001_init.sql`."));
add(H2("8.1 Tables"));
add(table(["Table", "Access", "Holds"], [
  ["`profiles`", "Private", "One row per user: age, gender, condition, smoker, occupation, area type, mask use, outdoor hours, optional BMI, exercise and family history, city, updated time"],
  ["`saved_forecasts`", "Private", "One row per prediction run: user, city, horizon, start date, models used, the air forecast"],
  ["`risk_predictions`", "Private", "One row per forecast day of a run: level, probabilities, confidence, score, borderline, range, alert level, input snapshot"],
  ["`aqi_forecasts_cache`", "Public read", "Cached forecasts (written only by the backend)"],
  ["`model_leaderboard`", "Public read", "Model rankings (written only by the backend)"],
], [1.8, 1.1, 4.6], "Database tables"));
add(H2("8.2 Row Level Security (theory)"));
add(P("Normally a database trusts the program that connects to it. **Row Level Security (RLS)** moves the rule into the database itself: a policy is attached to each table, and every query is filtered by it, whoever sends it. Here the policy is `auth.uid() = user_id`: a signed-in user can only see and change rows whose `user_id` is their own. Because the API uses each user's token, RLS applies to every request."));
add(B("History tables are **append-only**: users can add and delete runs but not edit them, so saved results cannot be altered afterwards."));
add(B("The public tables also have RLS, with a read-only policy. Without it, the public anon key could write to them."));
add(B("Only the public **anon key** is in the website. The **service-role key** (which bypasses RLS) is never placed in the frontend or in git; `.env` files are git-ignored."));

// ============================================================ 9
add(H1("9. The website (Next.js)"));
add(H2("9.1 Stack"));
add(table(["Tool", "Used for"], [
  ["Next.js 16 (App Router) and React 19", "Pages, routing, rendering"],
  ["TypeScript", "Type-checked code; the API's response shapes are typed in `src/lib/api.ts`"],
  ["Tailwind CSS v4 and shadcn/ui", "Styling and base components (shadcn's current style uses Base UI primitives)"],
  ["Motion", "Small fade-in animations (respects the user's reduced-motion setting)"],
  ["ECharts 6", "Charts (forecast, risk score, sparklines), loaded as small tree-shaken pieces"],
  ["Lucide React", "Icons"],
  ["@supabase/supabase-js", "Sign-in only; all data goes through the API"],
  ["IBM Plex Sans and Mono", "Typeface; Mono for numbers so columns align"],
], [2.8, 4.6], "Frontend tools"));
add(H2("9.2 Pages"));
add(table(["Route", "Needs login", "Shows"], [
  ["`/`", "No", "Landing page: what the project does, live example of two people breathing the same air, how it works, model results, FAQ"],
  ["`/dashboard`", "No", "Overview: city tabs, tomorrow's AQI on the CPCB scale, 7/30-day chart, pollutants, example risk, precautions, all-cities table"],
  ["`/sign-in`", "No", "Sign in or create account (email and password; new accounts confirm by email)"],
  ["`/profile`", "Yes", "Three-step health-profile form, saved once and editable"],
  ["`/risk`", "Yes", "Personal day-by-day risk, charts, precautions for the selected day, saves each new estimate"],
  ["`/history`, `/history/[id]`", "Yes", "Past estimates, full detail view, delete"],
  ["`/models`", "No", "Leaderboards for AQI, PM2.5, NO2 and health models, with the test windows"],
  ["`/forecast`", "No", "One city in depth: week-by-week summary, how reliable each model is, the last 30 measured days joined to the 30-day forecast, PM2.5 and NO2 against India's 24-hour standards, day-by-day table"],
  ["`/hospitals`", "No", "Hospital map and list for a city or the user's location, contact details only"],
], [1.7, 0.9, 4.8], "Pages"));
add(...figure(fig("ui_dashboard_c.png"), "The dashboard on the deployed site.", 470));
add(...figure(fig("ui_grid.png"), "Other pages of the deployed site: landing page, forecast page, hospital map and model leaderboard.", 500));
add(H2("9.3 How data reaches a page"));
add(B("`useAsync` is a small hook that runs a request when its inputs change, cancels the previous one, and keeps the last data on screen while a new request loads."));
add(B("`AuthProvider` keeps the Supabase session; `RequireAuth` sends signed-out visitors to `/sign-in?next=...` and returns them afterwards."));
add(B("`meApi(token)` wraps the signed-in endpoints. The My risk page shows the latest saved run and only calculates (and saves) a new one when none exists or the profile has changed since, so ordinary visits do not flood the history."));
add(H2("9.4 Design rules"));
add(B("A **data-first dashboard** using the full screen width, in the style of weather and air-quality sites, not a marketing template."));
add(B("Neutral greys with **one deep-teal brand colour**. The official CPCB colours are reserved for data so colour always means something."));
add(B("**Light and dark themes** with a toggle; the choice is applied before the page paints to avoid a flash."));
add(B("Every page is checked at **1280, 1536 and 1920 px** wide (a 1920x1080 laptop at 150%, 125% and 100% scaling)."));
add(B("A visible reminder on every result that it is an **estimate for decision support, not a medical diagnosis**."));
add(H2("9.5 Showing risk clearly"));
add(B("Each day card shows the level (or a range on borderline days), confidence, AQI and the score out of 100."));
add(B("The risk-score chart has the four level bands behind the line; the AQI chart is separate (no two-scale charts)."));
add(B("**Precautions follow the selected day** (tomorrow by default), using that day's alert level, with a note when risk rises later in the week."));
add(H2("9.6 When the server is asleep"));
add(P("The API runs on Render's free plan, which **stops the service after 15 minutes without requests**. The next visitor then waits 30 to 60 seconds while it starts again, and the site used to sit on empty grey boxes, which looked broken. Three changes handle this:"));
add(N("**Keep it awake.** A GitHub Actions job (`keep-api-awake.yml`) calls `/api/health` every 10 minutes, so the service rarely sleeps. One always-on free service uses about 744 of the 750 free hours a month.", "wake"));
add(N("**Explain the wait.** If any request takes longer than 4 seconds, a notice appears: \"Starting the forecast service... can take up to a minute. The page will fill in by itself.\"", "wake"));
add(N("**Retry instead of failing.** Requests that only read data (and the example risk estimate, which saves nothing) are retried for about a minute if the server is unreachable or answers 502, 503 or 504 while starting. Requests that save something are never repeated, so nothing can be saved twice.", "wake"));
add(P("GitHub sometimes starts scheduled jobs late, so an occasional cold start can still happen; the notice and retries cover it. A paid Render plan (about $7 a month) would remove sleeping completely."));

// ============================================================ 10
add(H1("10. End-to-end walkthrough"));
add(P("What happens when a signed-in user opens **My risk** for the first time:"));
add(table(["#", "Where", "Step"], [
  ["1", "Browser", "`RequireAuth` finds the Supabase session; if none, redirects to sign-in"],
  ["2", "Browser to API", "`GET /api/me/profile` with the token. If 404, redirect to the profile form"],
  ["3", "API to Supabase", "The API verifies the token and reads the `profiles` row under RLS"],
  ["4", "Browser to API", "`GET /api/me/history?limit=1` to look for a recent run"],
  ["5", "Browser to API", "No run (or profile changed since): `POST /api/me/risk {horizon: 7}`"],
  ["6", "API", "Cached forecast, profile validation, health models, boundary rule, summary"],
  ["7", "API to Supabase", "Insert one `saved_forecasts` row and one `risk_predictions` row per day"],
  ["8", "Browser", "Draw the summary, day cards, two charts and the precautions for tomorrow"],
  ["9", "Later visits", "The latest saved run is shown instantly; the user can change city or horizon and recalculate"],
], [0.4, 1.5, 5.5], "One My risk visit"));
add(...figure(fig("fig_pipeline.png"), "Pipeline from data to the user's screen.", 520));

// ============================================================ 11
add(H1("11. Running and checking the project"));
add(H2("11.1 Run it locally"));
add(P("Run these from the project folder, each in its own terminal."));
add(...code([
  "# backend (loads models; ready after about 20 seconds)",
  "venv\\Scripts\\python -m uvicorn src.api.main:app --port 8000",
  "",
  "# frontend",
  "npm --prefix frontend run dev",
]));
add(P("Open http://localhost:3000 for the site and http://localhost:8000/docs for the API documentation. The backend needs `SUPABASE_URL` and `SUPABASE_ANON_KEY` in the git-ignored `.env`; the frontend needs `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` in `frontend/.env.local`."));
add(H2("11.2 Retrain or regenerate"));
add(...code([
  "# 2015-2020 course comparison",
  "python -m src.run_forecasting --target AQI          # also PM2.5, NO2",
  "python -m src.train_final_models --target AQI",
  "",
  "# live models (what the website uses)",
  "python -m src.refresh_live                          # download, rebuild, refit, export",
  "python -m src.run_forecasting --source live --target AQI --tag all_seasons   # trial comparison",
  "python scripts/selection_report.py --tag all_seasons                          # before/after table",
  "",
  "python -m src.health.train          # train and save the health models",
  "pytest                              # 84 tests",
]));
add(P("A comparison run with `--tag` writes its results to a subfolder and never changes what is deployed. Changing a deployed model is a deliberate step: retrain it and update that city's entry in the live leaderboard, which the nightly job reads."));
add(H2("11.3 Quality checks"));
add(B("**Models:** naive-baseline comparison on every window, three LSTM seeds, reload-equals-original checks, the winter test."));
add(B("**API:** 84 automated tests; a live check against the real Supabase project; `/api/health` on the deployed API."));
add(B("**Frontend:** TypeScript type check, ESLint, production build, and screenshots at three widths in light and dark."));
add(H2("11.4 Deployment"));
add(table(["Part", "Where", "Notes"], [
  ["Website", "Vercel: aqi-forecasting-and-health-predicti.vercel.app", "Rebuilds automatically on every push to the main branch"],
  ["API", "Render (free plan, Singapore): airware-api.onrender.com", "Blueprint in `render.yaml`; installs exact library versions from `requirements.lock.txt`"],
  ["Database, sign-in, model bundle", "Supabase", "Row-level security; public storage bucket for the nightly bundle"],
  ["Nightly refresh, keep-awake", "GitHub Actions", "Secrets: OpenAQ key, Supabase URL and service-role key (only the job has it)"],
], [1.8, 3, 2.6], "Where everything runs"));

// ============================================================ 12
add(H1("12. Limits and what comes next"));
add(H2("12.1 Known limits"));
add(B("**Short live history.** The live data starts in February 2025 and contains one winter, so close model choices cannot be settled yet; they are rechecked in March 2027."));
add(B("**Horizon.** Accuracy falls with the horizon and in the most volatile seasons, so a 30-day forecast shows the trend rather than exact daily values."));
add(B("**Data gaps.** Station data occasionally has gaps at the provider (no readings anywhere on 11-19 January 2026)."));
add(B("**Error compounds.** Health-risk error now comes mostly from air-forecast error, especially in Delhi and Ahmedabad."));
add(B("**No single model dominates.** Averaging the top two or three models per city could make forecasts more stable."));
add(B("**Free hosting.** The API can still sleep now and then (section 9.6)."));
add(B("**Health dataset.** The risk labels come from a documented formula, so the models learn that formula; they are a demonstration of the method, not a validated clinical tool."));
add(H2("12.2 What comes next"));
add(table(["Step", "Notes"], [
  ["Recheck the near-ties", "March 2027, with two winters of live data: AQI in Lucknow and Hyderabad, PM2.5 in Chennai, NO2 in Delhi"],
  ["Weather inputs and ensembles", "Add weather forecasts (wind, temperature, humidity) and test averaging the top models per city"],
  ["Precautions assistant", "Built once (section 13) and postponed; can be restored from the code history"],
  ["Alerts and coverage", "Notify users when their risk rises; add more cities as the station network allows"],
  ["Course submission", "Final (16 to 27 Nov): ML/DL models and the comparison; the report is done (`docs/Airware_Mini_Project_Report.docx`, 23 pages)"],
], [2, 5.4], "Remaining work"));

// ============================================================ 13
add(H1("13. Recent changes (November 2026)"));
add(P("This chapter explains, in order, what changed in the last part of the project and why. Each change is described the same way: the problem, the change, and the result."));
const change = (title, problem, did, result) => [H2(title), P(`**Problem.** ${problem}`), P(`**Change.** ${did}`), P(`**Result.** ${result}`)];
add(...change("13.1 Winter test of the live models (12 Nov)",
  "The live models had been chosen on spring-to-autumn windows only, but north India's worst air is in winter.",
  "Every model was re-tested on four fixed 30-day windows covering November 2025 to February 2026 (`--window-ends`, `--tag winter`). The deployed models were not changed at this stage.",
  "Winter errors roughly doubled; PM2.5 models still beat the naive forecast in all six cities, but AQI models did so in only three. The seasonal prior cut the best model's winter error by about 11%. This set up the re-selection below."));
add(...change("13.2 AQI consistency floor (12 Nov, corrected 13 and 16 Nov)",
  "The separate AQI and PM2.5 models disagreed: in Delhi's winter the PM2.5 forecast implied a higher AQI than the AQI forecast on most days, which is impossible because AQI is the largest sub-index.",
  "The AQI is now raised to at least the sub-index of the PM2.5 and NO2 forecasts (section 5.7). The first version ran after the same-day correction and could override real readings with a stale forecast; the second ran only before it and let real readings drift apart again. The final version floors before and after, skipping a pollutant that has no reading yet today.",
  "No served day shows a PM2.5 or NO2 level implying a higher AQI than the one shown, and corrections based on real readings are never overridden. A test checks every served day."));
add(...change("13.3 Daily refresh moved earlier (12 Nov)",
  "GitHub started the 06:00 IST refresh five to seven hours late every day, so mornings used day-old models.",
  "The job now runs at 02:37 IST with a backup at 04:37 IST.",
  "New forecasts are normally ready before morning. A second run is harmless because it re-downloads the same six days."));
add(...change("13.4 Models re-chosen with winter included (13 and 16 Nov)",
  "Four deployed models lost to the naive forecast once winter was counted, and several others were clearly beaten.",
  "Selection was rerun on ten windows (six recent, four winter) with the switching rule in section 5.6: switch only if the current model loses to the naive forecast, or the new one is at least 5% better and no worse in winter. Delhi's AQI moved to XGBoost first (winter error 72 against 88), then nine more choices changed; four near-ties were kept.",
  "Summed error fell by 5-8% over all windows and 10-12% in winter. The deployed set is now nine machine-learning, eight classical and one naive forecaster."));
add(...change("13.5 Air-quality assistant built, then postponed (12 to 15 Nov)",
  "Users wanted to ask questions such as \"is it safe to walk tomorrow?\" in their own words.",
  "A chat assistant was built on a large language model, answering only from the site's own forecasts, the user's saved risk and a curated precautions list, with a fixed emergency reply and a daily limit. It was then removed from the site and the code on the team's decision, to be revisited later; the full version is kept in the code history.",
  "The site works exactly as before without it; precautions are still shown on the risk pages."));
add(...change("13.6 Final project report (16 Nov)",
  "The course needs a report on the university's mini-project template.",
  "A 23-page report was written on the template: literature review, use-case, class and ER diagrams, screenshots of the live site, pseudo code, source excerpts and the classical versus machine-learning comparison.",
  "`docs/Airware_Mini_Project_Report.docx` and `.pdf`."));
add(...change("13.7 Site looked down after idle periods (16 Nov)",
  "Render's free plan stops the API after 15 idle minutes; the next visitor waited up to a minute on empty boxes and the site looked broken.",
  "A keep-awake job, a \"starting\" notice and automatic retries for read-only requests (section 9.6).",
  "Tested locally with the API switched off and then started mid-load: the notice appeared and the page filled in by itself."));

// ============================================================ 14
add(H1("14. Glossary"));
add(table(["Term", "Meaning"], [
  ["AQI", "Air Quality Index, 0 to 500; the highest pollutant sub-index of the day"],
  ["CPCB", "Central Pollution Control Board, India's pollution regulator; source of the data"],
  ["PM2.5, PM10", "Particles smaller than 2.5 or 10 micrometres; PM2.5 reaches deep into the lungs"],
  ["NO2", "Nitrogen dioxide, mainly from traffic and combustion"],
  ["Time series", "Values recorded in time order"],
  ["Stationary", "A series whose mean and variance do not drift over time"],
  ["ADF, KPSS", "Two stationarity tests that ask opposite questions"],
  ["Differencing", "Subtracting the previous value to remove a trend"],
  ["Seasonality", "A pattern that repeats at a fixed period (weekly, yearly)"],
  ["STL", "Seasonal-trend decomposition using Loess; splits a series into trend, season and remainder"],
  ["ACF", "Autocorrelation function: how a series relates to its own past"],
  ["AIC", "A score that balances model fit against complexity; lower is better"],
  ["Baseline", "A trivial forecast (such as repeating the last value) that a model must beat"],
  ["Rolling-origin evaluation", "Testing on several windows, always training only on earlier data"],
  ["RMSE, MAE, MAPE", "Error measures: root mean squared error, mean absolute error, mean absolute percentage error"],
  ["F1, recall, precision", "Classification scores; recall is the share of true cases found, precision the share of predictions that were right"],
  ["R-squared", "Share of the variation a regression model explains"],
  ["Cross-validation", "Splitting training data into folds so each part is used for testing once"],
  ["Data leakage", "Giving a model a feature that contains the answer, which inflates scores"],
  ["Borderline day", "A day where the level and score point to neighbouring levels; shown as a range"],
  ["Alert level", "The higher of the two levels on a borderline day; drives warnings"],
  ["RLS", "Row Level Security: database rules that limit each user to their own rows"],
  ["Token (JWT)", "A signed proof of sign-in that the browser sends with each request"],
  ["Anon key, service-role key", "Public Supabase key (safe in the website) and the all-powerful private key (never in the website)"],
  ["OpenAQ", "Free public platform that republishes official air-quality readings; source of the live data"],
  ["Seasonal prior", "A city's average yearly shape from 2015-2020, removed before fitting the live models and added back after"],
  ["Nowcast", "Adjusting today's and the next few days' forecast towards the readings measured so far today"],
  ["Consistency floor", "Raising the AQI forecast to at least what the PM2.5 and NO2 forecasts imply"],
  ["Near-tie", "A model comparison too close to decide with one winter of data; the current model is kept"],
  ["Model bundle", "The nightly package of refitted models, data and forecasts that the API downloads"],
  ["Cold start", "The delay while a sleeping free server starts again on the first request"],
], [2, 5.4], "Glossary"));

// ------------------------------------------------------------------ document
const doc = new Document({
  creator: "Airware", title: "Airware: how the project works",
  styles: {
    default: { document: { run: { font: FONT, size: 22, color: INK } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, font: FONT, color: BRAND }, paragraph: { spacing: { before: 120, after: 200 }, outlineLevel: 0,
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BRAND, space: 6 } } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 27, bold: true, font: FONT, color: INK }, paragraph: { spacing: { before: 260, after: 100 }, outlineLevel: 1, keepNext: true } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 23, bold: true, font: FONT, color: BRAND }, paragraph: { spacing: { before: 160, after: 60 }, outlineLevel: 2, keepNext: true } },
    ],
  },
  numbering: { config: [
    { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] },
    ...["numbers", "journey", "aqi", "deploy", "risk", "auth", "refresh", "wake"].map((ref) => ({ reference: ref,
      levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 340 } } } }] })),
  ] },
  sections: [
    { properties: { page: { size: { width: PAGE_W, height: 16838 }, margin: { top: 1247, bottom: 1247, left: MARGIN, right: MARGIN } } }, children: titlePage },
    { properties: { page: { size: { width: PAGE_W, height: 16838 }, margin: { top: 1247, bottom: 1134, left: MARGIN, right: MARGIN }, pageNumbers: { start: 1 } } },
      headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: "Airware: how the project works", font: FONT, size: 18, color: "8A919E" })] })] }) },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: ["Page ", PageNumber.CURRENT], font: FONT, size: 18, color: "8A919E" })] })] }) },
      children: [
        new Paragraph({ spacing: { after: 200 }, children: [new TextRun({ text: "Contents", font: FONT, size: 36, bold: true, color: BRAND })] }),
        new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }),
        ...body,
      ] },
  ],
});

const out = path.join(ROOT, "docs", "Project_Working_Guide.docx");
Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(out, buf); console.log("Wrote", out); });
