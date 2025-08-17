from typing import List, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Modèle pour un message de chat"""

    role: str = Field(
        ..., description="Rôle de l'émetteur du message (user, assistant, system)"
    )
    content: str = Field(..., description="Contenu du message")


class ChatCompletionsRequest(BaseModel):
    """Modèle pour une requête de complétion de chat"""

    model: str = Field(..., description="Identifiant du modèle à utiliser")
    provider: str = Field(
        "mistral", description="Provider à utiliser (mistral, openai, anthropic)"
    )
    prompt: Optional[str] = Field(
        None, description="Prompt à utiliser pour la génération"
    )
    input: Optional[str] = Field(
        None, description="Entrée utilisateur pour la génération"
    )
    history: Optional[List[Message]] = Field(
        None, description="Historique des messages précédents"
    )
    temperature: float = Field(0.7, description="Température pour la génération (0-1)")
    max_tokens: int = Field(1024, description="Nombre maximum de tokens à générer")
    top_p: float = Field(0.9, description="Valeur top_p pour la génération")
    stream: bool = Field(False, description="Si vrai, la réponse sera streamée en SSE")


class ChatCompletionChunk(BaseModel):
    """Modèle pour un morceau de réponse en streaming"""

    chunk: str = Field(..., description="Portion de texte générée")
    finish_reason: Optional[str] = Field(
        None, description="Raison de fin du streaming (stop, length, etc.)"
    )
    job_id: str = Field(..., description="Identifiant unique de la tâche")


class ChatCompletionResponse(BaseModel):
    """Modèle pour une réponse complète (non-streaming)"""

    result: str = Field(..., description="Texte complet généré")
    job_id: str = Field(..., description="Identifiant unique de la tâche")

    class Config:
        json_schema_extra = {
            "example": {
                "result": "Voici une réponse complète à votre requête.",
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
            }
        }
