"""Request/response models for the public API.

Profile fields use the API/database naming (snake_case, matching the planned
Supabase ``profiles`` table) and are mapped to the health model's feature names in
``src.api.services``.
"""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Gender = Literal["F", "M"]
Condition = Literal["No Condition", "Asthma", "COPD", "HeartDisease", "Diabetes", "Hypertension"]
Occupation = Literal["Homemaker", "Indoor Worker", "Outdoor Worker", "Retired", "Student"]
AreaType = Literal["Commercial", "Industrial", "Residential"]
MaskUsage = Literal["No", "Sometimes", "Yes"]
RiskLevel = Literal["Low", "Moderate", "High", "Severe"]
Target = Literal["AQI", "PM2.5", "NO2"]

DISCLAIMER = ("Estimated risk for decision support only. This is not a medical diagnosis; "
              "consult a healthcare professional for medical advice.")


class Profile(BaseModel):
    """A user's health profile.

    The exposure fields (occupation, area type, mask usage, outdoor hours) are required
    along with the core fields: filling them with typical values badly understated risk
    (a 67-year-old COPD patient came out Low instead of Moderate). BMI, exercise and
    family history stay optional; missing ones are filled with typical values and
    reported back in ``imputed_fields``.
    """
    model_config = ConfigDict(extra="forbid")

    age: int = Field(ge=1, le=110)
    gender: Gender
    condition: Condition = Field(description="Pre-existing condition")
    smoker: bool
    occupation: Occupation
    area_type: AreaType
    mask_usage: MaskUsage
    outdoor_hours: float = Field(ge=0, le=24, description="Hours per day outdoors")
    bmi: float | None = Field(default=None, ge=10, le=70)
    exercise_hours: float | None = Field(default=None, ge=0, le=40, description="Hours per week")
    family_history: bool | None = Field(default=None, description="Family history of respiratory disease")


class RiskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    city: str
    horizon: int = Field(default=7, ge=1, le=30)
    profile: Profile


class ForecastDay(BaseModel):
    date: date
    aqi: float
    aqi_category: str
    pm25: float | None = None
    no2: float | None = None


class ModelInfo(BaseModel):
    model: str
    config: str
    selection: str | None = None


class ForecastResponse(BaseModel):
    city: str
    horizon: int
    origin_date: date = Field(description="Last day of observed data; forecasts start the day after")
    models: dict[str, ModelInfo]
    days: list[ForecastDay]


class RiskDay(ForecastDay):
    risk_level: RiskLevel
    confidence: float
    probabilities: dict[str, float]
    risk_score: float
    score_level: RiskLevel
    borderline: bool
    risk_range: str
    alert_level: RiskLevel


class RiskSummary(BaseModel):
    highest_alert_level: RiskLevel
    show_hospitals: bool = Field(description="True if any day's alert level is High or Severe")
    borderline_days: int
    days_by_level: dict[str, int]


class RiskResponse(BaseModel):
    city: str
    horizon: int
    origin_date: date
    feature_set: str
    health_models: dict[str, str]
    imputed_fields: list[str]
    warnings: list[str]
    disclaimer: str = DISCLAIMER
    summary: RiskSummary
    days: list[RiskDay]


class CityInfo(BaseModel):
    city: str
    origin_date: date
    targets: dict[str, str] = Field(description="Deployed model per forecast target")


class HealthStatus(BaseModel):
    status: Literal["ok"]
    cities: int
    forecasters: int
    health_models: list[str]
    startup_seconds: float
