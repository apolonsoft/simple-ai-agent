# app/routes/__init__.py
from fastapi import APIRouter

from app.routes.auth_routes import router as auth_router
from app.routes.chat_routes import router as chat_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(chat_router)
