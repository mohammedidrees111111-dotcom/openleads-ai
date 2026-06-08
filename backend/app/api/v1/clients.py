from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.client import Client, ClientStatus
from app.models.analytics import AnalyticsEvent
from app.schemas.client import ClientCreate, ClientResponse, ClientUpdate
from app.core.security import get_current_user

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("", response_model=dict)
async def get_clients(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Client).where(Client.agency_id == current_user.id)
    if status:
        query = query.where(Client.status == status)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    query = query.order_by(Client.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    clients = result.scalars().all()

    return {
        "items": [ClientResponse.model_validate(c) for c in clients],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.post("", response_model=ClientResponse, status_code=201)
async def create_client(
    data: ClientCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    subdomain = f"{data.company.lower().replace(' ', '-').replace('.', '')}-{current_user.id}" if data.company else f"client-{current_user.id}"
    client = Client(
        agency_id=current_user.id,
        subdomain=subdomain,
        **data.model_dump(exclude_none=True)
    )
    db.add(client)
    db.add(AnalyticsEvent(user_id=current_user.id, event_type="client", event_name="client_created"))
    current_user.mrr += data.monthly_price
    await db.commit()
    await db.refresh(client)
    return ClientResponse.model_validate(client)


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.agency_id == current_user.id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return ClientResponse.model_validate(client)


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    data: ClientUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.agency_id == current_user.id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    old_price = client.monthly_price
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(client, field, value)

    if data.monthly_price is not None and data.monthly_price != old_price:
        current_user.mrr += data.monthly_price - old_price

    await db.commit()
    await db.refresh(client)
    return ClientResponse.model_validate(client)


@router.delete("/{client_id}", status_code=204)
async def delete_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.agency_id == current_user.id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    current_user.mrr -= client.monthly_price
    await db.delete(client)
    await db.commit()
