import uuid
from datetime import datetime

from api.utils import CustomLogger, InferenceUtils
from api.v1.classes import TextGeneration
from api.v1.security import ensure_valid_token
from api.v1.services import MistralAIService
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from .chat_models import ChatCompletionResponse, ChatCompletionsRequest

logger = CustomLogger.get_logger(__name__)


# Fonction pour instancier TextGeneration
def get_text_generation(
    mistralai_service: MistralAIService = Depends(),
    inference_utils: InferenceUtils = Depends(),
) -> TextGeneration:
    return TextGeneration(mistralai_service, inference_utils)


router = APIRouter()


@router.post(
    "/completions",
    response_model=ChatCompletionResponse,
    tags=["chat"],
    summary="Get chat completions",
    dependencies=[Depends(ensure_valid_token)],
)
async def completions(
    request: Request,
    chat_request: ChatCompletionsRequest,
    text_generation: TextGeneration = Depends(get_text_generation),
):
    # Validation du modèle
    try:
        await text_generation.mistralai_service.check_model(chat_request.model)
    except ValueError as e:
        logger.error("Erreur lors du chargement du modèle : %s", e)
        raise HTTPException(status_code=404, detail="Modèle non trouvé") from e
    except ConnectionError as e:
        logger.error("Erreur lors de la connexion au service : %s", e)
        raise HTTPException(
            status_code=503, detail="Service indisponible ou modèle non trouvé"
        ) from e

    # Formatage des messages
    messages = text_generation.inference_utils.format_messages(
        chat_request.prompt, chat_request.input, chat_request.history
    )
    if not messages:
        raise HTTPException(status_code=400, detail="Aucune entrée fournie")

    # Génération d'un identifiant unique pour la tâche
    job_id: str = str(uuid.uuid4())

    # Log event to mongodb
    await request.app.mongodb_client.insert_one(
        "chat_completions_events",
        {
            "job_id": job_id,
            "model": chat_request.model,
            "messages": messages,
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
