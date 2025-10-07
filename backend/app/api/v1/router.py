from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, inbounds, nodes, subscriptions, webhooks, admins, templates, users_extensions, xray_sync
from app.api.v1.router_external import external_router

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(admins.router, prefix="/admins", tags=["Admins"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(users_extensions.router, prefix="/users", tags=["Users"])  # Additional user endpoints
api_router.include_router(inbounds.router, prefix="/inbounds", tags=["Inbounds"])
api_router.include_router(templates.router, prefix="/templates", tags=["Templates"])
api_router.include_router(nodes.router, prefix="/nodes", tags=["Nodes"])
api_router.include_router(xray_sync.router, prefix="/xray", tags=["Xray Sync"])  # Automatic Xray sync
api_router.include_router(subscriptions.router, prefix="/sub", tags=["Subscriptions"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])

# External API - требует API ключ для доступа
api_router.include_router(external_router, prefix="/external", tags=["External API"])
