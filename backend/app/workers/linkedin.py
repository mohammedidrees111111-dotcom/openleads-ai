from app.core.celery_app import celery_app
from app.services.linkedin import LinkedInService
from app.database import async_session_factory
from app.models.lead import Lead
from app.models.user import User
from sqlalchemy import select, and_
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, soft_time_limit=120)
def send_linkedin_message_task(self, user_id: int, lead_id: int, campaign_id: int, subject: str, body: str):
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_send_linkedin_message(user_id, lead_id, campaign_id, subject, body))
    finally:
        loop.close()


async def _send_linkedin_message(user_id: int, lead_id: int, campaign_id: int, subject: str, body: str):
    linkedin_service = LinkedInService()

    async with async_session_factory() as db:
        result = await db.execute(select(Lead).where(Lead.id == lead_id))
        lead = result.scalar_one_or_none()
        if not lead:
            logger.error(f"Lead {lead_id} not found")
            return {"error": "Lead not found"}

        if not lead.linkedin_url:
            logger.warning(f"Lead {lead_id} has no LinkedIn URL")
            return {"error": "No LinkedIn URL"}

        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            return {"error": "User not found"}

        result = await linkedin_service.send_message(
            profile_url=lead.linkedin_url,
            message=body,
        )

        if result.get("success"):
            lead.status = "contacted"
            lead.last_contacted = datetime.now(timezone.utc)
            await db.commit()

        return result


@celery_app.task(bind=True, max_retries=2, soft_time_limit=120)
def sync_linkedin_connections(self, user_id: int):
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_sync_connections(user_id))
    finally:
        loop.close()


async def _sync_connections(user_id: int):
    from app.services.linkedin import LinkedInService

    linkedin = LinkedInService()
    async with async_session_factory() as db:
        result = await db.execute(
            select(Lead).where(and_(Lead.user_id == user_id, Lead.linkedin_url.isnot(None)))
        )
        existing = {r.linkedin_url for r in result.scalars().all()}

        connections = await linkedin.search_profiles(
            keywords=["connected"],
            limit=50,
        )

        new_count = 0
        for profile in connections:
            url = profile.get("url", "")
            if url and url not in existing:
                lead = Lead(
                    user_id=user_id,
                    name=profile.get("name", "Unknown"),
                    linkedin_url=url,
                    source="linkedin",
                    status="new",
                    is_qualified=True,
                    score=50,
                )
                db.add(lead)
                new_count += 1

        await db.commit()
        logger.info(f"LinkedIn sync for user {user_id}: {new_count} new leads from {len(connections)} connections")
