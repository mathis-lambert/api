from fastapi import APIRouter, Body, Depends, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

from api.classes import OpenRouterProxy
from api.databases import MongoDBConnector
from api.v1.security import (
    ensure_valid_api_key_or_token,
    get_current_user_with_api_key_or_token,
)
from api.v1.services import get_mongo_client, get_openrouter_proxy

from ..llm_proxy import proxy_openrouter_request
from .responses_models import ResponsesRequest

router = APIRouter()


@router.post(
    "",
    summary="Create response",
    description="""Generate responses in OpenAI Responses format.

    - When `stream` = `false` (default), returns a `response` object.
    - When `stream` = `true`, returns a SSE stream where each `data:` contains
      a serialized response event.
    """,
    response_model=None,
    dependencies=[Depends(ensure_valid_api_key_or_token)],
)
async def create_response(
    request: Request,
    responses_request: ResponsesRequest = Body(
        ...,
        examples={
            "non_stream": {
                "summary": "Standard request (JSON)",
                "value": {
                    "model": "openai/gpt-4.1-mini",
                    "input": "Hello!",
                    "stream": False,
                },
            },
            "stream": {
                "summary": "Streaming request (SSE)",
                "value": {
                    "model": "openai/gpt-4.1-mini",
                    "input": "Hello!",
                    "stream": True,
                },
            },
        },
    ),
    openrouter_proxy: OpenRouterProxy = Depends(get_openrouter_proxy),
    user: dict = Depends(get_current_user_with_api_key_or_token),
    mongodb_client: MongoDBConnector = Depends(get_mongo_client),
):
    return await proxy_openrouter_request(
        request=request,
        fallback_body=responses_request.model_dump(exclude_none=True),
        openrouter_proxy=openrouter_proxy,
        mongodb_client=mongodb_client,
        user=user,
        endpoint="/responses",
        operation="responses",
    )
