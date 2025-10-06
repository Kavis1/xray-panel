from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, inbounds, nodes, subscriptions, webhooks, admins, templates, users_extensions

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(admins.router, prefix="/admins", tags=["Admins"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(users_extensions.router, prefix="/users", tags=["Users"])  # Additional user endpoints
api_router.include_router(inbounds.router, prefix="/inbounds", tags=["Inbounds"])
api_router.include_router(templates.router, prefix="/templates", tags=["Templates"])
api_router.include_router(nodes.router, prefix="/nodes", tags=["Nodes"])
api_router.include_router(subscriptions.router, prefix="/sub", tags=["Subscriptions"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
