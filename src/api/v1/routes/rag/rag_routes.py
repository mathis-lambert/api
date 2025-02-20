from typing import List, Dict, Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from api.v1.security import ensure_valid_token

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
    tags=["rag"],
    dependencies=[Depends(ensure_valid_token)]
)
async def list_collections(request: Request):
    """
    Liste les collections créées par l'utilisateur.
    """
    qdrant_client = request.app.qdrant_client
    collections_response = await qdrant_client.list_collections()
    collections = collections_response.collections
    return {"collections": collections}


# Route pour insérer des vecteurs dans une collection
@router.post(
    "/collections/{collection_name}/insert",
    summary="Insérer des vecteurs dans une collection",
    tags=["rag"],
    dependencies=[Depends(ensure_valid_token)]
)
async def insert_vectors(
        collection_name: str,
        vectors: List[VectorData],
        request: Request
):
    """
    Insère des vecteurs dans la collection spécifiée.
    """
    qdrant_client = request.app.qdrant_client

    points = [
        {
            "id": vector.id,
            "vector": vector.vector,
            "payload": vector.payload
        }
        for vector in vectors
    ]

    await qdrant_client.upsert(
        collection_name=collection_name,
        points=points
    )

    return {"status": "success", "inserted": len(points)}


# Route pour récupérer des vecteurs similaires
@router.post(
    "/collections/{collection_name}/retrieve",
    summary="Récupérer des vecteurs similaires",
    tags=["rag"],
    dependencies=[Depends(ensure_valid_token)]
)
async def retrieve_vectors(
        collection_name: str,
        query: QueryVector,
        request: Request
):
    """
    Récupère les vecteurs les plus similaires au vecteur de requête fourni.
    """
    qdrant_client = request.app.qdrant_client

    search_result = await qdrant_client.search(
        collection_name=collection_name,
        query_vector=query.vector,
        limit=query.top
    )

    return {"results": search_result}
