from fastapi import APIRouter

from .routes import auth_router, chat_router, models_router, rag_router

router = APIRouter()
router.include_router(chat_router, prefix="/chat")
router.include_router(models_router, prefix="/models")
router.include_router(auth_router, prefix="/auth")
router.include_router(rag_router, prefix="/rag")
