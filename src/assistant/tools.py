"""Tools the assistant calls to ground its answers in Airware's own data.

``build_tools`` returns the tools for one request, bound to the server's models and, when
the user is signed in with a saved profile, to that profile. Tools return compact JSON
text; errors come back as text the model can explain (e.g. an unknown city), not as
exceptions. Every call is recorded in ``ToolLog`` so the API can report what was used.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Literal

from anthropic import beta_tool

from src.api import hospitals
from src.api.services import ModelService, UnknownCity
from src.assistant import knowledge

Topic = Literal["aqi_categories", "masks", "exercise_and_outdoor_activity", "children", "older_adults",
                "pregnancy", "asthma_copd", "heart_conditions", "diabetes_hypertension", "indoor_air",
                "commuting_and_travel", "warning_signs"]
PROFILE_FOR_MODEL = ("age", "gender", "condition", "smoker", "bmi", "exercise_hours", "outdoor_hours",
                     "mask_usage", "occupation", "area_type", "family_history")
MAX_DAYS = 30


@dataclass
class ToolLog:
    calls: list[str] = field(default_factory=list)


def _json(obj) -> str:
    return json.dumps(obj, default=str, ensure_ascii=False, separators=(",", ":"))


def _days(days: int) -> int:
    return max(1, min(int(days), MAX_DAYS))


def build_tools(svc: ModelService, profile: dict | None, log: ToolLog) -> list:
    cities = sorted(svc.forecasts)

    def unknown(city: str) -> str:
        return f"Unknown city {city!r}. Airware covers: {', '.join(cities)}."

    @beta_tool
    def get_air_forecast(city: str, days: int = 7) -> str:
        """Daily air-quality forecast for a city, starting today.

        AQI on India's CPCB scale with its category, plus PM2.5 and NO2 in µg/m³. Call this for any question about upcoming air quality, the best
        or worst day, or whether a day will be safe. Never state forecast numbers without calling it.

        Args:
            city: One of Delhi, Bengaluru, Chennai, Hyderabad, Lucknow, Ahmedabad.
            days: How many days ahead to return, 1-30 (default 7).
        """
        log.calls.append("get_air_forecast")
        try:
            f = svc.forecast(city, _days(days))
        except UnknownCity:
            return unknown(city)
        return _json({"city": f["city"], "readings_as_of": f["readings_as_of"],
                      "models": {t: m["model"] for t, m in f["models"].items()}, "days": f["days"]})

    @beta_tool
    def get_recent_measurements(city: str, days: int = 7) -> str:
        """Measured air quality for recent days and today so far.

        Daily AQI, PM2.5 and NO2 for the last few complete days, and today's readings so far. Call this for questions about what the air has been like recently or right now.

        Args:
            city: One of Delhi, Bengaluru, Chennai, Hyderabad, Lucknow, Ahmedabad.
            days: How many past days to return, 1-30 (default 7).
        """
        log.calls.append("get_recent_measurements")
        try:
            return _json(svc.observed(city, _days(days)))
        except UnknownCity:
            return unknown(city)

    @beta_tool
    def get_my_health_risk(city: str, days: int = 7) -> str:
        """The signed-in user's estimated health risk for each forecast day.

        From their saved health profile and the city's forecast: risk level (Low, Moderate, High, Severe), risk score, the model's
        confidence, whether the day is borderline between two levels, and the alert level. Call this
        whenever the user asks about their own safety, their risk, or what they personally should do.

        Args:
            city: One of Delhi, Bengaluru, Chennai, Hyderabad, Lucknow, Ahmedabad.
            days: How many days ahead, 1-30 (default 7).
        """
        log.calls.append("get_my_health_risk")
        if profile is None:
            return ("The user has no saved health profile, so no personal estimate is possible. "
                    "Suggest saving one on the Profile page, and answer with general guidance meanwhile.")
        model_profile = {k: profile.get(k) for k in PROFILE_FOR_MODEL}
        try:
            r = svc.risk(city, _days(days), model_profile)
        except UnknownCity:
            return unknown(city)
        except ValueError as e:
            return f"The saved profile could not be used: {e}"
        keep = ("date", "aqi", "aqi_category", "risk_level", "risk_score", "confidence", "borderline",
                "risk_range", "alert_level")
        about = {k: profile.get(k) for k in ("age", "condition", "smoker", "occupation", "outdoor_hours", "mask_usage")}
        return _json({"city": r["city"], "profile": about, "summary": r["summary"],
                      "filled_with_typical_values": r["imputed_fields"],
                      "days": [{k: d[k] for k in keep} for d in r["days"]]})

    @beta_tool
    def get_precautions(topic: Topic) -> str:
        """Curated, general precautions for one topic.

        Call this before giving advice on that topic and base the advice on it.

        Args:
            topic: aqi_categories (what each AQI band means), masks, exercise_and_outdoor_activity,
                children, older_adults, pregnancy, asthma_copd, heart_conditions, diabetes_hypertension,
                indoor_air, commuting_and_travel, warning_signs (when to get medical help).
        """
        log.calls.append("get_precautions")
        return knowledge.get(topic) or f"No guidance stored for {topic!r}."

    @beta_tool
    def find_nearby_hospitals(city: str, limit: int = 5) -> str:
        """Hospitals near the city centre, with contact details.

        Phone numbers, address and distance (OpenStreetMap data). Call this when the user asks where to get care, or their risk is High or Severe. Airware shows
        contact details only; it cannot book appointments.

        Args:
            city: One of Delhi, Bengaluru, Chennai, Hyderabad, Lucknow, Ahmedabad.
            limit: How many hospitals to return, 1-10 (default 5).
        """
        log.calls.append("find_nearby_hospitals")
        try:
            name = svc.canonical_city(city)
        except UnknownCity:
            return unknown(city)
        lat, lon = hospitals.CITY_CENTRES[name]
        found = hospitals.from_stored(lat, lon, 10) or []
        found.sort(key=lambda h: (not h.get("phones"), h["distance_km"]))   # ones you can call first
        keep = ("name", "phones", "address", "distance_km", "emergency", "website")
        return _json({"city": name, "note": "Contact details only. In an emergency call 112 (or 108 for an ambulance).",
                      "hospitals": [{k: h.get(k) for k in keep} for h in found[: max(1, min(int(limit), 10))]]})

    return [get_air_forecast, get_recent_measurements, get_my_health_risk, get_precautions, find_nearby_hospitals]
