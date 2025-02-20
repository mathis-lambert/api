import json
from typing import AsyncGenerator

from api.utils import InferenceUtils
from api.v1.services import MistralAIService


class TextGeneration:
    def __init__(
        self, mistralai_service: MistralAIService, inference_utils: InferenceUtils
    ):
        self.mistralai_service = mistralai_service
        self.inference_utils = inference_utils

    async def generate_stream_response(
        self,
        model: str,
        messages: list,
        temperature: float,
        max_tokens: int,
        top_p: float,
        job_id: str,
    ) -> AsyncGenerator[str, None]:
        final_response = ""
        async for response in self.mistralai_service.stream(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
        ):
            final_response += response
            yield json.dumps(
                self.inference_utils.format_response(final_response, job_id)
            )

    async def complete(
        self,
        model: str,
        messages: list,
        temperature: float,
        max_tokens: int,
        top_p: float,
        job_id: str,
    ):
        response = await self.mistralai_service.complete(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
        )
        return self.inference_utils.format_response(response, job_id)
