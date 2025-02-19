from fastapi import APIRouter

from .routes import chat_router, models_router

router = APIRouter()
router.include_router(chat_router, prefix="/chat")
router.include_router(models_router, prefix="/models")
