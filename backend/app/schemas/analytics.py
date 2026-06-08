from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class DashboardStats(BaseModel):
    total_leads: int
    qualified_leads: int
    active_campaigns: int
    total_sent: int
    total_opened: int
    total_replied: int
    total_bounced: int
    total_conversions: int
    current_mrr: float
    monthly_revenue: float
    open_rate: float
    reply_rate: float
    conversion_rate: float
    bounce_rate: float
    subscription_tier: str = "free"


class LeadPipelineData(BaseModel):
    new: int
    contacted: int
    qualified: int
    converted: int
    lost: int


class DailyStatsResponse(BaseModel):
    date: str
    leads_found: int
    leads_qualified: int
    emails_sent: int
    emails_opened: int
    emails_replied: int
    conversions: int
    revenue: float


class MRRData(BaseModel):
    month: str
    mrr: float
    new_clients: int
    churned: int


class ChannelPerformance(BaseModel):
    channel: str
    sent: int
    opened: int
    replied: int
    converted: int
    rate: float


class AnalyticsEventResponse(BaseModel):
    id: int
    event_type: str
    event_name: Optional[str] = None
    channel: Optional[str] = None
    value: float = 0.0
    extra_data: Optional[Any] = None
    created_at: datetime

    class Config:
        from_attributes = True
