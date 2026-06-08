from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class CampaignChannel(str, enum.Enum):
    EMAIL = "email"
    LINKEDIN = "linkedin"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    MULTI = "multi"


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SAEnum(CampaignStatus), default=CampaignStatus.DRAFT)
    channel = Column(SAEnum(CampaignChannel), default=CampaignChannel.EMAIL)
    target_keywords = Column(JSON, default=list)
    target_locations = Column(JSON, default=list)
    target_industries = Column(JSON, default=list)
    target_company_size = Column(String(50), nullable=True)
    max_leads = Column(Integer, default=100)
    message_template = Column(Text, nullable=True)
    subject_template = Column(String(500), nullable=True)
    follow_up_days = Column(JSON, default=[3, 7, 14])
    max_follow_ups = Column(Integer, default=3)
    smart_timing = Column(Boolean, default=True)
    a_b_testing = Column(Boolean, default=False)
    a_b_variants = Column(JSON, default=list)
    schedule_start = Column(DateTime(timezone=True), nullable=True)
    schedule_end = Column(DateTime(timezone=True), nullable=True)
    send_during_business_hours = Column(Boolean, default=True)
    timezone = Column(String(50), default="UTC")
    leads_processed = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_replied = Column(Integer, default=0)
    linkedin_sent = Column(Integer, default=0)
    linkedin_accepted = Column(Integer, default=0)
    linkedin_replied = Column(Integer, default=0)
    whatsapp_sent = Column(Integer, default=0)
    whatsapp_replied = Column(Integer, default=0)
    total_conversions = Column(Integer, default=0)
    total_revenue = Column(Float, default=0.0)
    webhook_url = Column(String(500), nullable=True)
    zapier_webhook = Column(String(500), nullable=True)
    n8n_webhook = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="campaigns")
    client_rel = relationship("Client", back_populates="campaigns")
    leads = relationship("Lead", back_populates="campaign_rel", cascade="all, delete-orphan")


class CampaignSequence(Base):
    __tablename__ = "campaign_sequences"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)
    delay_days = Column(Integer, default=0)
    channel = Column(String(50), nullable=False)
    subject = Column(String(500), nullable=True)
    template = Column(Text, nullable=False)
    condition = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    campaign = relationship("Campaign")
