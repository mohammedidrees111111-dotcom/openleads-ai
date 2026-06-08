from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.client import ClientStatus
from app.models.user import SubscriptionTier


class ClientCreate(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    subscription_tier: SubscriptionTier = SubscriptionTier.STARTER
    monthly_price: float = 299.0
    trial_days: int = 14


class ClientResponse(BaseModel):
    id: int
    name: str
    email: str
    company: Optional[str]
    phone: Optional[str]
    website: Optional[str]
    industry: Optional[str]
    status: ClientStatus
    subscription_tier: SubscriptionTier
    subdomain: Optional[str]
    brand_color: Optional[str]
    monthly_price: float
    total_leads: int
    total_campaigns: int
    mrr_contribution: float
    trial_ends_at: Optional[datetime]
    subscription_ends_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    status: Optional[ClientStatus] = None
    subscription_tier: Optional[SubscriptionTier] = None
    monthly_price: Optional[float] = None
    brand_color: Optional[str] = None
    brand_logo: Optional[str] = None
