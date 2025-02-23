from pydantic import BaseModel


class ChatCompletionsRequest(BaseModel):
    model: str = "mistral-small-latest"
    input: str = "Hello, how are you?"
    prompt: str = "You are a helpful assistant."
    history: list = []
    temperature: float = 0.7
    max_tokens: int = 512
    top_p: float = 1.0
    stream: bool = False


class ChatCompletionResponse(BaseModel):
    response: str
    job_id: str
