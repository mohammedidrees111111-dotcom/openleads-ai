from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True, index=True)
    name = Column(String(500), nullable=False)
    company = Column(String(500), nullable=True)
    website = Column(String(500), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    twitter_url = Column(String(500), nullable=True)
    instagram_url = Column(String(500), nullable=True)
    whatsapp_number = Column(String(50), nullable=True)
    position = Column(String(255), nullable=True)
    industry = Column(String(255), nullable=True)
    company_size = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    source = Column(String(50), default="manual")
    status = Column(String(50), default="new", index=True)
    score = Column(Integer, default=0)
    ai_score = Column(Float, default=0.0)
    ai_qualification = Column(Text, nullable=True)
    pain_points = Column(JSON, default=list)
    tags = Column(JSON, default=list)
    custom_fields = Column(JSON, default=dict)
    is_qualified = Column(Boolean, default=False)
    is_enriched = Column(Boolean, default=False)
    enrichment_data = Column(JSON, default=dict)
    tech_stack = Column(JSON, default=list)
    notes = Column(Text, nullable=True)
    last_contacted = Column(DateTime(timezone=True), nullable=True)
    next_follow_up = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="leads")
    client_rel = relationship("Client", back_populates="leads")
    campaign_rel = relationship("Campaign", back_populates="leads")
    interactions = relationship("LeadInteraction", back_populates="lead", cascade="all, delete-orphan")
    sent_emails = relationship("SentEmail", back_populates="lead", cascade="all, delete-orphan")


class LeadInteraction(Base):
    __tablename__ = "lead_interactions"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    channel = Column(String(50), nullable=False)
    type = Column(String(50), nullable=False)
    content = Column(Text, nullable=True)
    extra_data = Column(JSON, default=dict)
    responded = Column(Boolean, default=False)
    response_content = Column(Text, nullable=True)
    response_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    lead = relationship("Lead", back_populates="interactions")
