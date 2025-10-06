from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.base import get_db
from app.models.admin import Admin
from app.models.webhook import Webhook
from app.api.deps import get_current_admin
from pydantic import BaseModel, Field

router = APIRouter()


class WebhookCreate(BaseModel):
    url: str = Field(..., min_length=1, max_length=512)
    secret: str = Field(..., min_length=16)
    events: List[str] = []


class WebhookUpdate(BaseModel):
    url: str | None = None
    secret: str | None = None
    is_enabled: bool | None = None
    events: List[str] | None = None


class WebhookResponse(BaseModel):
    id: int
    url: str
    is_enabled: bool
    events: List[str]
    total_deliveries: int
    failed_deliveries: int
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[WebhookResponse])
async def list_webhooks(
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    result = await db.execute(select(Webhook))
    webhooks = result.scalars().all()
    return webhooks


@router.post("/", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    webhook_data: WebhookCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    new_webhook = Webhook(
        url=webhook_data.url,
        secret=webhook_data.secret,
        events=webhook_data.events,
    )
    
    db.add(new_webhook)
    await db.commit()
    await db.refresh(new_webhook)
    
    return new_webhook


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    result = await db.execute(select(Webhook).where(Webhook.id == webhook_id))
    webhook = result.scalar_one_or_none()
    
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )
    
    await db.delete(webhook)
    await db.commit()
