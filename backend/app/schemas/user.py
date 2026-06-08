from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    company: Optional[str] = None
    phone: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    company: Optional[str]
    role: str
    subscription_tier: str
    is_active: bool
    is_verified: bool
    mrr: float
    total_leads_generated: int
    total_campaigns_sent: int
    subdomain: Optional[str]
    brand_color: Optional[str]
    paypal_email: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    locale: Optional[str] = None
    brand_color: Optional[str] = None
    brand_logo: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str
