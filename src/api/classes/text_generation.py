from typing import Any, AsyncGenerator, Dict, List, Optional

from api.providers import ProviderRegistry


class TextGeneration:
    def __init__(self, provider_registry: ProviderRegistry, inference_utils):
        self.provider_registry = provider_registry
        self.inference_utils = inference_utils

    def _resolve_provider_and_model(self, model: str):
        provider, normalized_model = self.provider_registry.resolve(model)
        if provider is None:
            # Try default provider if any explicitly registered under "mistral"
            provider = self.provider_registry.get("mistral")
        if provider is None:
            raise ValueError("Aucun provider compatible trouvé pour ce modèle")
        return provider, normalized_model

    async def generate_stream_response(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        top_p: float,
        job_id: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Génère une réponse en streaming pour SSE.

        Args:
            model: Identifiant du modèle à utiliser
            messages: Liste de messages normalisés au format OpenAI
                (p. ex. [{"role": "user", "content": "..."}])
            temperature: Contrôle de la randomisation (0-1)
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
        provider, normalized_model = self._resolve_provider_and_model(model)
        async for response, finish_reason in provider.chat_stream(
            model=normalized_model,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            tools=tools,
            tool_choice=tool_choice,
            **kwargs,
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
        top_p: float,
        job_id: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Génère une réponse complète (non-streaming) au format OpenAI
        `chat.completion`.

        Args:
            model: Identifiant du modèle à utiliser
            messages: Liste de messages normalisés au format OpenAI
                (p. ex. [{"role": "user", "content": "..."}])
            temperature: Contrôle de la randomisation (0-1)
            top_p: Valeur de top_p pour l'échantillonnage
            job_id: Identifiant unique de la tâche
            tools: Définition des outils (OpenAI Tools) si applicable
            tool_choice: Stratégie de sélection d'outil

        Returns:
            Un objet `ChatCompletionResponse` conforme aux schémas OpenAI.
        """
        provider, normalized_model = self._resolve_provider_and_model(model)
        response_dict = await provider.chat_complete(
            model=normalized_model,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            tools=tools,
            tool_choice=tool_choice,
            **kwargs,
        )
        # Retourne le dict conforme OpenAI; la route se charge de la validation/sérialisation
        return response_dict
