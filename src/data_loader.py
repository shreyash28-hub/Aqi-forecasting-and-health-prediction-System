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
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
ZIP_PATH = DATA_DIR / "Aqi.zip"
CSV_PATH = DATA_DIR / "city_day.csv"

CITIES = ["Delhi", "Bengaluru", "Chennai", "Hyderabad", "Lucknow", "Ahmedabad"]
POLLUTANTS = ["PM2.5", "PM10", "NO2", "SO2", "O3", "CO"]
DEFAULT_MAX_GAP = 21  # days


def ensure_city_day_csv() -> Path:
    """Extract ``city_day.csv`` from ``Aqi.zip`` if it isn't already on disk."""
    if not CSV_PATH.exists():
        if not ZIP_PATH.exists():
            raise FileNotFoundError(f"Neither {CSV_PATH} nor {ZIP_PATH} exists.")
        with zipfile.ZipFile(ZIP_PATH) as zf:
            zf.extract("city_day.csv", DATA_DIR)
    return CSV_PATH


def load_raw(cities: list[str] | None = None) -> pd.DataFrame:
    """Raw ``city_day.csv`` rows for the selected cities (default: the six)."""
    df = pd.read_csv(ensure_city_day_csv(), parse_dates=["Date"])
    return df[df["City"].isin(cities or CITIES)].reset_index(drop=True)


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
    return pd.DataFrame({"aqi": filled, "is_interpolated": missing})


def load_city_series(city: str, max_gap: int = DEFAULT_MAX_GAP,
                     raw: pd.DataFrame | None = None) -> pd.DataFrame:
    """Daily AQI for one city: DataFrame indexed by date with ``aqi`` and ``is_interpolated``."""
    raw = load_raw([city]) if raw is None else raw[raw["City"] == city]
    if raw.empty:
        raise ValueError(f"No rows for city {city!r}")
    out = clean_series(raw.set_index("Date")["AQI"], max_gap=max_gap)
    out.index.name = "date"
    return out


def load_all_cities(cities: list[str] | None = None,
                    max_gap: int = DEFAULT_MAX_GAP) -> dict[str, pd.DataFrame]:
    """``{city: load_city_series(city)}`` for every selected city, reading the CSV once."""
    cities = cities or CITIES
    raw = load_raw(cities)
    return {c: load_city_series(c, max_gap=max_gap, raw=raw) for c in cities}


def load_city_pollutants(city: str, max_gap: int = DEFAULT_MAX_GAP) -> pd.DataFrame:
    """Daily pollutant concentrations for one city, short gaps interpolated.

    Not used by the AQI forecasters yet; provided for the health pipeline join.
    """
    raw = load_raw([city]).set_index("Date")[POLLUTANTS].sort_index().asfreq("D")
    return raw.interpolate(method="time", limit=max_gap, limit_area="inside")


if __name__ == "__main__":
    for city, df in load_all_cities().items():
        print(f"{city:<10} {df.index.min().date()} -> {df.index.max().date()}  "
              f"n={len(df):>4}  interpolated={int(df['is_interpolated'].sum()):>3}")
