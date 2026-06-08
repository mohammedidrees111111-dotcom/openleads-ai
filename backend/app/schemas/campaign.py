from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.campaign import CampaignStatus, CampaignChannel


class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    channel: CampaignChannel = CampaignChannel.EMAIL
    target_keywords: List[str] = []
    target_locations: List[str] = []
    target_industries: List[str] = []
    target_company_size: Optional[str] = None
    max_leads: int = 100
    message_template: Optional[str] = None
    subject_template: Optional[str] = None
    follow_up_days: List[int] = [3, 7, 14]
    max_follow_ups: int = 3
    smart_timing: bool = True
    a_b_testing: bool = False
    a_b_variants: List[str] = []
    schedule_start: Optional[datetime] = None
    schedule_end: Optional[datetime] = None
    send_during_business_hours: bool = True
    timezone: str = "UTC"
    client_id: Optional[int] = None


class CampaignResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: CampaignStatus
    channel: CampaignChannel
    target_keywords: List[str]
    target_locations: List[str]
    target_industries: List[str]
    max_leads: int
    leads_processed: int
    emails_sent: int
    emails_opened: int
    emails_replied: int
    linkedin_sent: int
    linkedin_accepted: int
    linkedin_replied: int
    whatsapp_sent: int
    whatsapp_replied: int
    total_conversions: int
    total_revenue: float
    schedule_start: Optional[datetime]
    schedule_end: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CampaignStatus] = None
    message_template: Optional[str] = None
    subject_template: Optional[str] = None
    follow_up_days: Optional[List[int]] = None
    max_follow_ups: Optional[int] = None


class CampaignSequenceCreate(BaseModel):
    step_number: int
    delay_days: int = 0
    channel: str
    subject: Optional[str] = None
    template: str
    condition: Optional[str] = None


class CampaignSequenceResponse(BaseModel):
    id: int
    campaign_id: int
    step_number: int
    delay_days: int
    channel: str
    subject: Optional[str]
    template: str
    condition: Optional[str]

    class Config:
        from_attributes = True
