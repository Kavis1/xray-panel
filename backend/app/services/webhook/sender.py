import hmac
import hashlib
import json
import time
from typing import Dict, Any
import httpx

from app.core.config import settings
from app.models.webhook import Webhook, WebhookQueue


class WebhookSender:
    """Service for sending webhook notifications"""
    
    def __init__(self):
        self.secret = settings.WEBHOOK_SECRET_HEADER

    async def send(self, queue_item: WebhookQueue) -> None:
        """Send a webhook notification"""
        webhook = await self._get_webhook(queue_item.webhook_id)
        
        if not webhook or not webhook.is_enabled:
            raise Exception("Webhook is disabled or not found")

        payload = {
            "event": queue_item.event_type,
            "data": queue_item.payload,
            "timestamp": int(time.time()),
        }

        signature = self._generate_signature(payload, webhook.secret)

        headers = {
            "Content-Type": "application/json",
            "X-Remnawave-Signature": signature,
            "X-Remnawave-Timestamp": str(payload["timestamp"]),
            "User-Agent": "XrayPanel-Webhook/1.0",
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                webhook.url,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()

        webhook.total_deliveries += 1
        webhook.last_delivery_at = time.time()
        webhook.last_delivery_status = "success"

    def _generate_signature(self, payload: Dict[str, Any], secret: str) -> str:
        """Generate HMAC-SHA256 signature for webhook payload"""
        message = json.dumps(payload, sort_keys=True).encode()
        signature = hmac.new(
            secret.encode(),
            message,
            hashlib.sha256
        ).hexdigest()
        return signature

    async def _get_webhook(self, webhook_id: int) -> Webhook:
        """Get webhook from database"""
        from app.db.base import async_session_maker
        from sqlalchemy import select

        async with async_session_maker() as session:
            result = await session.execute(
                select(Webhook).where(Webhook.id == webhook_id)
            )
            return result.scalar_one_or_none()


async def trigger_webhook(event_type: str, data: Dict[str, Any]) -> None:
    """Queue a webhook event for delivery"""
    from app.db.base import async_session_maker
    from sqlalchemy import select

    async with async_session_maker() as session:
        result = await session.execute(
            select(Webhook).where(
                Webhook.is_enabled == True
            )
        )
        webhooks = result.scalars().all()

        for webhook in webhooks:
            if not webhook.events or event_type in webhook.events:
                queue_item = WebhookQueue(
                    webhook_id=webhook.id,
                    event_type=event_type,
                    payload=data,
                    status="pending",
                )
                session.add(queue_item)

        await session.commit()
