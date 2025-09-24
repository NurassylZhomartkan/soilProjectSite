from __future__ import annotations
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional
import httpx
from fastapi import HTTPException  # NEW

from .config import ExternalAPISettings

class ExternalAPIError(RuntimeError):
    pass

class ExternalAPIClient:
    """Thin async HTTP client for the external API.
    Forwards user Authorization if provided; falls back to service token if configured.
    """
    def __init__(self, settings: ExternalAPISettings):
        self.settings = settings
        self._client: httpx.AsyncClient | None = None

    @asynccontextmanager
    async def session(self):
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=str(self.settings.base_url),
                timeout=self.settings.timeout,
                verify=self.settings.verify_ssl,
                headers={"Accept": "application/json"},
            )
        try:
            yield self
        finally:
            pass  # keep-alive across requests

    async def _request(
        self, method: str, url: str, *, user_token: Optional[str] = None, **kwargs: Any
    ) -> httpx.Response:
        assert self._client is not None, "Use `async with client.session()`"
        headers = kwargs.pop("headers", {})
        if user_token:
            headers["Authorization"] = f"Bearer {user_token}"
        elif self.settings.service_token:
            headers["Authorization"] = f"Bearer {self.settings.service_token}"
        return await self._client.request(method, url, headers=headers, **kwargs)

    # --- Auth ---
    async def login(self, username: str, password: str, grant_type: str = "password") -> Dict[str, Any]:
        """POST /login with x-www-form-urlencoded; returns token dict."""
        data = {"username": username, "password": password, "grant_type": grant_type}
        headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
        r = await self._request("POST", "/login", data=data, headers=headers)
        _raise_for_status(r, "Failed to login")
        return r.json()

    # --- Generic (optional upstream endpoints) ---
    async def get_fields(self, *, page: int = 1, limit: int = 100, user_token: Optional[str] = None) -> Dict[str, Any]:
        r = await self._request("GET", "/fields", params={"page": page, "limit": limit}, user_token=user_token)
        _raise_for_status(r, "Failed to fetch fields")
        return r.json()

    async def get_field_geometry(self, field_id: str, *, user_token: Optional[str] = None) -> Dict[str, Any]:
        r = await self._request("GET", f"/fields/{field_id}/geometry", user_token=user_token)
        _raise_for_status(r, f"Failed to fetch geometry for field {field_id}")
        return r.json()

    # --- VKU specific ---
    async def get_fields_list(self, *, user_token: str | None = None):
        r = await self._request("GET", "/fields/list", user_token=user_token)
        _raise_for_status(r, "Failed to fetch fields list")
        return r.json()

    async def get_field(self, field_id: str | int, *, user_token: str | None = None):
        r = await self._request("GET", f"/field/get/{field_id}", user_token=user_token)
        _raise_for_status(r, f"Failed to fetch field {field_id}")
        return r.json()

def _raise_for_status(resp: httpx.Response, message: str):
    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        try:
            detail = e.response.json()
        except Exception:
            detail = e.response.text
        # Пробрасываем реальный код апстрима (401/403/404/5xx) вместо 500
        raise HTTPException(
            status_code=e.response.status_code,
            detail={"error": message, "upstream": detail},
        )
