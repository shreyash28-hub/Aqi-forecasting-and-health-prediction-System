// Mid-sem (Phase 2) presentation, 8 slides: classical time-series models for daily AQI.
// Numbers come from docs/phase2/deck_data.json (python docs/phase2/deck_data.py) and
// reports/phase2/*.csv (python -m src.phase2); the decomposition figure from reports/phase2/figures.
//
// Run:  cd docs/phase2 && npm install && node build_deck.js
// Out:  docs/phase2/AQI_Forecasting_Phase2_MidSem.pptx

const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const sharp = require("sharp");

const ROOT = path.resolve(__dirname, "..", "..");
const FIG = path.join(ROOT, "reports", "phase2", "figures");
const OUT = path.join(__dirname, "AQI_Forecasting_Phase2_MidSem.pptx");
const D = JSON.parse(fs.readFileSync(path.join(__dirname, "deck_data.json"), "utf8"));

const CITIES = ["Delhi", "Bengaluru", "Chennai", "Hyderabad", "Lucknow", "Ahmedabad"];
const BASELINES = ["Naive (last value)", "Seasonal naive (weekly)", "Seasonal naive (annual)"];
const rmse = (c, m) => D.mean_rmse.find((r) => r.city === c && r.model === m).rmse;
const bestOf = (c) => D.best.find((r) => r.City === c);
const param = (c, m) => D.params.find((r) => r.City === c && r.Model === m);

// Palette: deep ink for the frame, amber for pollution, teal for the models.
const K = {
  ink: "0F172A", ink2: "1E293B", body: "334155", muted: "64748B", faint: "94A3B8",
  rule: "E2E8F0", paper: "F8FAFC", white: "FFFFFF",
  amber: "F59E0B", orange: "EA580C", teal: "0D9488", tealLight: "5EEAD4", violet: "7C3AED",
};
const THEME = {
  name: "Phase 2", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: K.ink, lt1: K.white, dk2: K.body, lt2: K.paper, accent1: K.teal, accent2: K.orange,
    accent3: K.amber, accent4: K.violet, accent5: K.faint, accent6: K.rule, hlink: K.teal, folHlink: K.violet },
};

async function fit(file, box) {
  const { width, height } = await sharp(file).metadata();
  const r = Math.min(box.w / width, box.h / height);
  return { path: file, w: width * r, h: height * r, x: box.x + (box.w - width * r) / 2, y: box.y + (box.h - height * r) / 2 };
}

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in
  pres.author = "Shreyash Singh, Bhoomi Singh";
  pres.title = "AQI Forecasting: Mid-Sem Evaluation (Phase 2)";
  pres.theme = { headFontFace: "Cambria", bodyFontFace: "Calibri" };

  // Light content layout: kicker, headline, footer, page number.
  pres.defineSlideMaster({
    title: "LIGHT",
    background: { color: K.paper },
    margin: [0.5, 0.55, 0.5, 0.55],
    objects: [
      { placeholder: { options: { name: "kicker", type: "body", x: 0.55, y: 0.38, w: 8.9, h: 0.24, fontFace: "Calibri",
        fontSize: 10, bold: true, color: K.orange, charSpacing: 2, margin: 0, align: "left", valign: "middle" }, text: "" } },
      { placeholder: { options: { name: "title", type: "title", x: 0.55, y: 0.64, w: 8.9, h: 0.62, fontFace: "Cambria",
        fontSize: 26, bold: true, color: K.ink, margin: 0, align: "left", valign: "top" }, text: "" } },
      { text: { text: "AQI Forecasting  ·  Mid-Sem Evaluation, Phase 2", options: { x: 0.55, y: 5.25, w: 5, h: 0.2,
        fontFace: "Calibri", fontSize: 8, color: K.faint, margin: 0 } } },
    ],
    slideNumber: { x: 9.05, y: 5.25, w: 0.4, h: 0.2, fontFace: "Calibri", fontSize: 8, color: K.faint, align: "right" },
  });
  pres.defineSlideMaster({ title: "DARK", background: { color: K.ink }, objects: [] });

  const T = (s, t, o) => s.addText(t, { isTextBox: true, margin: 0, fontFace: "Calibri", color: K.body, valign: "top", ...o });
  const light = (kicker, title, section) => {
    const s = pres.addSlide({ masterName: "LIGHT", sectionTitle: section });
    s.addText(kicker, { placeholder: "kicker" });
    s.addText(title, { placeholder: "title" });
    return s;
  };
  const rule = (s, x, y, w, color = K.rule) =>
    s.addShape(pres.shapes.LINE, { x, y, w, h: 0, line: { color, width: 0.75 }, objectName: "rule" });
  const vrule = (s, x, y, h) =>
    s.addShape(pres.shapes.LINE, { x, y, w: 0, h, line: { color: K.rule, width: 0.75 }, objectName: "column rule" });
  const axis = { catAxisLabelColor: K.muted, valAxisLabelColor: K.muted, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
    catAxisLabelFontSize: 9, valAxisLabelFontSize: 9, valGridLine: { color: "E2E8F0", size: 0.5 }, catGridLine: { style: "none" },
    catAxisLineColor: "CBD5E1", valAxisLineShow: false, catAxisMajorTickMark: "none", valAxisMajorTickMark: "none" };

  // ------------------------------------------------------------------ 1. Title
  pres.addSection({ title: "Opening" });
  {
    const s = pres.addSlide({ masterName: "DARK", sectionTitle: "Opening" });
    T(s, "TIME SERIES & ANALYSIS PROJECT  ·  MID-SEM EVALUATION", { x: 0.6, y: 0.5, w: 8.8, h: 0.25, fontSize: 10, bold: true, color: K.amber, charSpacing: 3 });
    s.addText("AQI Forecasting Driven Health Prediction System", { isTextBox: true, x: 0.6, y: 0.9, w: 7.6, h: 1.25, margin: 0,
      fontFace: "Cambria", fontSize: 34, bold: true, color: K.white, valign: "top" });
    T(s, "Phase 2: forecasting daily AQI 30 days ahead with ARIMA, SARIMA and Holt-Winters, across six Indian cities", {
      x: 0.6, y: 2.2, w: 6.8, h: 0.6, fontSize: 15, color: "CBD5E1" });
    s.addChart(pres.charts.LINE, [{ name: "Delhi monthly mean AQI", labels: D.monthly.labels, values: D.monthly.values }], {
      x: 0.45, y: 2.95, w: 9.1, h: 1.55, chartColors: [K.amber], lineSize: 2, lineDataSymbol: "none", lineSmooth: true,
      catAxisHidden: true, valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" },
      showLegend: false, objectName: "Delhi monthly AQI line", altText: "Delhi monthly mean AQI, 2015 to 2020, peaking every winter" });
    T(s, "Delhi, monthly mean AQI, 2015–2020: the winter peaks we are trying to forecast", { x: 0.6, y: 4.45, w: 6, h: 0.22, fontSize: 9, italic: true, color: K.faint });
    T(s, [
      { text: "Shreyash Singh", options: { bold: true, color: K.white } }, { text: "  S24CSEU1290", options: { color: K.faint, breakLine: true } },
      { text: "Bhoomi Singh", options: { bold: true, color: K.white } }, { text: "  S24CSEU0886", options: { color: K.faint } },
    ], { x: 0.6, y: 4.8, w: 4, h: 0.5, fontSize: 11 });
    T(s, "CPCB daily data via Kaggle  ·  2015–2020", { x: 5.6, y: 5.0, w: 3.8, h: 0.25, fontSize: 10, color: K.faint, align: "right" });
    s.addNotes("Good morning. In Phase 1 we explored the data. In Phase 2 we built the first forecasting models: classical time-series models that predict daily AQI a month ahead for six cities. The line at the bottom is Delhi's monthly AQI; those winter peaks are what we are trying to forecast.");
  }

  // ------------------------------------------------------------------ 2. The question
  pres.addSection({ title: "Approach" });
  {
    const s = light("01  ·  FROM PLAN TO IMPLEMENTATION", "Every step we planned, built and tested", "Approach");
    T(s, [{ text: "The question for this phase: ", options: { bold: true, color: K.ink } },
      { text: `can a model forecast AQI a month ahead better than “tomorrow looks like today”? Six cities, ${D.total_days.toLocaleString("en-IN")} days of CPCB data, 2015–2020.` }],
      { x: 0.55, y: 1.4, w: 8.9, h: 0.3, fontSize: 12, color: K.body });
    const line = (pt, color) => ({ pt, color });
    const none = { type: "none" };
    const headCell = (t) => ({ text: t, options: { bold: true, color: K.muted, fontSize: 9, border: [none, none, line(1, K.faint), none] } });
    const cell = (t, o = {}) => ({ text: t, options: { border: [none, none, line(0.5, K.rule), none], ...o } });
    const code = (t) => cell(t, { fontFace: "Consolas", fontSize: 9, color: K.teal });
    const rows = [
      ["Clean the data (gaps found in EDA)", "Daily index, gaps ≤ 21 days interpolated, log(1 + AQI), Ahmedabad CO fixed", "src/data_loader.py\nsrc/preprocessing.py", "preprocessing.csv"],
      ["Test stationarity", "ADF and KPSS on the level and the first difference", "src/preprocessing.py", "stationarity.csv"],
      ["Let decomposition guide the models", "Decomposition and ACF / PACF of log AQI", "src/phase2.py", "decomposition, ACF plots"],
      ["ARIMA / SARIMA for trend and season", "ARIMA; SARIMA + annual Fourier terms; orders by AIC", "src/models/statistical.py", "parameters.csv, AIC grids"],
      ["Holt-Winters for the yearly cycle", "Damped trend; 7- vs 365-day season by AIC", "src/models/statistical.py", "parameters.csv"],
      ["Check model assumptions", "Ljung-Box and Jarque-Bera on the residuals", "src/phase2.py", "residual_diagnostics.csv"],
      ["Score with RMSE, MAE, MAPE", "6 rolling 30-day windows against 3 naive baselines", "src/run_forecasting.py", "metrics.csv, forecast plots"],
    ];
    s.addTable([
      ["Planned", "What we built", "Code", "Result (reports/)"].map(headCell),
      ...rows.map(([a, b, c, d]) => [cell(a, { bold: true, color: K.ink }), cell(b), code(c), cell(d, { color: K.muted })]),
    ], { x: 0.55, y: 1.85, w: 8.9, colW: [2.25, 3.05, 1.95, 1.65], rowH: 0.4, fontFace: "Calibri", fontSize: 10.5, color: K.body,
      valign: "middle", margin: [0.02, 0.06, 0.02, 0.02] });
    s.addNotes("This slide links the plan to the build. Each step we proposed in the synopsis, plus the checks the Phase 2 brief asks for, has a method, the code file that implements it, and the saved result. The question running through it all: can a model forecast AQI a month ahead better than assuming tomorrow looks like today? Running python -m src.run_forecasting and then python -m src.phase2 reproduces every number in this deck.");
  }

  // ------------------------------------------------------------------ 3. Data and stationarity
  pres.addSection({ title: "Analysis" });
  {
    const s = light("02  ·  DATA AND STATIONARITY", "Stationary, but the level breathes with the seasons", "Analysis");
    T(s, "WHAT WE DID TO THE DATA", { x: 0.55, y: 1.45, w: 3.7, h: 0.22, fontSize: 9, bold: true, color: K.muted, charSpacing: 2 });
    T(s, [
      { text: "Filled short gaps only. ", options: { bold: true, color: K.ink } },
      { text: "Gaps up to 21 days are interpolated (0.5–4% of days) and never used for scoring.", options: { breakLine: true } },
      { text: "Took the log. ", options: { bold: true, color: K.ink } },
      { text: "AQI is skewed and swings harder when it is high; log(1 + AQI) evens that out.", options: { breakLine: true } },
      { text: "Fixed Ahmedabad. ", options: { bold: true, color: K.ink } },
      { text: "A faulty CO sensor inflated its AQI, so we rebuilt it without CO." },
    ], { x: 0.55, y: 1.75, w: 3.75, h: 1.75, fontSize: 11.5, paraSpaceAfter: 7 });
    rule(s, 0.55, 3.6, 3.75);
    T(s, "WHAT THE TESTS SAID", { x: 0.55, y: 3.75, w: 3.7, h: 0.22, fontSize: 9, bold: true, color: K.muted, charSpacing: 2 });
    T(s, [
      { text: "ADF rejects a unit root in all 6 cities (p < 0.05). ", options: { color: K.ink } },
      { text: "KPSS objects in 5, because the mean moves with the seasons. ", options: { color: K.ink } },
      { text: "So no differencing (d = 0); the yearly cycle is modelled directly.", options: { bold: true, color: K.teal } },
    ], { x: 0.55, y: 4.03, w: 3.75, h: 1.05, fontSize: 11.5 });
    const img = await fit(path.join(FIG, "03_decomposition_delhi.png"), { x: 4.55, y: 1.4, w: 4.95, h: 3.75 });
    s.addImage({ ...img, objectName: "Delhi decomposition", altText: "Delhi log AQI split into trend, yearly seasonal pattern and residual" });
    s.addNotes("We kept preprocessing light: fill only short gaps, take the log, and fix Ahmedabad's faulty CO readings. The ADF test says there is no unit root anywhere; KPSS disagrees in five cities because the level moves with the seasons, which the decomposition on the right shows clearly for Delhi. So we do not difference; we model the yearly cycle instead.");
  }

  // ------------------------------------------------------------------ 4. ACF
  {
    const s = light("03  ·  READING THE STRUCTURE", "The autocorrelation chose our models for us", "Analysis");
    s.addChart(pres.charts.LINE, [{ name: "ACF, Delhi log AQI", labels: ["0", ...D.acf.lags.map(String)], values: [1, ...D.acf.values] }], {
      x: 0.45, y: 1.35, w: 5.9, h: 3.0, chartColors: [K.teal], lineSize: 2, lineDataSymbol: "none",
      ...axis, catAxisLabelFrequency: 50, valAxisMinVal: -0.4, valAxisMaxVal: 1, valAxisMajorUnit: 0.2, valAxisLabelFormatCode: "0.0",
      showLegend: false, showTitle: true, title: "Delhi: correlation of log AQI with itself, 0–400 days apart",
      titleFontSize: 10, titleColor: K.muted, titleFontFace: "+mn-lt", objectName: "ACF chart",
      altText: "Autocorrelation of Delhi log AQI, starting near 0.9, dipping negative around 130 days and peaking again near 365" });
    const marks = [["Lag 1:  " + D.acf.values[0].toFixed(2), "Yesterday predicts today"], ["Lags 100–250: negative", "Summer vs winter, opposite seasons"],
      ["Lag 365: back to " + Math.max(...D.acf.values.slice(340, 390)).toFixed(2), "The yearly cycle returns"]];
    marks.forEach(([h, d], i) => {
      const x = 0.65 + i * 1.93;
      T(s, h, { x, y: 4.42, w: 1.85, h: 0.24, fontSize: 10.5, bold: true, color: K.ink });
      T(s, d, { x, y: 4.66, w: 1.85, h: 0.4, fontSize: 10, color: K.muted });
    });
    vrule(s, 6.6, 1.45, 3.6);
    const imp = [["Strong persistence", "→ autoregressive terms", "ARIMA"], ["A yearly wave", "→ annual Fourier terms", "SARIMA"],
      ["Level + season smoothing", "→ exponential smoothing", "Holt-Winters"]];
    imp.forEach(([a, b, m], i) => {
      const y = 1.5 + i * 1.18;
      T(s, a, { x: 6.85, y, w: 2.65, h: 0.28, fontSize: 13, bold: true, color: K.ink });
      T(s, b, { x: 6.85, y: y + 0.3, w: 2.65, h: 0.26, fontSize: 11, color: K.muted });
      T(s, m, { x: 6.85, y: y + 0.58, w: 2.65, h: 0.28, fontFace: "Cambria", fontSize: 13, bold: true, color: K.teal });
    });
    s.addNotes("This is the autocorrelation of Delhi's log AQI. It starts around 0.9, so yesterday is a strong predictor of today. It turns negative for opposite seasons and climbs back near one year. Persistence points to AR terms, the yearly wave to Fourier terms in SARIMA, and Holt-Winters gives us a smoothing-based alternative. The weekly pattern turned out to be weak.");
  }

  // ------------------------------------------------------------------ 5. Models
  pres.addSection({ title: "Models" });
  {
    const s = light("04  ·  THE MODELS", "Three classical models, each tuned by AIC", "Models");
    const cols = [
      ["ARIMA", K.teal, "Uses the last few days of AQI and the last few errors.", "p, q ≤ 3 searched by AIC; d = 0 from the ADF test."],
      ["SARIMA", K.orange, "ARIMA plus a weekly term and three yearly sine/cosine waves.",
        "A 365-day seasonal ARIMA is too slow on ~1,900 days, so Fourier terms carry the year."],
      ["Holt-Winters", K.violet, "Smooths level, trend and season separately.", "Damped trend; season of 7 or 365 days chosen by AIC."],
    ];
    cols.forEach(([name, color, idea, why], i) => {
      const x = 0.55 + i * 3.0, w = 2.7;
      T(s, name, { x, y: 1.38, w, h: 0.4, fontFace: "Cambria", fontSize: 19, bold: true, color });
      T(s, idea, { x, y: 1.8, w, h: 0.48, fontSize: 11.5, color: K.ink });
      T(s, why, { x, y: 2.3, w, h: 0.5, fontSize: 10, color: K.muted });
      if (i < 2) vrule(s, x + w + 0.15, 1.42, 1.38);
    });

    // Orders chosen by AIC for every city, with the residual check alongside
    const none = { type: "none" };
    const cell = (t, o = {}) => ({ text: t, options: { border: [none, none, { pt: 0.5, color: K.rule }, none], align: "center", ...o } });
    const head = [cell("Chosen by AIC", { align: "left", bold: true, color: K.muted, fontSize: 9 }),
      ...CITIES.map((c) => cell(c, { bold: true, color: K.muted, fontSize: 9 })),
      cell("White-noise residuals*", { bold: true, color: K.muted, fontSize: 9 })];
    head.forEach((h) => { h.options.border = [none, none, { pt: 1, color: K.faint }, none]; });
    const order = (cfg) => cfg.replace(/^S?ARIMA/, "").replace(" + 3 annual Fourier pairs", "").replace(/, /g, ",").replace(")x(", ")(").replace(/,7\)$/, ")₇");
    const lb = (m) => cell(`${D.lb_pass[m]} / 6`, { bold: true, color: D.lb_pass[m] >= 4 ? K.teal : K.orange });
    const rowsT = [
      [cell("ARIMA", { align: "left", bold: true, color: K.teal }), ...CITIES.map((c) => cell(order(param(c, "ARIMA").Configuration))), lb("ARIMA")],
      [cell("SARIMA", { align: "left", bold: true, color: K.orange }), ...CITIES.map((c) => cell(order(param(c, "SARIMA").Configuration))), lb("SARIMA")],
      [cell("Holt-Winters", { align: "left", bold: true, color: K.violet }),
        ...CITIES.map((c) => cell(`m 7 · α ${Number(param(c, "Holt-Winters")["alpha (level)"]).toFixed(2)}`)), lb("Holt-Winters")],
    ];
    s.addTable([head, ...rowsT], { x: 0.55, y: 2.95, w: 8.9, colW: [1.05, 1.08, 1.08, 1.08, 1.08, 1.08, 1.08, 1.37], rowH: 0.3,
      fontFace: "Calibri", fontSize: 9.5, color: K.body, valign: "middle", margin: [0.02, 0.03, 0.02, 0.03] });

    const gaps = Object.values(D.aic);
    T(s, [
      { text: "Why these orders: ", options: { bold: true, color: K.ink } },
      { text: `in every city the runner-up ARIMA order is within ${Math.max(...gaps.map((g) => g.runner_up)).toFixed(0)} AIC points of the best, so the exact order matters little; ` },
      { text: `but the best model without an AR term is ${Math.min(...gaps.map((g) => g.no_ar))}–${Math.max(...gaps.map((g) => g.no_ar))} points worse, so the AR terms are essential.`, options: { bold: true, color: K.teal } },
    ], { x: 0.55, y: 4.3, w: 8.9, h: 0.45, fontSize: 10.5 });
    T(s, `*Ljung-Box at lag 14, by city. Residuals are heavy-tailed (kurtosis ${D.kurtosis[0].toFixed(1)}–${D.kurtosis[1].toFixed(1)}), and Holt-Winters, with no AR term, leaves day-to-day persistence in its errors.`,
      { x: 0.55, y: 4.82, w: 8.9, h: 0.35, fontSize: 9.5, italic: true, color: K.muted });
    s.addNotes("Three models. ARIMA uses recent days and errors. SARIMA adds a weekly term and yearly waves. Holt-Winters smooths level, trend and season. The table shows the orders AIC chose in each city. The AIC evidence: the second-best ARIMA order is always within about two points of the best, so the exact order is not critical, but dropping the AR terms costs hundreds of points. Then the assumption check: ARIMA and SARIMA leave white-noise residuals in four of six cities; Holt-Winters fails in all six because it has no autoregressive term.");
  }

  // ------------------------------------------------------------------ 6. Forecast example and testing
  pres.addSection({ title: "Results" });
  {
    const s = light("05  ·  FORECASTING A MONTH AHEAD", "Delhi, June 2020: a month-ahead forecast vs reality", "Results");
    const h = D.delhi_holdout, n = h.n_hist, total = h.actual.length;
    const pad = (arr) => Array(n).fill(null).concat(arr);
    const series = [
      { name: "Measured AQI", labels: h.labels, values: h.actual },
      { name: `Naive (RMSE ${h.rmse["Naive (last value)"]})`, labels: h.labels, values: pad(h.forecasts["Naive (last value)"]) },
      { name: `ARIMA (RMSE ${h.rmse.ARIMA})`, labels: h.labels, values: pad(h.forecasts.ARIMA) },
      { name: `SARIMA (RMSE ${h.rmse.SARIMA})`, labels: h.labels, values: pad(h.forecasts.SARIMA) },
      { name: `Holt-Winters (RMSE ${h.rmse["Holt-Winters"]})`, labels: h.labels, values: pad(h.forecasts["Holt-Winters"]) },
    ];
    s.addChart(pres.charts.LINE, series, {
      x: 0.45, y: 1.35, w: 5.95, h: 3.75, chartColors: [K.ink, K.faint, K.teal, K.orange, K.violet],
      lineSize: 2, lineDataSymbol: "none",
      ...axis, catAxisLabelFrequency: 10, valAxisLabelFormatCode: "0", valAxisMinVal: 40,
      showLegend: true, legendPos: "b", legendFontSize: 9, legendFontFace: "+mn-lt", legendColor: K.body,
      objectName: "Delhi hold-out forecast chart", altText: `Delhi AQI from ${h.labels[0]} with 30-day forecasts from 1 June 2020` });
    T(s, "HOW EVERY MODEL IS TESTED", { x: 6.75, y: 1.45, w: 2.7, h: 0.22, fontSize: 9, bold: true, color: K.muted, charSpacing: 2 });
    const wins = ["Oct–Nov 18", "Feb–Mar 19", "Jun–Jul 19", "Oct–Nov 19", "Feb–Mar 20", "Jun–Jul 20"];
    wins.forEach((lbl, i) => {
      const y = 1.78 + i * 0.27, x0 = 6.75, full = 1.75, end = x0 + full * (i + 1) / 6;
      s.addShape(pres.shapes.RECTANGLE, { x: x0, y, w: end - x0 - 0.12, h: 0.17, fill: { color: "CCFBF1" }, line: { type: "none" }, objectName: "train bar" });
      s.addShape(pres.shapes.RECTANGLE, { x: end - 0.12, y, w: 0.12, h: 0.17, fill: { color: K.orange }, line: { type: "none" }, objectName: "test bar" });
      T(s, lbl, { x: 8.6, y: y - 0.03, w: 0.9, h: 0.22, fontSize: 8.5, color: K.muted });
    });
    T(s, [
      { text: "Six 30-day windows, each trained only on earlier data. ", options: { color: K.ink } },
      { text: "Scored with RMSE (main), MAE and MAPE on measured days.", options: { color: K.muted } },
    ], { x: 6.75, y: 3.48, w: 2.75, h: 0.75, fontSize: 10.5 });
    rule(s, 6.75, 4.3, 2.75);
    T(s, "ARIMA wins this month in Delhi, but June is calm; the late-June spike surprised every model. That is why one window is never enough.",
      { x: 6.75, y: 4.4, w: 2.75, h: 0.75, fontSize: 10, italic: true, color: K.muted });
    s.addNotes("Here is a real forecast: made on 1 June 2020 for the next 30 days in Delhi. ARIMA has the lowest error this month, beating the naive guess. But no model saw the spike at the end of June. One month can mislead, so every model is tested on six windows spread across seasons, as shown on the right.");
  }

  // ------------------------------------------------------------------ 7. Results
  {
    const s = light("06  ·  RESULTS", "A classical model beats the naive forecast in every city", "Results");
    const bestBase = (c) => Math.min(...BASELINES.map((b) => rmse(c, b)));
    s.addChart(pres.charts.BAR, [
      { name: "Best naive forecast", labels: CITIES, values: CITIES.map(bestBase) },
      { name: "Best classical model", labels: CITIES, values: CITIES.map((c) => bestOf(c)["Mean RMSE"]) },
    ], {
      x: 0.45, y: 1.35, w: 4.9, h: 3.75, barDir: "col", barGrouping: "clustered", barGapWidthPct: 55, barOverlapPct: -8,
      chartColors: ["CBD5E1", K.teal], ...axis, valAxisLabelFormatCode: "0",
      showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 8.5, dataLabelColor: K.body, dataLabelFontFace: "+mn-lt", dataLabelFormatCode: "0",
      showLegend: true, legendPos: "b", legendFontSize: 9, legendFontFace: "+mn-lt", legendColor: K.body,
      showTitle: true, title: "Mean RMSE over six 30-day windows (AQI points, lower is better)", titleFontSize: 10, titleColor: K.muted, titleFontFace: "+mn-lt",
      objectName: "RMSE by city chart", altText: "Mean RMSE per city: best naive forecast against best classical model" });
    const head = ["City", "Best model", "RMSE", "MAE", "MAPE", "Gain"].map((t, i) => ({ text: t, options: {
      bold: true, color: K.muted, fontSize: 9, align: i > 1 ? "right" : "left", border: [{ type: "none" }, { type: "none" }, { pt: 1, color: K.faint }, { type: "none" }] } }));
    const body = CITIES.map((c) => {
      const r = bestOf(c), gain = r["RMSE vs baseline %"];
      const cell = (t, o = {}) => ({ text: t, options: { border: [{ type: "none" }, { type: "none" }, { pt: 0.5, color: K.rule }, { type: "none" }], ...o } });
      return [cell(c, { bold: true, color: K.ink }), cell(r["Best classical model"]), cell(r["Mean RMSE"].toFixed(1), { align: "right" }),
        cell(r["Mean MAE"].toFixed(1), { align: "right" }), cell(`${r["Mean MAPE %"].toFixed(0)}%`, { align: "right" }),
        cell(`${Math.abs(gain).toFixed(gain > -1 ? 1 : 0)}%`, { align: "right", bold: true, color: gain <= -10 ? K.teal : K.orange })];
    });
    s.addTable([head, ...body], { x: 5.65, y: 1.4, w: 3.85, colW: [0.92, 0.98, 0.5, 0.47, 0.5, 0.48], rowH: 0.33,
      fontFace: "Calibri", fontSize: 10.5, color: K.body, valign: "middle", margin: [0.02, 0.04, 0.02, 0.04] });
    const wins = {}; D.best.forEach((r) => { wins[r["Best classical model"]] = (wins[r["Best classical model"]] || 0) + 1; });
    T(s, [
      { text: `SARIMA wins ${wins.SARIMA} cities, Holt-Winters ${wins["Holt-Winters"]}, ARIMA ${wins.ARIMA}. `, options: { bold: true, color: K.ink } },
      { text: "The gains are largest where winters are worst (Delhi 30%, Lucknow 28%). Hyderabad's AQI is so steady that the naive guess almost ties." },
    ], { x: 5.65, y: 3.9, w: 3.85, h: 1.2, fontSize: 11 });
    s.addNotes("Averaged over all six windows, the best classical model beats the best naive forecast in every city. SARIMA is the winner in three cities, and the gains are biggest in Delhi and Lucknow, where the yearly cycle is strongest. Hyderabad is the honest near-tie. Gain is the RMSE reduction against the best naive forecast.");
  }

  // ------------------------------------------------------------------ 8. Close
  pres.addSection({ title: "Close" });
  {
    const s = pres.addSlide({ masterName: "DARK", sectionTitle: "Close" });
    T(s, "07  ·  WHAT WE LEARNED", { x: 0.6, y: 0.5, w: 8, h: 0.25, fontSize: 10, bold: true, color: K.amber, charSpacing: 3 });
    s.addText("The season is the signal; the spikes are the noise", { isTextBox: true, x: 0.6, y: 0.85, w: 8.8, h: 0.6, margin: 0,
      fontFace: "Cambria", fontSize: 26, bold: true, color: K.white });
    const pts = [
      ["01", "Model the year, don't difference it", "Log AQI has no unit root but a strong yearly cycle. Fourier terms let SARIMA carry it without differencing."],
      ["02", "Classical models earn their place", "The best one beats the naive forecast in all six cities, by up to 30% in Delhi."],
      ["03", "Spikes stay out of reach", "Diwali and crop-burning spikes do not land on fixed dates, so history cannot time them. Delhi’s typical error (RMSE 69) is still under one AQI band."],
    ];
    pts.forEach(([n, h, d], i) => {
      const x = 0.6 + i * 3.0;
      T(s, n, { x, y: 1.75, w: 1, h: 0.55, fontFace: "Cambria", fontSize: 28, bold: true, color: i === 2 ? K.amber : K.tealLight });
      T(s, h, { x, y: 2.35, w: 2.7, h: 0.35, fontSize: 13.5, bold: true, color: K.white });
      T(s, d, { x, y: 2.75, w: 2.7, h: 1.0, fontSize: 11, color: "CBD5E1" });
    });
    rule(s, 0.6, 4.15, 8.8, "334155");
    T(s, [{ text: "Next, Phase 3:  ", options: { bold: true, color: K.amber } },
      { text: "LSTM, XGBoost and Prophet on the same six windows, compared head to head with these results.", options: { color: "E2E8F0" } }],
      { x: 0.6, y: 4.32, w: 8.8, h: 0.3, fontSize: 12 });
    T(s, [{ text: "Live demo:  ", options: { bold: true, color: K.amber } },
      { text: "python -m src.run_forecasting  ·  python -m src.phase2  ·  notebooks/02_classical_models.ipynb", options: { fontFace: "Consolas", color: "E2E8F0" } }],
      { x: 0.6, y: 4.72, w: 8.8, h: 0.3, fontSize: 10.5 });
    s.addNotes("Three takeaways. Model the yearly cycle rather than differencing it away. Classical models beat the naive forecast everywhere. And the remaining error comes from pollution episodes the history cannot predict. Next phase we bring in LSTM, XGBoost and Prophet on the same windows. I'll now show the code running.");
  }

  await pres.writeFile({ fileName: OUT });
  await patchCharts(OUT);
  if (process.env.PPTX_SKILL) await require(process.env.PPTX_SKILL + "/scripts/apply_theme.js").applyTheme(OUT, THEME);
  console.log("Wrote", OUT);
}

// pptxgenjs can't dash individual chart series and writes blank points as empty <c:v>, which
// PowerPoint refuses to open. Forecast series ("... (RMSE n)") get dashed lines, the naive one
// dotted; blank points are dropped and shown as gaps.
async function patchCharts(file) {
  const JSZip = require("jszip");
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  for (const name of Object.keys(zip.files).filter((n) => /^ppt\/charts\/chart\d+\.xml$/.test(n))) {
    let xml = await zip.file(name).async("string");
    xml = xml.replace(/<c:pt idx="\d+"><c:v><\/c:v><\/c:pt>/g, "");
    xml = xml.replace(/<c:ser>[\s\S]*?<\/c:ser>/g, (ser) => {
      const title = (ser.match(/<c:tx>[\s\S]*?<c:v>([^<]*)<\/c:v>/) || [])[1] || "";
      const dash = /^Naive \(RMSE/.test(title) ? "sysDot" : /\(RMSE/.test(title) ? "dash" : "solid";
      return ser.replace(/<a:prstDash val="[^"]*"\/>/g, `<a:prstDash val="${dash}"/>`);
    });
    xml = xml.replace(/<c:dispBlanksAs val="span"\/>/, '<c:dispBlanksAs val="gap"/>');
    zip.file(name, xml);
  }
  fs.writeFileSync(file, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
}

main().catch((e) => { console.error(e); process.exit(1); });
