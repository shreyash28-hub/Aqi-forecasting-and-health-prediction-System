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

const LAST_UPDATED = "26 September 2026";
const LATEST_COMMIT = "836d8f7 Supabase accounts; design docs pending commit";

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
  ["Next.js frontend", "Not started", "Waiting for your go-ahead to start coding"],
  ["Hospital map", "Not started", "Leaflet + OpenStreetMap (Overpass)"],
  ["Recommendation assistant", "Not started", "Keyword matching + precautions list"],
  ["Deployment", "Not started", "Vercel (frontend), Render or Railway (backend)"],
  ["Course mid-sem submission (19-30 Oct)", "Results ready", "Report/presentation still to prepare"],
  ["Course final submission (16-27 Nov)", "Results ready", "Report/presentation still to prepare"],
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
  ["Next.js frontend", "Backend", "City forecast charts, one-time profile form, day-by-day risk view, history, leaderboard, disclaimer"],
  ["Hospital map", "Frontend", "Shown when the alert level is High/Severe; contact details only, no booking"],
  ["Recommendation assistant", "Frontend", "Keyword matching + curated precautions, personalised with AQI and risk"],
  ["Live 2026 data", "After the frontend", "Show today's AQI and forecast from today using recent station data; needs a free OpenAQ API key"],
  ["Deployment", "All of the above", "Vercel + Render/Railway; handle the ~20 s model-loading startup"],
  ["Mid-sem report/presentation (19-30 Oct)", "You + me", "Classical models: ARIMA, SARIMA, Holt-Winters, decomposition"],
  ["Final report/presentation (16-27 Nov)", "You + me", "LSTM, XGBoost, Prophet and the comparison"],
];

const ACTIONS_FOR_YOU = [
  "Tell me when to start coding the frontend (design is approved).",
  "Optional: confirm the small frontend choices (frontend/ folder in this repo, npm, react-leaflet for the map).",
];

const IMPROVEMENTS = [
  "Most of the remaining health-risk error comes from the air-quality forecasts (especially Delhi and Ahmedabad); better forecasting is the biggest accuracy lever.",
  "Holt-Winters always selects weekly seasonality; a proper annual version needs deseasonalising first.",
  "No single forecasting model dominates; averaging the top 2-3 models per city could make forecasts more stable.",
];

const CHANGE_LOG = [
  // newest first: [date, summary]
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
