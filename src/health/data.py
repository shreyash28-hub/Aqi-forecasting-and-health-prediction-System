"""Health-risk dataset loading and feature definitions.

Dataset note: ``data/synthetic_person_health.csv`` is a constructed dataset. Its
air-quality columns (AQI, PM2_5, PM10, NO2, SO2, O3) are real values sampled from
``city_day.csv`` by city and date. The person profiles and the risk targets are
synthetic, generated with a documented formula (vulnerability x effective exposure
+ noise, bucketed into four levels). See CLAUDE.md for the full construction.

Columns deliberately *not* used as features:
* ``VulnerabilityScore``: an intermediate term of the target formula (leakage).
* ``HospitalVisitsLastYear``: derived from the risk level (leakage).
* ``PersonID``, ``Name``: identifiers. ``Date``, ``City``: represented by the air
  values; keeping them would tie the model to the training cities and dates.
* ``BMICategory``: a binning of ``BMI``. ``IncomeLevel``, ``YearsLivedInCity``: not
  collected in the user profile and not part of the risk score.
"""
from __future__ import annotations

import pandas as pd

from src.data_loader import DATA_DIR

HEALTH_CSV = DATA_DIR / "synthetic_person_health.csv"

RISK_LEVELS = ["Low", "Moderate", "High", "Severe"]  # ordered; class index = position
# Boundaries of HealthRiskScore between consecutive levels, as observed in the data
# (Low < 1.0 <= Moderate < 1.8 <= High < 2.8 <= Severe).
RISK_SCORE_CUTS = [1.0, 1.8, 2.8]

CLS_TARGET = "HealthRiskLevel"
REG_TARGET = "HealthRiskScore"

PERSON_NUMERIC = ["Age", "BMI", "ExerciseHoursPerWeek", "OutdoorExposureHours"]
PERSON_CATEGORICAL = ["Gender", "Occupation", "AreaType", "PreexistingCondition",
                      "FamilyHistoryRespiratory", "Smoker", "MaskUsage"]
POLLUTANTS = ["PM2_5", "PM10", "NO2", "SO2", "O3"]

# Air features per set. "aqi_pm25_no2" is the primary deployed set: PM2.5 and NO2 are
# forecast for all six cities and carry the pollutant signal (adding PM10/SO2/O3 in
# "full" doesn't help). "aqi_only" is the fallback when pollutant forecasts are missing.
FEATURE_SETS = {
    "aqi_only": {"numeric": PERSON_NUMERIC + ["AQI"], "categorical": PERSON_CATEGORICAL},
    "aqi_pm25_no2": {"numeric": PERSON_NUMERIC + ["AQI", "PM2_5", "NO2"], "categorical": PERSON_CATEGORICAL},
    "full": {"numeric": PERSON_NUMERIC + ["AQI"] + POLLUTANTS, "categorical": PERSON_CATEGORICAL},
}
PRIMARY_FEATURE_SET = "aqi_pm25_no2"
FALLBACK_FEATURE_SET = "aqi_only"
DEPLOY_FEATURE_SETS = [PRIMARY_FEATURE_SET, FALLBACK_FEATURE_SET]
# Forecast column (src.model_store.forecast_air) -> health feature name.
AIR_COLUMNS = {"aqi": "AQI", "pm25": "PM2_5", "no2": "NO2"}

# Allowed values for categorical inputs (validated at prediction time).
CATEGORIES = {
    "Gender": ["F", "M"],
    "Occupation": ["Homemaker", "Indoor Worker", "Outdoor Worker", "Retired", "Student"],
    "AreaType": ["Commercial", "Industrial", "Residential"],
    "PreexistingCondition": ["Asthma", "COPD", "Diabetes", "HeartDisease", "Hypertension", "No Condition"],
    "FamilyHistoryRespiratory": ["No", "Yes"],
    "Smoker": ["No", "Yes"],
    "MaskUsage": ["No", "Sometimes", "Yes"],
}


def load_health_dataset() -> pd.DataFrame:
    df = pd.read_csv(HEALTH_CSV)
    unknown = {c: sorted(set(df[c]) - set(v)) for c, v in CATEGORIES.items() if set(df[c]) - set(v)}
    if unknown:
        raise ValueError(f"Unexpected category values in {HEALTH_CSV.name}: {unknown}")
    return df


def score_to_level(score) -> pd.Series:
    """Map risk scores to levels using the dataset's own boundaries."""
    return pd.Series(pd.cut(pd.Series(score, dtype=float), [-float("inf"), *RISK_SCORE_CUTS, float("inf")],
                            labels=RISK_LEVELS, right=False).astype(str))
