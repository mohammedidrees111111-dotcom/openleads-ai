from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from app.database import get_db
from app.models.user import User
from app.models.lead import Lead, LeadInteraction
from app.models.analytics import DailyStats, AnalyticsEvent
from app.schemas.lead import LeadCreate, LeadResponse, LeadUpdate, LeadSearch, LeadBatchCreate, AILeadFinderRequest
from app.core.security import get_current_user
from app.services.lead_scorer import AILeadScorer, RuleBasedScorer
from app.services.scraper import GoogleScraper
from app.services.linkedin import LinkedInService
from app.services.enrichment import DataEnrichmentService
from app.workers.leads import process_lead_search

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.get("", response_model=dict)
async def get_leads(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    source: Optional[str] = None,
    min_score: Optional[int] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Lead).where(Lead.user_id == current_user.id)

    if status:
        query = query.where(Lead.status == status)
    if source:
        query = query.where(Lead.source == source)
    if min_score is not None:
        query = query.where(Lead.score >= min_score)
    if search:
        query = query.where(
            or_(
                Lead.name.ilike(f"%{search}%"),
                Lead.company.ilike(f"%{search}%"),
                Lead.email.ilike(f"%{search}%"),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    sort_col = getattr(Lead, sort_by, Lead.created_at)
    order = sort_col.desc() if sort_order == "desc" else sort_col.asc()
    query = query.order_by(order).offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    leads = result.scalars().all()

    return {
        "items": [LeadResponse.model_validate(l) for l in leads],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.post("", response_model=LeadResponse, status_code=201)
async def create_lead(
    data: LeadCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lead = Lead(user_id=current_user.id, **data.model_dump(exclude={"tags", "custom_fields"}, exclude_none=True))
    lead.tags = data.tags
    lead.custom_fields = data.custom_fields
    db.add(lead)
    db.add(AnalyticsEvent(user_id=current_user.id, event_type="lead", event_name="lead_created"))
    current_user.total_leads_generated += 1
    await db.commit()
    await db.refresh(lead)
    return LeadResponse.model_validate(lead)


@router.post("/batch", response_model=List[LeadResponse], status_code=201)
async def create_leads_batch(
    data: LeadBatchCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    leads = []
    for lead_data in data.leads:
        lead = Lead(user_id=current_user.id, **lead_data.model_dump(exclude={"tags", "custom_fields"}, exclude_none=True))
        lead.tags = lead_data.tags
        lead.custom_fields = lead_data.custom_fields
        db.add(lead)
        leads.append(lead)
    current_user.total_leads_generated += len(leads)
    await db.commit()
    for l in leads:
        await db.refresh(l)
    return [LeadResponse.model_validate(l) for l in leads]


@router.post("/search", response_model=dict)
async def search_leads(
    data: LeadSearch,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    background_tasks.add_task(process_lead_search.delay, current_user.id, data.model_dump())
    return {"message": "Lead search started", "keywords": data.keywords, "locations": data.locations}


UNLIMITED_EMAILS = {"mohammedidrees840@gmail.com", "mohammedidrees111111@gmail.com"}

TIER_LIMITS = {
    "free": 5, "starter": 50, "growth": 200, "pro": 1000, "enterprise": 99999,
}


@router.post("/ai-find")
async def ai_find_leads(
    data: AILeadFinderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    is_unlimited = current_user.email in UNLIMITED_EMAILS
    max_allowed = 999999 if is_unlimited else TIER_LIMITS.get(current_user.subscription_tier.value, 5)
    max_leads = min(data.max_leads, 999999 if is_unlimited else max_allowed)

    if not is_unlimited:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        count_today = (
            await db.execute(
                select(func.count()).where(
                    and_(
                        Lead.user_id == current_user.id,
                        Lead.created_at >= today_start,
                    )
                )
            )
        ).scalar() or 0

        if count_today >= max_allowed:
            raise HTTPException(status_code=429, detail=f"Daily limit reached ({max_allowed}). Upgrade your plan for more.")

    scraper = GoogleScraper()
    scorer = RuleBasedScorer()

    parsed = GoogleScraper.parse_input(f"{data.keywords} {data.locations}")
    keywords = parsed["keywords"]
    locations = parsed["locations"]

    raw_leads = []
    per_search = max(2, max_leads // max(1, len(keywords) * len(locations)))
    for kw in keywords:
        for loc in locations:
            results = scraper.search(kw, loc, per_search)
            raw_leads.extend(results)

    saved_leads = []
    for lead_data in raw_leads[:max_leads]:
        existing = await db.execute(
            select(Lead).where(
                and_(
                    Lead.user_id == current_user.id,
                    Lead.website == lead_data.get("website", ""),
                )
            )
        )
        if existing.scalar_one_or_none():
            continue

        score_result = scorer.score(lead_data)
        lead = Lead(
            user_id=current_user.id,
            name=lead_data.get("name", "Unknown"),
            website=lead_data.get("website"),
            email=lead_data.get("email"),
            phone=lead_data.get("phone", ""),
            source="ai_finder",
            status="new",
            score=score_result["score"],
            is_qualified=score_result["is_qualified"],
            location=lead_data.get("location", ""),
            company=lead_data.get("description", "")[:200] if lead_data.get("description") else None,
        )
        db.add(lead)
        saved_leads.append(lead)

    if saved_leads:
        current_user.total_leads_generated += len(saved_leads)
        db.add(AnalyticsEvent(
            user_id=current_user.id, event_type="lead",
            event_name=f"ai_finder: {len(saved_leads)} leads found",
            extra_data={"keywords": keywords, "locations": locations},
        ))
        await db.commit()
        for l in saved_leads:
            await db.refresh(l)

    return {
        "leads": [LeadResponse.model_validate(l) for l in saved_leads],
        "count": len(saved_leads),
        "daily_remaining": 999999 if is_unlimited else max(0, max_allowed - count_today - len(saved_leads)),
        "unlimited": is_unlimited,
        "tier": current_user.subscription_tier.value,
    }


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.user_id == current_user.id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadResponse.model_validate(lead)


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: int,
    data: LeadUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.user_id == current_user.id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)
    await db.commit()
    await db.refresh(lead)
    return LeadResponse.model_validate(lead)


@router.delete("/{lead_id}", status_code=204)
async def delete_lead(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.user_id == current_user.id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    await db.delete(lead)
    await db.commit()


@router.post("/{lead_id}/enrich")
async def enrich_lead(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.user_id == current_user.id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    enrichment = DataEnrichmentService()
    enriched = await enrichment.enrich(lead)

    if enriched:
        for key, value in enriched.items():
            setattr(lead, key, value)
        lead.is_enriched = True
        await db.commit()
        await db.refresh(lead)

    return LeadResponse.model_validate(lead)


@router.post("/{lead_id}/qualify-ai")
async def ai_qualify_lead(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.user_id == current_user.id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    scorer = AILeadScorer()
    score_data = await scorer.score(lead)
    lead.ai_score = score_data["score"]
    lead.ai_qualification = score_data["reasoning"]
    lead.is_qualified = score_data["is_qualified"]
    lead.pain_points = score_data.get("pain_points", [])
    lead.score = int(score_data["score"] * 100)
    await db.commit()
    await db.refresh(lead)
    return LeadResponse.model_validate(lead)


@router.get("/pipeline/stats")
async def get_pipeline_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    statuses = ["new", "contacted", "qualified", "converted", "lost"]
    result = {}
    for status in statuses:
        count = (
            await db.execute(
                select(func.count()).where(
                    Lead.user_id == current_user.id, Lead.status == status
                )
            )
        ).scalar()
        result[status] = count
    return result
