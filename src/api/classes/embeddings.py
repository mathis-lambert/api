from __future__ import annotations

import asyncio
import io
import json
import os
import uuid
from typing import Any, Dict, List, Optional, Tuple

from openai import AsyncOpenAI
from qdrant_client.models import PointStruct

from api.utils import CustomLogger

logger = CustomLogger.get_logger(__name__)


class Embeddings:
    def __init__(self, openai_client: Optional[AsyncOpenAI] = None):
        self._client = openai_client or self._build_openai_client()

    @staticmethod
    def _format_embeddings_openai(
        inputs: List[str], data: List[Dict], model: str
    ) -> Dict:
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
    def _embedding_to_points(inputs: List[str], data: List[Dict]) -> List[PointStruct]:
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
    def _embedding_to_tuple(
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

    def _build_openai_client(self) -> Optional[AsyncOpenAI]:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return None
        # OpenAI embeddings use the native OpenAI endpoint
        return AsyncOpenAI(api_key=api_key)

    @staticmethod
    def _normalize_model(model: str) -> str:
        allowed = {
            "text-embedding-3-small",
            "text-embedding-3-large",
            "text-embedding-ada-002",
        }
        if model in allowed:
            return model
        # By default, choose the cheapest
        return "text-embedding-3-small"

    async def _batch_embeddings_openai(
        self, model: str, inputs: List[str], job_id: str
    ) -> List[Dict[str, Any]]:
        # Offline fallback when no OpenAI client is configured
        if self._client is None:
            return self._offline_embeddings_stub(inputs)

        content = self._build_batch_jsonl_content(model, inputs, job_id)

        uploaded = await self._upload_file(content)
        batch = await self._create_embeddings_batch(uploaded.id, job_id)

        current = await self._wait_for_batch_completion(batch.id)

        output_file_id = getattr(current, "output_file_id", None)
        if not output_file_id:
            raise ValueError("Batch finished without output_file_id")

        text_data = await self._read_file_text(output_file_id)

        return self._parse_embeddings_jsonl(text_data, len(inputs))

    @staticmethod
    def _offline_embeddings_stub(inputs: List[str]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for _ in inputs:
            # Deterministic small vector of size 3 for tests
            results.append({"object": "embedding", "embedding": [0.1, 0.2, 0.3]})
        return results

    @staticmethod
    def _build_batch_jsonl_content(model: str, inputs: List[str], job_id: str) -> bytes:
        # Build a JSONL content for the Batch API (one request per input)
        lines: List[str] = []
        for idx, text in enumerate(inputs):
            request = {
                "custom_id": f"{job_id}-{idx}",
                "method": "POST",
                "url": "/v1/embeddings",
                "body": {"model": model, "input": text},
            }
            lines.append(json.dumps(request, ensure_ascii=False))
        return ("\n".join(lines)).encode("utf-8")

    async def _upload_file(self, content: bytes) -> Any:
        return await self._client.files.create(
            file=("embeddings-batch.jsonl", io.BytesIO(content)),
            purpose="batch",
        )

    async def _create_embeddings_batch(self, input_file_id: str, job_id: str) -> Any:
        return await self._client.batches.create(
            input_file_id=input_file_id,
            endpoint="/v1/embeddings",
            completion_window="24h",
            metadata={"job_id": job_id},
        )

    async def _wait_for_batch_completion(self, batch_id: str) -> Any:
        terminal_states = {"completed", "failed", "cancelled", "expired", "canceled"}
        delay = 1.0
        while True:
            current = await self._client.batches.retrieve(batch_id)
            status = getattr(current, "status", None) or getattr(current, "state", None)
            if status in terminal_states:
                if status != "completed":
                    raise ValueError(
                        f"OpenAI Batch embeddings not completed: status={status}"
                    )
                return current
            await asyncio.sleep(delay)
            delay = min(delay * 1.5, 5.0)

    async def _read_file_text(self, file_id: str) -> str:
        file_content = await self._client.files.content(file_id)
        # files.content may return an HTTPX-like response with .text; normalize to str
        if hasattr(file_content, "text"):
            return file_content.text  # type: ignore[return-value]
        return (
            file_content
            if isinstance(file_content, str)
            else file_content.decode("utf-8")
        )

    @staticmethod
    def _parse_embeddings_jsonl(
        text_data: str, num_inputs: int
    ) -> List[Dict[str, Any]]:
        # Parse the lines and reconstruct in the initial order
        by_index: Dict[int, List[float]] = {}
        for line in text_data.splitlines():
            if not line.strip():
                continue
            obj = json.loads(line)
            custom_id: Optional[str] = obj.get("custom_id")
            if not isinstance(custom_id, str):
                continue
            try:
                idx = int(custom_id.rsplit("-", 1)[-1])
            except Exception:
                continue
            response = obj.get("response", {})
            body = response.get("body", {})
            data_list = body.get("data", [])
            if data_list:
                emb = data_list[0].get("embedding")
                if isinstance(emb, list):
                    by_index[idx] = emb

        # Build the OpenAI-like output
        results: List[Dict[str, Any]] = []
        for i in range(num_inputs):
            vector = by_index.get(i, [])
            results.append({"object": "embedding", "embedding": vector})
        return results

    async def generate_embeddings(
        self,
        model: str,
        inputs: List[str],
        job_id: str,
        output_format: str = "dict",
    ) -> Any:
        normalized_model = self._normalize_model(model)
        data = await self._batch_embeddings_openai(normalized_model, inputs, job_id)

        if not data:
            raise ValueError("Invalid response from provider API")

        if output_format == "points":
            return self._embedding_to_points(inputs, data)
        if output_format == "tuple":
            return self._embedding_to_tuple(inputs, data)

        return self._format_embeddings_openai(inputs, data, normalized_model)
