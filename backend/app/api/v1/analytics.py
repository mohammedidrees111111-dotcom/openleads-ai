from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract, cast, Date
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from app.database import get_db
from app.models.user import User
from app.models.lead import Lead
from app.models.campaign import Campaign
from app.models.email import SentEmail
from app.models.client import Client
from app.models.analytics import DailyStats, AnalyticsEvent
from app.schemas.analytics import (
    DashboardStats, LeadPipelineData, DailyStatsResponse, MRRData, ChannelPerformance, AnalyticsEventResponse,
)
from app.core.security import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    total_leads = (await db.execute(select(func.count()).where(Lead.user_id == current_user.id))).scalar()
    qualified = (await db.execute(select(func.count()).where(and_(Lead.user_id == current_user.id, Lead.is_qualified == True)))).scalar()
    active_campaigns = (await db.execute(select(func.count()).where(and_(Campaign.user_id == current_user.id, Campaign.status == "active")))).scalar()
    total_sent = (await db.execute(select(func.count()).where(SentEmail.user_id == current_user.id))).scalar()
    total_opened = (await db.execute(select(func.count()).where(and_(SentEmail.user_id == current_user.id, SentEmail.opens > 0)))).scalar()
    total_replied = (await db.execute(select(func.count()).where(and_(SentEmail.user_id == current_user.id, SentEmail.replied == True)))).scalar()
    total_bounced = (await db.execute(select(func.count()).where(and_(SentEmail.user_id == current_user.id, SentEmail.bounced == True)))).scalar()
    total_conversions = (await db.execute(select(func.count()).where(and_(Lead.user_id == current_user.id, Lead.status == "converted")))).scalar()

    current_mrr = current_user.mrr or 0.0

    return DashboardStats(
        total_leads=total_leads or 0,
        qualified_leads=qualified or 0,
        active_campaigns=active_campaigns or 0,
        total_sent=total_sent or 0,
        total_opened=total_opened or 0,
        total_replied=total_replied or 0,
        total_bounced=total_bounced or 0,
        total_conversions=total_conversions or 0,
        current_mrr=current_mrr,
        monthly_revenue=current_mrr,
        open_rate=(total_opened / total_sent * 100) if total_sent else 0,
        reply_rate=(total_replied / total_sent * 100) if total_sent else 0,
        conversion_rate=(total_conversions / total_leads * 100) if total_leads else 0,
        bounce_rate=(total_bounced / total_sent * 100) if total_sent else 0,
        subscription_tier=current_user.subscription_tier.value,
    )


@router.get("/pipeline", response_model=LeadPipelineData)
async def get_pipeline_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    counts = {}
    for status in ["new", "contacted", "qualified", "converted", "lost"]:
        count = (await db.execute(
            select(func.count()).where(and_(Lead.user_id == current_user.id, Lead.status == status))
        )).scalar()
        counts[status] = count or 0
    return LeadPipelineData(**counts)


@router.get("/daily", response_model=List[DailyStatsResponse])
async def get_daily_stats(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(DailyStats)
        .where(and_(DailyStats.user_id == current_user.id, DailyStats.date >= since))
        .order_by(DailyStats.date.asc())
    )
    stats = result.scalars().all()
    return [
        DailyStatsResponse(
            date=s.date.strftime("%Y-%m-%d"),
            leads_found=s.leads_found,
            leads_qualified=s.leads_qualified,
            emails_sent=s.emails_sent,
            emails_opened=s.emails_opened,
            emails_replied=s.emails_replied,
            conversions=s.conversions,
            revenue=s.revenue,
        )
        for s in stats
    ]


@router.get("/mrr", response_model=List[MRRData])
async def get_mrr_data(
    months: int = Query(12, ge=1, le=24),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.now(timezone.utc) - timedelta(days=months * 30)
    result = await db.execute(
        select(DailyStats)
        .where(and_(DailyStats.user_id == current_user.id, DailyStats.date >= since))
        .order_by(DailyStats.date.asc())
    )
    stats = result.scalars().all()

    monthly = {}
    for s in stats:
        key = s.date.strftime("%Y-%m")
        if key not in monthly:
            monthly[key] = {"mrr": 0, "new_clients": 0, "churned": 0}
        monthly[key]["mrr"] += s.mrr
    # Also count new clients per month
    clients_result = await db.execute(
        select(Client).where(Client.agency_id == current_user.id).order_by(Client.created_at.asc())
    )
    for client in clients_result.scalars().all():
        key = client.created_at.strftime("%Y-%m")
        if key in monthly:
            monthly[key]["new_clients"] += 1

    return [MRRData(month=k, **v) for k, v in sorted(monthly.items())]


@router.get("/channels", response_model=List[ChannelPerformance])
async def get_channel_performance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    email_sent = (await db.execute(select(func.count()).where(SentEmail.user_id == current_user.id))).scalar() or 0
    email_opened = (await db.execute(select(func.count()).where(and_(SentEmail.user_id == current_user.id, SentEmail.opens > 0)))).scalar() or 0
    email_replied = (await db.execute(select(func.count()).where(and_(SentEmail.user_id == current_user.id, SentEmail.replied == True)))).scalar() or 0
    email_converted = (await db.execute(select(func.count()).where(and_(Lead.user_id == current_user.id, Lead.source == "email", Lead.status == "converted")))).scalar() or 0

    linkedin_converted = (await db.execute(select(func.count()).where(and_(Lead.user_id == current_user.id, Lead.source == "linkedin", Lead.status == "converted")))).scalar() or 0
    linkedin_total = (await db.execute(select(func.count()).where(and_(Lead.user_id == current_user.id, Lead.source == "linkedin")))).scalar() or 0

    whatsapp_converted = (await db.execute(select(func.count()).where(and_(Lead.user_id == current_user.id, Lead.source == "whatsapp", Lead.status == "converted")))).scalar() or 0
    whatsapp_total = (await db.execute(select(func.count()).where(and_(Lead.user_id == current_user.id, Lead.source == "whatsapp")))).scalar() or 0

    sms_converted = (await db.execute(select(func.count()).where(and_(Lead.user_id == current_user.id, Lead.source == "sms", Lead.status == "converted")))).scalar() or 0
    sms_total = (await db.execute(select(func.count()).where(and_(Lead.user_id == current_user.id, Lead.source == "sms")))).scalar() or 0

    return [
        ChannelPerformance(
            channel="email",
            sent=email_sent,
            opened=email_opened,
            replied=email_replied,
            converted=email_converted,
            rate=(email_replied / email_sent * 100) if email_sent else 0,
        ),
        ChannelPerformance(
            channel="linkedin",
            sent=linkedin_total,
            opened=0,
            replied=0,
            converted=linkedin_converted,
            rate=0,
        ),
        ChannelPerformance(
            channel="whatsapp",
            sent=whatsapp_total,
            opened=0,
            replied=0,
            converted=whatsapp_converted,
            rate=0,
        ),
        ChannelPerformance(
            channel="sms",
            sent=sms_total,
            opened=0,
            replied=0,
            converted=sms_converted,
            rate=0,
        ),
    ]


@router.get("/activity", response_model=List[AnalyticsEventResponse])
async def get_recent_activity(
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AnalyticsEvent)
        .where(AnalyticsEvent.user_id == current_user.id)
        .order_by(AnalyticsEvent.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/leads-by-location")
async def get_leads_by_location(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lead.country, Lead.city, Lead.latitude, Lead.longitude, func.count().label("count"))
        .where(and_(Lead.user_id == current_user.id, Lead.country.isnot(None)))
        .group_by(Lead.country, Lead.city, Lead.latitude, Lead.longitude)
        .order_by(func.count().desc())
    )
    rows = result.all()

    if not rows:
        result = await db.execute(
            select(Lead.country, Lead.city, func.count().label("count"))
            .where(Lead.user_id == current_user.id)
            .group_by(Lead.country, Lead.city)
            .order_by(func.count().desc())
        )
        rows = [(r.country, r.city, None, None, r.count) for r in result.all()]

    return [
        {"country": r.country, "city": r.city, "count": r.count, "latitude": r.latitude, "longitude": r.longitude}
        for r in rows
    ]
