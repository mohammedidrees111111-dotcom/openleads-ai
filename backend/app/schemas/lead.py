from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class LeadCreate(BaseModel):
    name: str
    company: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    position: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    source: str = "manual"
    tags: List[str] = []
    custom_fields: dict = {}
    client_id: Optional[int] = None
    campaign_id: Optional[int] = None


class LeadBatchCreate(BaseModel):
    leads: List[LeadCreate]


class LeadSearch(BaseModel):
    keywords: List[str] = []
    locations: List[str] = []
    industries: List[str] = []
    min_score: int = 0
    max_leads: int = 50
    source: Optional[str] = None
    status: Optional[str] = None


class LeadResponse(BaseModel):
    id: int
    name: str
    company: Optional[str]
    website: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    linkedin_url: Optional[str]
    position: Optional[str]
    industry: Optional[str]
    location: Optional[str]
    city: Optional[str]
    country: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    source: str
    status: str
    score: int
    ai_score: float
    is_qualified: bool
    is_enriched: bool
    tags: List[str]
    pain_points: List[str]
    tech_stack: List[Any]
    notes: Optional[str]
    last_contacted: Optional[datetime]
    next_follow_up: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class AILeadFinderRequest(BaseModel):
    keywords: str
    locations: str = ""
    max_leads: int = 10


class LeadUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    position: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    score: Optional[int] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
