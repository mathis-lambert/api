from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class ResponsesRequest(BaseModel):
    model: str
    input: Any
    stream: Optional[bool] = None

    model_config = ConfigDict(extra="allow")
