from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from api.config import get_settings


class Models:
    def __init__(self, http_client: Optional[httpx.AsyncClient] = None) -> None:
        self._client = http_client or self._build_client()

    def _build_client(self) -> Optional[httpx.AsyncClient]:
        settings = get_settings()
        api_key = settings.openrouter_api_key
        if not api_key:
            return None
        base_url = settings.openrouter_base_url
        headers: Dict[str, str] = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        site = settings.openrouter_site_url
        app_name = settings.openrouter_app_name
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
        json_data = r.json()
        model_data = json_data.get("data", {})
        return model_data
