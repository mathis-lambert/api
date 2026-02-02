import json
import uuid

from fastapi import APIRouter, Depends, HTTPException

from api.databases import MongoDBConnector
from api.v1.security import (
    ensure_valid_api_key_or_token,
    get_current_user_with_api_key_or_token,
)
from api.v1.services import get_embeddings, get_mongo_client

from .embeddings_models import EmbeddingsRequest, EmbeddingsResponse

router = APIRouter()


@router.post(
    "",
    summary="Get embeddings",
    response_model=EmbeddingsResponse,
    dependencies=[Depends(ensure_valid_api_key_or_token)],
)
async def embeddings(
    body: EmbeddingsRequest,
    embeddings=Depends(get_embeddings),
    user: dict = Depends(get_current_user_with_api_key_or_token),
    mongodb_client: MongoDBConnector = Depends(get_mongo_client),
):
    """Get embeddings for the input text."""
    # Validation of the input
    if not body.input:
        raise HTTPException(status_code=400, detail="No input provided")

    job_id: str = str(uuid.uuid4())

    # Log event to MongoDB
    await mongodb_client.log_event(
        user["_id"], job_id, "embeddings", json.loads(body.model_dump_json())
    )

    # Generation of embeddings
    embeddings_data = await embeddings.generate_embeddings(
        model=body.model,
        inputs=body.input,
        job_id=job_id,
    )

    return embeddings_data
