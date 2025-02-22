import json
from typing import Any, Dict, List

from api.databases import MongoDBConnector, QdrantConnector
from api.v1.security import ensure_valid_token, get_current_user
from api.v1.services import (
    check_collection_ownership,
    get_mongo_client,
    get_qdrant_client,
)
from bson import ObjectId
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from .vector_db_models import CollectionsResponse

router = APIRouter()


# Modèles de données
class VectorData(BaseModel):
    id: int
    vector: List[float]
    payload: Dict[str, Any] = {}


class QueryVector(BaseModel):
    vector: List[float]
    top: int = 5


# Route pour lister les collections
@router.get(
    "/collections",
    response_model=CollectionsResponse,
    summary="Lister les collections créées par l'utilisateur",
    dependencies=[Depends(ensure_valid_token)],
)
async def list_collections(
    qdrant_client: QdrantConnector = Depends(get_qdrant_client),
    mongodb_client: MongoDBConnector = Depends(get_mongo_client),
    user: dict = Depends(get_current_user),
):
    """Liste les collections créées par l'utilisateur."""
    user_collections = await mongodb_client.find_many(
        "vector_db_collections", {"user_id": ObjectId(user["_id"])}
    )

    qdrant_collections = []
    for collection in user_collections:
        collection_info = await qdrant_client.get_collection(collection["name"])
        qdrant_collections.append(
            {
                "name": collection["name"],
                "info": collection_info,
            }
        )

    return {"collections": qdrant_collections}


# Route pour avoir des informations sur une collection
@router.get(
    "/collections/{collection_name}",
    summary="Lister les informations sur une collection",
    dependencies=[Depends(ensure_valid_token), Depends(check_collection_ownership)],
)
async def get_collection(
    collection_name: str,
    qdrant_client: QdrantConnector = Depends(get_qdrant_client),
):
    """Liste les informations sur une collection."""
    collection = await qdrant_client.get_collection(collection_name)

    if not collection:
        return {"message": f"La collection '{collection_name}' n'existe pas."}

    collection_json = collection.model_dump_json()

    return json.loads(collection_json)
