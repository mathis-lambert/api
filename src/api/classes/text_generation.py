from typing import Any, AsyncGenerator, Dict, List, Optional

from api.providers import ProviderRegistry


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
        messages: list,
        temperature: float,
        max_tokens: int,
        top_p: float,
        job_id: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Génère une réponse en streaming formatée pour SSE.

        Args:
            model: Identifiant du modèle à utiliser
            messages: Liste des messages de l'historique de conversation
            temperature: Contrôle de la randomisation (0-1)
            max_tokens: Nombre maximum de tokens à générer
            top_p: Valeur de top_p pour l'échantillonnage
            job_id: Identifiant unique de la tâche

        Returns:
            Un générateur asynchrone de dictionnaires contenant les chunks et métadonnées
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
        messages: list,
        temperature: float,
        max_tokens: int,
        top_p: float,
        job_id: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Génère une réponse complète (non-streaming).

        Args:
            model: Identifiant du modèle à utiliser
            messages: Liste des messages de l'historique de conversation
            temperature: Contrôle de la randomisation (0-1)
            max_tokens: Nombre maximum de tokens à générer
            top_p: Valeur de top_p pour l'échantillonnage
            job_id: Identifiant unique de la tâche

        Returns:
            Un dictionnaire contenant la réponse et l'identifiant de la tâche
        """
        provider = self._get_provider(model)
        response = await provider.chat_complete(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            tools=tools,
            tool_choice=tool_choice,
        )
        # Les providers doivent retourner une réponse OpenAI-compat déjà formatée
        return response
