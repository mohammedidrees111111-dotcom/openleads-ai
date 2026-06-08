from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.campaign import Campaign, CampaignSequence, CampaignStatus
from app.models.lead import Lead
from app.models.analytics import AnalyticsEvent
from app.schemas.campaign import (
    CampaignCreate, CampaignResponse, CampaignUpdate,
    CampaignSequenceCreate, CampaignSequenceResponse,
)
from app.core.security import get_current_user
from app.workers.campaigns import launch_campaign

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@router.get("", response_model=dict)
async def get_campaigns(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[CampaignStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Campaign).where(Campaign.user_id == current_user.id)
    if status:
        query = query.where(Campaign.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(Campaign.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    campaigns = result.scalars().all()

    return {
        "items": [CampaignResponse.model_validate(c) for c in campaigns],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.post("", response_model=CampaignResponse, status_code=201)
async def create_campaign(
    data: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    campaign = Campaign(
        user_id=current_user.id,
        **data.model_dump(exclude={"follow_up_days", "a_b_variants", "target_keywords", "target_locations", "target_industries"}, exclude_none=True)
    )
    campaign.follow_up_days = data.follow_up_days
    campaign.a_b_variants = data.a_b_variants
    campaign.target_keywords = data.target_keywords
    campaign.target_locations = data.target_locations
    campaign.target_industries = data.target_industries
    db.add(campaign)
    db.add(AnalyticsEvent(user_id=current_user.id, event_type="campaign", event_name="campaign_created"))
    await db.commit()
    await db.refresh(campaign)
    return CampaignResponse.model_validate(campaign)


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return CampaignResponse.model_validate(campaign)


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int,
    data: CampaignUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(campaign, field, value)
    await db.commit()
    await db.refresh(campaign)
    return CampaignResponse.model_validate(campaign)


@router.post("/{campaign_id}/launch")
async def launch_campaign_endpoint(
    campaign_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.status = CampaignStatus.ACTIVE
    await db.commit()
    background_tasks.add_task(launch_campaign.delay, campaign_id)
    return {"message": f"Campaign '{campaign.name}' launched", "campaign_id": campaign_id}


@router.post("/{campaign_id}/pause")
async def pause_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign.status = CampaignStatus.PAUSED
    await db.commit()
    return {"message": "Campaign paused"}


@router.delete("/{campaign_id}", status_code=204)
async def delete_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    await db.delete(campaign)
    await db.commit()


@router.get("/{campaign_id}/sequences", response_model=List[CampaignSequenceResponse])
async def get_campaign_sequences(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CampaignSequence).where(CampaignSequence.campaign_id == campaign_id).order_by(CampaignSequence.step_number)
    )
    return [CampaignSequenceResponse.model_validate(s) for s in result.scalars().all()]


@router.post("/{campaign_id}/sequences", response_model=CampaignSequenceResponse, status_code=201)
async def create_campaign_sequence(
    campaign_id: int,
    data: CampaignSequenceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    campaign = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
    )
    if not campaign.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Campaign not found")

    seq = CampaignSequence(campaign_id=campaign_id, **data.model_dump())
    db.add(seq)
    await db.commit()
    await db.refresh(seq)
    return CampaignSequenceResponse.model_validate(seq)
