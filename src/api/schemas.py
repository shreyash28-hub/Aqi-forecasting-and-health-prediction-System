"""Request/response models for the public API.

Profile fields use the API/database naming (snake_case, matching the planned
Supabase ``profiles`` table) and are mapped to the health model's feature names in
``src.api.services``.
"""
from __future__ import annotations

from datetime import date, datetime
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


class ObservedDay(BaseModel):
    date: date
    aqi: float | None = Field(default=None, description="Daily AQI from station readings; null if too few hours")
    pm25: float | None = None
    no2: float | None = None


class TodaySoFar(BaseModel):
    date: date
    as_of: str = Field(description="Time (IST) of the latest reading")
    hours: int
    aqi: float | None = None
    pm25: float | None = None
    no2: float | None = None


class ObservedResponse(BaseModel):
    city: str
    days: list[ObservedDay] = Field(description="Complete past days, oldest first")
    today_so_far: TodaySoFar | None = Field(default=None, description="Average of today's readings so far")


class ModelInfo(BaseModel):
    model: str
    config: str
    selection: str | None = None


class ForecastResponse(BaseModel):
    city: str
    horizon: int
    origin_date: date = Field(description="Last day of observed data; forecasts start the day after")
    models: dict[str, ModelInfo]
    readings_as_of: str | None = Field(default=None, description=(
        "Time (IST) of the latest station reading used to adjust today's and the next days' "
        "forecast (see src/nowcast.py); null if the forecast is the model's own"))
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
    accounts_enabled: bool
    assistant_enabled: bool = Field(default=False, description="An Anthropic API key is set, so /api/me/assistant answers")
    live: dict | None = Field(default=None, description=(
        "Live forecasts: where they are served from (precomputed export or the models), their "
        "issue date, and the last bundle and readings refreshes with any error"))


# ---------------------------------------------------------------------------- signed-in user

class SavedProfile(Profile):
    """Profile as stored in Supabase; ``city`` remembers the user's last selected city."""
    city: str | None = None


class ProfileRecord(SavedProfile):
    """A stored profile as returned to its owner (database-only columns are dropped)."""
    model_config = ConfigDict(extra="ignore")

    updated_at: datetime | None = None


class MyRiskRequest(BaseModel):
    """Run a prediction with the saved profile. ``city`` defaults to the profile's city."""
    model_config = ConfigDict(extra="forbid")

    city: str | None = None
    horizon: int = Field(default=7, ge=1, le=30)


class SavedRiskResponse(RiskResponse):
    forecast_id: str = Field(description="History id of this run")
    predicted_at: datetime


class HistoryItem(BaseModel):
    forecast_id: str
    city: str
    horizon: int
    origin_date: date
    predicted_at: datetime
    summary: RiskSummary


class HistoryDetail(HistoryItem):
    models: dict
    days: list[RiskDay]


# ---------------------------------------------------------------------------- assistant

class AssistantTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class AssistantRequest(BaseModel):
    """One question to the assistant. The browser sends the recent turns of the conversation;
    nothing is stored on the server."""
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=1000)
    history: list[AssistantTurn] = Field(default_factory=list, max_length=12)
    city: str | None = Field(default=None, description="City selected on the site; defaults to the profile's city")


class AssistantResponse(BaseModel):
    reply: str = Field(description="Markdown text")
    emergency: bool = Field(description="True when the message described an emergency (fixed reply, no model call)")
    tools_used: list[str]
    model: str | None
    remaining_today: int = Field(description="Questions left today for this user")
    disclaimer: str = DISCLAIMER
