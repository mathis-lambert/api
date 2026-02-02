import hashlib
import json
import time
import uuid
from typing import Any, AsyncGenerator, Dict, Tuple

import httpx
from fastapi import Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

from api.classes import OpenRouterProxy
from api.databases import MongoDBConnector


def _simple_error_payload(message: str) -> Dict[str, Any]:
    return {"error": message}


async def _read_payload(
    request: Request, fallback_body: Dict[str, Any]
) -> Tuple[Dict[str, Any] | None, JSONResponse | None, Dict[str, Any]]:
    raw_body_bytes = await request.body()
    meta = {
        "request_bytes": len(raw_body_bytes),
        "request_hash": hashlib.sha256(raw_body_bytes).hexdigest()
        if raw_body_bytes
        else None,
    }
    try:
        raw_body = json.loads(raw_body_bytes) if raw_body_bytes else fallback_body
    except json.JSONDecodeError:
        return (
            None,
            JSONResponse(
                status_code=400,
                content=_simple_error_payload("Invalid JSON body"),
            ),
            meta,
        )
    if not isinstance(raw_body, dict):
        return (
            None,
            JSONResponse(
                status_code=400,
                content=_simple_error_payload("Invalid request body"),
            ),
            meta,
        )
    return raw_body.copy(), None, meta


def _build_log_doc(
    *,
    user: dict,
    job_id: str,
    payload: Dict[str, Any],
    meta: Dict[str, Any],
    operation: str,
    endpoint: str,
) -> Dict[str, Any]:
    messages = payload.get("messages")
    input_value = payload.get("input")
    return {
        "user_id": user.get("_id"),
        "job_id": job_id,
        "provider": "openrouter",
        "operation": operation,
        "endpoint": endpoint,
        "model": payload.get("model"),
        "stream": bool(payload.get("stream", False)),
        "request_hash": meta.get("request_hash"),
        "request_bytes": meta.get("request_bytes"),
        "messages_count": len(messages) if isinstance(messages, list) else None,
        "input_count": len(input_value) if isinstance(input_value, list) else None,
        "status_code": None,
        "latency_ms": None,
        "usage": None,
        "provider_response_id": None,
        "finish_reason": None,
        "error": None,
    }


def _response_from_upstream(response: httpx.Response) -> Response:
    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type=response.headers.get("content-type"),
    )


def _extract_usage(
    response: httpx.Response,
) -> Tuple[dict | None, str | None, str | None]:
    usage = None
    provider_response_id = None
    finish_reason = None
    if "application/json" in response.headers.get("content-type", ""):
        try:
            response_payload = response.json()
            if isinstance(response_payload, dict):
                provider_response_id = response_payload.get("id")
                usage = response_payload.get("usage")
                choices = response_payload.get("choices") or []
                if choices:
                    finish_reason = choices[0].get("finish_reason")
        except Exception:
            pass
    return usage, provider_response_id, finish_reason


async def _handle_non_stream(
    *,
    openrouter_proxy: OpenRouterProxy,
    mongodb_client: MongoDBConnector,
    endpoint: str,
    job_id: str,
    payload: Dict[str, Any],
) -> JSONResponse | Response:
    start_time = time.perf_counter()
    try:
        response = await openrouter_proxy.post(endpoint, payload)
    except httpx.RequestError as exc:
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        await mongodb_client.update_llm_request(
            job_id,
            {
                "status_code": 502,
                "latency_ms": latency_ms,
                "error": str(exc),
            },
        )
        return JSONResponse(status_code=502, content=_simple_error_payload(str(exc)))

    latency_ms = int((time.perf_counter() - start_time) * 1000)
    status_code = response.status_code
    if status_code >= 400:
        await mongodb_client.update_llm_request(
            job_id,
            {
                "status_code": status_code,
                "latency_ms": latency_ms,
                "error": response.text,
            },
        )
        return _response_from_upstream(response)

    usage, provider_response_id, finish_reason = _extract_usage(response)
    await mongodb_client.update_llm_request(
        job_id,
        {
            "status_code": status_code,
            "latency_ms": latency_ms,
            "usage": usage,
            "provider_response_id": provider_response_id,
            "finish_reason": finish_reason,
        },
    )
    return _response_from_upstream(response)


async def _handle_stream(
    *,
    openrouter_proxy: OpenRouterProxy,
    mongodb_client: MongoDBConnector,
    endpoint: str,
    job_id: str,
    payload: Dict[str, Any],
) -> JSONResponse | Response | StreamingResponse:
    start_time = time.perf_counter()
    stream_cm = openrouter_proxy.stream(endpoint, payload)
    try:
        response = await stream_cm.__aenter__()
    except httpx.RequestError as exc:
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        await mongodb_client.update_llm_request(
            job_id,
            {
                "status_code": 502,
                "latency_ms": latency_ms,
                "error": str(exc),
            },
        )
        return JSONResponse(status_code=502, content=_simple_error_payload(str(exc)))

    status_code = response.status_code
    if status_code >= 400:
        await stream_cm.__aexit__(None, None, None)
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        await mongodb_client.update_llm_request(
            job_id,
            {
                "status_code": status_code,
                "latency_ms": latency_ms,
                "error": response.text,
            },
        )
        return _response_from_upstream(response)

    async def event_stream() -> AsyncGenerator[bytes, None]:
        error: str | None = None
        try:
            async for chunk in response.aiter_bytes():
                yield chunk
        except Exception as exc:
            error = str(exc)
            raise
        finally:
            await stream_cm.__aexit__(None, None, None)
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            update = {
                "status_code": status_code,
                "latency_ms": latency_ms,
                "usage": None,
                "provider_response_id": None,
                "finish_reason": None,
            }
            if error is not None:
                update["error"] = error
            await mongodb_client.update_llm_request(job_id, update)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def proxy_openrouter_request(
    *,
    request: Request,
    fallback_body: Dict[str, Any],
    openrouter_proxy: OpenRouterProxy,
    mongodb_client: MongoDBConnector,
    user: dict,
    endpoint: str,
    operation: str,
) -> JSONResponse | Response | StreamingResponse:
    if not openrouter_proxy.is_configured():
        return JSONResponse(
            status_code=503,
            content=_simple_error_payload("OpenRouter client not configured"),
        )

    payload, error_response, meta = await _read_payload(request, fallback_body)
    if error_response is not None:
        return error_response
    if payload is None:
        return JSONResponse(
            status_code=500,
            content=_simple_error_payload("Invalid request payload"),
        )

    job_id = str(uuid.uuid4())
    await mongodb_client.log_llm_request(
        _build_log_doc(
            user=user,
            job_id=job_id,
            payload=payload,
            meta=meta,
            operation=operation,
            endpoint=endpoint,
        )
    )

    if payload.get("stream"):
        return await _handle_stream(
            openrouter_proxy=openrouter_proxy,
            mongodb_client=mongodb_client,
            endpoint=endpoint,
            job_id=job_id,
            payload=payload,
        )

    return await _handle_non_stream(
        openrouter_proxy=openrouter_proxy,
        mongodb_client=mongodb_client,
        endpoint=endpoint,
        job_id=job_id,
        payload=payload,
    )
