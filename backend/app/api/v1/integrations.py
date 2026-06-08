from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.models.user import User
from app.models.integration import Integration, IntegrationProvider
from app.core.security import get_current_user

router = APIRouter(prefix="/integrations", tags=["Integrations"])


@router.get("")
async def get_integrations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Integration).where(Integration.user_id == current_user.id)
    )
    integrations = result.scalars().all()
    return [
        {
            "id": i.id,
            "provider": i.provider.value,
            "name": i.name or i.provider.value,
            "is_active": i.is_active,
            "last_sync_at": i.last_sync_at,
            "error_message": i.error_message,
            "config_keys": list(i.config.keys()) if i.config else [],
        }
        for i in integrations
    ]


@router.post("/{provider}")
async def connect_integration(
    provider: IntegrationProvider,
    credentials: dict = Body(...),
    config: dict = Body(default={}),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(Integration).where(
            Integration.user_id == current_user.id,
            Integration.provider == provider,
        )
    )
    integration = existing.scalar_one_or_none()

    if integration:
        integration.credentials = credentials
        integration.config = {**integration.config, **config}
        integration.is_active = True
        integration.error_message = None
    else:
        integration = Integration(
            user_id=current_user.id,
            provider=provider,
            name=provider.value,
            credentials=credentials,
            config=config,
            is_active=True,
        )
        db.add(integration)

    await db.commit()
    await db.refresh(integration)
    return {"message": f"{provider.value} connected successfully", "id": integration.id}


@router.delete("/{integration_id}", status_code=204)
async def disconnect_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Integration).where(
            Integration.id == integration_id,
            Integration.user_id == current_user.id,
        )
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    integration.is_active = False
    integration.credentials = {}
    await db.commit()


@router.post("/{integration_id}/sync")
async def sync_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timezone
    result = await db.execute(
        select(Integration).where(
            Integration.id == integration_id,
            Integration.user_id == current_user.id,
            Integration.is_active == True,
        )
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found or inactive")
    integration.last_sync_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": f"Sync completed for {integration.provider.value}"}
