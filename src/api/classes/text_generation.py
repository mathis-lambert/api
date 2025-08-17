from typing import Any, AsyncGenerator, Dict, List, Optional

from api.providers import ProviderRegistry
from api.v1.routes.chat.chat_models import ChatCompletionResponse


class TextGeneration:
    def __init__(self, provider_registry: ProviderRegistry, inference_utils):
        self.provider_registry = provider_registry
        self.inference_utils = inference_utils

    def _get_provider(self, model: str):
        provider = self.provider_registry.get_by_model_prefix(model)
        if provider is None:
            # Try default provider if any explicitly registered under "mistral"
            provider = self.provider_registry.get("mistral")
        if provider is None:
            raise ValueError("Aucun provider compatible trouvé pour ce modèle")
        return provider

    async def generate_stream_response(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        top_p: float,
        job_id: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Génère une réponse en streaming pour SSE.

        Args:
            model: Identifiant du modèle à utiliser
            messages: Liste de messages normalisés au format OpenAI
                (p. ex. [{"role": "user", "content": "..."}])
            temperature: Contrôle de la randomisation (0-1)
            max_tokens: Nombre maximum de tokens à générer
            top_p: Valeur de top_p pour l'échantillonnage
            job_id: Identifiant unique de la tâche
            tools: Définition des outils (OpenAI Tools) si applicable
            tool_choice: Stratégie de sélection d'outil

        Returns:
            Un générateur qui émet, à chaque itération, un dictionnaire
            minimal {"chunk": str, "finish_reason": Optional[str], "job_id": str}.
            Ces éléments sont ensuite encapsulés par la route dans des objets
            `ChatCompletionChunk` (OpenAI) pour le flux SSE.
        """
        provider = self._get_provider(model)
        async for response, finish_reason in provider.chat_stream(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            tools=tools,
            tool_choice=tool_choice,
        ):
            # Formater chaque chunk comme un dictionnaire pour la sérialisation JSON
            chunk_data = {
                "chunk": response,
                "finish_reason": finish_reason,
                "job_id": job_id,
            }
            yield chunk_data

    async def complete(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        top_p: float,
        job_id: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
    ) -> ChatCompletionResponse:
        """
        Génère une réponse complète (non-streaming) au format OpenAI
        `chat.completion`.

        Args:
            model: Identifiant du modèle à utiliser
            messages: Liste de messages normalisés au format OpenAI
                (p. ex. [{"role": "user", "content": "..."}])
            temperature: Contrôle de la randomisation (0-1)
            max_tokens: Nombre maximum de tokens à générer
            top_p: Valeur de top_p pour l'échantillonnage
            job_id: Identifiant unique de la tâche
            tools: Définition des outils (OpenAI Tools) si applicable
            tool_choice: Stratégie de sélection d'outil

        Returns:
            Un objet `ChatCompletionResponse` conforme aux schémas OpenAI.
        """
        provider = self._get_provider(model)
        response_dict = await provider.chat_complete(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            tools=tools,
            tool_choice=tool_choice,
        )
        # Validation/normalisation selon le modèle Pydantic exposé
        # par `api.v1.routes.chat.chat_models.ChatCompletionResponse`.
        return ChatCompletionResponse.model_validate(response_dict)
