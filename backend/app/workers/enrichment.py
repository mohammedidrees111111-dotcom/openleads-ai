from app.core.celery_app import celery_app
from app.services.enrichment import DataEnrichmentService
from app.database import async_session_factory
from app.models.lead import Lead
from sqlalchemy import select, and_
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=2, soft_time_limit=120)
def bulk_enrich_leads(self, user_id: int, lead_ids: list):
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_bulk_enrich(user_id, lead_ids))
    finally:
        loop.close()


async def _bulk_enrich(user_id: int, lead_ids: list):
    enrichment = DataEnrichmentService()
    async with async_session_factory() as db:
        for lead_id in lead_ids:
            result = await db.execute(
                select(Lead).where(and_(Lead.id == lead_id, Lead.user_id == user_id))
            )
            lead = result.scalar_one_or_none()
            if not lead or lead.is_enriched:
                continue

            enriched = await enrichment.enrich(lead)
            if enriched:
                for key, value in enriched.items():
                    if value and not getattr(lead, key, None):
                        setattr(lead, key, value)
                lead.is_enriched = True

        await db.commit()
        logger.info(f"Enriched {len(lead_ids)} leads for user {user_id}")


@celery_app.task
def enrich_new_lead(lead_id: int):
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_enrich_single(lead_id))
    finally:
        loop.close()


async def _enrich_single(lead_id: int):
    enrichment = DataEnrichmentService()
    async with async_session_factory() as db:
        result = await db.execute(select(Lead).where(Lead.id == lead_id))
        lead = result.scalar_one_or_none()
        if lead and not lead.is_enriched:
            enriched = await enrichment.enrich(lead)
            if enriched:
                for key, value in enriched.items():
                    if value:
                        setattr(lead, key, value)
                lead.is_enriched = True
                await db.commit()
