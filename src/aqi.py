"""CPCB National AQI: pollutant sub-indices and the overall index.

``daily_aqi_from_hourly`` reproduces how ``city_day.csv``'s AQI was built: hourly
sub-indices from 24-hour rolling means (PM2.5, PM10, NOx, SO2, NH3) and 8-hour
rolling maxima (CO, O3), overall hourly AQI = max sub-index, daily AQI = mean of
the hourly values. For single-station cities (Ahmedabad) this matches the
published daily AQI exactly (all 1,334 comparable days within +/-1).

Breakpoints follow the CPCB National Air Quality Index (2014). Above the top
breakpoint the last band is extended linearly, which is the same convention used
to build ``city_day.csv`` (its AQI goes above 500 in several cities).

Rules applied, as in CPCB:
* AQI = max of the available sub-indices.
* At least 3 sub-indices must be available, one of which is PM2.5 or PM10;
  otherwise AQI is undefined (NaN).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# (concentration breakpoints, index breakpoints) per pollutant.
# Units: mg/m3 for CO, ug/m3 for the rest.
_INDEX_BP = [0, 50, 100, 200, 300, 400, 500]
BREAKPOINTS = {
    "PM2.5": [0, 30, 60, 90, 120, 250, 380],
    "PM10": [0, 50, 100, 250, 350, 430, 510],
    "NO2": [0, 40, 80, 180, 280, 400, 520],
    "SO2": [0, 40, 80, 380, 800, 1600, 2400],
    "NH3": [0, 200, 400, 800, 1200, 1800, 2400],
    "CO": [0, 1.0, 2.0, 10, 17, 34, 51],
    "O3": [0, 50, 100, 168, 208, 748, 1288],
}
ROLLING_MEAN_24H = ("PM2.5", "PM10", "NOx", "SO2", "NH3")
ROLLING_MAX_8H = ("CO", "O3")
# city_day.csv derives the NO2 sub-index from the NOx column.
SOURCE_COLUMN = {"NO2": "NOx"}
PM = ("PM2.5", "PM10")


def sub_index(conc: pd.Series, pollutant: str) -> pd.Series:
    """Piecewise-linear sub-index; the top band is extrapolated linearly."""
    x = conc.to_numpy(dtype=float)
    bp = np.array(BREAKPOINTS[pollutant], dtype=float)
    ib = np.array(_INDEX_BP, dtype=float)
    out = np.interp(x, bp, ib)
    top = x > bp[-2]
    slope = (ib[-1] - ib[-2]) / (bp[-1] - bp[-2])
    out[top] = ib[-2] + (x[top] - bp[-2]) * slope
    out[np.isnan(x)] = np.nan
    return pd.Series(out, index=conc.index, name=f"{pollutant}_SI")


def sub_indices(df: pd.DataFrame, exclude: tuple[str, ...] = ()) -> pd.DataFrame:
    return pd.concat([sub_index(df[SOURCE_COLUMN.get(p, p)], p)
                      for p in BREAKPOINTS if p not in exclude], axis=1)


def compute_aqi(df: pd.DataFrame, exclude: tuple[str, ...] = ()) -> pd.Series:
    """Overall AQI from a frame of pollutant columns; ``exclude`` drops pollutants (e.g. CO)."""
    si = sub_indices(df, exclude)
    valid = (si.notna().sum(axis=1) >= 3) & si[[f"{p}_SI" for p in PM]].notna().any(axis=1)
    return si.max(axis=1).where(valid).rename("AQI")


def daily_aqi_from_hourly(hourly: pd.DataFrame, exclude: tuple[str, ...] = ()) -> pd.Series:
    """Daily AQI for one city from its ``city_hour.csv`` rows (``Datetime`` + pollutant columns)."""
    h = hourly.set_index("Datetime").sort_index().asfreq("h")
    agg = pd.DataFrame(index=h.index)
    for col in ROLLING_MEAN_24H:
        agg[col] = h[col].rolling(24, min_periods=16).mean()
    for col in ROLLING_MAX_8H:
        agg[col] = h[col].rolling(8, min_periods=1).max()
    return compute_aqi(agg, exclude).resample("D").mean().round()
