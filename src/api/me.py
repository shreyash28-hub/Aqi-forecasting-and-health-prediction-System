"""Signed-in user endpoints: saved profile, prediction runs and history.

Every request needs ``Authorization: Bearer <Supabase access token>`` (the frontend
gets it from supabase-js after sign-in). Table access is made with that token, so
Row Level Security guarantees users only ever touch their own rows.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder

from src.api.schemas import (HistoryDetail, HistoryItem, MyRiskRequest, ProfileRecord, SavedProfile,
                             SavedRiskResponse)
from src.api.services import ModelService, UnknownCity, score_level_of, summarize
from src.api.supabase_client import AuthUser, NotAuthenticated, SupabaseClient, SupabaseError

router = APIRouter(prefix="/api/me", tags=["me (sign-in required)"])

PROFILE_COLUMNS = list(SavedProfile.model_fields)
AIR_KEYS = ("date", "aqi", "aqi_category", "pm25", "no2")
RISK_KEYS = ("risk_level", "confidence", "probabilities", "risk_score", "borderline", "risk_range", "alert_level")


def _supabase(request: Request) -> SupabaseClient:
    sb = request.app.state.supabase
    if sb is None:
        raise HTTPException(503, "Accounts are not configured on this server (SUPABASE_URL / SUPABASE_ANON_KEY).")
    return sb


def current_user(request: Request, authorization: str | None = Header(default=None)) -> AuthUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Sign in required", headers={"WWW-Authenticate": "Bearer"})
    try:
        return _supabase(request).get_user(authorization.split(" ", 1)[1].strip())
    except NotAuthenticated as e:
        raise HTTPException(401, e.message, headers={"WWW-Authenticate": "Bearer"})
    except SupabaseError as e:
        raise HTTPException(e.status, e.message)


def _db(call, *args, **kwargs):
    try:
        return call(*args, **kwargs)
    except NotAuthenticated as e:
        raise HTTPException(401, e.message, headers={"WWW-Authenticate": "Bearer"})
    except SupabaseError as e:
        raise HTTPException(e.status, e.message)


def _svc(request: Request) -> ModelService:
    return request.app.state.models


def _load_profile(sb: SupabaseClient, user: AuthUser) -> dict | None:
    rows = _db(sb.select, user, "profiles", select="*", user_id=f"eq.{user.id}")
    return rows[0] if rows else None


# ---------------------------------------------------------------------------- profile

@router.get("/profile", response_model=ProfileRecord)
def get_profile(request: Request, user: AuthUser = Depends(current_user)):
    profile = _load_profile(_supabase(request), user)
    if profile is None:
        raise HTTPException(404, "No profile yet")
    return profile


@router.put("/profile", response_model=ProfileRecord)
def save_profile(request: Request, body: SavedProfile, user: AuthUser = Depends(current_user)):
    """Create or replace the user's profile (filled once, reused on every visit)."""
    row = body.model_dump()
    if row.get("city"):
        try:
            row["city"] = _svc(request).canonical_city(row["city"])
        except UnknownCity:
            raise HTTPException(422, f"Unknown city {row['city']!r}. Available: {sorted(_svc(request).forecasts)}")
    saved = _db(_supabase(request).upsert, user, "profiles", {**row, "user_id": user.id}, on_conflict="user_id")
    return saved[0]


# ---------------------------------------------------------------------------- prediction runs

@router.post("/risk", response_model=SavedRiskResponse)
def run_prediction(request: Request, body: MyRiskRequest, user: AuthUser = Depends(current_user)):
    """Predict with the saved profile and save the run to the user's history."""
    sb, svc = _supabase(request), _svc(request)
    profile = _load_profile(sb, user)
    if profile is None:
        raise HTTPException(409, "Save a profile first (PUT /api/me/profile)")
    city = body.city or profile.get("city")
    if not city:
        raise HTTPException(422, "No city given and none saved in the profile")
    try:
        result = svc.risk(city, body.horizon, {k: profile.get(k) for k in PROFILE_COLUMNS if k != "city"})
    except UnknownCity:
        raise HTTPException(404, f"Unknown city {city!r}. Available: {sorted(svc.forecasts)}")

    days = jsonable_encoder(result["days"])
    run = _db(sb.insert, user, "saved_forecasts", [{
        "user_id": user.id, "city": result["city"], "horizon": result["horizon"],
        "origin_date": str(result["origin_date"]),
        "model_used": {t: m["model"] for t, m in svc.model_info(result["city"]).items()},
        "forecast_json": [{k: d.get(k) for k in AIR_KEYS} for d in days],
    }])[0]
    snapshot_profile = {k: profile.get(k) for k in PROFILE_COLUMNS if k != "city"}
    model_used = {"feature_set": result["feature_set"], **result["health_models"]}
    rows = [{
        "user_id": user.id, "forecast_id": run["id"], "city": result["city"],
        "date_of_prediction": d["date"], **{k: d[k] for k in RISK_KEYS}, "model_used": model_used,
        "input_snapshot_json": {"profile": snapshot_profile, "imputed_fields": result["imputed_fields"],
                                "air": {k: d.get(k) for k in ("aqi", "pm25", "no2")}},
    } for d in days]
    try:
        _db(sb.insert, user, "risk_predictions", rows)
    except HTTPException:
        # Don't leave a run without its days in the history.
        _db(sb.delete, user, "saved_forecasts", id=f"eq.{run['id']}")
        raise
    return {**result, "forecast_id": run["id"], "predicted_at": run["generated_at"]}


# ---------------------------------------------------------------------------- history

HISTORY_SELECT = ("id,city,horizon,origin_date,generated_at,model_used,forecast_json,"
                  "risk_predictions(date_of_prediction,risk_level,confidence,probabilities,risk_score,"
                  "borderline,risk_range,alert_level,model_used)")


def _history_days(run: dict) -> list[dict]:
    air = {d["date"]: d for d in run.get("forecast_json") or []}
    days = []
    for p in sorted(run["risk_predictions"], key=lambda p: p["date_of_prediction"]):
        a = air.get(p["date_of_prediction"], {})
        days.append({**{k: a.get(k) for k in AIR_KEYS}, "date": p["date_of_prediction"],
                     **{k: p[k] for k in RISK_KEYS}, "score_level": score_level_of(p["risk_score"])})
    return days


def _history_item(run: dict) -> dict:
    return {"forecast_id": run["id"], "city": run["city"], "horizon": run["horizon"],
            "origin_date": run["origin_date"], "predicted_at": run["generated_at"],
            "summary": summarize(run["risk_predictions"])}


@router.get("/history", response_model=list[HistoryItem])
def list_history(request: Request, limit: int = Query(20, ge=1, le=100), user: AuthUser = Depends(current_user)):
    runs = _db(_supabase(request).select, user, "saved_forecasts", select=HISTORY_SELECT,
               order="generated_at.desc", limit=str(limit))
    return [_history_item(r) for r in runs if r["risk_predictions"]]


@router.get("/history/{forecast_id}", response_model=HistoryDetail)
def get_history_run(request: Request, forecast_id: UUID, user: AuthUser = Depends(current_user)):
    runs = _db(_supabase(request).select, user, "saved_forecasts", select=HISTORY_SELECT, id=f"eq.{forecast_id}")
    if not runs or not runs[0]["risk_predictions"]:
        raise HTTPException(404, "Run not found")
    run = runs[0]
    models = {"forecast": run["model_used"], "health": run["risk_predictions"][0]["model_used"]}
    return {**_history_item(run), "models": models, "days": _history_days(run)}


@router.delete("/history/{forecast_id}", status_code=204)
def delete_history_run(request: Request, forecast_id: UUID, user: AuthUser = Depends(current_user)):
    deleted = _db(_supabase(request).delete, user, "saved_forecasts", id=f"eq.{forecast_id}")
    if not deleted:
        raise HTTPException(404, "Run not found")
