import json
import uuid
from datetime import datetime
from typing import Any, AsyncGenerator, Dict

from api.classes import TextGeneration
from api.databases import MongoDBConnector
from api.utils import CustomLogger
from api.v1.security import (
    ensure_valid_api_key_or_token,
    get_current_user_with_api_key_or_token,
)
from api.v1.services import get_mongo_client, get_text_generation
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import StreamingResponse

from .chat_models import (
    ChatCompletionResponse,
    ChatCompletionsRequest,
    ChatCompletionChunk,
    ChatChunkChoice,
    ChatDelta,
)

logger = CustomLogger.get_logger(__name__)

router = APIRouter(tags=["Chat"])


async def sse_stream_generator(
    generator: AsyncGenerator[Dict[str, Any], None],
    job_id: str,
    model: str,
) -> AsyncGenerator[str, None]:
    """
    Flux SSE produisant des événements au format OpenAI `chat.completion.chunk`.

    - Entrée: un générateur asynchrone qui émet des éléments
      {"chunk": str, "finish_reason": Optional[str], "job_id": str}.
    - Sortie: lignes SSE (texte) où chaque ligne `data:` contient un
      `ChatCompletionChunk` sérialisé.
    """
    try:
        final_answer = ""
        last_finish_reason = None
        # Premier événement avec rôle assistant
        prelude = ChatCompletionChunk(
            id=f"chatcmpl-{job_id}",
            object="chat.completion.chunk",
            created=int(datetime.now().timestamp()),
            model=model,
            choices=[ChatChunkChoice(index=0, delta=ChatDelta(role="assistant", content=""))],
        ).model_dump_json()
        yield f"data: {prelude}\n\n"
        async for chunk in generator:
            delta_text = chunk.get("chunk", "")
            if chunk.get("finish_reason"):
                last_finish_reason = chunk.get("finish_reason")
            final_answer += delta_text
            data = ChatCompletionChunk(
                id=f"chatcmpl-{job_id}",
                object="chat.completion.chunk",
                created=int(datetime.now().timestamp()),
                model=model,
                choices=[ChatChunkChoice(index=0, delta=ChatDelta(content=delta_text))],
            ).model_dump_json()
            yield f"data: {data}\n\n"

        # Evénement de fin
        done_data = ChatCompletionChunk(
            id=f"chatcmpl-{job_id}",
            object="chat.completion.chunk",
            created=int(datetime.now().timestamp()),
            model=model,
            choices=[ChatChunkChoice(index=0, delta=ChatDelta(), finish_reason=last_finish_reason or "stop")],
        ).model_dump_json()
        yield f"data: {done_data}\n\n"
    except Exception as e:
        logger.error(f"Erreur pendant le streaming SSE: {str(e)}")
        error_data = json.dumps({"error": str(e)})
        yield f"event: error\ndata: {error_data}\n\n"


@router.post(
    "/completions",
    summary="Get chat completions",
    description="""Génère des complétions de chat au format OpenAI Chat Completions.

    - Quand `stream` = `false` (par défaut), retourne un objet `chat.completion`.
    - Quand `stream` = `true`, retourne un flux SSE dont chaque `data:` contient
      un objet `chat.completion.chunk` sérialisé.
    
    Compatible avec les outils (OpenAI Tools) via `tools` et `tool_choice`.
    """,
    response_model=ChatCompletionResponse,
    responses={
        200: {
            "description": "Réponse réussie",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ChatCompletionResponse"},
                    "example": {
                        "id": "chatcmpl-abc123",
                        "object": "chat.completion",
                        "created": 1700000000,
                        "model": "mistral-small",
                        "choices": [
                            {
                                "index": 0,
                                "message": {"role": "assistant", "content": "Bonjour !"},
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
                    },
                },
                "text/event-stream": {
                    "schema": {
                        "type": "string",
                        "format": "binary",
                        "description": "Flux SSE contenant des chunks de réponse JSON",
                    },
                    "example": 'data: {"id":"chatcmpl-550e8400-e29b-41d4-a716-446655440000","object":"chat.completion.chunk","created":1700000001,"model":"mistral-small","choices":[{"index":0,"delta":{"role":"assistant","content":""}}]}\n\n'
                    'data: {"id":"chatcmpl-550e8400-e29b-41d4-a716-446655440000","object":"chat.completion.chunk","created":1700000002,"model":"mistral-small","choices":[{"index":0,"delta":{"content":"Bonjour"}}]}\n\n'
                    'data: {"id":"chatcmpl-550e8400-e29b-41d4-a716-446655440000","object":"chat.completion.chunk","created":1700000003,"model":"mistral-small","choices":[{"index":0,"delta":{"content":" !"}}]}\n\n'
                    'data: {"id":"chatcmpl-550e8400-e29b-41d4-a716-446655440000","object":"chat.completion.chunk","created":1700000004,"model":"mistral-small","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}\n\n',
                },
            },
        }
    },
    dependencies=[Depends(ensure_valid_api_key_or_token)],
)
async def completions(
    chat_request: ChatCompletionsRequest = Body(
        ...,
        examples={
            "non_stream": {
                "summary": "Requête standard (JSON)",
                "value": {
                    "model": "mistral-small",
                    "messages": [{"role": "user", "content": "Bonjour"}],
                    "stream": False,
                    "temperature": 0.7,
                    "max_tokens": 64,
                    "top_p": 0.9,
                },
            },
            "stream": {
                "summary": "Requête en streaming (SSE)",
                "value": {
                    "model": "mistral-small",
                    "messages": [{"role": "user", "content": "Bonjour"}],
                    "stream": True,
                    "temperature": 0.7,
                    "max_tokens": 64,
                    "top_p": 0.9,
                },
            },
        },
    ),
    text_generation: TextGeneration = Depends(get_text_generation),
    user: dict = Depends(get_current_user_with_api_key_or_token),
    mongodb_client: MongoDBConnector = Depends(get_mongo_client),
) -> ChatCompletionResponse | StreamingResponse:
    """
    Endpoint OpenAI-compatible `POST /v1/chat/completions`.

    - Quand `stream` est `false`, renvoie un `ChatCompletionResponse` (objet
      OpenAI `chat.completion`).
    - Quand `stream` est `true`, renvoie un flux SSE dont chaque `data:`
      contient un `ChatCompletionChunk` sérialisé.
    """
    # Validation minimale: le provider sera résolu dynamiquement

    # Formatage des messages
    messages = text_generation.inference_utils.format_messages(
        chat_request.prompt, chat_request.input, chat_request.history, chat_request.messages
    )
    if not messages:
        raise HTTPException(status_code=400, detail="Aucune entrée fournie")

    # Génération d'un identifiant unique pour la tâche
    job_id: str = str(uuid.uuid4())

    # Log event to mongodb
    await mongodb_client.log_event(
        user["_id"],
        job_id,
        "chat_completions",
        {
            "model": chat_request.model,
            "messages": messages,
            "temperature": chat_request.temperature,
            "max_tokens": chat_request.max_tokens,
            "top_p": chat_request.top_p,
            "stream": chat_request.stream,
            "job_id": job_id,
            "timestamp": datetime.now(),
        },
    )

    # Choix entre streaming ou réponse complète
    if chat_request.stream:
        # Obtenir le générateur de stream
        stream_generator = text_generation.generate_stream_response(
            model=chat_request.model,
            messages=messages,
            temperature=chat_request.temperature,
            max_tokens=chat_request.max_tokens,
            top_p=chat_request.top_p,
            job_id=job_id,
            tools=chat_request.tools,
            tool_choice=chat_request.tool_choice,
        )

        # Transformer le générateur en flux SSE
        sse_generator = sse_stream_generator(stream_generator, job_id, chat_request.model)

        return StreamingResponse(
            sse_generator,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Désactive la mise en tampon Nginx
            },
        )
    else:
        response = await text_generation.complete(
            model=chat_request.model,
            messages=messages,
            temperature=chat_request.temperature,
            max_tokens=chat_request.max_tokens,
            top_p=chat_request.top_p,
            job_id=job_id,
            tools=chat_request.tools,
            tool_choice=chat_request.tool_choice,
        )
        return response
