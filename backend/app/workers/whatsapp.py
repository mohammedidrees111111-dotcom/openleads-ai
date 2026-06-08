from app.core.celery_app import celery_app
from app.services.whatsapp import WhatsAppService
from app.database import async_session_factory
from app.models.lead import Lead
from app.models.user import User
from sqlalchemy import select
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, soft_time_limit=60)
def send_whatsapp_message_task(self, user_id: int, lead_id: int, campaign_id: int, body: str):
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_send_whatsapp_message(user_id, lead_id, campaign_id, body))
    finally:
        loop.close()


async def _send_whatsapp_message(user_id: int, lead_id: int, campaign_id: int, body: str):
    whatsapp_service = WhatsAppService()

    async with async_session_factory() as db:
        result = await db.execute(select(Lead).where(Lead.id == lead_id))
        lead = result.scalar_one_or_none()
        if not lead:
            logger.error(f"Lead {lead_id} not found")
            return {"error": "Lead not found"}

        if not lead.phone:
            logger.warning(f"Lead {lead_id} has no phone number")
            return {"error": "No phone number"}

        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            return {"error": "User not found"}

        result = await whatsapp_service.send_message(
            to_number=lead.phone,
            message=body,
        )

        if result.get("success"):
            lead.status = "contacted"
            lead.last_contacted = datetime.now(timezone.utc)
            await db.commit()

        return result
