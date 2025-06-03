from typing import Any, AsyncGenerator, Dict

from api.providers import AIProvider


class TextGeneration:
    def __init__(self, provider: AIProvider, inference_utils):
        self.provider = provider
        self.inference_utils = inference_utils

    async def generate_stream_response(
        self,
        model: str,
        messages: list,
        temperature: float,
        max_tokens: int,
        top_p: float,
        job_id: str,
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
        async for response, finish_reason in self.provider.stream(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
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
    ) -> Dict[str, str]:
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
        response = await self.provider.complete(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
        )
        return self.inference_utils.format_response(response, job_id)
