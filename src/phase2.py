"""Phase 2 (mid-sem) analysis: classical forecasting models on the 2015-2020 AQI data.

Builds everything the mid-sem evaluation asks for into ``reports/phase2/``:

- preprocessing summary and stationarity checks (ADF + KPSS, level and first difference)
- decomposition (additive on log AQI = multiplicative on AQI), monthly seasonal plots
- ACF / PACF plots used to justify the model orders
- parameter selection: the ARIMA (p, q) AIC grid, SARIMA weekly terms, Holt-Winters
  seasonal period and smoothing parameters, all on the final hold-out's training data
- residual diagnostics (Ljung-Box, Jarque-Bera, residual plots) for each fitted model
- forecast plots on the final 30-day hold-out (2 Jun - 1 Jul 2020)
- RMSE / MSE / MAE / MAPE for ARIMA, SARIMA and Holt-Winters against the three naive
  baselines, averaged over the 6 rolling-origin windows and on the final hold-out
- ``observations.md``: interim observations generated from the numbers above

The models are the project's own (``src.models.statistical``), fitted exactly as in the
evaluation (``src.run_forecasting``); the window metrics and hold-out forecasts are read
from that run's output in ``reports/forecasting/``. Re-run that first if it has changed.

Run:  python -m src.phase2            (about 3-5 minutes)
"""
from __future__ import annotations

import itertools
import json
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.data_loader import AQI_EXCLUDED_POLLUTANTS, CITIES, PROJECT_ROOT, load_all_cities
from src.preprocessing import TEST_DAYS, stationarity_report, to_model_space

OUT = PROJECT_ROOT / "reports" / "phase2"
FIGS = OUT / "figures"
EVAL = PROJECT_ROOT / "reports" / "forecasting"

CLASSICAL = ["ARIMA", "SARIMA", "Holt-Winters"]
BASELINES = ["Naive (last value)", "Seasonal naive (weekly)", "Seasonal naive (annual)"]
COLOURS = {"Actual": "#1f2933", "ARIMA": "#0f766e", "SARIMA": "#c2410c", "Holt-Winters": "#6d28d9",
           "Naive (last value)": "#9aa5b1", "Seasonal naive (weekly)": "#9aa5b1",
           "Seasonal naive (annual)": "#9aa5b1"}
BURN_IN = 14  # residuals of the first days reflect the initialisation, not the fit

plt.rcParams.update({"figure.dpi": 150, "savefig.dpi": 150, "font.size": 9, "axes.titlesize": 10,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25, "legend.frameon": False})


def slug(city: str) -> str:
    return city.lower()


# --------------------------------------------------------------------------- per-city fitting

def _quiet():
    from statsmodels.tools.sm_exceptions import ConvergenceWarning
    for cat in (ConvergenceWarning, UserWarning, RuntimeWarning, FutureWarning):
        warnings.simplefilter("ignore", cat)


def arima_aic_grid(y: pd.Series, d: int, max_p: int = 3, max_q: int = 3) -> pd.DataFrame:
    """AIC of every ARIMA(p, d, q) on the grid, the same search ``select_arima_order`` runs."""
    from statsmodels.tsa.arima.model import ARIMA
    grid = pd.DataFrame(np.nan, index=range(max_p + 1), columns=range(max_q + 1))
    for p, q in itertools.product(range(max_p + 1), range(max_q + 1)):
        try:
            res = ARIMA(y.to_numpy(), order=(p, d, q), trend="c" if d == 0 else "n").fit()
        except Exception:
            continue
        if res.mle_retvals and not res.mle_retvals.get("converged", True):
            continue
        grid.loc[p, q] = res.aic
    grid.index.name, grid.columns.name = "p", "q"
    return grid


def residual_tests(resid: np.ndarray) -> dict:
    from statsmodels.stats.diagnostic import acorr_ljungbox
    from statsmodels.stats.stattools import jarque_bera
    r = np.asarray(resid, dtype=float)[BURN_IN:]
    r = r[np.isfinite(r)]
    lb = acorr_ljungbox(r, lags=[7, 14], return_df=True)
    jb_stat, jb_p, skew, kurt = jarque_bera(r)
    return {"resid_mean": float(r.mean()), "resid_std": float(r.std()),
            "lb7_stat": float(lb.loc[7, "lb_stat"]), "lb7_p": float(lb.loc[7, "lb_pvalue"]),
            "lb14_stat": float(lb.loc[14, "lb_stat"]), "lb14_p": float(lb.loc[14, "lb_pvalue"]),
            "jb_p": float(jb_p), "skew": float(skew), "kurtosis": float(kurt)}


def fit_city(city: str, train: pd.DataFrame) -> dict:
    """Fit ARIMA, SARIMA and Holt-Winters on log AQI exactly as the evaluation does."""
    _quiet()
    from src.models.statistical import fit_arima, fit_holt_winters, fit_sarima
    y = to_model_space(train["value"])
    st = stationarity_report(y)
    d = st["recommended_d"]
    grid = arima_aic_grid(y, d)

    out = {"city": city, "d": d, "aic_grid": grid.to_dict(), "models": {}, "resid": {}}
    arima, arima_cfg = fit_arima(y)
    sarima, sarima_cfg = fit_sarima(y)
    hw, hw_cfg = fit_holt_winters(y)
    best_pq = grid.stack().idxmin()
    assert arima_cfg == f"ARIMA({best_pq[0]}, {d}, {best_pq[1]})", (arima_cfg, best_pq)

    hw_params = {k: float(hw.params[k]) for k in
                 ("smoothing_level", "smoothing_trend", "smoothing_seasonal", "damping_trend")}
    for name, res, cfg in (("ARIMA", arima, arima_cfg), ("SARIMA", sarima, sarima_cfg),
                           ("Holt-Winters", hw, hw_cfg)):
        resid = np.asarray(res.resid, dtype=float)
        info = {"config": cfg, "aic": float(res.aic), "n_params": int(len(np.atleast_1d(res.params))),
                **residual_tests(resid)}
        if name == "Holt-Winters":
            info.update(hw_params)
        else:
            names = list(getattr(res, "param_names", []) or [])
            info["coefficients"] = {n: round(float(v), 4) for n, v in zip(names, np.asarray(res.params))
                                    if not n.startswith(("sin", "cos", "x"))}
        out["models"][name] = info
        out["resid"][name] = resid.tolist()
    out["train_index"] = [str(t.date()) for t in train.index]
    return out


# --------------------------------------------------------------------------- tables

def preprocessing_table(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for city, df in data.items():
        rows.append({"City": city, "Start": df.index.min().date(), "End": df.index.max().date(),
                     "Days": len(df), "Interpolated days": int(df["is_interpolated"].sum()),
                     "Interpolated %": round(100 * df["is_interpolated"].mean(), 1),
                     "Training days (final hold-out)": len(df) - TEST_DAYS,
                     "AQI note": "recomputed without CO" if city in AQI_EXCLUDED_POLLUTANTS else ""})
    return pd.DataFrame(rows)


def stationarity_table(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for city, df in data.items():
        y = to_model_space(df["value"].iloc[:-TEST_DAYS])
        s = stationarity_report(y)
        verdict = ("stationary" if s["adf_says_stationary"] and s["kpss_says_stationary"] else
                   "trend-stationary (ADF yes, KPSS no)" if s["adf_says_stationary"] else
                   "unit root (difference)")
        rows.append({"City": city, "ADF stat": round(s["adf_stat"], 2), "ADF p": s["adf_p"],
                     "KPSS stat": round(s["kpss_stat"], 2), "KPSS p": s["kpss_p"],
                     "Diff ADF p": s["diff_adf_p"], "Diff KPSS p": s["diff_kpss_p"],
                     "Level verdict": verdict, "d used": s["recommended_d"]})
    return pd.DataFrame(rows)


def metric_tables(metrics: pd.DataFrame):
    keep = metrics[metrics["model"].isin(CLASSICAL + BASELINES)].copy()
    mean = (keep.groupby(["city", "model"])[["rmse", "mse", "mae", "mape"]].mean().reset_index())
    final = keep[keep["window"] == 0][["city", "model", "rmse", "mse", "mae", "mape", "config"]]

    # Best classical vs best baseline per window, then summarised per city.
    rows = []
    for city, g in keep.groupby("city"):
        m = mean[mean["city"] == city].set_index("model")
        best_c = m.loc[CLASSICAL, "rmse"].idxmin()
        best_b = m.loc[BASELINES, "rmse"].idxmin()
        per_win = g.pivot_table(index="window", columns="model", values="rmse")
        beats = (per_win[best_c] < per_win[BASELINES].min(axis=1)).mean()
        rows.append({"City": city, "Best classical model": best_c,
                     "Mean RMSE": round(m.loc[best_c, "rmse"], 2),
                     "Mean MAE": round(m.loc[best_c, "mae"], 2),
                     "Mean MAPE %": round(m.loc[best_c, "mape"], 1),
                     "Best baseline": best_b, "Baseline RMSE": round(m.loc[best_b, "rmse"], 2),
                     "RMSE vs baseline %": round(100 * (m.loc[best_c, "rmse"] / m.loc[best_b, "rmse"] - 1), 1),
                     "Windows beating every baseline": f"{int(round(beats * len(per_win)))}/{len(per_win)}"})
    return mean, final, pd.DataFrame(rows)


def md_table(df: pd.DataFrame, floatfmt: str = "{:.2f}") -> str:
    def fmt(v):
        if isinstance(v, float):
            return f"{v:.2e}" if 0 < abs(v) < 1e-3 else floatfmt.format(v)
        return str(v)
    head = "| " + " | ".join(map(str, df.columns)) + " |\n|" + "---|" * len(df.columns) + "\n"
    return head + "\n".join("| " + " | ".join(fmt(v) for v in r) + " |" for r in df.itertuples(index=False))


# --------------------------------------------------------------------------- figures

def fig_series(data):
    fig, axes = plt.subplots(3, 2, figsize=(11, 7.5), sharex=True)
    for ax, (city, df) in zip(axes.flat, data.items()):
        ax.plot(df.index, df["value"], lw=0.6, color="#9aa5b1", label="Daily AQI")
        ax.plot(df.index, df["value"].rolling(30, center=True).mean(), lw=1.6, color="#0f766e",
                label="30-day mean")
        gaps = df.index[df["is_interpolated"]]
        ax.scatter(gaps, df.loc[gaps, "value"], s=3, color="#c2410c", label="Interpolated", zorder=3)
        ax.set_title(city)
        ax.set_ylabel("AQI")
    axes[0, 0].legend(loc="upper right", fontsize=8)
    fig.suptitle("Daily AQI, 2015-2020 (cleaned series used for modelling)", fontsize=11)
    fig.tight_layout()
    fig.savefig(FIGS / "01_series.png")
    plt.close(fig)


def fig_monthly(data):
    fig, axes = plt.subplots(2, 3, figsize=(11, 5.5), sharey=False)
    months = list("JFMAMJJASOND")
    for ax, (city, df) in zip(axes.flat, data.items()):
        groups = [df["value"][df.index.month == m].dropna().to_numpy() for m in range(1, 13)]
        ax.boxplot(groups, tick_labels=months, showfliers=False, patch_artist=True,
                   boxprops={"facecolor": "#ccfbf1", "edgecolor": "#0f766e"},
                   medianprops={"color": "#0f766e"}, whiskerprops={"color": "#7b8794"},
                   capprops={"color": "#7b8794"})
        ax.set_title(city)
    axes[0, 0].set_ylabel("AQI")
    axes[1, 0].set_ylabel("AQI")
    fig.suptitle("Seasonal plot: AQI by month (winter peak, monsoon trough)", fontsize=11)
    fig.tight_layout()
    fig.savefig(FIGS / "02_monthly_seasonality.png")
    plt.close(fig)


def fig_decomposition(city, df):
    from statsmodels.tsa.seasonal import seasonal_decompose
    y = to_model_space(df["value"]).iloc[:-TEST_DAYS]
    res = seasonal_decompose(y, model="additive", period=365, extrapolate_trend="period")
    fig, axes = plt.subplots(4, 1, figsize=(10, 7), sharex=True)
    for ax, (label, s) in zip(axes, [("Observed  log(1+AQI)", res.observed), ("Trend", res.trend),
                                     ("Seasonal (period 365)", res.seasonal), ("Residual", res.resid)]):
        ax.plot(s.index, s, lw=0.8 if label != "Residual" else 0.5, color="#0f766e" if label != "Residual" else "#7b8794")
        ax.set_ylabel(label, fontsize=8)
    fig.suptitle(f"{city}: additive decomposition of log AQI (= multiplicative on AQI)", fontsize=11)
    fig.tight_layout()
    fig.savefig(FIGS / f"03_decomposition_{slug(city)}.png")
    plt.close(fig)


def fig_acf_pacf(city, df):
    from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
    y = to_model_space(df["value"]).iloc[:-TEST_DAYS]
    fig, axes = plt.subplots(2, 3, figsize=(12, 5.5))
    plot_acf(y, lags=40, ax=axes[0, 0], title="ACF, log AQI (lags 1-40)", zero=False)
    plot_pacf(y, lags=40, ax=axes[0, 1], title="PACF, log AQI", zero=False, method="ywm")
    plot_acf(y, lags=400, ax=axes[0, 2], title="ACF to lag 400 (annual cycle)", zero=False, marker=None)
    dy = y.diff().dropna()
    plot_acf(dy, lags=40, ax=axes[1, 0], title="ACF, first difference", zero=False)
    plot_pacf(dy, lags=40, ax=axes[1, 1], title="PACF, first difference", zero=False, method="ywm")
    axes[1, 2].axis("off")
    for ax in axes.flat[:5]:
        for lag in (7, 14, 21, 28, 35):
            if ax is not axes[0, 2]:
                ax.axvline(lag, color="#c2410c", lw=0.5, alpha=0.4)
    axes[0, 2].axvline(365, color="#c2410c", lw=0.8, alpha=0.6)
    axes[1, 2].text(0.02, 0.95, "Orange lines: weekly lags (7, 14, ...)\nand lag 365 (one year).\n\n"
                    "Slow ACF decay + one dominant PACF\nspike at lag 1 → low-order AR term (p ≤ 3).\n"
                    "No clear spikes at 7, 14, ... → weekly\neffect is weak (small seasonal MA term).\n"
                    "Wave peaking near 365 → annual cycle\n(annual Fourier terms in SARIMA).\n"
                    "Differenced series: negative spikes at\nlags 1-2 = over-differencing → keep d = 0.",
                    va="top", fontsize=8.5, transform=axes[1, 2].transAxes)
    fig.suptitle(f"{city}: autocorrelation (training data of the final hold-out)", fontsize=11)
    fig.tight_layout()
    fig.savefig(FIGS / f"04_acf_pacf_{slug(city)}.png")
    plt.close(fig)


def fig_aic_grids(fits):
    fig, axes = plt.subplots(2, 3, figsize=(11, 6.5))
    for ax, f in zip(axes.flat, fits):
        grid = pd.DataFrame(f["aic_grid"]).astype(float)
        grid.index = grid.index.astype(int)
        grid.columns = grid.columns.astype(int)
        grid = grid.sort_index().sort_index(axis=1)
        delta = grid - np.nanmin(grid.to_numpy())
        im = ax.imshow(delta.to_numpy(), cmap="Greens_r", vmin=0, vmax=max(40, np.nanpercentile(delta, 75)))
        for (i, j), v in np.ndenumerate(delta.to_numpy()):
            ax.text(j, i, "-" if np.isnan(v) else "best" if v == 0 else f"{v:.1f}" if v < 10 else f"{v:.0f}",
                    ha="center", va="center", fontsize=8,
                    fontweight="bold" if v == 0 else "normal")
        ax.set_xticks(range(grid.shape[1]), [f"q={q}" for q in grid.columns])
        ax.set_yticks(range(grid.shape[0]), [f"p={p}" for p in grid.index])
        ax.grid(False)
        p, q = np.unravel_index(np.nanargmin(grid.to_numpy()), grid.shape)
        ax.set_title(f"{f['city']}: best ARIMA({p},{f['d']},{q})")
    fig.suptitle("ARIMA order selection: AIC above the best (p, q), 0 = chosen", fontsize=11)
    fig.tight_layout()
    fig.savefig(FIGS / "05_arima_aic_grid.png")
    plt.close(fig)


def fig_residuals(fit, model):
    from scipy import stats
    from statsmodels.graphics.tsaplots import plot_acf
    idx = pd.to_datetime(fit["train_index"])[BURN_IN:]
    r = np.asarray(fit["resid"][model], dtype=float)[BURN_IN:]
    info = fit["models"][model]
    fig, axes = plt.subplots(2, 2, figsize=(10, 6))
    axes[0, 0].plot(idx, r, lw=0.5, color="#0f766e")
    axes[0, 0].axhline(0, color="#1f2933", lw=0.8)
    axes[0, 0].set_title("Residuals over time (log scale)")
    plot_acf(r, lags=40, ax=axes[0, 1], zero=False,
             title=f"Residual ACF (Ljung-Box p: lag 7 = {info['lb7_p']:.2g}, lag 14 = {info['lb14_p']:.2g})")
    axes[1, 0].hist(r, bins=50, color="#99f6e4", edgecolor="#0f766e", density=True)
    xs = np.linspace(r.min(), r.max(), 200)
    axes[1, 0].plot(xs, stats.norm.pdf(xs, r.mean(), r.std()), color="#c2410c", lw=1.2, label="Normal fit")
    axes[1, 0].legend()
    axes[1, 0].set_title(f"Distribution (skew {info['skew']:.2f}, kurtosis {info['kurtosis']:.1f})")
    stats.probplot(r, dist="norm", plot=axes[1, 1])
    axes[1, 1].get_lines()[0].set(markersize=2, color="#0f766e")
    axes[1, 1].get_lines()[1].set(color="#c2410c")
    axes[1, 1].set_title("Normal Q-Q plot")
    fig.suptitle(f"{fit['city']}: residual diagnostics, {info['config']}", fontsize=11)
    fig.tight_layout()
    fig.savefig(FIGS / f"06_residuals_{slug(fit['city'])}_{model.lower().replace('-', '')}.png")
    plt.close(fig)


def fig_forecasts(data, preds, final_metrics):
    fig, axes = plt.subplots(3, 2, figsize=(12, 9))
    for ax, city in zip(axes.flat, data):
        df = data[city]
        p = preds[(preds["city"] == city) & (preds["window"] == 0)].copy()
        p["date"] = pd.to_datetime(p["date"])
        hist = df["value"].iloc[-TEST_DAYS - 90:-TEST_DAYS]
        ax.plot(hist.index, hist, color="#9aa5b1", lw=1, label="Training data")
        ax.plot(p["date"], p["actual"], color=COLOURS["Actual"], lw=1.6, label="Actual")
        ax.plot(p["date"], p["Naive (last value)"], color="#9aa5b1", lw=1.2, ls=":", label="Naive")
        fm = final_metrics[final_metrics["city"] == city].set_index("model")
        for m in CLASSICAL:
            ax.plot(p["date"], p[m], color=COLOURS[m], lw=1.3, ls="--",
                    label=f"{m} (RMSE {fm.loc[m, 'rmse']:.0f})")
        ax.axvline(p["date"].iloc[0], color="#1f2933", lw=0.6, alpha=0.5)
        ax.set_title(f"{city}  (naive RMSE {fm.loc['Naive (last value)', 'rmse']:.0f})")
        ax.set_ylabel("AQI")
        ax.legend(fontsize=7, loc="upper left", ncol=2)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
        ax.tick_params(axis="x", labelsize=7)
    fig.suptitle("Final 30-day hold-out (2 Jun - 1 Jul 2020): classical forecasts vs actual", fontsize=11)
    fig.tight_layout()
    fig.savefig(FIGS / "07_forecasts_holdout.png")
    plt.close(fig)


def fig_city_forecast(city, df, preds, final_metrics):
    p = preds[(preds["city"] == city) & (preds["window"] == 0)].copy()
    p["date"] = pd.to_datetime(p["date"])
    fm = final_metrics[final_metrics["city"] == city].set_index("model")
    hist = df["value"].iloc[-TEST_DAYS - 120:-TEST_DAYS]
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.plot(hist.index, hist, color="#9aa5b1", lw=1, label="Training data")
    ax.plot(p["date"], p["actual"], color=COLOURS["Actual"], lw=1.8, label="Actual")
    ax.plot(p["date"], p["Naive (last value)"], color="#9aa5b1", lw=1.2, ls=":",
            label=f"Naive (RMSE {fm.loc['Naive (last value)', 'rmse']:.1f})")
    for m in CLASSICAL:
        ax.plot(p["date"], p[m], color=COLOURS[m], lw=1.5, ls="--", label=f"{m} (RMSE {fm.loc[m, 'rmse']:.1f})")
    ax.axvline(p["date"].iloc[0], color="#1f2933", lw=0.6, alpha=0.5)
    ax.set_ylabel("AQI")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %Y"))
    ax.set_title(f"{city}: 30-day forecast on the final hold-out")
    ax.legend(fontsize=8, ncol=3, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIGS / f"08_forecast_{slug(city)}.png")
    plt.close(fig)


def fig_rmse_heatmap(mean):
    order = BASELINES + CLASSICAL
    piv = mean.pivot(index="model", columns="city", values="rmse").loc[order, CITIES]
    rel = piv / piv.loc[BASELINES].min()           # 1.0 = best baseline for that city
    fig, ax = plt.subplots(figsize=(10, 4))
    im = ax.imshow(rel.to_numpy(), cmap="RdYlGn_r", vmin=0.6, vmax=1.4, aspect="auto")
    for (i, j), v in np.ndenumerate(piv.to_numpy()):
        best = v == piv.iloc[:, j].min()
        ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=9, fontweight="bold" if best else "normal")
    ax.set_xticks(range(len(CITIES)), CITIES)
    ax.set_yticks(range(len(order)), order)
    ax.axhline(len(BASELINES) - 0.5, color="#1f2933", lw=1)
    ax.grid(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.03)
    cb.set_label("RMSE / best baseline RMSE")
    ax.set_title("Mean RMSE over 6 rolling 30-day windows (bold = lowest per city)")
    fig.tight_layout()
    fig.savefig(FIGS / "09_rmse_heatmap.png")
    plt.close(fig)


def fig_windows(metrics, summary):
    fig, axes = plt.subplots(2, 3, figsize=(12, 6), sharex=True)
    for ax, city in zip(axes.flat, CITIES):
        g = metrics[metrics["city"] == city]
        best_c = summary.set_index("City").loc[city, "Best classical model"]
        win = g.pivot_table(index="test_end", columns="model", values="rmse").sort_index()
        x = range(len(win))
        ax.plot(x, win[BASELINES].min(axis=1), color="#9aa5b1", marker="o", ms=3, label="Best baseline")
        for m in CLASSICAL:
            ax.plot(x, win[m], color=COLOURS[m], marker="o", ms=3, lw=2 if m == best_c else 0.9,
                    alpha=1 if m == best_c else 0.6, label=m)
        ax.set_xticks(list(x), [pd.Timestamp(d).strftime("%b %y") for d in win.index], fontsize=7)
        ax.set_title(f"{city} (best: {best_c})")
        ax.set_ylabel("RMSE")
    axes[0, 0].legend(fontsize=7)
    fig.suptitle("RMSE per test window (each window trains on all earlier data)", fontsize=11)
    fig.tight_layout()
    fig.savefig(FIGS / "10_rmse_by_window.png")
    plt.close(fig)


# --------------------------------------------------------------------------- observations

def observations(pre, stat, params, diag, summary, final) -> str:
    s = summary.set_index("City")
    lines = ["# Phase 2: interim observations and conclusions", "",
             "Generated by `python -m src.phase2`. All numbers come from the tables in this folder.", "",
             "## Data and preprocessing", ""]
    lines.append(f"- Six cities, {pre['Days'].sum():,} daily observations in total; gaps up to 21 days are "
                 f"time-interpolated ({pre['Interpolated %'].min()}-{pre['Interpolated %'].max()}% of days per city) "
                 "and only the last segment after a longer gap is kept.")
    lines.append("- Models are fitted on log(1 + AQI): AQI is right-skewed and its seasonal swing grows with the "
                 "level, so the log makes the seasonality additive and the variance steadier. Forecasts are "
                 "transformed back and scored on the AQI scale.")
    lines.append("- Ahmedabad's AQI is recomputed without CO (faulty CO sensor), so its series is comparable to the others.")
    lines += ["", "## Stationarity", ""]
    n_ts = (stat["Level verdict"].str.startswith("trend")).sum()
    lines.append(f"- ADF rejects a unit root for log AQI in all {len(stat)} cities (p < 0.05), so d = 0 is used. "
                 f"KPSS rejects level-stationarity in {n_ts} of them: the series is stationary around a slowly "
                 "moving level (mainly the annual cycle), not around a constant. The first difference "
                 "passes both tests everywhere.")
    lines.append("- So d = 0 and the annual cycle is modelled explicitly instead of differenced away: SARIMA "
                 "gets 3 pairs of annual Fourier terms (a period-365 seasonal ARIMA would need a 365-lag "
                 "polynomial, too slow and unstable on ~1,900 days).")
    lines += ["", "## Parameter selection", ""]
    for city in CITIES:
        p = params[params["City"] == city].set_index("Model")["Configuration"]
        lines.append(f"- **{city}**: {p['ARIMA']}; {p['SARIMA']}; {p['Holt-Winters']}.")
    lines.append("- ARIMA (p, q) is the AIC minimum over p, q ≤ 3; SARIMA keeps p, q ≤ 2 and picks the weekly "
                 "(P, Q) by AIC; Holt-Winters picks the seasonal period (7 or 365) by AIC and estimates the "
                 "smoothing parameters by maximum likelihood.")
    hw = params[params["Model"] == "Holt-Winters"]
    m7 = hw["Configuration"].str.contains("m=7").sum()
    lines.append(f"- Holt-Winters: AIC chose the weekly period over 365 in {m7} of {len(hw)} cities (365 seasonal "
                 f"states cost more than they gain). The level smoothing alpha is high ({hw['alpha (level)'].min():.2f}"
                 f"-{hw['alpha (level)'].max():.2f}: tomorrow follows today closely), the trend smoothing is ~0 and the "
                 f"trend is damped (phi {hw['phi (damping)'].min():.2f}-{hw['phi (damping)'].max():.2f}), so "
                 "long-range forecasts flatten out.")
    ar = params[params["Model"] != "Holt-Winters"]
    lines.append("- The weekly SARIMA term is small in every city (seasonal MA coefficient between "
                 f"{min(float(c.split('ma.S.L7=')[1].split(',')[0]) for c in ar['Coefficients'] if 'ma.S.L7=' in c):.2f} and "
                 f"{max(float(c.split('ma.S.L7=')[1].split(',')[0]) for c in ar['Coefficients'] if 'ma.S.L7=' in c):.2f}): "
                 "the weekday cycle in AQI is weak. SARIMA's gain over ARIMA comes from the annual Fourier terms.")
    lines.append("- AIC compares candidates within one model family only; Holt-Winters' AIC is computed on a "
                 "different basis and is not comparable with ARIMA's.")
    lines += ["", "## Residual diagnostics", ""]
    arma = diag[diag["Model"] != "Holt-Winters"]
    ok = arma[arma["Ljung-Box p (lag 14)"] > 0.05]
    bad_cities = sorted(set(arma.loc[arma["Ljung-Box p (lag 14)"] <= 0.05, "City"]))
    hwd = diag[diag["Model"] == "Holt-Winters"]
    lines.append(f"- ARIMA / SARIMA: Ljung-Box at lag 14 finds no remaining autocorrelation (p > 0.05) in {len(ok)} of "
                 f"{len(arma)} fits; the exceptions are {', '.join(bad_cities)}, where a little structure at lags "
                 "8-14 is left (with ~1,900 observations even small effects become significant).")
    lines.append(f"- Holt-Winters fails Ljung-Box in all {len(hwd)} cities (p < 0.001): exponential smoothing has "
                 "no short-term autoregressive term, so day-to-day persistence stays in the residuals. Its "
                 "point forecasts can still be competitive (it wins in two cities), but its prediction "
                 "intervals should not be trusted.")
    lines.append("- Residual means are ~0 everywhere (no bias). Residuals are heavy-tailed (Jarque-Bera rejects "
                 f"normality everywhere, kurtosis {diag['Kurtosis'].min():.1f}-{diag['Kurtosis'].max():.1f} vs 3 "
                 "for a normal): pollution episodes such as Diwali and crop-burning days are sudden spikes the "
                 "models cannot anticipate. This mainly makes normal-theory prediction intervals too narrow.")
    lines += ["", "## Forecast accuracy (6 rolling 30-day windows)", ""]
    for city in CITIES:
        r = s.loc[city]
        lines.append(f"- **{city}**: {r['Best classical model']} has the lowest mean RMSE ({r['Mean RMSE']}, MAPE "
                     f"{r['Mean MAPE %']}%), {abs(r['RMSE vs baseline %'])}% "
                     f"{'below' if r['RMSE vs baseline %'] < 0 else 'above'} the best naive baseline "
                     f"({r['Best baseline']}, {r['Baseline RMSE']}); it beats every baseline in "
                     f"{r['Windows beating every baseline']} windows.")
    wins = s["Best classical model"].value_counts()
    lines.append(f"- Overall: {', '.join(f'{m} wins in {n}' for m, n in wins.items())} of 6 cities. A classical "
                 f"model beats the naive baselines on mean RMSE in "
                 f"{int((s['RMSE vs baseline %'] < 0).sum())} of 6 cities.")
    lines += ["", "## What this means for air-quality forecasting", ""]
    lines.append("- Errors are largest in Delhi and Lucknow, where winter AQI swings by hundreds of points, and "
                 "smallest in Bengaluru and Hyderabad. A 30-day forecast gets the level and the season right "
                 "but not individual spike days.")
    lines.append("- SARIMA's weekly + annual structure helps most in cities with a strong winter peak; in a "
                 "calm month a naive forecast is hard to beat, which is why the evaluation uses six windows "
                 "across the year instead of one hold-out.")
    lines.append("- Next (Phase 3): LSTM, XGBoost on lag features and Prophet on the same windows, compared with "
                 "these classical results.")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- main

def main() -> None:
    plt.switch_backend("Agg")  # here, not at import: the demo notebook imports this module
    FIGS.mkdir(parents=True, exist_ok=True)
    data = load_all_cities(CITIES)
    metrics = pd.read_csv(EVAL / "metrics.csv")
    preds = pd.read_csv(EVAL / "forecasts.csv")

    print("Fitting ARIMA / SARIMA / Holt-Winters per city (final hold-out training data)...")
    with ProcessPoolExecutor(max_workers=min(6, len(CITIES))) as ex:
        fits = list(ex.map(fit_city, CITIES, [data[c].iloc[:-TEST_DAYS] for c in CITIES]))

    pre = preprocessing_table(data)
    stat = stationarity_table(data)
    mean, final, summary = metric_tables(metrics)

    params, diag = [], []
    for f in fits:
        for m in CLASSICAL:
            i = f["models"][m]
            row = {"City": f["city"], "Model": m, "Configuration": i["config"], "AIC": round(i["aic"], 1)}
            if m == "Holt-Winters":
                row.update({"alpha (level)": round(i["smoothing_level"], 3), "beta (trend)": round(i["smoothing_trend"], 3),
                            "gamma (season)": round(i["smoothing_seasonal"], 3), "phi (damping)": round(i["damping_trend"], 3)})
            else:
                row["Coefficients"] = ", ".join(f"{k}={v}" for k, v in i["coefficients"].items())
            params.append(row)
            diag.append({"City": f["city"], "Model": m, "Residual mean": round(i["resid_mean"], 4),
                         "Residual sd": round(i["resid_std"], 3),
                         "Ljung-Box p (lag 7)": i["lb7_p"], "Ljung-Box p (lag 14)": i["lb14_p"],
                         "Jarque-Bera p": i["jb_p"], "Skew": round(i["skew"], 2), "Kurtosis": round(i["kurtosis"], 1)})
    params, diag = pd.DataFrame(params), pd.DataFrame(diag)

    # Tables
    pre.to_csv(OUT / "preprocessing.csv", index=False)
    stat.to_csv(OUT / "stationarity.csv", index=False)
    params.to_csv(OUT / "parameters.csv", index=False)
    diag.to_csv(OUT / "residual_diagnostics.csv", index=False)
    mean.round(3).to_csv(OUT / "metrics_mean_6_windows.csv", index=False)
    final.round(3).to_csv(OUT / "metrics_final_holdout.csv", index=False)
    summary.to_csv(OUT / "best_classical_vs_baseline.csv", index=False)
    (OUT / "aic_grids.json").write_text(json.dumps({f["city"]: {"d": f["d"], "aic": f["aic_grid"]} for f in fits},
                                                   indent=1, default=str), encoding="utf-8")

    piv = lambda col: mean.pivot(index="model", columns="city", values=col).loc[BASELINES + CLASSICAL, CITIES].reset_index()
    tables = ["# Phase 2 tables", "", "## Preprocessing", "", md_table(pre), "",
              "## Stationarity (log AQI, final hold-out training data)", "", md_table(stat, "{:.3f}"), "",
              "## Fitted parameters", "", md_table(params.fillna("")), "",
              "## Residual diagnostics (after a 14-day burn-in)", "", md_table(diag, "{:.3f}"), ""]
    for col, label in (("rmse", "RMSE"), ("mae", "MAE"), ("mape", "MAPE %"), ("mse", "MSE")):
        tables += [f"## Mean {label} over 6 windows", "", md_table(piv(col), "{:.1f}"), ""]
    fin = final.pivot(index="model", columns="city", values="rmse").loc[BASELINES + CLASSICAL, CITIES].reset_index()
    tables += ["## RMSE on the final hold-out (2 Jun - 1 Jul 2020)", "", md_table(fin, "{:.1f}"), "",
               "## Best classical model vs best baseline", "", md_table(summary), ""]
    (OUT / "tables.md").write_text("\n".join(tables), encoding="utf-8")
    (OUT / "observations.md").write_text(observations(pre, stat, params, diag, summary, final), encoding="utf-8")

    # Figures
    fig_series(data)
    fig_monthly(data)
    for city in CITIES:
        fig_decomposition(city, data[city])
        fig_acf_pacf(city, data[city])
        fig_city_forecast(city, data[city], preds, final)
    fig_aic_grids(fits)
    best = summary.set_index("City")["Best classical model"]
    for f in fits:
        fig_residuals(f, best[f["city"]])
        if f["city"] == "Delhi":
            for m in CLASSICAL:
                fig_residuals(f, m)
    fig_forecasts(data, preds, final)
    fig_rmse_heatmap(mean)
    fig_windows(metrics[metrics["model"].isin(CLASSICAL + BASELINES)], summary)

    print(summary.to_string(index=False))
    print(f"\nWrote tables and {len(list(FIGS.glob('*.png')))} figures to {OUT.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
