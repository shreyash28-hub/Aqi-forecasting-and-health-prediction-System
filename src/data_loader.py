"""Load per-city daily AQI series from the CPCB ``city_day.csv`` dataset.

Source: Kaggle "Air Quality Data in India" (CPCB), shipped in ``data/Aqi.zip``.
Only the six well-covered cities agreed in CLAUDE.md are used.

Gap handling
------------
* Leading NaNs (before a city's first reading) are dropped.
* Interior gaps of up to ``max_gap`` days are filled by time-linear interpolation.
* If a gap longer than ``max_gap`` remains, only the most recent contiguous
  segment is kept (a long outage can't be interpolated honestly). In practice
  this only affects Ahmedabad, which has 232- and 340-day outages in 2015-2017.
* An ``is_interpolated`` flag is kept so evaluation can score observed days only.

Ahmedabad: AQI recomputed without CO
------------------------------------
Ahmedabad's CO readings are implausible: its median daily CO is 16 mg/m3 against
0.6-1.4 in the other five cities, and CO is the dominant sub-index in 82% of hours,
pushing the published AQI up to 2,049 (CPCB scale tops out at 500). For
Ahmedabad only, AQI is recomputed from ``city_hour.csv`` with the same method the
dataset used (see ``src/aqi.py``), leaving CO out. In the other cities CO moves the
median AQI by only 7-15 points, so their published AQI is used as-is.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd

from src.aqi import daily_aqi_from_hourly

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
ZIP_PATH = DATA_DIR / "Aqi.zip"
CSV_PATH = DATA_DIR / "city_day.csv"
HOURLY_CSV_PATH = DATA_DIR / "city_hour.csv"

CITIES = ["Delhi", "Bengaluru", "Chennai", "Hyderabad", "Lucknow", "Ahmedabad"]
POLLUTANTS = ["PM2.5", "PM10", "NO2", "SO2", "O3", "CO"]
DEFAULT_MAX_GAP = 21  # days
# Series that can be forecast: city_day.csv column -> short slug used in paths/columns.
# PM2.5 and NO2 feed the health model (together with AQI); they're the only
# pollutants with usable history in all six cities.
TARGETS = {"AQI": "aqi", "PM2.5": "pm25", "NO2": "no2"}
# Pollutants left out when recomputing a city's AQI (see module docstring).
AQI_EXCLUDED_POLLUTANTS = {"Ahmedabad": ("CO",)}


def _ensure_extracted(path: Path) -> Path:
    """Extract ``path`` from ``Aqi.zip`` if it isn't already on disk."""
    if not path.exists():
        if not ZIP_PATH.exists():
            raise FileNotFoundError(f"Neither {path} nor {ZIP_PATH} exists.")
        with zipfile.ZipFile(ZIP_PATH) as zf:
            zf.extract(path.name, DATA_DIR)
    return path


def ensure_city_day_csv() -> Path:
    return _ensure_extracted(CSV_PATH)


def load_raw(cities: list[str] | None = None) -> pd.DataFrame:
    """Raw ``city_day.csv`` rows for the selected cities (default: the six)."""
    df = pd.read_csv(ensure_city_day_csv(), parse_dates=["Date"])
    return df[df["City"].isin(cities or CITIES)].reset_index(drop=True)


def load_hourly(cities: list[str]) -> pd.DataFrame:
    """``city_hour.csv`` rows for the given cities."""
    df = pd.read_csv(_ensure_extracted(HOURLY_CSV_PATH), parse_dates=["Datetime"])
    return df[df["City"].isin(cities)].reset_index(drop=True)


def daily_series(city: str, raw: pd.DataFrame, hourly: pd.DataFrame | None = None,
                 target: str = "AQI") -> pd.Series:
    """Raw daily values of ``target`` (AQI or a pollutant column) for one city."""
    if target == "AQI":
        return daily_aqi(city, raw, hourly)
    if target not in TARGETS:
        raise ValueError(f"Unknown target {target!r}; expected one of {list(TARGETS)}")
    return raw[raw["City"] == city].set_index("Date")[target]


def daily_aqi(city: str, raw: pd.DataFrame, hourly: pd.DataFrame | None = None) -> pd.Series:
    """Daily AQI: published values, or recomputed from hourly data for excluded-pollutant cities."""
    exclude = AQI_EXCLUDED_POLLUTANTS.get(city)
    if not exclude:
        return raw[raw["City"] == city].set_index("Date")["AQI"]
    hourly = load_hourly([city]) if hourly is None else hourly
    return daily_aqi_from_hourly(hourly[hourly["City"] == city], exclude=exclude)


def _gap_lengths(mask: pd.Series) -> pd.Series:
    """For each NaN position, the length of the NaN run it belongs to (0 elsewhere)."""
    run_id = (mask != mask.shift()).cumsum()
    sizes = mask.groupby(run_id).transform("sum")
    return sizes.where(mask, 0)


def clean_series(s: pd.Series, max_gap: int = DEFAULT_MAX_GAP) -> pd.DataFrame:
    """Regularise to daily frequency, interpolate short gaps, keep last clean segment."""
    s = s.sort_index().asfreq("D")
    s = s.loc[s.first_valid_index(): s.last_valid_index()]

    missing = s.isna()
    long_gap = _gap_lengths(missing) > max_gap
    if long_gap.any():
        s = s.loc[long_gap[long_gap].index.max() + pd.Timedelta(days=1):]
        missing = missing.loc[s.index]

    filled = s.interpolate(method="time", limit_area="inside")
    return pd.DataFrame({"value": filled, "is_interpolated": missing})


def load_city_series(city: str, max_gap: int = DEFAULT_MAX_GAP, raw: pd.DataFrame | None = None,
                     hourly: pd.DataFrame | None = None, target: str = "AQI") -> pd.DataFrame:
    """Daily ``target`` for one city: DataFrame indexed by date with ``value`` and ``is_interpolated``."""
    raw = load_raw([city]) if raw is None else raw[raw["City"] == city]
    if raw.empty:
        raise ValueError(f"No rows for city {city!r}")
    out = clean_series(daily_series(city, raw, hourly, target), max_gap=max_gap)
    out.index.name = "date"
    return out


def load_all_cities(cities: list[str] | None = None, max_gap: int = DEFAULT_MAX_GAP,
                    target: str = "AQI") -> dict[str, pd.DataFrame]:
    """``{city: load_city_series(city)}`` for every selected city, reading the CSV once."""
    cities = cities or CITIES
    raw = load_raw(cities)
    recomputed = [c for c in cities if c in AQI_EXCLUDED_POLLUTANTS] if target == "AQI" else []
    hourly = load_hourly(recomputed) if recomputed else None
    return {c: load_city_series(c, max_gap=max_gap, raw=raw, hourly=hourly, target=target)
            for c in cities}


def load_city_pollutants(city: str, max_gap: int = DEFAULT_MAX_GAP) -> pd.DataFrame:
    """Daily pollutant concentrations for one city, short gaps interpolated.

    Not used by the AQI forecasters yet; provided for the health pipeline join.
    """
    raw = load_raw([city]).set_index("Date")[POLLUTANTS].sort_index().asfreq("D")
    return raw.interpolate(method="time", limit=max_gap, limit_area="inside")


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "AQI"
    for city, df in load_all_cities(target=target).items():
        print(f"{city:<10} {df.index.min().date()} -> {df.index.max().date()}  "
              f"n={len(df):>4}  interpolated={int(df['is_interpolated'].sum()):>3}")
