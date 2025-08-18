from __future__ import annotations

import asyncio
import io
import json
import os
import uuid
from typing import Any, Dict, List, Optional, Tuple, Literal

from openai import AsyncOpenAI
from qdrant_client.models import PointStruct

from api.utils import CustomLogger

logger = CustomLogger.get_logger(__name__)

EMBEDDING_MODELS = {
    "text-embedding-3-small": {
        "vector_size": 1536,
    },
    "text-embedding-3-large": {
        "vector_size": 3072,
    },
}


Mode = Literal["auto", "realtime", "batch"]
OutputFormat = Literal["dict", "points", "tuple"]


class Embeddings:
    """
    Async embeddings helper that supports both:
      1) Realtime requests via /v1/embeddings
      2) Asynchronous Batch API via /v1/batches

    Public API:
        await Embeddings(...).generate_embeddings(
            model: str,
            inputs: List[str],
            mode: Literal["auto", "realtime", "batch"] = "auto",
            job_id: Optional[str] = None,
            output_format: Literal["dict", "points", "tuple"] = "dict",
        ) -> Any

    Output formats:
        - "dict": OpenAI-like list object
        - "points": List[PointStruct] for Qdrant
        - "tuple": (ids, vectors, payloads)
    """

    def __init__(
        self,
        openai_client: Optional[AsyncOpenAI] = None,
        *,
        batch_threshold: int = 256,  # switch to Batch API if inputs >= threshold when mode="auto"
    ):
        self._client = openai_client or self._build_openai_client()
        self.batch_threshold = max(1, int(batch_threshold))

    # ----------------------------- Core entrypoint -----------------------------
    async def generate_embeddings(
        self,
        model: str,
        inputs: List[str],
        *,
        mode: Mode = "auto",
        job_id: Optional[str] = None,
        output_format: OutputFormat = "dict",
    ) -> Any:
        if not isinstance(inputs, list) or not all(isinstance(x, str) for x in inputs):
            raise TypeError("inputs must be List[str]")

        normalized_model = self._normalize_model(model)

        if mode == "auto":
            chosen = "batch" if len(inputs) >= self.batch_threshold else "realtime"
        else:
            chosen = mode

        if chosen == "realtime":
            data = await self._embeddings_realtime(normalized_model, inputs)
        else:
            # Batch API requires a job id; generate if not provided
            job_id = job_id or f"emb-{uuid.uuid4().hex[:12]}"
            data = await self._embeddings_batch_api(normalized_model, inputs, job_id)

        if not data:
            raise ValueError("Empty embeddings response")

        if output_format == "points":
            return self._embedding_to_points(inputs, data)
        if output_format == "tuple":
            return self._embedding_to_tuple(inputs, data)
        return self._format_embeddings_openai(inputs, data, normalized_model)

    # ----------------------------- Realtime path -------------------------------
    async def _embeddings_realtime(
        self, model: str, inputs: List[str]
    ) -> List[Dict[str, Any]]:
        if self._client is None:
            logger.warning(
                "OpenAI client not configured; returning offline stub embeddings"
            )
            return self._offline_embeddings_stub(inputs)

        # The embeddings endpoint accepts a list of inputs directly
        resp = await self._client.embeddings.create(model=model, input=inputs)
        # Normalize to a simple list[{object:"embedding", embedding:[...]}]
        return [
            {"object": "embedding", "embedding": item.embedding}
            for item in getattr(resp, "data", [])
        ]

    # ------------------------------ Batch path --------------------------------
    async def _embeddings_batch_api(
        self, model: str, inputs: List[str], job_id: str
    ) -> List[Dict[str, Any]]:
        if self._client is None:
            logger.warning(
                "OpenAI client not configured; returning offline stub embeddings"
            )
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

    # ------------------------------ Helpers -----------------------------------
    @staticmethod
    def _normalize_model(model: str) -> str:
        return model if model in EMBEDDING_MODELS else "text-embedding-3-small"

    def _build_openai_client(self) -> Optional[AsyncOpenAI]:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set; Embeddings will use offline stub")
            return None
        return AsyncOpenAI(api_key=api_key)

    @staticmethod
    def _format_embeddings_openai(
        inputs: List[str], data: List[Dict], model: str
    ) -> Dict[str, Any]:
        return {
            "id": f"embd-{uuid.uuid4().hex[:12]}",
            "object": "list",
            "model": model,
            "data": [
                {"object": "embedding", "embedding": emb["embedding"], "index": i}
                for i, emb in enumerate(data)
                if emb.get("object") == "embedding"
            ],
            "usage": {"prompt_tokens": 0, "total_tokens": 0},
        }

    @staticmethod
    def _embedding_to_points(inputs: List[str], data: List[Dict]) -> List[PointStruct]:
        # Qdrant PointStruct accepts dicts; keep ids stable by index
        return [
            {
                "id": i,
                "vector": emb["embedding"],
                "payload": {"source_text": inputs[i]},
            }
            for i, emb in enumerate(data)
            if emb.get("object") == "embedding"
        ]

    @staticmethod
    def _embedding_to_tuple(
        inputs: List[str], data: List[Dict]
    ) -> Tuple[List[int], List[List[float]], List[Dict]]:
        ids: List[int] = []
        vectors: List[List[float]] = []
        payloads: List[Dict] = []
        for i, emb in enumerate(data):
            if emb.get("object") == "embedding":
                ids.append(i)
                vectors.append(emb["embedding"])  # type: ignore[index]
                payloads.append({"source_text": inputs[i]})
        return ids, vectors, payloads

    # ---------------------------- Batch internals ------------------------------
    @staticmethod
    def _build_batch_jsonl_content(model: str, inputs: List[str], job_id: str) -> bytes:
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
        terminal = {"completed", "failed", "cancelled", "canceled", "expired"}
        delay = 1.0
        while True:
            cur = await self._client.batches.retrieve(batch_id)
            status = getattr(cur, "status", None) or getattr(cur, "state", None)
            if status in terminal:
                if status != "completed":
                    raise ValueError(f"Batch not completed: status={status}")
                return cur
            await asyncio.sleep(delay)
            delay = min(delay * 1.5, 5.0)

    async def _read_file_text(self, file_id: str) -> str:
        resp = await self._client.files.content(file_id)
        # Try common async interfaces
        # 1) httpx-like: .text
        text = getattr(resp, "text", None)
        if isinstance(text, str):
            return text
        # 2) aio stream with .read()
        read = getattr(resp, "read", None)
        if callable(read):
            data = await read()
            return (
                data.decode("utf-8")
                if isinstance(data, (bytes, bytearray))
                else str(data)
            )
        # 3) raw bytes
        if isinstance(resp, (bytes, bytearray)):
            return resp.decode("utf-8")
        return str(resp)

    @staticmethod
    def _parse_embeddings_jsonl(
        text_data: str, num_inputs: int
    ) -> List[Dict[str, Any]]:
        by_index: Dict[int, List[float]] = {}
        for line in text_data.splitlines():
            if not line.strip():
                continue
            obj = json.loads(line)
            custom_id = obj.get("custom_id")
            if not isinstance(custom_id, str):
                continue
            try:
                idx = int(custom_id.rsplit("-", 1)[-1])
            except Exception:
                continue
            body = obj.get("response", {}).get("body", {})
            data_list = body.get("data", [])
            if data_list:
                emb = data_list[0].get("embedding")
                if isinstance(emb, list):
                    by_index[idx] = emb
        # Rebuild in input order
        return [
            {"object": "embedding", "embedding": by_index.get(i, [])}
            for i in range(num_inputs)
        ]

    # ------------------------------ Offline stub -------------------------------
    @staticmethod
    def _offline_embeddings_stub(inputs: List[str]) -> List[Dict[str, Any]]:
        return [{"object": "embedding", "embedding": [0.1, 0.2, 0.3]} for _ in inputs]
