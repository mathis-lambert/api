from fastapi import APIRouter

from .routes import (
    auth_router,
    chat_router,
    embeddings_router,
    models_router,
    rag_router,
    vector_db_router,
)

router = APIRouter()
router.include_router(chat_router, prefix="/chat", tags=["Chat inference"])
router.include_router(models_router, prefix="/models", tags=["AI Models"])
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(vector_db_router, prefix="/vector-db", tags=["Vector DB"])
router.include_router(embeddings_router, prefix="/embeddings", tags=["Embeddings"])
router.include_router(rag_router, prefix="/rag", tags=["RAG"])
