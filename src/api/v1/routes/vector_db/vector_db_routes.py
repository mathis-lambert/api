import json

from bson import ObjectId
from fastapi import APIRouter, Depends
from qdrant_client.models import CollectionInfo

from api.databases import MongoDBConnector, QdrantConnector
from api.v1.security import (
    ensure_valid_api_key_or_token,
    get_current_user_with_api_key_or_token,
)
from api.v1.services import (
    check_collection_ownership,
    get_mongo_client,
    get_qdrant_client,
)

from .vector_db_models import CollectionsResponse

router = APIRouter()


# Route pour lister les collections
@router.get(
    "/collections",
    response_model=CollectionsResponse,
    summary="Lister les collections créées par l'utilisateur",
    dependencies=[Depends(ensure_valid_api_key_or_token)],
)
async def list_collections(
    qdrant_client: QdrantConnector = Depends(get_qdrant_client),
    mongodb_client: MongoDBConnector = Depends(get_mongo_client),
    user: dict = Depends(get_current_user_with_api_key_or_token),
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
    response_model=CollectionInfo,
    summary="Lister les informations sur une collection",
    dependencies=[
        Depends(ensure_valid_api_key_or_token),
        Depends(check_collection_ownership),
    ],
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
