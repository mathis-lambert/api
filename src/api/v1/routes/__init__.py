from .auth.auth_routes import router as auth_router
from .chat.chat_routes import router as chat_router
from .embeddings.embeddings_routes import router as embeddings_router
from .models.models_routes import router as models_router
from .rag.rag_routes import router as rag_router
from .vector_db.vector_db_routes import router as vector_db_router

__all__ = [
    "chat_router",
    "models_router",
    "auth_router",
    "vector_db_router",
    "embeddings_router",
    "rag_router",
]
