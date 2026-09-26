"""Minimal Supabase client: token verification (Auth) and table access (PostgREST).

Every table call is made *as the signed-in user*: the user's access token is sent as
the bearer token, so Postgres Row Level Security decides what they can read or write.
The backend never needs the service-role key for user data.

Configuration (environment or ``.env``): ``SUPABASE_URL``, ``SUPABASE_ANON_KEY``.
"""
from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv

from src.data_loader import PROJECT_ROOT

load_dotenv(PROJECT_ROOT / ".env")

USER_CACHE_SECONDS = 60
USER_CACHE_MAX = 1000


class SupabaseError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status, self.message = status, message


class NotAuthenticated(SupabaseError):
    def __init__(self, message: str = "Not signed in or session expired"):
        super().__init__(401, message)


@dataclass
class AuthUser:
    id: str
    email: str | None
    token: str


class SupabaseClient:
    def __init__(self, url: str, anon_key: str, transport: httpx.BaseTransport | None = None,
                 timeout: float = 10.0):
        self.url = url.rstrip("/")
        self.anon_key = anon_key
        self.http = httpx.Client(base_url=self.url, timeout=timeout, transport=transport,
                                 headers={"apikey": anon_key})
        self._users: dict[str, tuple[float, AuthUser]] = {}

    @classmethod
    def from_env(cls) -> "SupabaseClient | None":
        url, key = os.getenv("SUPABASE_URL", ""), os.getenv("SUPABASE_ANON_KEY", "")
        if not url or not key or "YOUR-PROJECT-REF" in url:
            return None
        return cls(url, key)

    def close(self):
        self.http.close()

    # ------------------------------------------------------------------ auth

    def get_user(self, token: str) -> AuthUser:
        """Resolve an access token to its user via Supabase Auth (cached briefly)."""
        key = hashlib.sha256(token.encode()).hexdigest()
        now = time.monotonic()
        hit = self._users.get(key)
        if hit and hit[0] > now:
            return hit[1]
        r = self.http.get("/auth/v1/user", headers={"Authorization": f"Bearer {token}"})
        if r.status_code in (401, 403):
            raise NotAuthenticated()
        if r.status_code != 200:
            raise SupabaseError(502, f"Supabase Auth error ({r.status_code})")
        data = r.json()
        user = AuthUser(id=data["id"], email=data.get("email"), token=token)
        if len(self._users) >= USER_CACHE_MAX:
            self._users.clear()
        self._users[key] = (now + USER_CACHE_SECONDS, user)
        return user

    # ------------------------------------------------------------------ tables (as the user)

    def _request(self, user: AuthUser, method: str, table: str, *, params=None, json=None,
                 prefer: str | None = None):
        headers = {"Authorization": f"Bearer {user.token}"}
        if prefer:
            headers["Prefer"] = prefer
        r = self.http.request(method, f"/rest/v1/{table}", params=params, json=json, headers=headers)
        if r.status_code == 401:
            raise NotAuthenticated()
        if r.status_code >= 400:
            try:
                msg = r.json().get("message", r.text)
            except ValueError:
                msg = r.text
            raise SupabaseError(502 if r.status_code >= 500 else r.status_code, f"Database error: {msg}")
        return r.json() if r.content else None

    def select(self, user, table, **params):
        return self._request(user, "GET", table, params=params)

    def insert(self, user, table, rows):
        return self._request(user, "POST", table, json=rows, prefer="return=representation")

    def upsert(self, user, table, row, on_conflict: str):
        return self._request(user, "POST", table, params={"on_conflict": on_conflict}, json=row,
                             prefer="resolution=merge-duplicates,return=representation")

    def delete(self, user, table, **params):
        return self._request(user, "DELETE", table, params=params, prefer="return=representation")
