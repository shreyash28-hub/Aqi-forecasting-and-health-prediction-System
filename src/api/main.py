"""FastAPI backend: public forecast, leaderboard and risk endpoints.

Run locally::

    uvicorn src.api.main:app --reload            # http://localhost:8000/docs

Environment:
    ALLOWED_ORIGINS   comma-separated CORS origins (default: http://localhost:3000)

Everything here is public (no login). Saving profiles and prediction history comes
with the Supabase integration.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from src.api.schemas import CityInfo, ForecastResponse, HealthStatus, RiskRequest, RiskResponse, Target
from src.api.services import MAX_HORIZON, ModelService, UnknownCity, forecast_leaderboard, health_leaderboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.models = ModelService.load()
    yield


app = FastAPI(
    title="AQI Forecast & Health Risk API",
    version="0.1.0",
    description="City air-quality forecasts (AQI, PM2.5, NO2) and personalised, estimated health "
                "risk for decision support. Not a medical diagnosis.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",") if o.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _svc(request: Request) -> ModelService:
    return request.app.state.models


def _unknown_city(city: str, svc: ModelService) -> HTTPException:
    return HTTPException(404, f"Unknown city {city!r}. Available: {sorted(svc.forecasts)}")


@app.get("/api/health", response_model=HealthStatus, tags=["meta"])
def health(request: Request):
    svc = _svc(request)
    return {"status": "ok", "cities": len(svc.forecasts), "forecasters": len(svc.forecasters),
            "health_models": sorted(f"{t}/{fs}" for t, fs in svc.health.models),
            "startup_seconds": svc.startup_seconds}


@app.get("/api/cities", response_model=list[CityInfo], tags=["forecast"])
def cities(request: Request):
    return _svc(request).cities()


@app.get("/api/forecast/{city}", response_model=ForecastResponse, tags=["forecast"])
def forecast(request: Request, city: str,
             horizon: int = Query(7, ge=1, le=MAX_HORIZON, description="Days ahead (7 or 30 in the UI)")):
    svc = _svc(request)
    try:
        return svc.forecast(city, horizon)
    except UnknownCity:
        raise _unknown_city(city, svc)


@app.post("/api/risk/predict", response_model=RiskResponse, tags=["risk"])
def predict_risk(request: Request, body: RiskRequest):
    """Per-day estimated health risk for a profile and a city's forecast. Nothing is stored."""
    svc = _svc(request)
    try:
        return svc.risk(body.city, body.horizon, body.profile.model_dump())
    except UnknownCity:
        raise _unknown_city(body.city, svc)


@app.get("/api/profile/schema", tags=["risk"])
def profile_schema(request: Request):
    """Fields, allowed values and defaults for the profile form."""
    return _svc(request).profile_schema()


@app.get("/api/leaderboard/forecast", tags=["leaderboard"])
def leaderboard_forecast(target: Target = "AQI"):
    return forecast_leaderboard(target)


@app.get("/api/leaderboard/health", tags=["leaderboard"])
def leaderboard_health(task: Literal["classification", "regression"] | None = None):
    board = health_leaderboard()
    if task:
        board["tasks"] = {task: board["tasks"][task]}
    return board
