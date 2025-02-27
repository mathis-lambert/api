import uuid
from datetime import datetime

from api.classes import TextGeneration
from api.databases import MongoDBConnector
from api.utils import CustomLogger
from api.v1.security import (
    ensure_valid_api_key_or_token,
    get_current_user_with_api_key_or_token,
)
from api.v1.services import get_mongo_client, get_text_generation
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from .chat_models import ChatCompletionResponse, ChatCompletionsRequest

logger = CustomLogger.get_logger(__name__)

# Fonction pour instancier TextGeneration


router = APIRouter()


@router.post(
    "/completions",
    response_model=ChatCompletionResponse,
    summary="Get chat completions",
    dependencies=[Depends(ensure_valid_api_key_or_token)],
)
async def completions(
    chat_request: ChatCompletionsRequest,
    text_generation: TextGeneration = Depends(get_text_generation),
    user: dict = Depends(get_current_user_with_api_key_or_token),
    mongodb_client: MongoDBConnector = Depends(get_mongo_client),
):
    # Validation du modèle
    await text_generation.mistralai_service.check_model(chat_request.model)

    # Formatage des messages
    messages = text_generation.inference_utils.format_messages(
        chat_request.prompt, chat_request.input, chat_request.history
    )
    if not messages:
        raise HTTPException(status_code=400, detail="Aucune entrée fournie")

    # Génération d'un identifiant unique pour la tâche
    job_id: str = str(uuid.uuid4())

    # Log event to mongodb
    await mongodb_client.log_event(
        user["_id"],
        job_id,
        "chat_completions",
        {
            "model": chat_request.model,
            "messages": messages,
            "temperature": chat_request.temperature,
            "max_tokens": chat_request.max_tokens,
            "top_p": chat_request.top_p,
            "stream": chat_request.stream,
            "job_id": job_id,
            "timestamp": datetime.now(),
        },
    )

    # Choix entre streaming ou réponse complète
    if chat_request.stream:
        return StreamingResponse(
            text_generation.generate_stream_response(
                model=chat_request.model,
                messages=messages,
                temperature=chat_request.temperature,
                max_tokens=chat_request.max_tokens,
                top_p=chat_request.top_p,
                job_id=job_id,
            ),
            media_type="text/event-stream",
        )
    else:
        response = await text_generation.complete(
            model=chat_request.model,
            messages=messages,
            temperature=chat_request.temperature,
            max_tokens=chat_request.max_tokens,
            top_p=chat_request.top_p,
            job_id=job_id,
        )
        return JSONResponse(response)
