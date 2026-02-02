from typing import Any, Dict, Iterable, Optional

from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, ConfigDict


class ChatCompletionsRequest(BaseModel):
    model: str
    messages: Iterable[ChatCompletionMessageParam]
    stream: Optional[bool] = None
    stream_options: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra="allow")
