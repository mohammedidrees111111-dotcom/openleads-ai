from typing import Optional, Dict, Any
from app.core.config import settings
import stripe
import logging
import requests
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


class StripeBilling:
    def __init__(self):
        self.secret_key = settings.STRIPE_SECRET_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        if self.secret_key:
            stripe.api_key = self.secret_key

    async def create_checkout_session(self, customer_email: str, price_id: str, success_url: str, cancel_url: str) -> Dict[str, Any]:
        if not self.secret_key:
            return {"error": "Stripe not configured"}
        try:
            session = stripe.checkout.Session.create(
                customer_email=customer_email,
                line_items=[{"price": price_id, "quantity": 1}],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
            )
            return {"url": session.url, "session_id": session.id}
        except Exception as e:
            logger.error(f"Stripe checkout failed: {e}")
            return {"error": str(e)}

    async def create_subscription(self, customer_id: str, price_id: str) -> Dict[str, Any]:
        if not self.secret_key:
            return {"error": "Stripe not configured"}
        try:
            sub = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
                payment_behavior="default_incomplete",
                expand=["latest_invoice.payment_intent"],
            )
            return {"subscription_id": sub.id, "client_secret": sub.latest_invoice.payment_intent.client_secret}
        except Exception as e:
            return {"error": str(e)}

    async def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        if not self.secret_key:
            return {"error": "Stripe not configured"}
        try:
            stripe.Subscription.delete(subscription_id)
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}

    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        if not self.secret_key:
            return {"error": "Stripe not configured"}
        try:
            sub = stripe.Subscription.retrieve(subscription_id)
            return {
                "id": sub.id,
                "status": sub.status,
                "current_period_start": datetime.fromtimestamp(sub.current_period_start),
                "current_period_end": datetime.fromtimestamp(sub.current_period_end),
                "cancel_at_period_end": sub.cancel_at_period_end,
            }
        except Exception as e:
            return {"error": str(e)}


class PayPalBilling:
    def __init__(self):
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET
        self.base_url = "https://api-m.paypal.com"
        self.token = None

    async def _get_token(self) -> Optional[str]:
        if not self.client_id or not self.client_secret:
            return None
        try:
            resp = requests.post(
                f"{self.base_url}/v1/oauth2/token",
                data={"grant_type": "client_credentials"},
                auth=(self.client_id, self.client_secret),
                headers={"Accept": "application/json"},
                timeout=15,
            )
            resp.raise_for_status()
            self.token = resp.json().get("access_token")
            return self.token
        except Exception as e:
            logger.error(f"PayPal auth failed: {e}")
            return None

    async def create_subscription(self, plan_id: str, subscriber_email: str) -> Dict[str, Any]:
        token = await self._get_token()
        if not token:
            return {"error": "PayPal not configured"}
        try:
            resp = requests.post(
                f"{self.base_url}/v1/billing/subscriptions",
                json={
                    "plan_id": plan_id,
                    "subscriber": {"email_address": subscriber_email},
                },
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            return {"subscription_id": data.get("id"), "status": data.get("status"), "links": data.get("links")}
        except Exception as e:
            return {"error": str(e)}
