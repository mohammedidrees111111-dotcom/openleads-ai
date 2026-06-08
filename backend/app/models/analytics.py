from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, JSON, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    event_name = Column(String(255), nullable=True)
    channel = Column(String(50), nullable=True)
    value = Column(Float, default=0.0)
    extra_data = Column(JSON, default=dict)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class DailyStats(Base):
    __tablename__ = "daily_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    leads_found = Column(Integer, default=0)
    leads_qualified = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_replied = Column(Integer, default=0)
    emails_bounced = Column(Integer, default=0)
    emails_unsubscribed = Column(Integer, default=0)
    linkedin_sent = Column(Integer, default=0)
    linkedin_accepted = Column(Integer, default=0)
    linkedin_replied = Column(Integer, default=0)
    whatsapp_sent = Column(Integer, default=0)
    whatsapp_replied = Column(Integer, default=0)
    calls_made = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)
    mrr = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
