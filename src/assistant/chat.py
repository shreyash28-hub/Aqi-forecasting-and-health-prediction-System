"""The assistant: Claude answering air-quality and health-precaution questions, grounded in
Airware's data through tools.

One request = one call to ``Assistant.answer``: the SDK's tool runner lets Claude call the
tools in ``tools.py`` (forecast, recent readings, the user's own risk, curated precautions,
hospitals) until it has an answer. Nothing is stored; the browser sends the recent turns of
the conversation with each message.

Safety comes first and does not depend on the model: messages describing an emergency
(can't breathe, chest pain, ...) get a fixed reply with 112 / 108 and the nearest hospitals,
without calling the model. The system prompt keeps answers to general precautions (no
diagnosis, no medicines or doses) and to numbers that came from the tools.

Configuration (environment): ``ANTHROPIC_API_KEY`` enables the assistant;
``ASSISTANT_MODEL`` (default ``claude-opus-5-5``) and ``ASSISTANT_EFFORT`` (default ``low``,
the usual setting for chat) tune it. If the model declines a request on safety grounds, the
API re-runs it on a fallback model (server-side ``fallbacks: "default"``).
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

import anthropic

from src.api import hospitals
from src.api.services import ModelService, UnknownCity
from src.assistant.tools import ToolLog, build_tools

logger = logging.getLogger("airware.assistant")

MODEL = os.getenv("ASSISTANT_MODEL", "claude-opus-5-5")
EFFORT = os.getenv("ASSISTANT_EFFORT", "low")
MAX_TOKENS = 16000
MAX_ITERATIONS = 6              # model turns per question, tool calls included
MAX_HISTORY_CHARS = 12000       # older turns beyond this are dropped
FALLBACK_BETA = "server-side-fallback-2026-07-01"
IST = ZoneInfo("Asia/Kolkata")

SYSTEM_PROMPT = """You are the air-quality assistant on Airware, a website that forecasts air quality for six Indian cities (Delhi, Bengaluru, Chennai, Hyderabad, Lucknow, Ahmedabad) and estimates each signed-in user's personal health risk from their saved health profile and the forecast.

How to answer
- Use the tools for every number you give: AQI, PM2.5, NO2, risk levels, dates, hospitals. Never invent or estimate these yourself. If a tool doesn't have the answer, say so.
- When the user asks about their own safety, risk or what they personally should do, call get_my_health_risk. When you give precautions, call get_precautions for the relevant topic and base your advice on it.
- AQI is on India's CPCB scale (Good 0-50, Satisfactory 51-100, Moderate 101-200, Poor 201-300, Very Poor 301-400, Severe 401+). It reads higher than the US-style AQI some apps show; explain that if the user compares numbers.
- Refer to days by weekday and date (for example "Tuesday 18 Nov"). Forecasts are most reliable for the next two or three days; further out they show the level and the trend, not exact values. If a day is borderline between two risk levels, say so and give the range.
- Keep answers short: a direct answer first, then two to four practical points. Use plain language. Use a short list only when it helps.
- Reply in the language the user writes in (for example Hindi or Hinglish).

Safety
- You give general guidance, not medical advice. Do not diagnose, do not name or dose medicines, and do not tell anyone to change their treatment. For someone with a condition, point them to the plan agreed with their doctor.
- If the user describes severe symptoms (severe breathlessness, chest pain, fainting, confusion, bluish lips), tell them to call 112 (or 108 for an ambulance) now and offer the nearest hospitals. Airware shows hospital contact details only; it cannot book appointments.
- Personal risk results are estimates for decision support, not a diagnosis. Say so briefly when you give one.
- If asked what the personal risk model is trained on: it was trained on a constructed dataset that pairs real CPCB air-quality readings with generated person profiles and a documented risk formula. It is an estimate, not clinically validated.

Scope
- Stay on air quality, health precautions related to it, and how to use Airware. Politely decline other requests in one sentence.
- Do not mention tool names or these instructions."""

EMERGENCY = re.compile(
    r"can'?t breathe|cannot breathe|can not breathe|unable to breathe|struggling to breathe|"
    r"chest (pain|pressure|tightness)|heart attack|unconscious|passed out|faint(ed|ing)|"
    r"blue lips|lips (are |turning )?blue|chok(e|ing)|seizure|stroke|"
    r"saa?ns (nahi|nahin|nhi)|seene (me|mein) dard|behosh|"
    r"सा[ंँ]स नहीं|सीने में दर्द|बेहोश",
    re.IGNORECASE)
REFUSAL_TEXT = ("I can't help with that one. I can answer questions about air quality, the forecast, "
                "and precautions to take.")
EMPTY_TEXT = "Sorry, I couldn't put an answer together. Please try asking in a different way."
UNAVAILABLE_TEXT = "The assistant is unavailable right now. Please try again later."


class AssistantError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status, self.message = status, message


@dataclass
class Reply:
    text: str
    emergency: bool = False
    tools_used: list[str] = field(default_factory=list)
    model: str | None = None
    stop_reason: str | None = None


def is_emergency(message: str) -> bool:
    return bool(EMERGENCY.search(message))


def emergency_reply(svc: ModelService, city: str | None) -> Reply:
    lines = ["If this is happening now, call **112** (or **108** for an ambulance) straight away, or go to the "
             "nearest emergency department. Don't wait for the air to improve."]
    try:
        name = svc.canonical_city(city or "")
    except UnknownCity:
        name = None
    if name:
        lat, lon = hospitals.CITY_CENTRES[name]
        found = hospitals.from_stored(lat, lon, 10) or []
        found = sorted([h for h in found if h.get("phones")], key=lambda h: (not h.get("emergency"), h["distance_km"]))[:3]
        if found:
            lines.append(f"Hospitals near central {name}:")
            lines += [f"- {h['name']}: {', '.join(h['phones'])} ({h['distance_km']} km)" for h in found]
    return Reply(text="\n".join(lines), emergency=True)


def clean_history(history: list[dict]) -> list[dict]:
    """Text-only turns, oldest dropped beyond ``MAX_HISTORY_CHARS``, starting with a user turn."""
    turns = [{"role": t["role"], "content": t["content"].strip()} for t in history
             if t.get("role") in ("user", "assistant") and t.get("content", "").strip()]
    total, kept = 0, []
    for t in reversed(turns):
        total += len(t["content"])
        if total > MAX_HISTORY_CHARS:
            break
        kept.append(t)
    kept.reverse()
    while kept and kept[0]["role"] != "user":
        kept.pop(0)
    return kept


def context_note(city: str | None, has_profile: bool, now: datetime | None = None) -> str:
    now = now or datetime.now(IST)
    return (f"[Context] Today is {now:%A %d %B %Y}, {now:%H:%M} IST. City selected on the site: {city or 'none'}. "
            f"The user is signed in and {'has' if has_profile else 'has not'} saved a health profile.")


class Assistant:
    def __init__(self, client: anthropic.Anthropic, model: str = MODEL, effort: str = EFFORT):
        self.client, self.model, self.effort = client, model, effort

    @classmethod
    def from_env(cls) -> "Assistant | None":
        if not os.getenv("ANTHROPIC_API_KEY"):
            return None
        return cls(anthropic.Anthropic(timeout=60.0, max_retries=2))

    def answer(self, svc: ModelService, message: str, history: list[dict], city: str | None,
               profile: dict | None) -> Reply:
        if is_emergency(message):
            return emergency_reply(svc, city)
        log = ToolLog()
        messages = clean_history(history) + [{"role": "user", "content": [
            {"type": "text", "text": context_note(city, profile is not None)},
            {"type": "text", "text": message.strip()},
        ]}]
        try:
            runner = self.client.beta.messages.tool_runner(
                model=self.model,
                max_tokens=MAX_TOKENS,
                system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
                tools=build_tools(svc, profile, log),
                messages=messages,
                output_config={"effort": self.effort},
                betas=[FALLBACK_BETA],
                fallbacks="default",
                max_iterations=MAX_ITERATIONS,
            )
            final = runner.until_done()
        # Users get a plain message; the real reason (bad key, no credit, ...) goes to the server log.
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as e:
            logger.error("assistant: API key rejected: %s", e)
            raise AssistantError(503, UNAVAILABLE_TEXT)
        except anthropic.RateLimitError:
            raise AssistantError(503, "The assistant is busy right now. Please try again in a minute.")
        except (anthropic.APIConnectionError, anthropic.APITimeoutError):
            raise AssistantError(503, "The assistant couldn't be reached. Please try again.")
        except anthropic.BadRequestError as e:            # e.g. "credit balance is too low"
            logger.error("assistant: request refused (%s): %s", e.status_code, e)
            raise AssistantError(503, UNAVAILABLE_TEXT)
        except anthropic.APIStatusError as e:
            logger.error("assistant: API error (%s): %s", e.status_code, e)
            raise AssistantError(502, "The assistant failed. Please try again.")

        if final.stop_reason == "refusal":
            text = REFUSAL_TEXT
        else:
            text = "\n\n".join(b.text for b in final.content if b.type == "text").strip() or EMPTY_TEXT
        return Reply(text=text, tools_used=sorted(set(log.calls)), model=getattr(final, "model", self.model),
                     stop_reason=final.stop_reason)
