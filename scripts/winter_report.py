"""Winter test of the live forecasting models: how they do on last winter (Nov 2025 - Feb 2026).

The regular live evaluation steps back 45 days from the end of the data, so its test windows
cover April to October only. This report reads a separate run on four winter windows::

    python -m src.run_forecasting --source live --target T \\
        --window-ends 2025-11-30 2025-12-30 2026-01-29 2026-02-28 --tag winter   # T = AQI, PM2.5, NO2
    python -m src.run_forecasting --source live --target AQI --no-prior \\
        --window-ends 2025-11-30 2025-12-30 2026-01-29 2026-02-28 --tag winter   # prior on/off
    python scripts/winter_report.py

and writes ``reports/forecasting/live/winter.md``: for each city and target, whether the
deployed model still beats the naive baselines in winter, which model would win in winter
and over all nine windows, what the 2015-2020 seasonal prior is worth in winter, and whether
the AQI and PM2.5 forecasts stay consistent (PM2.5 alone must not imply a higher AQI).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.aqi import sub_index  # noqa: E402

LIVE = ROOT / "reports" / "forecasting" / "live"
OUT = LIVE / "winter.md"
TARGETS = {"AQI": "aqi", "PM2.5": "pm25", "NO2": "no2"}
CITIES = ["Delhi", "Lucknow", "Ahmedabad", "Bengaluru", "Chennai", "Hyderabad"]


def deployed(slug: str) -> dict[str, str]:
    reg = json.loads((ROOT / "models" / "live" / slug / "registry.json").read_text(encoding="utf-8"))
    return {c: v["model"] for c, v in reg["cities"].items()}


def load(slug: str, sub: str = "winter") -> pd.DataFrame | None:
    p = LIVE / slug / sub / "metrics.csv" if sub else LIVE / slug / "metrics.csv"
    return pd.read_csv(p) if p.exists() else None


def table(header: list[str], rows: list[list]) -> list[str]:
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(v) for v in r) + " |" for r in rows]
    return out + [""]


def per_target(target: str, slug: str) -> tuple[list[str], dict]:
    w, s = load(slug), load(slug, sub="")
    if w is None:
        return [f"_No winter run for {target} yet._", ""], {}
    dep = deployed(slug)
    ok = w[w["error"].isna()]
    mean_w = ok.groupby(["city", "model"])["rmse"].mean()
    base = ok[ok["kind"] == "baseline"].groupby(["city", "window"])["rmse"].min()
    mean_s = s[s["error"].isna()].groupby(["city", "model"])["rmse"].mean()
    allrows = pd.concat([ok, s[s["error"].isna()]])
    both = allrows[allrows["kind"] == "model"].groupby(["city", "model"])["rmse"].mean()
    rows, facts = [], {"beats": 0, "n": 0, "changes": []}
    for city in CITIES:
        if city not in dep:
            continue
        model = dep[city]
        c = ok[ok["city"] == city]
        models = c[c["kind"] == "model"].groupby("model")["rmse"].mean().sort_values()
        bases = c[c["kind"] == "baseline"].groupby("model")["rmse"].mean().sort_values()
        dm = mean_w.get((city, model), np.nan)
        wins = 0
        if model in set(c["model"]):
            per_win = c[c["model"] == model].set_index("window")["rmse"]
            wins = int(sum(per_win[k] < base[(city, k)] for k in per_win.index))
        gain = 100 * (dm / bases.iloc[0] - 1)
        facts["n"] += 1
        facts["beats"] += int(dm < bases.iloc[0])
        best_all = both.loc[city].idxmin()
        if best_all != model:
            facts["changes"].append(f"{city}: {model} -> {best_all}")
        rows.append([city, model, f"{dm:.1f}", f"{bases.index[0]} {bases.iloc[0]:.1f}",
                     f"{gain:+.0f}%", f"{wins}/{c['window'].nunique()}",
                     f"{models.index[0]} {models.iloc[0]:.1f}",
                     f"{mean_s.get((city, model), np.nan):.1f}", best_all])
    lines = table(["City", "Deployed model", "Winter RMSE", "Best naive (winter)", "vs naive", "Windows beating naive",
                   "Best in winter", "Apr-Oct RMSE", "Best over all 9 windows"], rows)
    return lines, facts


def prior_effect() -> list[str]:
    w, n = load("aqi"), None
    p = LIVE / "aqi" / "no_prior" / "winter" / "metrics.csv"
    if w is None or not p.exists():
        return ["_No winter run without the prior yet._", ""]
    n = pd.read_csv(p)
    dep = deployed("aqi")
    rows, changes = [], []
    for city in CITIES:
        m = dep.get(city)
        a = w[(w["city"] == city) & (w["model"] == m) & w["error"].isna()]["rmse"].mean()
        b = n[(n["city"] == city) & (n["model"] == m) & n["error"].isna()]["rmse"].mean()
        best_with = w[(w["city"] == city) & (w["kind"] == "model") & w["error"].isna()].groupby("model")["rmse"].mean().min()
        best_without = n[(n["city"] == city) & (n["kind"] == "model") & n["error"].isna()].groupby("model")["rmse"].mean().min()
        changes.append(100 * (best_with / best_without - 1))
        rows.append([city, m, f"{a:.1f}", f"{b:.1f}", f"{100 * (a / b - 1):+.0f}%",
                     f"{best_with:.1f}", f"{best_without:.1f}", f"{changes[-1]:+.0f}%"])
    return table(["City", "Deployed AQI model", "Winter RMSE with prior", "without", "change",
                  "Best model with prior", "Best without", "change"], rows) + [
        f"Average change in the best model's winter RMSE from the prior: {np.mean(changes):+.1f}%.", ""]


def consistency() -> list[str]:
    fa, fp = LIVE / "aqi" / "winter" / "forecasts.csv", LIVE / "pm25" / "winter" / "forecasts.csv"
    if not (fa.exists() and fp.exists()):
        return ["_Needs the AQI and PM2.5 winter runs._", ""]
    a, p = pd.read_csv(fa), pd.read_csv(fp)
    da, dp = deployed("aqi"), deployed("pm25")
    rows, total_bad, total = [], 0, 0
    for city in CITIES:
        ca, cp = a[a["city"] == city], p[p["city"] == city]
        if da.get(city) not in ca or dp.get(city) not in cp:
            continue
        m = (ca[["date", "window", da[city]]].rename(columns={da[city]: "aqi"})
             .merge(cp[["date", "window", dp[city]]].rename(columns={dp[city]: "pm25"}), on=["date", "window"]))
        si = sub_index(m["pm25"], "PM2.5").to_numpy()
        bad = int((si > 1.10 * m["aqi"].to_numpy()).sum())
        total_bad += bad
        total += len(m)
        rows.append([city, f"{da[city]} / {dp[city]}", f"{bad}/{len(m)}"])
    return table(["City", "AQI model / PM2.5 model", "Days where PM2.5 implies a higher AQI"], rows) + [
        f"Overall: {total_bad} of {total} forecast days inconsistent (10% tolerance).", ""]


def main() -> None:
    L = ["# Live models: winter test", "",
         "Four 30-day test windows covering last winter (1 Nov 2025 to 28 Feb 2026), each trained only on the "
         "data before it (from Feb 2025), with the same models, settings and seasonal prior as the regular live "
         "evaluation. The regular evaluation's windows cover April to October, so this is the first test of the "
         "live models in the smog season. Generated by `scripts/winter_report.py`.", "",
         "**Caveats.** With under a year of training data before last winter, the same-day-last-year baseline "
         "cannot run, so the naive comparison uses the last-value and same-weekday-last-week baselines. The "
         "seasonal prior's per-city scale needs 300 training days, so the November and December windows use the "
         "prior at full strength (scale 1.0), exactly as the live system would have then.", ""]
    for target, slug in TARGETS.items():
        lines, facts = per_target(target, slug)
        L += [f"## {target}", ""]
        if facts:
            L += [f"The deployed model beats the best naive forecast on mean winter RMSE in {facts['beats']} of "
                  f"{facts['n']} cities. "
                  + (f"Over all nine windows (5 Apr-Oct + 4 winter) the best model would change in: "
                     f"{'; '.join(facts['changes'])}." if facts["changes"] else
                     "Over all nine windows the deployed model stays the best in every city."), ""]
        L += lines
    L += ["## What the seasonal prior is worth in winter (AQI)", ""] + prior_effect()
    L += ["## Are the AQI and PM2.5 forecasts consistent in winter?", "",
          "AQI is the largest pollutant sub-index, so the PM2.5 forecast alone should never imply a higher AQI "
          "than the AQI forecast.", ""] + consistency()
    OUT.write_text("\n".join(L), encoding="utf-8")
    print("Wrote", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
