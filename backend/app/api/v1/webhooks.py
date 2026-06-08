from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional
from datetime import datetime, timezone
from app.database import get_db, async_session_factory
from app.models.user import User
from app.models.client import Client, ClientStatus
from app.models.analytics import AnalyticsEvent
from app.models.campaign import Campaign, CampaignStatus
from app.models.lead import Lead
from app.models.email import SentEmail
from app.core.config import settings
import stripe
import json

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

stripe.api_key = settings.STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET = settings.STRIPE_WEBHOOK_SECRET


@router.post("/stripe")
async def stripe_webhook(request: Request, stripe_signature: Optional[str] = Header(None)):
    payload = await request.body()

    if STRIPE_WEBHOOK_SECRET and stripe_signature:
        try:
            event = stripe.Webhook.construct_event(
                payload, stripe_signature, STRIPE_WEBHOOK_SECRET
            )
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")
    else:
        event = json.loads(payload)

    event_type = event.get("type", "")
    data = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        customer_email = data.get("customer_email") or data.get("customer_details", {}).get("email", "")
        stripe_customer_id = data.get("customer", "")
        subscription_id = data.get("subscription", "")

        async with async_session_factory() as db:
            result = await db.execute(select(User).where(User.email == customer_email))
            user = result.scalar_one_or_none()
            if not user:
                client_result = await db.execute(select(Client).where(Client.email == customer_email))
                client = client_result.scalar_one_or_none()
                if client:
                    client.stripe_subscription_id = subscription_id
                    client.stripe_customer_id = stripe_customer_id
                    client.status = ClientStatus.ACTIVE
                    await db.commit()
            else:
                user.stripe_customer_id = stripe_customer_id
                await db.commit()

        return {"status": "success", "action": "subscription_created"}

    if event_type == "invoice.paid":
        subscription_id = data.get("subscription", "")
        amount = data.get("amount_paid", 0)
        customer_email = data.get("customer_email", "")

        async with async_session_factory() as db:
            c_result = await db.execute(select(Client).where(Client.stripe_subscription_id == subscription_id))
            client = c_result.scalar_one_or_none()
            if client:
                db.add(AnalyticsEvent(
                    user_id=client.agency_id,
                    event_type="payment",
                    event_name="invoice_paid",
                    metadata_value={"amount": amount, "client_id": client.id},
                ))
                await db.commit()

            u_result = await db.execute(select(User).where(User.stripe_customer_id == data.get("customer", "")))
            user = u_result.scalar_one_or_none()
            if user:
                db.add(AnalyticsEvent(
                    user_id=user.id,
                    event_type="payment",
                    event_name="invoice_paid",
                    metadata_value={"amount": amount},
                ))
                await db.commit()

        return {"status": "success", "action": "payment_recorded"}

    if event_type == "customer.subscription.deleted":
        subscription_id = data.get("id", "")

        async with async_session_factory() as db:
            c_result = await db.execute(select(Client).where(Client.stripe_subscription_id == subscription_id))
            client = c_result.scalar_one_or_none()
            if client:
                client.status = ClientStatus.INACTIVE
                client.subscription_ends_at = datetime.now(timezone.utc)
                await db.commit()

        return {"status": "success", "action": "subscription_cancelled"}

    if event_type == "customer.subscription.updated":
        subscription_id = data.get("id", "")
        status = data.get("status", "")

        async with async_session_factory() as db:
            c_result = await db.execute(select(Client).where(Client.stripe_subscription_id == subscription_id))
            client = c_result.scalar_one_or_none()
            if client:
                if status == "past_due":
                    client.status = ClientStatus.OVERDUE
                elif status == "canceled" or status == "unpaid":
                    client.status = ClientStatus.INACTIVE
                elif status == "active":
                    client.status = ClientStatus.ACTIVE
                await db.commit()

        return {"status": "success", "action": "subscription_updated"}

    return {"status": "received", "type": event_type}


@router.post("/email-status")
async def email_status_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    event = data.get("event", "")
    message_id = data.get("message_id", "") or data.get("sg_message_id", "")

    result = await db.execute(select(SentEmail).where(SentEmail.message_id == message_id))
    email = result.scalar_one_or_none()
    if not email:
        return {"status": "not_found"}

    if event == "opened":
        email.opens += 1
        email.opened_at = datetime.now(timezone.utc)
    elif event == "clicked":
        email.clicks += 1
    elif event == "replied":
        email.replied = True
        email.replied_at = datetime.now(timezone.utc)
    elif event == "bounced":
        email.bounced = True
        email.status = "bounced"
    elif event == "unsubscribed":
        email.unsubscribed = True
        email.status = "unsubscribed"
    elif event == "spam":
        email.spam = True
        email.status = "spam"

    await db.commit()
    return {"status": "processed"}


@router.post("/n8n")
async def n8n_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    action = data.get("action", "")
    payload = data.get("payload", {})

    if action == "lead.created":
        lead = Lead(**payload)
        db.add(lead)
        await db.commit()
        return {"status": "lead_created", "id": lead.id}

    if action == "campaign.trigger":
        campaign_id = payload.get("campaign_id")
        result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
        campaign = result.scalar_one_or_none()
        if campaign:
            campaign.status = CampaignStatus.ACTIVE
            await db.commit()
            return {"status": "campaign_triggered"}

    return {"status": "received"}


@router.post("/zapier")
async def zapier_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    hook_type = data.get("hook_type", "catch")

    if hook_type == "lead.new":
        lead_data = data.get("lead", {})
        lead = Lead(**lead_data)
        db.add(lead)
        await db.commit()
        return {"status": "created", "id": lead.id}

    return {"status": "received"}
