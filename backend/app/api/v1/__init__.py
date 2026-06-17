"""OpenAI-compatible /v1 router package."""

from fastapi import APIRouter

from app.api.v1 import chat, models

router = APIRouter(prefix="/v1", tags=["openai"])
router.include_router(models.router)
router.include_router(chat.router)
