import json
import uuid
from datetime import datetime

from api.classes import TextGeneration
from api.databases import MongoDBConnector
from api.utils import CustomLogger
from api.v1.security import (
    ensure_valid_api_key_or_token,
    get_current_user_with_api_key_or_token,
)
from api.v1.services import get_mongo_client, get_text_generation
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from .chat_models import (
    ChatCompletionResponse,
    ChatCompletionsRequest,
    ChatCompletionChunk,
    ChatChunkChoice,
    ChatDelta,
)

logger = CustomLogger.get_logger(__name__)

router = APIRouter()


async def sse_stream_generator(generator, job_id, model):
    """Flux SSE au format OpenAI chat.completion.chunk."""
    try:
        final_answer = ""
        last_finish_reason = None
        # Premier événement avec rôle assistant
        prelude = ChatCompletionChunk(
            id=f"chatcmpl-{job_id}",
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
                created=int(datetime.now().timestamp()),
                model=model,
                choices=[ChatChunkChoice(index=0, delta=ChatDelta(content=delta_text))],
            ).model_dump_json()
            yield f"data: {data}\n\n"

        # Evénement de fin
        done_data = ChatCompletionChunk(
            id=f"chatcmpl-{job_id}",
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
    description="""Génère des complétion de chat basées sur les messages fournis.

    Si le paramètre `stream` dans le corps de la requête est à `true`, la réponse sera un flux SSE (Server-Sent Events).
    Chaque événement contiendra un chunk de la réponse au format JSON.
    """,
    response_model=ChatCompletionResponse,
    responses={
        200: {
            "description": "Réponse réussie",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ChatCompletionResponse"}
                },
                "text/event-stream": {
                    "schema": {
                        "type": "string",
                        "format": "binary",
                        "description": "Flux SSE contenant des chunks de réponse JSON",
                    },
                    "example": 'data: {"chunk": "Bonjour", "finish_reason": null, "job_id": "550e8400-e29b-41d4-a716-446655440000"}\n\n'
                    'data: {"chunk": " comment", "finish_reason": null, "job_id": "550e8400-e29b-41d4-a716-446655440000"}\n\n'
                    'data: {"chunk": " allez-vous ?", "finish_reason": "stop", "job_id": "550e8400-e29b-41d4-a716-446655440000"}\n\n'
                    'event: done\ndata: {"result": "Bonjour comment allez-vous ?", "finish_reason": "stop", "job_id": "550e8400-e29b-41d4-a716-446655440000"}\n\n',
                },
            },
        }
    },
    dependencies=[Depends(ensure_valid_api_key_or_token)],
)
async def completions(
    chat_request: ChatCompletionsRequest,
    text_generation: TextGeneration = Depends(get_text_generation),
    user: dict = Depends(get_current_user_with_api_key_or_token),
    mongodb_client: MongoDBConnector = Depends(get_mongo_client),
):
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
