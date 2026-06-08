from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from app.models.user import SubscriptionTier
import enum


class ClientStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    TRIAL = "trial"


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    website = Column(String(500), nullable=True)
    industry = Column(String(255), nullable=True)
    company_size = Column(String(50), nullable=True)
    status = Column(SAEnum(ClientStatus), default=ClientStatus.TRIAL)
    subscription_tier = Column(SAEnum(SubscriptionTier), default=SubscriptionTier.STARTER)
    subdomain = Column(String(100), unique=True, nullable=True)
    brand_color = Column(String(7), default="#0ea5e9")
    brand_logo = Column(String(500), nullable=True)
    custom_domain = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)
    paypal_subscription_id = Column(String(255), nullable=True)
    monthly_price = Column(Float, default=299.0)
    billing_cycle = Column(String(20), default="monthly")
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    subscription_ends_at = Column(DateTime(timezone=True), nullable=True)
    total_leads = Column(Integer, default=0)
    total_campaigns = Column(Integer, default=0)
    mrr_contribution = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    agency = relationship("User", back_populates="clients")
    leads = relationship("Lead", back_populates="client_rel", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="client_rel", cascade="all, delete-orphan")
