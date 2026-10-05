"""Figures for the project report (docs/Project_Report.docx).

Run from the repo root:  venv\\Scripts\\python docs/report/make_figures.py
Writes PNGs to docs/report/figures/. Numbers come from the saved pipeline outputs
(reports/forecasting/*, reports/health/*) and the cleaned data loader.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "report" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

import sys  # noqa: E402

sys.path.insert(0, str(ROOT))
from src.data_loader import CITIES, load_all_cities, load_raw  # noqa: E402

# Palette (validated: blue, orange, aqua) + recessive neutrals.
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID, SURFACE = "#1f1f1e", "#6b6a64", "#e4e3de", "#fcfcfb"
TEAL = "#0b6e74"
NL = chr(10)  # line break inside diagram labels
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": MUTED,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "axes.titlesize": 10, "axes.titleweight": "bold",
    "axes.titlecolor": INK, "figure.facecolor": "white", "axes.facecolor": "white", "savefig.dpi": 200,
})


def save(fig, name):
    fig.savefig(OUT / name, bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


# ---------------------------------------------------------------- 1. AQI overview (small multiples)
def fig_aqi_overview():
    data = load_all_cities()
    fig, axes = plt.subplots(3, 2, figsize=(9, 6.2), sharex=True)
    for ax, city in zip(axes.flat, CITIES):
        s = data[city]["value"]
        ax.plot(s.index, s.values, color=BLUE, lw=0.7)
        ax.plot(s.index, s.rolling(30, center=True).mean(), color=INK, lw=1.4)
        ax.set_title(f"{city}  (n = {len(s):,} days)", loc="left")
        ax.set_ylabel("AQI")
    axes[0, 0].plot([], [], color=BLUE, lw=0.7, label="Daily AQI")
    axes[0, 0].plot([], [], color=INK, lw=1.4, label="30-day mean")
    axes[0, 0].legend(frameon=False, loc="upper right", fontsize=8)
    fig.tight_layout()
    save(fig, "fig_aqi_overview.png")


# ---------------------------------------------------------------- 2. STL decomposition (Delhi)
def fig_stl():
    from statsmodels.tsa.seasonal import STL
    s = np.log1p(load_all_cities(["Delhi"])["Delhi"]["value"])
    res = STL(s.to_numpy(), period=365, robust=True).fit()
    idx = s.index
    fig, axes = plt.subplots(4, 1, figsize=(9, 5.6), sharex=True)
    for ax, y, t in zip(axes, [s.values, res.trend, res.seasonal, res.resid],
                        ["Observed: log(1 + AQI)", "Trend", "Seasonal (period 365 days)", "Remainder"]):
        ax.plot(idx, y, color=BLUE if t != "Remainder" else MUTED, lw=0.9)
        ax.set_title(t, loc="left", fontsize=9)
    fig.tight_layout()
    save(fig, "fig_stl_delhi.png")


# ---------------------------------------------------------------- 3. Ahmedabad CO fix
def fig_ahmedabad():
    raw = load_raw(["Ahmedabad"]).set_index("Date")["AQI"]
    fixed = load_all_cities(["Ahmedabad"])["Ahmedabad"]["value"]
    m_raw = raw.loc["2017-10-11":].rolling(14, min_periods=5).mean()
    m_fix = fixed.rolling(14, min_periods=5).mean()
    fig, ax = plt.subplots(figsize=(9, 3.2))
    ax.plot(m_raw.index, m_raw.values, color=ORANGE, lw=1.6, label="Published AQI (with faulty CO sensor)")
    ax.plot(m_fix.index, m_fix.values, color=BLUE, lw=1.6, label="Recomputed AQI (without CO)")
    ax.axhline(500, color=MUTED, lw=0.8, ls="--", label="CPCB scale maximum (500)")
    ax.set_ylim(0, None)
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="lower left", bbox_to_anchor=(0, 1.0))
    ax.set_ylabel("AQI, 14-day mean")
    fig.tight_layout()
    save(fig, "fig_ahmedabad_co.png")


# ---------------------------------------------------------------- 4. Rolling-origin windows
def fig_windows():
    s = load_all_cities(["Delhi"])["Delhi"]["value"]
    fig, ax = plt.subplots(figsize=(9, 2.8))
    ax.plot(s.index, s.values, color=MUTED, lw=0.6)
    for w in range(6):
        end = len(s) - w * 120
        a, b = s.index[end - 30], s.index[end - 1]
        ax.axvspan(a, b, color=BLUE, alpha=0.25, lw=0)
        ax.text(a + (b - a) / 2, s.max() * 0.97, f"W{w}", ha="center", fontsize=8, color=INK)
    ax.set_xlim(pd.Timestamp("2018-06-01"), s.index[-1] + pd.Timedelta(days=10))
    ax.set_ylabel("AQI")
    ax.set_title("Delhi: six 30-day test windows (W0 = final hold-out), each trained on all earlier data",
                 loc="left")
    fig.tight_layout()
    save(fig, "fig_windows.png")


# ---------------------------------------------------------------- 5. Model comparison heatmap
def fig_heatmap():
    s = pd.read_csv(ROOT / "reports/forecasting/multiwindow_summary.csv")
    models = ["ARIMA", "SARIMA", "Holt-Winters", "LSTM", "XGBoost", "Prophet"]
    piv = s.pivot_table(index="model", columns="city", values="mean_rmse").reindex(columns=CITIES)
    base = s[s["kind"] == "baseline"].groupby("city")["mean_rmse"].min().reindex(CITIES)
    pct = (piv.loc[models] / base - 1) * 100
    fig, ax = plt.subplots(figsize=(8.6, 3.6))
    lim = 40
    im = ax.imshow(pct.clip(-lim, lim), cmap="RdBu_r", vmin=-lim, vmax=lim, aspect="auto")
    ax.set_xticks(range(len(CITIES)), CITIES)
    ax.set_yticks(range(len(models)), models)
    ax.grid(False)
    best = pct.idxmin()
    for i, m in enumerate(models):
        for j, c in enumerate(CITIES):
            v = pct.loc[m, c]
            star = " *" if best[c] == m else ""
            label = "0%" if round(v) == 0 else f"{v:+.0f}%"
            ax.text(j, i, f"{label}{star}", ha="center", va="center", fontsize=8.5,
                    color="white" if abs(v) > 28 else INK, fontweight="bold" if star else "normal")
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cb.set_label("Mean RMSE vs best naive baseline (%)", color=MUTED)
    cb.outline.set_visible(False)
    ax.set_title("Mean RMSE over 6 windows relative to the best baseline (blue = better, * = selected)",
                 loc="left")
    fig.tight_layout()
    save(fig, "fig_model_heatmap.png")


# ---------------------------------------------------------------- 6. Health model comparison
def fig_health():
    h = pd.read_csv(ROOT / "reports/health/metrics.csv")
    h = h[(h["kind"] == "model")]
    sets = [("aqi_only", "Profile + AQI"), ("aqi_pm25_no2", "Profile + AQI + PM2.5 + NO2"), ("full", "All 5 pollutants")]
    models, colors = ["Random Forest", "XGBoost", "MLP"], [BLUE, ORANGE, AQUA]
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.1))
    for ax, (task, metric, label) in zip(axes, [("classification", "test_f1_weighted", "Weighted F1 (higher is better)"),
                                                ("regression", "test_rmse", "RMSE (lower is better)")]):
        x = np.arange(len(sets))
        for k, (m, col) in enumerate(zip(models, colors)):
            vals = [h[(h.task == task) & (h.feature_set == fs) & (h.model == m)][metric].iloc[0] for fs, _ in sets]
            bars = ax.bar(x + (k - 1) * 0.26, vals, width=0.24, color=col, label=m, edgecolor="white", linewidth=1.5)
            for b, v in zip(bars, vals):
                ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.2f}", ha="center", va="bottom", fontsize=7, color=INK)
        ax.set_xticks(x, [s[1] for s in sets], fontsize=8)
        ax.set_title(label, loc="left")
        if task == "classification":
            ax.set_ylim(0.7, 0.9)
    axes[0].legend(frameon=False, fontsize=8, loc="upper left", ncol=3)
    fig.tight_layout()
    save(fig, "fig_health_models.png")


# ---------------------------------------------------------------- 7. Diagrams
def box(ax, x, y, w, h, title, sub="", fc="#f3f6f8", ec="#9aa5b1", tc=INK):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec=ec, lw=1))
    lines = sub.count(NL) + 1 if sub else 0
    ax.text(x + w / 2, y + h / 2 + (0.1 + 0.1 * lines if sub else 0), title, ha="center", va="center",
            fontsize=8.3, fontweight="bold", color=tc)
    if sub:
        ax.text(x + w / 2, y + h / 2 - 0.12 - 0.05 * lines, sub, ha="center", va="center", fontsize=7.5,
                color=MUTED, linespacing=1.3)


def arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.2))


def fig_pipeline():
    fig, ax = plt.subplots(figsize=(9.2, 1.9))
    ax.set_xlim(0, 15.2); ax.set_ylim(0.75, 2.85); ax.axis("off")
    steps = [("CPCB data", "city_day," + NL + "city_hour"), ("Cleaning", "gap filling," + NL + "CO fix"),
             ("Diagnostics", "ADF, KPSS," + NL + "ACF, STL"), ("Models", "6 models +" + NL + "3 baselines"),
             ("Evaluation", "6 rolling" + NL + "windows"), ("Selection", "lowest mean" + NL + "RMSE"),
             ("Deployment", "saved model" + NL + "per city")]
    w = 1.85
    for i, (t_, s) in enumerate(steps):
        x = 0.1 + i * 2.15
        hl = t_ in ("Evaluation", "Selection")
        box(ax, x, 0.85, w, 1.35, t_, s, fc="#e3f1f1" if hl else "#f3f6f8", ec=TEAL if hl else "#9aa5b1")
        if i < len(steps) - 1:
            arrow(ax, x + w + 0.02, 1.52, x + 2.13, 1.52)
    ax.text(0.1, 2.55, "Forecasting methodology (run separately for AQI, PM2.5 and NO2)", fontsize=9, color=INK,
            fontweight="bold")
    save(fig, "fig_pipeline.png")


def fig_architecture():
    fig, ax = plt.subplots(figsize=(9.4, 3.9))
    ax.set_xlim(0, 19); ax.set_ylim(1.6, 8.6); ax.axis("off")
    # offline
    box(ax, 0.2, 6.4, 3.0, 1.4, "CPCB dataset", "2015-2020, 6 cities")
    box(ax, 0.2, 4.2, 3.0, 1.4, "Health dataset", "7,500 profiles + AQI")
    box(ax, 3.9, 6.4, 3.4, 1.4, "Forecasting pipeline", "AQI, PM2.5, NO2")
    box(ax, 3.9, 4.2, 3.4, 1.4, "Health-risk pipeline", "RF / XGBoost / MLP")
    box(ax, 8.0, 4.2, 2.6, 3.6, "Saved models", "18 forecasters" + NL + "4 risk models")
    # online
    box(ax, 11.6, 4.2, 2.8, 1.4, "FastAPI backend", "public + /api/me", fc="#e3f1f1", ec=TEAL)
    box(ax, 11.6, 2.0, 2.8, 1.4, "Supabase", "Postgres, Auth, RLS")
    box(ax, 15.6, 6.4, 3.0, 1.4, "User", "web browser")
    box(ax, 15.6, 4.2, 3.0, 1.4, "Next.js web app", "Airware")
    box(ax, 15.6, 2.0, 3.0, 1.4, "OpenStreetMap", "Overpass hospitals")
    for (x1, y1), (x2, y2) in [((3.2, 7.1), (3.9, 7.1)), ((3.2, 4.9), (3.9, 4.9)), ((7.3, 7.1), (8.0, 7.1)),
                               ((7.3, 4.9), (8.0, 4.9)), ((10.6, 4.9), (11.6, 4.9)), ((13.0, 4.2), (13.0, 3.4)),
                               ((15.6, 4.9), (14.4, 4.9)), ((17.1, 6.4), (17.1, 5.6)), ((17.1, 4.2), (17.1, 3.4))]:
        arrow(ax, x1, y1, x2, y2)
    ax.text(0.2, 8.25, "Offline: data and model training", fontsize=9, fontweight="bold", color=INK)
    ax.text(11.6, 8.25, "Online: serving and user interface", fontsize=9, fontweight="bold", color=INK)
    ax.plot([11.1, 11.1], [1.8, 8.4], color=GRID, lw=1, ls="--")
    save(fig, "fig_architecture.png")


if __name__ == "__main__":
    fig_aqi_overview(); fig_stl(); fig_ahmedabad(); fig_windows(); fig_heatmap(); fig_health()
    fig_pipeline(); fig_architecture()
