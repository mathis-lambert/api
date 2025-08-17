from typing import Iterable, Optional
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel


class TextGenerationRequest(BaseModel):
    model: str
    messages: Iterable[ChatCompletionMessageParam]
    stream: Optional[bool] = None
