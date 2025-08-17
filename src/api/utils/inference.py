import time
import uuid
from typing import Dict, List, Tuple

from pydantic import BaseModel, Field
from qdrant_client.models import PointStruct


class Message(BaseModel):
    """Modèle pour un message de chat"""

    role: str = Field(
        ..., description="Rôle de l'émetteur du message (user, assistant, system)"
    )
    content: str = Field(..., description="Contenu du message")


class InferenceUtils:
    @staticmethod
    def format_messages(prompt: str | None, input: str | None, history: List[Message] | None, messages: List[Message] | None = None) -> List:
        output: List[Dict[str, str]] = []
        # OpenAI-style messages prennent le dessus si fournis
        if messages:
            for m in messages:
                role = m.role
                # Normalisation des rôles pour Chat Completions
                if role == "developer":
                    role = "system"
                output.append({"role": role, "content": m.content})
        else:
            if prompt:
                output.append({"role": "system", "content": prompt})
            if history:
                for entry in history:
                    role = entry.role
                    if role == "developer":
                        role = "system"
                    output.append({"role": role, "content": entry.content})
            if input:
                output.append({"role": "user", "content": input})
        return output

    @staticmethod
    def chat_openai_response(model: str, content: str) -> Dict:
        now = int(time.time())
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
            "object": "chat.completion",
            "created": now,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content,
                        "refusal": None,
                        "annotations": [],
                    },
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

    @staticmethod
    def format_embeddings_openai(inputs: List[str], data: List[Dict], model: str) -> Dict:
        return {
            "id": f"embd-{uuid.uuid4().hex[:12]}",
            "object": "list",
            "model": model,
            "data": [
                {
                    "object": "embedding",
                    "embedding": embedding["embedding"],
                    "index": i,
                }
                for i, embedding in enumerate(data)
                if embedding["object"] == "embedding"
            ],
            "usage": {"prompt_tokens": 0, "total_tokens": 0},
        }

    @staticmethod
    def embedding_to_points(inputs: List[str], data: List[Dict]) -> List[PointStruct]:
        points: List = [
            {
                "id": i,
                "vector": embedding["embedding"],
                "payload": {"source_text": inputs[i]},
            }
            for i, embedding in enumerate(data)
            if embedding["object"] == "embedding"
        ]
        return points

    @staticmethod
    def embedding_to_tuple(
        inputs: List[str], data: List[Dict]
    ) -> Tuple[List[int], List[List[float]], List[Dict]]:
        ids = []
        vectors = []
        payloads = []

        for i, embedding in enumerate(data):
            if embedding["object"] == "embedding":
                ids.append(i)
                vectors.append(embedding["embedding"])
                payloads.append({"source_text": inputs[i]})

        return ids, vectors, payloads
