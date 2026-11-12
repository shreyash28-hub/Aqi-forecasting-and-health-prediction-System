"""Signed-in endpoint for the air-quality assistant (``src/assistant``).

``POST /api/me/assistant`` answers one question, using the user's saved profile (if any)
for personal answers. Signed-in only, with a per-user daily limit, because every question
is a paid model call. The question and the profile details needed to answer it are sent
to the model provider (Anthropic); Airware stores neither.

``ASSISTANT_DAILY_LIMIT`` (default 30) sets the limit; the counter is in memory and resets
at midnight IST (and when the server restarts).
"""
from __future__ import annotations

import os
import threading
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request

from src.api.me import PROFILE_COLUMNS, _load_profile, _supabase, _svc, current_user
from src.api.schemas import AssistantRequest, AssistantResponse
from src.api.supabase_client import AuthUser
from src.assistant.chat import IST, AssistantError

router = APIRouter(prefix="/api/me", tags=["me (sign-in required)"])

_usage: dict[tuple[str, str], int] = {}
_usage_lock = threading.Lock()


def daily_limit() -> int:
    return int(os.getenv("ASSISTANT_DAILY_LIMIT", "30"))


def _take(user_id: str) -> int:
    """Count one question for today; returns how many are left, or raises 429."""
    today = datetime.now(IST).date().isoformat()
    with _usage_lock:
        for key in [k for k in _usage if k[1] != today]:   # forget earlier days
            del _usage[key]
        used = _usage.get((user_id, today), 0)
        if used >= daily_limit():
            raise HTTPException(429, f"You've used today's {daily_limit()} questions. The limit resets at midnight IST.")
        _usage[(user_id, today)] = used + 1
        return daily_limit() - used - 1


def _give_back(user_id: str) -> None:
    today = datetime.now(IST).date().isoformat()
    with _usage_lock:
        if _usage.get((user_id, today), 0) > 0:
            _usage[(user_id, today)] -= 1


@router.post("/assistant", response_model=AssistantResponse)
def ask(request: Request, body: AssistantRequest, user: AuthUser = Depends(current_user)):
    assistant = getattr(request.app.state, "assistant", None)
    if assistant is None:
        raise HTTPException(503, "The assistant isn't configured on this server (ANTHROPIC_API_KEY).")
    sb, svc = _supabase(request), _svc(request)
    row = _load_profile(sb, user)
    profile = {k: row.get(k) for k in PROFILE_COLUMNS if k != "city"} if row else None
    city = body.city or (row or {}).get("city") or "Delhi"

    left = _take(user.id)
    try:
        reply = assistant.answer(svc, body.message, [t.model_dump() for t in body.history], city, profile)
    except AssistantError as e:
        _give_back(user.id)            # a failed call doesn't use up a question
        raise HTTPException(e.status, e.message)
    if reply.emergency:
        _give_back(user.id)            # nor does the fixed emergency reply
        left += 1
    return {"reply": reply.text, "emergency": reply.emergency, "tools_used": reply.tools_used,
            "model": reply.model, "remaining_today": left}
