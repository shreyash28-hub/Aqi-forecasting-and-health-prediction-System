"""Daily city AQI and pollutants from the live OpenAQ station downloads (Feb 2025 onwards).

Input: ``data/openaq/raw/<City>/<station>_<param>/<YYYY-MM>.csv``, written by
``scripts/download_openaq.py`` (hourly CPCB station readings, 4 stations per city).
Output: ``data/processed/live_city_day.csv`` with one row per city and day, in the same
units and with the same AQI method as ``city_day.csv``, so the 2015-2020 history and
the live data can sit on one time axis.

How the daily values are built
------------------------------
* Units: OpenAQ labels the CPCB gas readings "ppb", but they are CPCB's own units
  (ug/m3, and mg/m3 for CO). CO medians are 0.3-1.3, which is impossible in ppb
  (ambient CO is hundreds of ppb) and matches city_day.csv's 0.6-1.2 mg/m3. NO2 and
  SO2 also match city_day.csv levels as ug/m3. So no conversion is applied.
* Cleaning per station: negative readings, values above ``MAX_VALUE`` and runs of
  ``STUCK_HOURS`` or more identical hourly readings (a stuck sensor) are dropped, and
  so are hours where PM2.5 reads above PM10 (physically impossible; 0-7% of hours).
* Cleaning across stations: a station's day is dropped for a pollutant when it reads
  far above the city's other stations (``OUTLIER_RATIO``/``OUTLIER_MARGIN``). This
  catches e.g. Chennai Manali's O3 sensor pinned at 500 ug/m3 in Sep 2026.
* Stamps are converted to Indian time (UTC+5:30), so days run midnight to midnight
  IST as in the CPCB bulletins.
* City hourly concentration = mean over the stations reporting that hour, as in
  ``city_hour.csv``; then ``src.aqi.hourly_aqi`` (24-h means, 8-h maxima for CO/O3).
* Daily AQI = mean of the hourly AQI, kept only if at least ``MIN_HOURS`` hours have
  an AQI. Daily pollutant values are 24-hour means under the same rule.
* NO2: city_day.csv's AQI took the NO2 sub-index from its NOx column. These stations
  have no NOx sensor in the download, so NO2 itself is used, which is CPCB's rule.
* CO is included for every city, Ahmedabad too: its live CO sensors read normally
  (median 0.5-0.7 mg/m3), unlike the faulty 2015-2020 one.

Daily refresh: ``python -m src.live_data --recent`` rebuilds only the last few days from
``data/openaq/recent/`` (``src.openaq.fetch_recent``) and merges them into the saved file,
so a server without the full download can keep it current. The first day of the recent
window has no 24-hour history behind it and today is incomplete, so only the days in
between are merged; a day with no new reading keeps its saved value.

Usage::

    python -m src.live_data           # rebuild data/processed/live_city_day.csv from the full download
    python -m src.live_data --recent  # merge the last few days from data/openaq/recent/
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.aqi import hourly_aqi
from src.data_loader import CITIES, DATA_DIR, clean_series

RAW_DIR = DATA_DIR / "openaq" / "raw"
RECENT_DIR = DATA_DIR / "openaq" / "recent"
OUT_PATH = DATA_DIR / "processed" / "live_city_day.csv"

# OpenAQ parameter -> city_day.csv column
COLUMNS = {"pm25": "PM2.5", "pm10": "PM10", "no2": "NO2", "so2": "SO2", "co": "CO", "o3": "O3"}
MAX_VALUE = {"PM2.5": 1000, "PM10": 1500, "NO2": 1000, "SO2": 1000, "CO": 50, "O3": 1000}
STUCK_HOURS = 12
PM_MARGIN = 5                 # ug/m3 of tolerance before PM2.5 > PM10 counts as an error
# A station-day is an outlier above max(ratio x, margin +) the other stations' median.
OUTLIER_RATIO = 4
OUTLIER_MARGIN = {"PM2.5": 60, "PM10": 100, "NO2": 40, "SO2": 40, "CO": 1.5, "O3": 60}
MIN_HOURS = 16
IST = pd.Timedelta(hours=5, minutes=30)


def _drop_stuck(s: pd.Series) -> pd.Series:
    """NaN out runs of ``STUCK_HOURS`` or more identical consecutive hourly readings."""
    run_id = (s != s.shift()).cumsum()
    run_len = s.groupby(run_id).transform("size")
    return s.mask(run_len >= STUCK_HOURS)


def load_station_hourly(folder: Path) -> pd.Series:
    """One sensor's cleaned hourly readings, indexed by IST hour."""
    col = COLUMNS[folder.name.split("_", 1)[1]]
    frames = [pd.read_csv(f, usecols=["datetime_utc", "value"]) for f in sorted(folder.glob("*.csv"))]
    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["datetime_utc", "value"])
    if df.empty:
        return pd.Series(dtype=float, index=pd.DatetimeIndex([]), name=col)
    stamp = (pd.to_datetime(df["datetime_utc"], utc=True).dt.tz_localize(None) + IST).dt.floor("h")
    s = pd.Series(df["value"].to_numpy(dtype=float), index=stamp).groupby(level=0).mean()
    s = s.asfreq("h")
    s = s.where((s >= 0) & (s <= MAX_VALUE[col]))
    return _drop_stuck(s).rename(col)


def load_station(city: str, station: str, raw: Path | None = None) -> pd.DataFrame:
    """One station's cleaned hourly pollutants. Hours with PM2.5 above PM10 are dropped
    for both: PM2.5 is part of PM10, so one of the two sensors is wrong."""
    cols = [load_station_hourly(f) for f in sorted(((raw or RAW_DIR) / city).glob(f"{station}_*"))
            if f.name.split("_", 1)[1] in COLUMNS]
    df = pd.concat(cols, axis=1)
    if {"PM2.5", "PM10"} <= set(df):
        bad = df["PM2.5"] > df["PM10"] + PM_MARGIN
        df.loc[bad, ["PM2.5", "PM10"]] = np.nan
    return df


def _drop_outlier_days(stations: dict[str, pd.Series], col: str) -> dict[str, pd.Series]:
    """Drop a station's day when it reads far above the other stations in the city
    (a saturated or drifting sensor, e.g. an O3 sensor pinned at 500)."""
    daily = pd.DataFrame({k: s.resample("D").mean() for k, s in stations.items()})
    out = {}
    for k, s in stations.items():
        others = daily.drop(columns=k).median(axis=1)
        limit = np.maximum(others * OUTLIER_RATIO, others + OUTLIER_MARGIN[col])
        bad_days = daily.index[daily[k] > limit]
        out[k] = s.mask(s.index.normalize().isin(bad_days))
    return out


def city_hourly(city: str, raw: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """City hourly concentrations (station mean) and the number of stations per hour and pollutant."""
    raw = raw or RAW_DIR
    ids = sorted({f.name.split("_", 1)[0] for f in (raw / city).iterdir() if f.is_dir()})
    stations = {sid: load_station(city, sid, raw) for sid in ids}
    means, counts = {}, {}
    for col in COLUMNS.values():
        per_station = {sid: df[col] for sid, df in stations.items() if col in df}
        if not per_station:
            continue
        stacked = pd.concat(_drop_outlier_days(per_station, col), axis=1)
        means[col], counts[col] = stacked.mean(axis=1), stacked.notna().sum(axis=1)
    return pd.DataFrame(means).asfreq("h"), pd.DataFrame(counts).asfreq("h").fillna(0).astype(int)


def city_hourly_aqi(city: str, raw: Path | None = None) -> tuple[pd.Series, pd.DataFrame, pd.DataFrame]:
    """Hourly AQI, hourly concentrations and station counts for one city (IST hours)."""
    conc, counts = city_hourly(city, raw)
    frame = conc.reindex(columns=list(COLUMNS.values()))   # a missing pollutant becomes NaN
    frame["NOx"] = frame["NO2"]   # the AQI's NO2 sub-index reads the NOx column (see docstring)
    frame["NH3"] = np.nan
    return hourly_aqi(frame.rename_axis("Datetime").reset_index()), conc, counts


def city_daily(city: str, raw: Path | None = None) -> pd.DataFrame:
    """Daily AQI and 24-hour mean pollutants for one city."""
    aqi_h, conc, counts = city_hourly_aqi(city, raw)

    daily = pd.DataFrame(index=aqi_h.resample("D").mean().index)
    daily["AQI"] = aqi_h.resample("D").mean().round().where(aqi_h.resample("D").count() >= MIN_HOURS)
    for col in COLUMNS.values():
        if col in conc:
            daily[col] = conc[col].resample("D").mean().where(conc[col].resample("D").count() >= MIN_HOURS)
    daily["stations"] = counts.get("PM2.5", pd.Series(0, index=counts.index)).resample("D").mean().round(1)
    daily = daily.round({c: 2 for c in COLUMNS.values()})
    daily.insert(0, "City", city)
    return daily.rename_axis("Date").reset_index()


def _today_ist() -> pd.Timestamp:
    return (pd.Timestamp.now(tz="UTC").tz_localize(None) + IST).normalize()


def build(cities: list[str] | None = None) -> pd.DataFrame:
    out = pd.concat([city_daily(c) for c in cities or CITIES], ignore_index=True)
    # The current day is still in progress: keep only complete days.
    return out[out["Date"] < _today_ist()]


def merge_recent(raw: Path | None = None, cities: list[str] | None = None, path: Path | None = None) -> pd.DataFrame:
    """Merge the complete days of the recent download into the saved daily file.

    The window's first day is dropped (its rolling 24-hour values lack history) and so is
    today (incomplete). Cells with a new value replace the saved ones; cells the new data
    lacks keep what was saved."""
    path = path or OUT_PATH
    key = ["City", "Date"]
    parts = []
    for city in cities or CITIES:
        d = city_daily(city, raw or RECENT_DIR)
        first = d["Date"].min()
        parts.append(d[(d["Date"] > first) & (d["Date"] < _today_ist())])
    new = pd.concat(parts, ignore_index=True).set_index(key)
    old = pd.read_csv(path, parse_dates=["Date"]).set_index(key) if path.exists() else new.iloc[:0]
    merged = new.combine_first(old).reset_index().sort_values(key)
    merged.to_csv(path, index=False)
    return merged


def load_live(city: str) -> pd.DataFrame:
    """The saved daily rows for one city (run ``python -m src.live_data`` first)."""
    df = pd.read_csv(OUT_PATH, parse_dates=["Date"])
    return df[df["City"] == city].set_index("Date").drop(columns="City")


def load_live_cities(cities: list[str] | None = None, target: str = "AQI") -> dict[str, pd.DataFrame]:
    """``{city: frame}`` like ``data_loader.load_all_cities`` (``value``, ``is_interpolated``),
    from the live daily data: short gaps interpolated the same way."""
    df = pd.read_csv(OUT_PATH, parse_dates=["Date"])
    out = {}
    for city in cities or CITIES:
        s = df[df["City"] == city].set_index("Date")[target]
        frame = clean_series(s)
        frame.index.name = "date"
        out[city] = frame
    return out


def main() -> None:
    import sys
    if "--recent" in sys.argv:
        df = merge_recent()
        last = df.groupby("City")["Date"].max().dt.date.astype(str).to_dict()
        print(f"Merged the recent readings into {OUT_PATH}; latest day per city: {last}")
        return
    df = build()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print(f"Saved {len(df)} rows to {OUT_PATH}")
    summary = df.groupby("City").agg(first=("Date", "min"), last=("Date", "max"), days=("Date", "size"),
                                     aqi_days=("AQI", "count"), aqi_median=("AQI", "median"),
                                     aqi_max=("AQI", "max"), pm25_median=("PM2.5", "median"))
    print(summary.to_string())


if __name__ == "__main__":
    main()
