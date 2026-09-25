# Data

## `Aqi.zip` (not in git — download it yourself)

The AQI pipeline needs the Kaggle dataset **"Air Quality Data in India (2015-2020)"**
(CPCB data, by Vopani / rohanrao):
https://www.kaggle.com/datasets/rohanrao/air-quality-data-in-india

Download the dataset archive and save it as **`data/Aqi.zip`** before running the
pipeline. It's ~76 MB and publicly re-downloadable, so it's kept out of git.

`src/data_loader.py` extracts what it needs from the zip on first use:
- `city_day.csv`: daily AQI and pollutants per city (main forecasting input)
- `city_hour.csv`: hourly data, used to recompute Ahmedabad's AQI without CO

Both extracted files are git-ignored.

## `synthetic_person_health.csv` (tracked)

Health-risk training data for the health prediction pipeline. It is a constructed
dataset: real city-and-date AQI/pollutant values from `city_day.csv` joined to
synthetic person profiles and a documented risk-scoring formula (see `CLAUDE.md`).
