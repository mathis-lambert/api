from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class Architecture(BaseModel):
    input_modalities: Optional[List[str]] = None
    output_modalities: Optional[List[str]] = None
    tokenizer: Optional[str] = None
    instruct_type: Optional[str] = None


class TopProvider(BaseModel):
    is_moderated: Optional[bool] = None
    context_length: Optional[int] = None
    max_completion_tokens: Optional[int] = None


class Pricing(BaseModel):
    prompt: Optional[str] = None
    completion: Optional[str] = None
    image: Optional[str] = None
    request: Optional[str] = None
    web_search: Optional[str] = None
    internal_reasoning: Optional[str] = None
    input_cache_read: Optional[str] = None
    input_cache_write: Optional[str] = None


class EndpointDTO(BaseModel):
    context_length: Optional[int] = None
    pricing: Optional[Pricing] = None
    provider_name: Optional[str] = None
    tag: Optional[str] = None
    quantization: Optional[str] = None
    max_completion_tokens: Optional[int] = None
    max_prompt_tokens: Optional[int] = None
    supported_parameters: Optional[List[str]] = None
    status: Optional[int] = None
    uptime_last_30m: Optional[int] = None


class ModelDTO(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    created: Optional[int] = None
    description: Optional[str] = None
    architecture: Optional[Architecture] = None
    top_provider: Optional[TopProvider] = None
    pricing: Optional[Pricing] = None
    canonical_slug: Optional[str] = None
    context_length: Optional[int] = None
    hugging_face_id: Optional[str] = None
    per_request_limits: Optional[Dict[str, Any]] = None
    supported_parameters: Optional[List[str]] = None
    endpoints: Optional[List[EndpointDTO]] = None


class ListModelsResponse(BaseModel):
    data: List[ModelDTO]
