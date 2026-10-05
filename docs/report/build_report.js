// Builds docs/Project_Report.docx (course project report, 4 evaluation criteria).
// Run from the repo root after `python docs/report/make_figures.py`:
//     node docs/report/build_report.js
// Then open in Word and update the table of contents (or let scripts update it).
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, HeadingLevel, AlignmentType,
  WidthType, ShadingType, BorderStyle, LevelFormat, Footer, Header, PageNumber, ImageRun,
  TableOfContents, PageBreak,
} = require("../progress/node_modules/docx");

const ROOT = path.join(__dirname, "..", "..");
const FIG = path.join(__dirname, "figures");
const FONT = "Times New Roman";
const PAGE_W = 11906, MARGIN = 1440, CONTENT_W = PAGE_W - 2 * MARGIN;  // A4, 1" margins (9026 DXA)
const border = { style: BorderStyle.SINGLE, size: 4, color: "808080" };
const borders = { top: border, bottom: border, left: border, right: border };

// ------------------------------------------------------------------ helpers
let figN = 0, tabN = 0;
function runs(text, base = {}) {          // **bold** inline markup
  return text.split(/(\*\*[^*]+\*\*)/).filter(Boolean).map((s) =>
    s.startsWith("**") ? new TextRun({ text: s.slice(2, -2), bold: true, font: FONT, ...base })
                       : new TextRun({ text: s, font: FONT, ...base }));
}
const P = (t, opts = {}) => new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 100, line: 264 }, ...opts, children: runs(t) });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: [new TextRun({ text: t, font: FONT })] });
const H1c = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: t, font: FONT })] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text: t, font: FONT })] });
const H3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun({ text: t, font: FONT })] });
const B = (t) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, alignment: AlignmentType.JUSTIFIED, spacing: { after: 50, line: 259 }, children: runs(t) });
const N = (t, ref = "numbers") => new Paragraph({ numbering: { reference: ref, level: 0 }, alignment: AlignmentType.JUSTIFIED, spacing: { after: 50, line: 259 }, children: runs(t) });
const caption = (t) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 200 }, children: runs(t, { italics: true, size: 20 }) });

function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}
// Print width (px at 96 dpi) per figure; content width is about 600 px.
const FIG_WIDTH = {
  "fig_architecture.png": 520, "fig_pipeline.png": 520, "fig_aqi_overview.png": 430, "fig_ahmedabad_co.png": 470,
  "fig_stl_delhi.png": 420, "fig_windows.png": 470, "fig_model_heatmap.png": 510, "forecast_delhi.png": 430,
  "fig_health_models.png": 460, "health_confusion_matrix.png": 215, "fig_dashboard.png": 420,
};
function figure(file, text) {
  figN += 1;
  const { w, h } = pngSize(file);
  const width = FIG_WIDTH[path.basename(file)] || 500;
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
    borders, width: { size: w[i], type: WidthType.DXA }, margins: { top: 50, bottom: 50, left: 90, right: 90 },
    shading: head ? { fill: "D9E2F3", type: ShadingType.CLEAR, color: "auto" } : undefined,
    children: [new Paragraph({ children: runs(String(v), { size: 18, bold: head || undefined }) })],
  });
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 160, after: 80 }, children: runs(`Table ${tabN}: ${title}`, { italics: true, size: 20 }) }),
    new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: w,
      rows: [new TableRow({ tableHeader: true, children: header.map((h, i) => cell(h, i, true)) }),
             ...rows.map((r) => new TableRow({ children: r.map((v, i) => cell(v, i, false)) }))] }),
    new Paragraph({ spacing: { after: 120 }, children: [] }),
  ];
}
const fig = (name) => path.join(FIG, name);
const rep = (name) => path.join(ROOT, "reports", "figures", name);

// ------------------------------------------------------------------ title page
const center = (t, o = {}) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 }, children: [new TextRun({ text: t, font: FONT, ...o })] });
const title = [
  new Paragraph({ spacing: { before: 1200 }, children: [] }),
  center("PROJECT REPORT", { size: 28, bold: true, color: "404040" }),
  new Paragraph({ spacing: { after: 200 }, children: [] }),
  center("AQI Forecasting Driven Health Prediction System", { size: 40, bold: true }),
  center("Time-series forecasting of urban air quality with personalised health-risk estimation", { size: 26, italics: true }),
  new Paragraph({ spacing: { after: 600 }, children: [] }),
  center("Course: Time Series and Analysis Project", { size: 24 }),
  new Paragraph({ spacing: { after: 400 }, children: [] }),
  center("Submitted by", { size: 24, bold: true }),
  center("[Student Name 1]  ([Roll Number])", { size: 24 }),
  center("[Student Name 2]  ([Roll Number])", { size: 24 }),
  new Paragraph({ spacing: { after: 300 }, children: [] }),
  center("Under the guidance of", { size: 24, bold: true }),
  center("[Guide Name], [Designation]", { size: 24 }),
  new Paragraph({ spacing: { after: 600 }, children: [] }),
  center("[Department Name]", { size: 24 }),
  center("[Institute Name]", { size: 24, bold: true }),
  center("[Month Year]", { size: 24 }),
];

// ------------------------------------------------------------------ front matter
const front = [
  H1("Abstract"),
  P("Air pollution is one of the largest environmental health risks in India, yet the public mostly receives a single city-level Air Quality Index (AQI) number that says nothing about what that air means for a particular person. This project builds an end-to-end system that (i) forecasts daily AQI, PM2.5 and NO2 up to 30 days ahead for six major Indian cities using time-series and machine-learning models, and (ii) converts the forecast into a personalised, day-by-day health-risk estimate based on a user's age, health conditions and daily exposure."),
  P("Daily data from Central Pollution Control Board (CPCB) monitoring stations for Delhi, Bengaluru, Chennai, Hyderabad, Lucknow and Ahmedabad (2015-2020) were cleaned with gap-aware interpolation, and a faulty carbon-monoxide sensor in Ahmedabad was detected and corrected by recomputing AQI from hourly data with the official CPCB method. Stationarity (ADF, KPSS) and seasonality (ACF, STL) diagnostics confirmed an annual cycle of about 365 days. Six forecasting models (ARIMA, SARIMA with Fourier terms, Holt-Winters, LSTM, XGBoost and Prophet) were compared with three naive baselines on six rolling 30-day test windows per city using RMSE, MSE, MAE and MAPE. The selected model in every city beats the best baseline on mean RMSE, by 5% (Ahmedabad) to 33% (Lucknow). For the health component, Random Forest, XGBoost and a multilayer perceptron (MLP) were compared; the MLP achieved a weighted F1 of 0.873 for risk level and an RMSE of 0.198 (R² = 0.986) for risk score on held-out data."),
  P("The models are deployed behind a FastAPI backend with Supabase authentication and row-level security, tested with 41 automated tests, and a professional web interface (Airware) has been designed. Results are presented as estimated decision support, not as medical diagnosis."),
  P("**Keywords:** air quality forecasting, AQI, SARIMA, Holt-Winters, LSTM, XGBoost, Prophet, rolling-origin evaluation, health-risk prediction, FastAPI."),
  H1c("Table of Contents"),
  new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-1" }),
];

// ------------------------------------------------------------------ 1. Introduction
const intro = [
  H1("1. Introduction"),
  H2("1.1 Background"),
  P("Indian cities regularly record some of the highest particulate-matter concentrations in the world. The CPCB National Air Quality Index [1] summarises pollutant concentrations into a single value from 0 to 500 with six categories (Good, Satisfactory, Moderate, Poor, Very Poor, Severe), each with a general health advisory. Air quality is strongly seasonal: in north India, post-monsoon crop-residue burning, festival emissions and winter temperature inversions push AQI to very high levels from October to January, while the monsoon brings the cleanest air of the year."),
  H2("1.2 Problem statement"),
  P("Existing services tell people what the air quality is today or, at best, for the next few days. They do not answer two questions that matter for planning: **what will the air be like over the coming week or month**, and **what does that mean for me specifically?** A 67-year-old with chronic obstructive pulmonary disease (COPD) working outdoors in an industrial area faces a very different risk from a healthy 25-year-old office worker breathing the same air."),
  H2("1.3 Scope of this report"),
  P("The graded focus of the course is the time-series forecasting of AQI. This report covers that work in full and also documents how the forecasts are used in a complete application: personalised health-risk models, a backend API, a database with user accounts, and the web interface design. The report is organised around the four evaluation criteria: review of existing systems and feasibility (Chapter 2), objectives and methodology (Chapter 3), relevance of algorithms and techniques (Chapter 4), and synchronisation of design and implementation (Chapter 5)."),
];

// ------------------------------------------------------------------ 2. Review + feasibility
const review = [
  H1c("2. Review of Existing Systems and Project Feasibility"),
  H2("2.1 Existing air-quality information systems"),
  P("Several established systems provide air-quality information for Indian cities. They were reviewed for the type of information they provide, how far ahead they look, and whether they personalise the information."),
  B("**SAMEER (CPCB):** the official mobile application of the Central Pollution Control Board. It reports near real-time AQI from the national monitoring network with the standard category advisories."),
  B("**SAFAR (IITM Pune, Ministry of Earth Sciences):** an air-quality forecasting system for selected metropolitan cities that issues short-range forecasts, typically one to three days ahead, using numerical chemical-transport modelling."),
  B("**IQAir / AirVisual and the World Air Quality Index project (aqicn.org):** global platforms that aggregate station data and publish current AQI, maps and short-term forecasts."),
  B("**Copernicus Atmosphere Monitoring Service (CAMS):** a global atmospheric model that provides gridded pollutant forecasts for a few days ahead, used by services such as Windy and Open-Meteo."),
  ...table(["System", "Information provided", "Forecast horizon", "Personal health risk", "Model transparency"], [
    ["SAMEER (CPCB)", "Current AQI, category advisory", "None (current only)", "No", "Official AQI method"],
    ["SAFAR", "City AQI forecast", "About 1-3 days", "No", "Numerical model"],
    ["IQAir / AQICN", "Current AQI, maps, short forecast", "A few days", "No (general advice)", "Not disclosed"],
    ["CAMS-based services", "Gridded pollutant forecast", "About 5 days", "No", "Physical model"],
    ["**This project (Airware)**", "AQI, PM2.5, NO2 forecast + personal risk", "**7 and 30 days**", "**Yes, day by day**", "**Open, evaluated against baselines**"],
  ], [2.2, 2.6, 1.6, 1.6, 1.8], "Comparison of existing systems with the proposed system"),
  H2("2.2 Review of forecasting techniques"),
  P("Classical statistical methods remain strong baselines for univariate forecasting. The Box-Jenkins ARIMA family [3] models autocorrelation and, in its seasonal form (SARIMA), repeating cycles. Exponential smoothing with trend and seasonality (Holt-Winters) [5] weights recent observations more heavily and is robust and cheap. Seasonal-trend decomposition with LOESS (STL) [6] separates trend, seasonal and remainder components and is widely used for diagnosis. Hyndman and Athanasopoulos [4] recommend comparing every model against naive benchmarks and evaluating on multiple forecast origins rather than a single split [13]."),
  P("Machine-learning approaches treat forecasting as supervised learning on lagged values. Gradient-boosted trees such as XGBoost [8] capture non-linear interactions between lags and calendar features; recurrent neural networks, in particular the Long Short-Term Memory (LSTM) network [7], learn temporal dependencies directly from sequences; and Prophet [9] fits an additive model of trend, yearly and weekly seasonality that tolerates missing data. No single family dominates across datasets, which motivates comparing all of them on the same data and the same evaluation protocol."),
  H2("2.3 Gap analysis"),
  P("The review shows three gaps that this project addresses:"),
  N("**Horizon:** public systems focus on current conditions or forecasts of a few days; planning a week or a month needs longer horizons."),
  N("**Personalisation:** advisories are generic per AQI category; none combine the forecast with an individual's vulnerability and exposure."),
  N("**Transparency:** most services do not publish how their forecasts compare with simple baselines. This project selects models by measured accuracy and shows the comparison on a public leaderboard."),
  H2("2.4 Feasibility study"),
  ...table(["Aspect", "Assessment", "Outcome"], [
    ["Data", "CPCB daily data for 26 cities (2015-2020) is publicly available [2]. Six cities have 1,000-2,000 usable days with low missingness after cleaning.", "Feasible"],
    ["Technical", "All methods are available in mature open-source libraries (statsmodels, scikit-learn, XGBoost, PyTorch, Prophet). Training all models for six cities takes about 11 minutes on a laptop CPU.", "Feasible"],
    ["Economic", "Every tool is free: Python libraries, FastAPI, Supabase free tier, Next.js, Vercel and Render free tiers, OpenStreetMap. No paid API keys are required.", "Feasible at zero cost"],
    ["Operational", "Saved models load in about 20 seconds and answer a request in well under a second. Users need only a web browser.", "Feasible"],
    ["Schedule", "Forecasting pipeline, health models, backend and database are complete; the web interface is designed and is the next implementation step.", "On track"],
    ["Risks", "Data ends in mid-2020; one city had a faulty sensor; health estimates must not be presented as diagnosis.", "Mitigated (Sections 3.3, 5.6, 6.2)"],
  ], [1.3, 5.2, 1.7], "Feasibility assessment"),
];

// ------------------------------------------------------------------ 3. Objectives + methodology
const method = [
  H1c("3. Objectives and Methodology of the Proposed Work"),
  H2("3.1 Objectives"),
  N("O1. Build a clean, reusable daily time series of AQI, PM2.5 and NO2 for six Indian cities, with documented handling of missing and faulty values.", "obj"),
  N("O2. Diagnose stationarity and seasonality to guide model design.", "obj"),
  N("O3. Implement and compare classical (ARIMA, SARIMA, Holt-Winters) and machine-learning (LSTM, XGBoost, Prophet) forecasting models against naive baselines using RMSE, MSE, MAE and MAPE.", "obj"),
  N("O4. Select the best model per city by a robust, multi-window evaluation and deploy it for 7- and 30-day forecasts.", "obj"),
  N("O5. Predict a personalised health-risk level and score from the forecast and a user profile, with per-class confidence.", "obj"),
  N("O6. Deliver the forecasts and risk estimates through a secure API and a usable web interface, clearly labelled as decision support.", "obj"),
  H2("3.2 Overall methodology"),
  ...figure(fig("fig_architecture.png"), "System architecture: offline training pipelines produce saved models that the online backend serves to the web application"),
  ...figure(fig("fig_pipeline.png"), "Forecasting methodology, applied separately to AQI, PM2.5 and NO2", 560),
  H2("3.3 Datasets"),
  P("**Air-quality data.** The primary dataset is the CPCB city-level daily dataset published on Kaggle [2] (city_day.csv, about 29,500 rows, 26 cities, 1 January 2015 to 1 July 2020, with PM2.5, PM10, NO, NO2, NOx, NH3, CO, SO2, O3, benzene, toluene, xylene and AQI). Six cities with the most complete records were selected. An hourly companion file (city_hour.csv) was used to verify and recompute AQI."),
  P("**Health-risk data.** The health component uses a dataset of 7,500 person profiles. Each profile (age, gender, occupation, area type, pre-existing condition, family history of respiratory disease, smoking, BMI, weekly exercise, daily outdoor hours and mask use) is linked by city and date to the CPCB pollutant readings for that day, together with a continuous health-risk score and a four-level risk label (Low, Moderate, High, Severe). The score combines a vulnerability term with an effective-exposure term. The classes are imbalanced (Low 41%, Moderate 30%, Severe 15%, High 14%)."),
  ...figure(fig("fig_aqi_overview.png"), "Cleaned daily AQI for the six cities with a 30-day moving average", 500),
  H2("3.4 Data preprocessing"),
  P("**Missing values.** Each city's series was placed on a complete daily calendar so that missing days become explicit. Leading and trailing missing days were trimmed rather than filled. Interior gaps of up to 21 days were filled by time-weighted linear interpolation, because air quality changes gradually from day to day and the neighbouring days are a better estimate than a seasonal average. Gaps longer than 21 days were not filled; instead, the series restarts after the last long outage, since bridging months of missing data would invent a season. Every filled day is flagged and **excluded from all accuracy calculations**."),
  ...table(["City", "Period used", "Days", "Interpolated days"], [
    ["Delhi", "1 Jan 2015 - 1 Jul 2020", "2,009", "10 (0.5%)"],
    ["Bengaluru", "21 Mar 2015 - 1 Jul 2020", "1,930", "20 (1.0%)"],
    ["Chennai", "24 Mar 2015 - 1 Jul 2020", "1,927", "43 (2.2%)"],
    ["Hyderabad", "31 Mar 2015 - 1 Jul 2020", "1,920", "40 (2.1%)"],
    ["Lucknow", "21 Mar 2015 - 1 Jul 2020", "1,930", "37 (1.9%)"],
    ["Ahmedabad", "11 Oct 2017 - 1 Jul 2020", "995", "41 (4.1%)"],
  ], [1.6, 3.2, 1.2, 2.0], "AQI series after cleaning"),
  P("**Faulty sensor correction (Ahmedabad).** Ahmedabad's published AQI reached 2,049, far above the CPCB scale maximum of 500. Its median CO reading was 16.2 mg/m³ against 0.6-1.4 mg/m³ in the other five cities, and CO was the dominant sub-index in 82% of hours. The CPCB AQI calculation [1] was re-implemented from hourly data (24-hour rolling means for PM2.5, PM10, NOx, SO2 and NH3; 8-hour rolling maxima for CO and O3; AQI = maximum sub-index). With CO included, this reproduced the published Ahmedabad AQI on all 1,334 comparable days within ±1, which validates the implementation. Ahmedabad's AQI was then recomputed without CO, reducing its median from 384 to 129. In the other cities CO changes the median AQI by only 7-15 points, so their published AQI was kept."),
  ...figure(fig("fig_ahmedabad_co.png"), "Ahmedabad AQI as published (inflated by a faulty CO sensor) and as recomputed without CO"),
  P("**Transformation.** AQI and pollutant concentrations are positive and right-skewed, so all models are fitted on log(1 + x) and forecasts are transformed back before evaluation."),
  H2("3.5 Exploratory diagnostics"),
  P("The Augmented Dickey-Fuller test [11] rejects a unit root for every city (p ≤ 0.012), so no differencing is required (d = 0). The KPSS test [12] rejects level-stationarity in five cities, which together indicates series that are stationary around a strong seasonal pattern rather than trending. The autocorrelation of each detrended series peaks at lags 363-370, and STL seasonal strength [4] at a period of 365 days (0.20-0.75) is far above that at 7 days (≤ 0.07), confirming that the annual cycle dominates and weekly seasonality is weak."),
  ...table(["City", "ADF p", "KPSS p", "ACF peak near 365 (lag)", "STL strength, 365 d", "STL strength, 7 d"], [
    ["Delhi", "0.009", "0.011", "0.53 (370)", "0.67", "0.06"],
    ["Bengaluru", "<0.001", "0.010", "0.13 (363)", "0.40", "0.00"],
    ["Chennai", "<0.001", "0.010", "0.03 (367)", "0.20", "0.05"],
    ["Hyderabad", "0.002", "0.010", "0.11 (363)", "0.51", "0.05"],
    ["Lucknow", "0.012", "0.100", "0.57 (367)", "0.75", "0.07"],
    ["Ahmedabad", "<0.001", "0.010", "0.11 (368)", "0.71", "0.06"],
  ], [1.5, 1, 1, 2, 1.6, 1.4], "Stationarity and seasonality diagnostics (training series)"),
  ...figure(fig("fig_stl_delhi.png"), "STL decomposition of Delhi's log AQI with a 365-day period", 500),
  H2("3.6 Evaluation design"),
  P("A single 30-day hold-out proved misleading: the final month (June 2020) coincided with the COVID-19 lockdown and monsoon onset, when AQI was far below the same weeks of 2019, which unfairly favours a 'repeat yesterday' forecast. The project therefore uses **rolling-origin evaluation** [13]: six non-overlapping 30-day test windows per city, spaced 120 days apart so that they cover different seasons. For each window every model is trained on all data before it and forecasts the next 30 days. Accuracy is measured with RMSE (primary), MSE, MAE and MAPE on observed days only."),
  ...figure(fig("fig_windows.png"), "Rolling-origin evaluation: six 30-day test windows for Delhi"),
  P("Every model must beat three naive baselines: the last observed value, the value from the same weekday last week, and the value from the same date last year. The model with the lowest mean RMSE across the six windows is selected for each city; if no model beats the best baseline, the baseline itself is deployed. Because neural-network results depend on random initialisation, LSTM metrics are averaged over three fixed seeds (42, 43, 44)."),
  H2("3.7 Health-risk methodology"),
  P("Health risk is modelled as two supervised tasks: classification of the risk level (selected by weighted F1, also reporting accuracy, precision, recall and per-class recall) and regression of the risk score (selected by RMSE, also reporting MSE, MAE and R²). The data are split 80/20 with stratification by risk level; models are selected by 5-fold stratified cross-validation on the 80% and reported once on the untouched 20%. Balanced sample weights counter class imbalance. Two columns that would leak the target (an intermediate vulnerability score and past hospital visits) are excluded. Because the forecasting models predict AQI, PM2.5 and NO2, the deployed model uses exactly these air features, with an AQI-only model as a fallback."),
];

// ------------------------------------------------------------------ 4. Algorithms
const algos = [
  H1c("4. Relevance of Algorithms and Techniques"),
  P("Each algorithm was chosen for a specific property of air-quality data identified in Chapter 3: strong autocorrelation, a dominant annual cycle, weak weekly effects, non-linear episodes (festival and crop-burning spikes) and occasional missing data."),
  H2("4.1 Forecasting algorithms"),
  H3("Naive baselines"),
  P("Persistence (last value), seasonal naive (last week) and seasonal naive (last year) require no fitting and set the minimum standard. Persistence is surprisingly strong for slowly varying air quality, so beating it demonstrates genuine skill."),
  H3("ARIMA"),
  P("ARIMA(p, d, q) models the current value as a linear function of past values and past errors [3]. It suits the strong short-term autocorrelation of AQI (lag-7 ACF 0.42-0.81). Here d = 0 from the ADF test, and p, q ∈ {0,...,3} are chosen by the Akaike Information Criterion (AIC); the most frequently selected order was ARIMA(2,0,2). On its own ARIMA has no seasonal term, so its long-range forecasts revert to the mean."),
  H3("SARIMA with Fourier terms"),
  P("Seasonal ARIMA adds seasonal autoregressive and moving-average terms. A seasonal period of 365 days would require a 365-lag polynomial, which is extremely slow and numerically unstable on about 2,000 points. Following standard practice [4], the annual cycle is represented by three pairs of Fourier terms (sine and cosine) as external regressors, with SARIMA errors at a weekly period, for example SARIMA(2,0,2)(0,0,1)7. This captures both the annual cycle and the short-term dynamics, and it explains why SARIMA was the most consistent model."),
  H3("Holt-Winters exponential smoothing"),
  P("Holt-Winters [5] updates level, trend and seasonal components with exponentially decaying weights. An additive damped trend was used to avoid runaway extrapolation over 30 days. It is fast and stable, and it adapts quickly to level shifts."),
  H3("LSTM"),
  P("The LSTM [7] is a recurrent neural network whose gated memory cells learn long-range dependencies and non-linear patterns. A single-layer LSTM (64 units) reads the previous 60 days (scaled log AQI plus day-of-year sine and cosine) and outputs all 30 forecast days at once, which avoids the error build-up of step-by-step forecasting. Early stopping on a chronological validation split prevents overfitting."),
  H3("XGBoost on lag features"),
  P("XGBoost [8] builds an ensemble of gradient-boosted decision trees. Forecasting is reframed as regression on 21 engineered features: lags of 1-7, 14, 21 and 28 days, 7/14/30-day rolling means and standard deviations, the last daily change, and calendar features. Trees capture non-linear interactions (for example, high recent levels combined with winter months) without assuming linearity. Forecasts are made recursively, one day at a time."),
  H3("Prophet"),
  P("Prophet [9] fits a decomposable model of piecewise-linear trend plus Fourier-based yearly and weekly seasonality. It handles missing days natively and adapts its trend at changepoints, which helps with abrupt level shifts such as the 2020 lockdown."),
  H2("4.2 Health-risk algorithms"),
  P("**Random Forest** [10] averages many decision trees trained on bootstrap samples and is robust to mixed categorical and numeric features. **XGBoost** [8] adds boosting for higher accuracy on tabular data. A **multilayer perceptron (MLP)** with two hidden layers (64 and 32 neurons) from scikit-learn [14] learns smooth, multiplicative interactions between vulnerability and exposure, which matches the structure of the risk score and explains why it performed best."),
  H2("4.3 Supporting techniques"),
  P("Several techniques support the models: the **ADF and KPSS tests** [11, 12] decide the differencing order; the **ACF and STL decomposition** [6] confirm the 365-day period and measure seasonal strength; the **log(1 + x) transform** stabilises the variance of skewed pollutant data; **AIC** selects ARIMA and SARIMA orders without overfitting; **rolling-origin evaluation** [13] estimates accuracy across seasons rather than for one month; **naive baselines** prove that each model adds real skill; **stratified k-fold cross-validation with balanced sample weights** gives reliable health-model selection under class imbalance; and the **CPCB sub-index method** [1] validates and recomputes AQI to correct the faulty sensor."),
  H2("4.4 Comparative relevance"),
  ...table(["Model", "Captures", "Strength for AQI", "Limitation observed"], [
    ["ARIMA", "Short-term autocorrelation", "Simple, interpretable", "No seasonality; reverts to mean"],
    ["SARIMA + Fourier", "Autocorrelation + annual cycle", "Most consistent (best mean rank in 5 of 6 cities)", "Slower to fit"],
    ["Holt-Winters", "Level, damped trend", "Fast, adapts to level shifts", "Annual season too costly; used weekly"],
    ["LSTM", "Non-linear sequences", "Strong in Lucknow and Delhi", "Seed-sensitive; weak on short histories"],
    ["XGBoost", "Non-linear lag interactions", "Good in Hyderabad and Chennai", "Recursive error accumulation"],
    ["Prophet", "Trend changes, yearly/weekly seasonality", "Best in Lucknow and Hyderabad", "Unstable with less than 2 years of data"],
  ], [1.4, 2.2, 2.6, 2.4], "Relevance and observed behaviour of each forecasting model"),
];

// ------------------------------------------------------------------ 5. Design & implementation
const impl = [
  H1c("5. Synchronization of Project Design and Implementation"),
  P("This chapter shows how each element of the design in Chapters 3 and 4 was implemented and verified, and presents the results."),
  H2("5.1 Implementation structure"),
  ...table(["Design element", "Implementation (module)", "Status"], [
    ["Data loading and cleaning", "src/data_loader.py, src/aqi.py", "Complete"],
    ["Diagnostics and splits", "src/preprocessing.py", "Complete"],
    ["Forecasting models and baselines", "src/models/ (baselines, statistical, ml_models, deep_models, prophet_model)", "Complete"],
    ["Rolling-origin evaluation and reports", "src/run_forecasting.py, src/evaluation.py", "Complete"],
    ["Final training and model storage", "src/train_final_models.py, src/model_store.py", "Complete (18 forecasters)"],
    ["Health-risk models", "src/health/ (data, models, train, store, backtest)", "Complete (4 models)"],
    ["REST API", "src/api/ (FastAPI, 12 endpoints)", "Complete, 41 tests"],
    ["Database and accounts", "supabase/migrations/0001_init.sql (Supabase, RLS)", "Complete, live-tested"],
    ["Web interface (Airware)", "docs/frontend_design.md, approved designs", "Designed; build in progress"],
  ], [2.6, 4.2, 1.6], "Design-to-implementation mapping"),
  H2("5.2 Forecasting results"),
  P("Table 7 summarises the selected model for each city over the six test windows. In every city the selected model beats the best naive baseline. Gains are largest where the annual cycle is strongest (Lucknow, Delhi) and smallest in Ahmedabad, whose usable history is shortest."),
  ...table(["City", "Selected model", "Mean RMSE", "Mean MAE", "Mean MAPE", "Best baseline RMSE", "Improvement"], [
    ["Delhi", "SARIMA", "69.21", "55.88", "26.2%", "98.91", "-30%"],
    ["Lucknow", "Prophet", "55.90", "43.82", "23.6%", "83.16", "-33%"],
    ["Bengaluru", "SARIMA", "19.35", "15.78", "20.0%", "25.55", "-24%"],
    ["Chennai", "ARIMA", "37.45", "27.48", "24.7%", "42.87", "-13%"],
    ["Hyderabad", "Prophet", "22.39", "19.00", "29.9%", "25.88", "-13%"],
    ["Ahmedabad", "Holt-Winters", "57.44", "48.17", "32.2%", "60.75", "-5%"],
  ], [1.4, 1.5, 1.1, 1.1, 1.1, 1.5, 1.2], "AQI forecasting: selected model per city (mean over six 30-day windows)"),
  ...figure(fig("fig_model_heatmap.png"), "Mean RMSE of every model relative to the best baseline in each city"),
  P("Three findings stand out. First, no single model wins everywhere: SARIMA has the best average rank in five of six cities, while Prophet wins in Lucknow and Hyderabad. Second, seasonal knowledge matters most at the start of winter; in Delhi's October-November 2019 window, persistence had an RMSE of 246 while Prophet (105) and SARIMA (126) anticipated the rise. Third, the single June 2020 window would have selected a different model in five of six cities, which justifies the multi-window design. Applying the same pipeline to PM2.5 and NO2, a model beat the baseline in 10 of 12 city-pollutant pairs; in the other two (Hyderabad PM2.5, Ahmedabad NO2) the baseline is deployed, as the methodology requires."),
  ...figure(rep("forecast_delhi.png"), "Delhi: 30-day forecasts of all models on the final test window"),
  H2("5.3 Health-risk results"),
  ...table(["Model", "Weighted F1", "Accuracy", "Precision (w)", "Recall (w)", "Score RMSE", "Score MAE", "Score R²"], [
    ["Baseline (majority / mean)", "0.236", "0.408", "0.166", "0.408", "1.648", "1.072", "0.000"],
    ["Random Forest", "0.845", "0.845", "0.845", "0.845", "0.403", "0.225", "0.940"],
    ["XGBoost", "0.858", "0.858", "0.858", "0.858", "0.296", "0.162", "0.968"],
    ["**MLP (selected)**", "**0.873**", "**0.873**", "**0.875**", "**0.873**", "**0.198**", "**0.147**", "**0.986**"],
  ], [2.2, 1.1, 1, 1.1, 1, 1.1, 1, 1], "Health-risk models on the held-out test set (profile + AQI + PM2.5 + NO2)"),
  P("The MLP was selected for both tasks. Per-class recall on the test set is 92% (Low), 79% (Moderate), 88% (High) and 91% (Severe); almost all errors fall into a neighbouring level. Adding PM2.5 and NO2 to AQI raised weighted F1 from 0.839 to 0.873 and cut score RMSE by 47% compared with AQI alone, whereas adding PM10, SO2 and O3 brought no further gain."),
  ...figure(fig("fig_health_models.png"), "Health-risk model comparison across three feature sets"),
  ...figure(rep("health_confusion_matrix.png"), "Confusion matrix of the selected risk-level classifier (test set)", 260),
  P("Because the classifier and regressor are trained separately, they can disagree near a level boundary (6.8% of test cases). A boundary rule resolves this: the classifier's level is shown, the day is flagged as borderline and displayed as a range (for example Moderate-High), and the higher level drives alerts such as the hospital map. With this rule 95.9% of true High/Severe cases trigger an alert. A backtest that feeds the health model with actual historical forecasts rather than measured air confirmed that the pollutant-aware model remains better (73.3% versus 68.5% level agreement with the reference) and showed that forecast error, not the health model, is now the main source of uncertainty."),
  H2("5.4 Deployment design"),
  P("**Model serving.** Each selected model is retrained on its city's full history and saved in its native format (joblib for statsmodels and scikit-learn, XGBoost's binary format, PyTorch state dictionaries, Prophet JSON) with metadata recording configuration, training span, metrics and library versions. Reloaded models reproduce the in-memory forecasts exactly."),
  P("**Backend.** A FastAPI service loads all models at start-up and exposes public endpoints (cities, 1-30 day forecasts with CPCB categories, risk prediction, profile schema and leaderboards) and signed-in endpoints (save profile, run a prediction that is stored in history, list, view and delete past runs). Input validation enforces the required profile fields."),
  P("**Database and security.** Supabase (PostgreSQL with authentication) stores profiles and prediction history. Row-level security ensures each user can read and change only their own rows; the backend performs every database call with the user's own access token, so these rules also apply inside the backend. Public tables are read-only to the public."),
  P("**Web interface.** The interface, named Airware, follows a data-first dashboard design: city tabs, tomorrow's AQI on the CPCB scale with the official health advisory, an interactive forecast chart, pollutant trends, a day-by-day personal risk strip with confidence, precautions, and a comparison of all cities, in light and dark themes. Every risk view carries the disclaimer that results are estimated decision support, not a medical diagnosis."),
  ...figure(fig("fig_dashboard.png"), "Approved design of the Airware dashboard, populated with real model output", 500),
  H2("5.5 Traceability of objectives"),
  ...table(["Objective", "Design decision", "Evidence of implementation"], [
    ["O1 Clean data", "Gap-aware interpolation; CPCB AQI recomputation", "Table 3; Figure 4; exact match on 1,334 days"],
    ["O2 Diagnostics", "ADF, KPSS, ACF, STL", "Table 4; Figure 5"],
    ["O3 Model comparison", "6 models + 3 baselines, 4 metrics", "Figure 7; full results in project reports"],
    ["O4 Robust selection", "6 rolling windows, lowest mean RMSE", "Table 7; all cities beat baseline"],
    ["O5 Personal risk", "RF/XGBoost/MLP, boundary rule", "Table 8; Figures 9-10"],
    ["O6 Delivery", "FastAPI, Supabase RLS, Airware UI", "12 endpoints, 41 tests, live check, Figure 11"],
  ], [1.7, 3.0, 3.5], "Traceability from objectives to implementation evidence"),
  H2("5.6 Testing and verification"),
  B("**Model reproducibility:** saved models reproduce training-time forecasts exactly; LSTM and XGBoost runs are seeded and single-threaded for repeatability."),
  B("**Regression checks:** refactoring the models was verified to change no evaluation result."),
  B("**API tests:** 41 automated tests cover all endpoints, input validation, consistency with saved models, and data isolation between users (using an in-memory database stand-in that enforces the same security rules)."),
  B("**Live test:** an end-to-end check against the real Supabase project passed all 8 steps (save and read profile, run and store a prediction, list and read history, access denied without sign-in, delete)."),
  B("**Sanity checks:** predicted risk rises with AQI and falls with mask use, matching domain expectations."),
];

// ------------------------------------------------------------------ 6. Conclusion
const concl = [
  H1c("6. Conclusion and Future Work"),
  H2("6.1 Conclusion"),
  P("The project delivers a complete, evaluated pipeline from raw CPCB measurements to personalised, day-by-day health-risk estimates. Careful data preparation, including the detection and correction of a faulty sensor, produced a trustworthy dataset. Rolling-origin evaluation over six seasons showed that the selected model in every city beats naive forecasts, by up to 33%, and that seasonal models such as SARIMA with Fourier terms are the most consistent, while no single algorithm dominates. The health-risk MLP reached a weighted F1 of 0.873. The design is implemented end-to-end through a tested API and a secure database, with the web interface designed and in development."),
  H2("6.2 Limitations"),
  B("The air-quality data end in July 2020, so forecasts start from that date."),
  B("Forecast accuracy decreases with horizon and in volatile cities (Delhi, Ahmedabad); 30-day forecasts indicate the trend rather than exact daily values."),
  B("Health-risk outputs are estimates for decision support and must not be used as medical diagnosis."),
  H2("6.3 Future work"),
  B("Integrate live station data (for example through OpenAQ) with a daily refresh so the system forecasts from the current date."),
  B("Ensemble the top models per city and add weather variables to improve accuracy."),
  B("Complete the web interface, hospital map (OpenStreetMap and Overpass) and precautions assistant, and deploy on Vercel and Render."),
];

// ------------------------------------------------------------------ references
const refs = [
  "Central Pollution Control Board (CPCB), \"National Air Quality Index,\" Ministry of Environment, Forest and Climate Change, Government of India, 2014.",
  "V. Rao, \"Air Quality Data in India (2015-2020),\" Kaggle dataset, 2020. [Online]. Available: kaggle.com/datasets/rohanrao/air-quality-data-in-india",
  "G. E. P. Box, G. M. Jenkins, G. C. Reinsel and G. M. Ljung, Time Series Analysis: Forecasting and Control, 5th ed. Hoboken, NJ: Wiley, 2015.",
  "R. J. Hyndman and G. Athanasopoulos, Forecasting: Principles and Practice, 3rd ed. Melbourne: OTexts, 2021.",
  "P. R. Winters, \"Forecasting sales by exponentially weighted moving averages,\" Management Science, vol. 6, no. 3, pp. 324-342, 1960.",
  "R. B. Cleveland, W. S. Cleveland, J. E. McRae and I. Terpenning, \"STL: A seasonal-trend decomposition procedure based on loess,\" Journal of Official Statistics, vol. 6, no. 1, pp. 3-73, 1990.",
  "S. Hochreiter and J. Schmidhuber, \"Long short-term memory,\" Neural Computation, vol. 9, no. 8, pp. 1735-1780, 1997.",
  "T. Chen and C. Guestrin, \"XGBoost: A scalable tree boosting system,\" in Proc. 22nd ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining, 2016, pp. 785-794.",
  "S. J. Taylor and B. Letham, \"Forecasting at scale,\" The American Statistician, vol. 72, no. 1, pp. 37-45, 2018.",
  "L. Breiman, \"Random forests,\" Machine Learning, vol. 45, no. 1, pp. 5-32, 2001.",
  "D. A. Dickey and W. A. Fuller, \"Distribution of the estimators for autoregressive time series with a unit root,\" Journal of the American Statistical Association, vol. 74, pp. 427-431, 1979.",
  "D. Kwiatkowski, P. C. B. Phillips, P. Schmidt and Y. Shin, \"Testing the null hypothesis of stationarity against the alternative of a unit root,\" Journal of Econometrics, vol. 54, pp. 159-178, 1992.",
  "L. J. Tashman, \"Out-of-sample tests of forecasting accuracy: an analysis and review,\" International Journal of Forecasting, vol. 16, no. 4, pp. 437-450, 2000.",
  "F. Pedregosa et al., \"Scikit-learn: Machine learning in Python,\" Journal of Machine Learning Research, vol. 12, pp. 2825-2830, 2011.",
  "S. Seabold and J. Perktold, \"Statsmodels: Econometric and statistical modeling with Python,\" in Proc. 9th Python in Science Conf., 2010.",
];
const references = [H1c("References"), ...refs.map((r, i) => new Paragraph({ spacing: { after: 100, line: 276 }, indent: { left: 540, hanging: 540 }, children: [new TextRun({ text: `[${i + 1}]\t${r}`, font: FONT, size: 22 })] }))];

// ------------------------------------------------------------------ document
const doc = new Document({
  creator: "[Student Names]",
  title: "AQI Forecasting Driven Health Prediction System - Project Report",
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, font: FONT }, paragraph: { spacing: { before: 360, after: 180 }, outlineLevel: 0, keepNext: true } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 25, bold: true, font: FONT }, paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 1, keepNext: true } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 22, bold: true, italics: true, font: FONT }, paragraph: { spacing: { before: 120, after: 60 }, outlineLevel: 2, keepNext: true } },
    ],
  },
  numbering: { config: [
    { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] },
    { reference: "numbers", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 300 } } } }] },
    { reference: "obj", levels: [{ level: 0, format: LevelFormat.NONE, text: "", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 360, hanging: 0 } } } }] },
  ] },
  sections: [
    { properties: { page: { size: { width: PAGE_W, height: 16838 }, margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN } } },
      children: title },
    { properties: { page: { size: { width: PAGE_W, height: 16838 }, margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN }, pageNumbers: { start: 1 } } },
      headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: "AQI Forecasting Driven Health Prediction System", font: FONT, size: 18, italics: true, color: "666666" })] })] }) },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 20 })] })] }) },
      children: [...front, ...intro, ...review, ...method, ...algos, ...impl, ...concl, ...references] },
  ],
});

const out = path.join(ROOT, "docs", "Project_Report.docx");
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(out, b); console.log("Wrote", out, "| figures:", figN, "| tables:", tabN); });
