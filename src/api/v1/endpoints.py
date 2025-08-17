from fastapi import APIRouter

from .routes import (
    auth_router,
    chat_router,
    embeddings_router,
    models_router,
    vector_store_router,
)

router = APIRouter()

# OpenAI-compatible:
router.include_router(chat_router, prefix="/chat", tags=["Chat inference"])
router.include_router(embeddings_router, prefix="/embeddings", tags=["Embeddings"])
router.include_router(models_router, prefix="/models", tags=["AI Models"])
router.include_router(
    vector_store_router, prefix="/vector_stores", tags=["Vector Stores"]
)

# Auth
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])


# Health check
@router.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "API is running!"}
