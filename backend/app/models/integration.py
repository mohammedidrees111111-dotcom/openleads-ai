from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class IntegrationProvider(str, enum.Enum):
    HUBSPOT = "hubspot"
    SALESFORCE = "salesforce"
    PIPEDRIVE = "pipedrive"
    ZOHO = "zoho"
    GOOGLE_SHEETS = "google_sheets"
    CLEARBIT = "clearbit"
    HUNTER = "hunter"
    APOLLO = "apollo"
    STRIPE = "stripe"
    PAYPAL = "paypal"
    TWILIO = "twilio"
    WHATSAPP = "whatsapp"
    LINKEDIN = "linkedin"
    N8N = "n8n"
    ZAPIER = "zapier"


class Integration(Base):
    __tablename__ = "integrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    provider = Column(SAEnum(IntegrationProvider), nullable=False)
    name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    credentials = Column(JSON, default=dict)
    config = Column(JSON, default=dict)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    sync_frequency = Column(String(20), default="manual")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="integrations")
