from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str
    content: str


class ChatCompletionsRequest(BaseModel):
    model: str
    messages: Optional[List[Message]] = None
    # Compat internes
    prompt: Optional[str] = None
    input: Optional[str] = None
    history: Optional[List[Message]] = None
    temperature: float = 0.7
    max_tokens: int = 1024
    top_p: float = 0.9
    stream: bool = False
    # Tool calling (OpenAI-compat)
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Any] = None


class ToolCallFunction(BaseModel):
    name: str
    arguments: str


class ToolCall(BaseModel):
    id: str
    type: str
    function: ToolCallFunction


class ChatMessage(BaseModel):
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    refusal: Optional[str] = None
    annotations: List[dict] = []


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    logprobs: Optional[dict] = None
    finish_reason: Optional[str] = None


class TokenDetails(BaseModel):
    cached_tokens: int = 0
    audio_tokens: int = 0


class CompletionTokenDetails(BaseModel):
    reasoning_tokens: int = 0
    audio_tokens: int = 0
    accepted_prediction_tokens: int = 0
    rejected_prediction_tokens: int = 0


class ChatUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    prompt_tokens_details: TokenDetails = TokenDetails()
    completion_tokens_details: CompletionTokenDetails = CompletionTokenDetails()


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: ChatUsage
    service_tier: str = "default"
    system_fingerprint: Optional[str] = None


# Streaming chunk DTOs
class ChatDelta(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None


class ChatChunkChoice(BaseModel):
    index: int
    delta: ChatDelta
    logprobs: Optional[dict] = None
    finish_reason: Optional[str] = None


class ChatCompletionChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatChunkChoice]
    system_fingerprint: Optional[str] = None
