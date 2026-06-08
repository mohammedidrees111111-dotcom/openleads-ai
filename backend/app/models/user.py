from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    AGENCY = "agency"
    CLIENT = "client"


class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    STARTER = "starter"
    GROWTH = "growth"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    role = Column(SAEnum(UserRole), default=UserRole.AGENCY)
    subscription_tier = Column(SAEnum(SubscriptionTier), default=SubscriptionTier.FREE)
    avatar_url = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    timezone = Column(String(50), default="UTC")
    locale = Column(String(10), default="en")
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_daily_limit = Column(Integer, default=50)
    linkedin_daily_limit = Column(Integer, default=30)
    whatsapp_daily_limit = Column(Integer, default=100)
    sms_daily_limit = Column(Integer, default=50)
    subdomain = Column(String(100), unique=True, nullable=True)
    brand_color = Column(String(7), default="#0ea5e9")
    brand_logo = Column(String(500), nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)
    paypal_email = Column(String(255), nullable=True)
    mrr = Column(Float, default=0.0)
    total_leads_generated = Column(Integer, default=0)
    total_campaigns_sent = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    leads = relationship("Lead", back_populates="owner", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="owner", cascade="all, delete-orphan")
    integrations = relationship("Integration", back_populates="owner", cascade="all, delete-orphan")
    clients = relationship("Client", back_populates="agency", cascade="all, delete-orphan")
    sent_emails = relationship("SentEmail", back_populates="sender", cascade="all, delete-orphan")
