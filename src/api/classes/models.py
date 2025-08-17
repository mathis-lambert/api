from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx


class Models:
    def __init__(self, http_client: Optional[httpx.AsyncClient] = None) -> None:
        self._client = http_client or self._build_client()

    def _build_client(self) -> Optional[httpx.AsyncClient]:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            return None
        base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        headers: Dict[str, str] = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        site = os.environ.get("OPENROUTER_SITE_URL")
        app_name = os.environ.get("OPENROUTER_APP_NAME")
        if site:
            headers["HTTP-Referer"] = site
        if app_name:
            headers["X-Title"] = app_name
        return httpx.AsyncClient(base_url=base_url, headers=headers, timeout=30.0)

    async def list_models(self) -> Dict[str, Any]:
        if self._client is None:
            # Fallback hors-ligne: retour minimal compatible
            return {"object": "list", "data": []}
        r = await self._client.get("/models")
        r.raise_for_status()
        return r.json()

    async def read_model(self, author: str, model: str) -> Dict[str, Any]:
        if self._client is None:
            return {"id": model, "object": "model"}
        r = await self._client.get(f"/models/{author}/{model}/endpoints")
        r.raise_for_status()
        return r.json()
