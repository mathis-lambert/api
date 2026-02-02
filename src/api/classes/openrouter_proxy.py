from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, Optional

import httpx

from api.config import get_settings


class OpenRouterProxy:
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
        timeout = httpx.Timeout(60.0, read=None)
        return httpx.AsyncClient(base_url=base_url, headers=headers, timeout=timeout)

    def is_configured(self) -> bool:
        return self._client is not None

    async def post(self, path: str, payload: Dict[str, Any]) -> httpx.Response:
        if self._client is None:
            raise RuntimeError("OpenRouter client not configured")
        return await self._client.post(path, json=payload)

    @asynccontextmanager
    async def stream(
        self, path: str, payload: Dict[str, Any]
    ) -> AsyncIterator[httpx.Response]:
        if self._client is None:
            raise RuntimeError("OpenRouter client not configured")
        async with self._client.stream("POST", path, json=payload) as response:
            yield response

    async def chat_completions(self, payload: Dict[str, Any]) -> httpx.Response:
        return await self.post("/chat/completions", payload)

    @asynccontextmanager
    async def stream_chat_completions(
        self, payload: Dict[str, Any]
    ) -> AsyncIterator[httpx.Response]:
        async with self.stream("/chat/completions", payload) as response:
            yield response

    async def responses(self, payload: Dict[str, Any]) -> httpx.Response:
        return await self.post("/responses", payload)

    @asynccontextmanager
    async def stream_responses(
        self, payload: Dict[str, Any]
    ) -> AsyncIterator[httpx.Response]:
        async with self.stream("/responses", payload) as response:
            yield response
