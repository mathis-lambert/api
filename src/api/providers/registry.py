from __future__ import annotations

from typing import Dict, Optional

from .base import Provider


class ProviderRegistry:
    def __init__(self):
        self._providers: Dict[str, Provider] = {}

    def register(self, provider: Provider) -> None:
        self._providers[provider.name] = provider

    def get(self, name: str) -> Optional[Provider]:
        return self._providers.get(name)

    def get_by_model_prefix(self, model: str) -> Optional[Provider]:
        # Heuristique simple par préfixe (ex: "gpt-" -> OpenAI)
        model_lower = model.lower()
        if model_lower.startswith("mistral") or model_lower.startswith("open-mistral"):
            return self.get("mistral")
        if model_lower.startswith("gpt-") or model_lower.startswith("o3") or model_lower.startswith("o4"):
            return self.get("openai")
        if model_lower.startswith("claude"):
            return self.get("anthropic")
        if model_lower.startswith("gemini") or model_lower.startswith("textembedding-gecko"):
            return self.get("google")
        return None


