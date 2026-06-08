from app.core.celery_app import celery_app
from app.database import async_session_factory
from app.models.campaign import Campaign, CampaignSequence, CampaignStatus
from app.models.lead import Lead
from app.models.user import User
from app.services.email_service import EmailService
from app.services.ai_orchestrator import AIOrchestrator
from app.services.linkedin import LinkedInService
from app.services.whatsapp import WhatsAppService
from app.workers.email import send_email_task
from sqlalchemy import select, and_
from datetime import datetime, timezone, timedelta
import logging
import json

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=2, soft_time_limit=600)
def launch_campaign(self, campaign_id: int):
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_launch_campaign(campaign_id))
    finally:
        loop.close()


async def _launch_campaign(campaign_id: int):
    async with async_session_factory() as db:
        result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
        campaign = result.scalar_one_or_none()
        if not campaign:
            logger.error(f"Campaign {campaign_id} not found")
            return

        user_result = await db.execute(select(User).where(User.id == campaign.user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            return

        # Get or create leads based on campaign targets
        leads = []
        for kw in campaign.target_keywords:
            for loc in campaign.target_locations:
                from app.services.scraper import GoogleScraper
                scraper = GoogleScraper()
                results = scraper.search(kw, loc, campaign.max_leads // max(1, len(campaign.target_keywords)))
                for r in results:
                    leads.append(r)

        # Save leads and send initial messages
        ai = AIOrchestrator()
        for lead_data in leads[:campaign.max_leads]:
            existing = await db.execute(
                select(Lead).where(
                    and_(
                        Lead.user_id == campaign.user_id,
                        Lead.website == lead_data.get("website", ""),
                    )
                )
            )
            if existing.scalar_one_or_none():
                continue

            lead = Lead(
                user_id=campaign.user_id,
                campaign_id=campaign_id,
                client_id=campaign.client_id,
                name=lead_data.get("name", "Unknown"),
                website=lead_data.get("website"),
                email=lead_data.get("email"),
                source="campaign",
                status="new",
            )
            db.add(lead)
            await db.flush()

            if lead.email and campaign.channel in ["email", "multi"]:
                msg_data = await ai.generate_message(
                    {"name": lead.name, "company": lead.company, "website": lead.website},
                    channel="email",
                )
                if isinstance(msg_data, str):
                    try:
                        msg_data = json.loads(msg_data)
                    except json.JSONDecodeError:
                        msg_data = {"subject": campaign.subject_template, "body": campaign.message_template}
                from app.workers.email import send_email_task
                send_email_task.delay(
                    campaign.user_id, lead.id, campaign_id,
                    msg_data.get("subject", campaign.subject_template),
                    msg_data.get("body", campaign.message_template),
                )
                campaign.emails_sent += 1

        campaign.status = CampaignStatus.ACTIVE
        await db.commit()
        logger.info(f"Campaign {campaign_id} launched with {len(leads)} leads")


@celery_app.task
def check_scheduled_campaigns():
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_check_scheduled())
    finally:
        loop.close()


async def _check_scheduled():
    async with async_session_factory() as db:
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(Campaign).where(
                and_(
                    Campaign.status == CampaignStatus.DRAFT,
                    Campaign.schedule_start <= now,
                )
            )
        )
        for campaign in result.scalars().all():
            launch_campaign.delay(campaign.id)
