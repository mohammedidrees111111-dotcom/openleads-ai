from app.core.celery_app import celery_app
from app.services.email_service import EmailService
from app.database import async_session_factory
from app.models.email import SentEmail
from app.models.lead import Lead
from app.models.analytics import DailyStats
from app.models.user import User
from sqlalchemy import select, and_, func
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, soft_time_limit=60)
def send_email_task(self, user_id: int, lead_id: int, campaign_id: int, subject: str, body: str):
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_send_email(user_id, lead_id, campaign_id, subject, body))
    finally:
        loop.close()


async def _send_email(user_id: int, lead_id: int, campaign_id: int, subject: str, body: str):
    email_service = EmailService()

    async with async_session_factory() as db:
        result = await db.execute(select(Lead).where(Lead.id == lead_id))
        lead = result.scalar_one_or_none()
        if not lead:
            logger.error(f"Lead {lead_id} not found")
            return {"error": "Lead not found"}

        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            return {"error": "User not found"}

        # Check daily limit
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        sent_today = await db.execute(
            select(func.count()).where(
                and_(
                    SentEmail.user_id == user_id,
                    func.date(SentEmail.sent_at) == today.date(),
                )
            )
        )
        if sent_today.scalar() >= user.email_daily_limit:
            logger.warning(f"Daily email limit reached for user {user_id}")
            return {"error": "Daily limit reached"}

        result = await email_service.send(
            to_email=lead.email,
            subject=subject,
            body_text=body,
            from_name=user.name,
        )

        sent_email = SentEmail(
            user_id=user_id,
            lead_id=lead_id,
            campaign_id=campaign_id,
            from_email=user.email,
            to_email=lead.email,
            subject=subject,
            body_text=body,
            status="sent" if result["success"] else "failed",
            error_message=result.get("error"),
        )
        db.add(sent_email)

        if result["success"]:
            lead.status = "contacted"
            lead.last_contacted = datetime.now(timezone.utc)

            daily = await db.execute(
                select(DailyStats).where(
                    and_(DailyStats.user_id == user_id, DailyStats.date == today)
                )
            )
            stats = daily.scalar_one_or_none()
            if not stats:
                stats = DailyStats(user_id=user_id, date=today)
                db.add(stats)
            stats.emails_sent += 1

        await db.commit()
        return result


@celery_app.task
def reset_daily_limits():
    """Reset daily counters (called by Celery Beat)"""
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_reset_limits())
    finally:
        loop.close()


async def _reset_limits():
    async with async_session_factory() as db:
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        daily = await db.execute(select(DailyStats).where(DailyStats.date == today))
        existing = daily.scalar_one_or_none()
        if not existing:
            stats = DailyStats(date=today)
            db.add(stats)

        result = await db.execute(select(SentEmail).where(
            and_(
                SentEmail.sent_at >= today,
                SentEmail.status == "sent",
            )
        ))
        sent_count = len(result.scalars().all())

        if existing:
            existing.emails_sent = sent_count

        await db.commit()
        logger.info(f"Daily limits reset: {sent_count} emails sent today")


@celery_app.task
def process_bounce(lead_id: int, email_id: int):
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_process_bounce(lead_id, email_id))
    finally:
        loop.close()


async def _process_bounce(lead_id: int, email_id: int):
    async with async_session_factory() as db:
        result = await db.execute(select(SentEmail).where(SentEmail.id == email_id))
        email = result.scalar_one_or_none()
        if email:
            email.bounced = True
            email.status = "bounced"
            await db.commit()
