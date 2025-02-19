import json
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from api.utils import InferenceUtils, CustomLogger
from api.v1.services import MistralAIService

logger = CustomLogger.get_logger(__name__)

router = APIRouter()


class ChatCompletionRequest(BaseModel):
    model: str
    input: str
    prompt: str = "You are a helpful assistant."
    history: list = []
    temperature: float = 0.7
    max_tokens: int = 512
    top_p: float = 1.0
    stream: bool = False


async def generate_stream_response(
        mistralai_service: MistralAIService,
        inference_utils: InferenceUtils,
        model: str,
        messages: list,
        temperature: float,
        max_tokens: int,
        top_p: float,
        job_id: str
) -> AsyncGenerator[str, None]:
    final_response = ""
    async for response in mistralai_service.stream(model=model, messages=messages, temperature=temperature,
                                                   max_tokens=max_tokens, top_p=top_p):
        final_response += response
        yield json.dumps(inference_utils.format_response(final_response, job_id))


@router.post("/completions", tags=["chat"], summary="Get chat completions")
async def completions(
        request: ChatCompletionRequest,
        inference_utils: InferenceUtils = Depends(),
        mistralai_service: MistralAIService = Depends()
):
    # Validation du modèle
    try:
        await mistralai_service.check_model(request.model)
    except ValueError as e:
        logger.error("Erreur lors du chargement du modèle : %s", e)
        raise HTTPException(status_code=404, detail="Modèle non trouvé")
    except ConnectionError as e:
        logger.error("Erreur lors de la connexion au service : %s", e)
        raise HTTPException(status_code=503, detail="Service indisponible")

    # Formatage des messages
    messages = inference_utils.format_messages(request.prompt, request.input, request.history)

    if not messages:
        raise HTTPException(status_code=400, detail="Aucune entrée fournie")

    # Génération d'un identifiant unique pour la tâche
    job_id: str = str(uuid.uuid4())

    # Choix entre streaming ou réponse complète
    if request.stream:
        return StreamingResponse(
            generate_stream_response(mistralai_service, inference_utils, request.model, messages, request.temperature,
                                     request.max_tokens, request.top_p, job_id),
            media_type="text/event-stream"
        )
    else:
        response = await mistralai_service.complete(model=request.model, messages=messages,
                                                    temperature=request.temperature,
                                                    max_tokens=request.max_tokens, top_p=request.top_p)
        return JSONResponse(inference_utils.format_response(response, job_id))
