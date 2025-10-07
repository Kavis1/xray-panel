from fastapi import APIRouter
from app.api.v1.endpoints import external_users, api_keys

# External API Router - для внешних приложений
external_router = APIRouter(tags=["External API"])

# API Keys Management (для администраторов)
external_router.include_router(
    api_keys.router,
    prefix="/api-keys",
    tags=["API Keys Management"]
)

# Users API (для внешних приложений с API ключом)
external_router.include_router(
    external_users.router,
    prefix="/users",
    tags=["External Users API"]
)
