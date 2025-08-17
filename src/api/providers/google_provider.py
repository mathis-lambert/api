from __future__ import annotations

import os
from typing import Any, AsyncGenerator, Dict, Iterable, List, Optional, Tuple

import asyncio
from google.generativeai import GenerativeModel, configure, embed_content

from .base import ModelCard, Provider


class GoogleProvider(Provider):
    name = "google"

    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        configure(api_key=api_key)
        # Le modèle sera instancié à la volée selon l'id

    async def list_models(self) -> List[ModelCard]:
        # google.generativeai ne liste pas facilement tous les modèles; fournir un sous-ensemble courant
        common = ["gemini-2.0-flash", "gemini-1.5-pro", "text-embedding-004"]
        return [ModelCard(id=m, provider=self.name) for m in common]

    async def get_model(self, model_id: str) -> ModelCard:
        return ModelCard(id=model_id, provider=self.name)

    async def chat_complete(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        top_p: float,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
    ) -> Dict[str, Any]:
        # Concatène le contexte et les messages; Gemini utilise un format différent
        system = "\n".join(m["content"] for m in messages if m["role"] == "system")
        history = [m for m in messages if m["role"] != "system"]
        prompt = "\n".join(f"{m['role']}: {m['content']}" for m in history)
        gm = GenerativeModel(model)
        def _run():
            return gm.generate_content(
                [system, prompt],
                generation_config={
                    "temperature": temperature,
                    "top_p": top_p,
                    "max_output_tokens": max_tokens,
                },
            )
        resp = await asyncio.to_thread(_run)
        text = getattr(resp, "text", "") or ""
        import time, uuid
        now = int(time.time())
        result = {
            "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
            "object": "chat.completion",
            "created": now,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": text},
                    "logprobs": None,
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "prompt_tokens_details": {"cached_tokens": 0, "audio_tokens": 0},
                "completion_tokens_details": {
                    "reasoning_tokens": 0,
                    "audio_tokens": 0,
                    "accepted_prediction_tokens": 0,
                    "rejected_prediction_tokens": 0,
                },
            },
            "service_tier": "default",
        }
        return result

    async def chat_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        top_p: float,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
    ) -> AsyncGenerator[Tuple[str, Optional[str]], None]:
        system = "\n".join(m["content"] for m in messages if m["role"] == "system")
        history = [m for m in messages if m["role"] != "system"]
        prompt = "\n".join(f"{m['role']}: {m['content']}" for m in history)
        # Fallback: pas de vrai streaming; on génère tout et on renvoie en un seul chunk
        text = await self.chat_complete(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
        )
        if text:
            yield text, "stop"

    async def create_embeddings(self, model: str, inputs: Iterable[str]) -> Dict[str, Any]:
        # Utilise la fonction synchrone dans un thread
        def _embed_one(text: str):
            return embed_content(model=model, content=text)
        data = []
        for text in inputs:
            resp = await asyncio.to_thread(_embed_one, text)
            values = resp["embedding"]["values"] if isinstance(resp, dict) else getattr(resp, "embedding", {}).get("values", [])
            data.append({"object": "embedding", "embedding": values})
        return {"data": data}


