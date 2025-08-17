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

    def resolve(self, model: str) -> tuple[Optional[Provider], str]:
        """
        Résout un identifiant de modèle vers (provider, model_normalisé).

        Supporte le format explicite "provider/model" ainsi que la
        compatibilité avec l'ancien format basé sur heuristique de préfixe.
        """
        model_stripped = model.strip()
        model_lower = model_stripped.lower()

        # Aliases connus pour les providers
        alias_to_provider = {
            "openai": "openai",
            "oai": "openai",
            "mistral": "mistral",
            "mistralai": "mistral",
        }

        # Format explicite provider/model
        if "/" in model_lower:
            provider_part, model_part = model_lower.split("/", 1)
            provider_key = alias_to_provider.get(provider_part)
            provider = self.get(provider_key) if provider_key else None
            # On retourne le modèle normalisé sans le préfixe provider
            normalized_model = model_stripped.split("/", 1)[1] if "/" in model_stripped else model_stripped
            return provider, normalized_model

        # Ancien format: déduction par préfixe
        if model_lower.startswith("mistral") or model_lower.startswith("open-mistral"):
            return self.get("mistral"), model_stripped
        if model_lower.startswith("gpt-") or model_lower.startswith("o3") or model_lower.startswith("o4"):
            return self.get("openai"), model_stripped

        return None, model_stripped

    def get_by_model_prefix(self, model: str) -> Optional[Provider]:
        """
        Conservé pour compatibilité: retourne uniquement le provider.
        Préfère utiliser `resolve` pour aussi obtenir le modèle normalisé.
        """
        provider, _ = self.resolve(model)
        return provider


