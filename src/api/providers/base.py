from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, Iterable, List, Optional, Tuple


@dataclass
class ModelCard:
    id: str
    provider: str
    object: str = "model"
    owned_by: Optional[str] = None
    context_length: Optional[int] = None
    description: Optional[str] = None


class Provider(ABC):
    name: str

    @abstractmethod
    async def list_models(self) -> List[ModelCard]:
        ...

    @abstractmethod
    async def get_model(self, model_id: str) -> ModelCard:
        ...

    # Chat completions
    @abstractmethod
    async def chat_complete(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        top_p: float,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
    ) -> Dict[str, Any]:
        ...

    @abstractmethod
    async def chat_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        top_p: float,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
    ) -> AsyncGenerator[Tuple[str, Optional[str]], None]:
        ...

    # Embeddings
    @abstractmethod
    async def create_embeddings(
        self, model: str, inputs: Iterable[str]
    ) -> Dict[str, Any]:
        ...


