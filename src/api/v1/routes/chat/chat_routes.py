import json
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict

from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_chunk import (
    ChatCompletionChunk,
    Choice,
    ChoiceDelta,
)

from .chat_models import TextGenerationRequest
from api.classes import TextGeneration
from api.databases import MongoDBConnector
from api.utils import CustomLogger
from api.v1.security import (
    ensure_valid_api_key_or_token,
    get_current_user_with_api_key_or_token,
)
from api.v1.services import get_mongo_client, get_text_generation
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import StreamingResponse

logger = CustomLogger.get_logger(__name__)

router = APIRouter()


async def sse_stream_generator(
    generator: AsyncGenerator[Dict[str, Any], None],
    job_id: str,
    model: str,
) -> AsyncGenerator[str, None]:
    """
    SSE stream producing OpenAI `chat.completion.chunk` events.

    - Input: an asynchronous generator emitting elements
      {"chunk": str, "finish_reason": Optional[str], "job_id": str}.
    - Output: SSE lines (text) where each line `data:` contains a
      serialized `ChatCompletionChunk`.
    """
    try:
        final_answer = ""
        last_finish_reason = None

        # First event with assistant role
        prelude = ChatCompletionChunk(
            id=f"chatcmpl-{job_id}",
            object="chat.completion.chunk",
            created=int(datetime.now().timestamp()),
            model=model,
            choices=[Choice(index=0, delta=ChoiceDelta(role="assistant", content=""))],
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
                choices=[Choice(index=0, delta=ChoiceDelta(content=delta_text))],
            ).model_dump_json()

            yield f"data: {data}\n\n"

        # Finish event
        done_data = ChatCompletionChunk(
            id=f"chatcmpl-{job_id}",
            object="chat.completion.chunk",
            created=int(datetime.now().timestamp()),
            model=model,
            choices=[
                Choice(
                    index=0,
                    delta=ChoiceDelta(),
                    finish_reason=last_finish_reason or "stop",
                )
            ],
        ).model_dump_json()

        yield f"data: {done_data}\n\n"

    except Exception as e:
        logger.error(f"Error during SSE streaming: {str(e)}")
        error_data = json.dumps({"error": str(e)})

        yield f"event: error\ndata: {error_data}\n\n"


@router.post(
    "/completions",
    summary="Get chat completions",
    description="""Generate chat completions in OpenAI Chat Completions format.

    - When `stream` = `false` (default), return a `chat.completion` object.
    - When `stream` = `true`, return a SSE stream where each `data:` contains
      un objet `chat.completion.chunk` sérialisé.

    Compatible avec les outils (OpenAI Tools) via `tools` et `tool_choice`.
    """,
    response_model=ChatCompletion,
    responses={
        200: {
            "description": "Success response",
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
                                "message": {
                                    "role": "assistant",
                                    "content": "Bonjour !",
                                },
                                "logprobs": None,
                                "finish_reason": "stop",
                            }
                        ],
                        "usage": {
                            "prompt_tokens": 0,
                            "completion_tokens": 0,
                            "total_tokens": 0,
                            "prompt_tokens_details": {
                                "cached_tokens": 0,
                                "audio_tokens": 0,
                            },
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
                        "description": "SSE stream containing JSON response chunks",
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
    chat_request: TextGenerationRequest = Body(
        ...,
        examples={
            "non_stream": {
                "summary": "Standard request (JSON)",
                "value": {
                    "model": "mistral-small",
                    "messages": [{"role": "user", "content": "Bonjour"}],
                    "stream": False,
                },
            },
            "stream": {
                "summary": "Streaming request (SSE)",
                "value": {
                    "model": "mistral-small",
                    "messages": [{"role": "user", "content": "Bonjour"}],
                    "stream": True,
                },
            },
        },
    ),
    text_generation: TextGeneration = Depends(get_text_generation),
    user: dict = Depends(get_current_user_with_api_key_or_token),
    mongodb_client: MongoDBConnector = Depends(get_mongo_client),
) -> ChatCompletion | StreamingResponse:
    """
    Endpoint OpenAI-compatible `POST /v1/chat/completions`.

    - When `stream` is `false`, return a `ChatCompletionResponse` (OpenAI `chat.completion` object).
    - When `stream` is `true`, return a SSE stream where each `data:`
      contient un `ChatCompletionChunk` sérialisé.
    """
    # Minimal validation: the provider will be resolved dynamically

    if not chat_request.messages:
        raise HTTPException(status_code=400, detail="Aucune entrée fournie")

    # Generation of a unique identifier for the task
    job_id: str = str(uuid.uuid4())

    # Log event to MongoDB
    request_body = {
        "model": chat_request.model,
        "messages": chat_request.messages,
        "stream": chat_request.stream,
        "job_id": job_id,
        "timestamp": datetime.now(timezone.utc),
    }

    await mongodb_client.log_event(
        user["_id"],
        job_id,
        "chat_completions",
        request_body,
    )

    body_dict = chat_request.model_dump(exclude_none=True)

    standard_fields = {
        "model",
        "messages",
        "tools",
        "tool_choice",
    }
    provider_kwargs = {k: v for k, v in body_dict.items() if k not in standard_fields}

    # Choice between streaming or complete response
    if chat_request.stream:
        # Get the stream generator
        stream_generator = text_generation.generate_stream_response(
            model=chat_request.model,
            messages=chat_request.messages,
            job_id=job_id,
            tools=chat_request.tools,
            tool_choice=chat_request.tool_choice,
            **provider_kwargs,
        )

        # Transform the generator into an SSE stream
        sse_generator = sse_stream_generator(
            stream_generator, job_id, chat_request.model
        )

        return StreamingResponse(
            sse_generator,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable Nginx buffering
            },
        )
    else:
        response = await text_generation.complete(
            model=chat_request.model,
            messages=chat_request.messages,
            job_id=job_id,
            tools=chat_request.tools,
            tool_choice=chat_request.tool_choice,
            **provider_kwargs,
        )
        return response
