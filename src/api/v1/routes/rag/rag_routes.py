import json
import uuid
from datetime import datetime

from api.databases import MongoDBConnector
from api.utils import CustomLogger
from api.v1.security import ensure_valid_token, get_current_user
from api.v1.services import (
    RagService,
    check_collection_non_existence,
    check_collection_ownership,
    get_mongo_client,
    get_rag_service,
)
from fastapi import APIRouter, Depends, HTTPException

from .rag_models import (
    RagEncodeRequest,
    RagEncodeResponse,
    RagRetrieveRequest,
    RagRetrieveResponse,
)

router = APIRouter()

logger = CustomLogger.get_logger(__name__)


@router.post(
    "/encode/{collection_name}",
    response_model=RagEncodeResponse,
    summary="Encode text to a collection",
    dependencies=[Depends(ensure_valid_token), Depends(check_collection_non_existence)],
)
async def encode(
    collection_name: str,
    body: RagEncodeRequest,
    rag_service: RagService = Depends(get_rag_service),
    mongodb_client: MongoDBConnector = Depends(get_mongo_client),
    user: dict = Depends(get_current_user),
):
    """Encode text to a collection."""
    # Validation de l'entrée
    if not body.chunks:
        raise HTTPException(status_code=400, detail="Aucune entrée fournie")

    job_id: str = str(uuid.uuid4())

    await rag_service.encode_to_collection(
        collection_name,
        body.chunks,
        body.model,
        body.encoding_format,
    )

    # Save collection_name
    await mongodb_client.insert_one(
        "vector_db_collections",
        {
            "name": collection_name,
            "encoding_format": body.encoding_format,
            "model": body.model,
            "chunks": body.chunks,
            "user_id": mongodb_client.object_id(user["_id"]),
            "created_at": datetime.now(),
        },
    )

    # Log event to mongodb
    await mongodb_client.log_event(
        user["_id"], job_id, "encode", json.loads(body.model_dump_json())
    )

    return {
        "collection_name": body.collection_name,
        "success": True,
    }


@router.post(
    "/retrieve/{collection_name}",
    response_model=RagRetrieveResponse,
    summary="Retrieve text from a collection",
    dependencies=[Depends(ensure_valid_token), Depends(check_collection_ownership)],
)
async def retrieve(
    collection_name: str,
    body: RagRetrieveRequest,
    rag_service: RagService = Depends(get_rag_service),
    mongodb_client: MongoDBConnector = Depends(get_mongo_client),
    user: dict = Depends(get_current_user),
):
    """Retrieve text from a collection."""
    # Validation de l'entrée
    if not input:
        raise HTTPException(status_code=400, detail="Aucune entrée fournie")

    job_id: str = str(uuid.uuid4())

    results = await rag_service.retrieve_in_collection(
        collection_name,
        body.query,
        body.model,
        body.limit,
    )

    # Log event to mongodb
    await mongodb_client.log_event(
        user["_id"], job_id, "retrieve", json.loads(body.model_dump_json())
    )

    return {
        "collection_name": collection_name,
        "results": results,
        "success": True,
    }
