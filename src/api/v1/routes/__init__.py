from .auth.auth_routes import router as auth_router
from .chat.chat_routes import router as chat_router
from .embeddings.embeddings_routes import router as embeddings_router
from .models.models_routes import router as models_router
from .vector_stores.vector_store_routes import router as vector_store_router

__all__ = [
    "chat_router",
    "models_router",
    "auth_router",
    "embeddings_router",
    "vector_store_router",
]
