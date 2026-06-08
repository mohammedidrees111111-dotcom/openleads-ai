from app.core.celery_app import celery_app
from app.services.scraper import GoogleScraper
from app.services.lead_scorer import RuleBasedScorer
from app.database import async_session_factory
from app.models.lead import Lead
from app.models.analytics import DailyStats, AnalyticsEvent
from sqlalchemy import select, and_
from datetime import datetime, timezone, timedelta
import json
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, soft_time_limit=300)
def process_lead_search(self, user_id: int, search_data: dict):
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_do_search(user_id, search_data))
    finally:
        loop.close()


async def _do_search(user_id: int, search_data: dict):
    scraper = GoogleScraper()
    scorer = RuleBasedScorer()
    keywords = search_data.get("keywords", [])
    locations = search_data.get("locations", [])
    max_leads = search_data.get("max_leads", 50)

    all_leads = []
    per_search = max(2, max_leads // max(1, len(keywords) * len(locations)))

    for kw in keywords:
        for loc in locations:
            results = scraper.search(kw, loc, per_search)
            all_leads.extend(results)

    async with async_session_factory() as db:
        saved = 0
        for lead_data in all_leads:
            existing = await db.execute(
                select(Lead).where(
                    and_(
                        Lead.user_id == user_id,
                        Lead.website == lead_data.get("website", ""),
                    )
                )
            )
            if existing.scalar_one_or_none():
                continue

            score_result = scorer.score(lead_data)
            lead = Lead(
                user_id=user_id,
                name=lead_data.get("name", "Unknown"),
                website=lead_data.get("website"),
                email=lead_data.get("email"),
                source="google",
                status="new",
                score=score_result["score"],
                is_qualified=score_result["is_qualified"],
            )
            db.add(lead)
            saved += 1

        if saved > 0:
            today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            daily = await db.execute(
                select(DailyStats).where(
                    and_(DailyStats.user_id == user_id, DailyStats.date == today)
                )
            )
            stats = daily.scalar_one_or_none()
            if not stats:
                stats = DailyStats(user_id=user_id, date=today)
                db.add(stats)
            stats.leads_found += saved

            qualified = sum(1 for l in all_leads if l.get("score", 0) >= 60)
            stats.leads_qualified += qualified

            db.add(AnalyticsEvent(user_id=user_id, event_type="search", event_name="lead_search_completed"))

        await db.commit()

    logger.info(f"Search complete: {saved} leads saved for user {user_id}")


@celery_app.task
def cleanup_expired_leads():
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_cleanup())
    finally:
        loop.close()


async def _cleanup():
    async with async_session_factory() as db:
        from sqlalchemy import delete
        from app.models.analytics import DailyStats

        cutoff = datetime.now(timezone.utc) - timedelta(days=90)

        result = await db.execute(
            select(Lead).where(Lead.created_at < cutoff)
        )
        expired = result.scalars().all()

        for lead in expired:
            lead.status = "expired"
            lead.notes = f"Auto-expired: inactive for 90+ days (cutoff: {cutoff.date()})"

        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        daily = await db.execute(
            select(DailyStats).where(DailyStats.date == today)
        )
        stats_list = daily.scalars().all()

        monthly_cutoff = datetime.now(timezone.utc) - timedelta(days=365)
        await db.execute(
            delete(DailyStats).where(DailyStats.date < monthly_cutoff)
        )

        await db.commit()
        logger.info(f"Cleanup complete: {len(expired)} leads expired, old daily stats pruned")
