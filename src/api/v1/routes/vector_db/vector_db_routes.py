import json
from typing import Any, Dict, List

from api.databases import QdrantConnector
from api.v1.security import ensure_valid_token
from api.v1.services import check_collection_ownership, get_qdrant_client
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

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
    summary="Lister les collections créées par l'utilisateur",
    dependencies=[Depends(ensure_valid_token)],
)
async def list_collections(request: Request):
    """Liste les collections créées par l'utilisateur."""
    qdrant_client = request.app.qdrant_client
    collections_response = await qdrant_client.list_collections()
    collections = collections_response.collections
    return {"collections": collections}


# Route pour avoir des informations sur une collection
@router.get(
    "/collections/{collection_name}",
    summary="Lister les informations sur une collection",
    dependencies=[Depends(ensure_valid_token), Depends(check_collection_ownership)],
)
async def get_collection(
    collection_name: str, qdrant_client: QdrantConnector = Depends(get_qdrant_client)
):
    """Liste les informations sur une collection."""
    collection = await qdrant_client.get_collection(collection_name)

    if not collection:
        return {"message": f"La collection '{collection_name}' n'existe pas."}

    collection_json = collection.model_dump_json()

    return json.loads(collection_json)
