from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG, pool_size=20, max_overflow=10)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# Import all models so SQLAlchemy knows about them
from app.models.user import User
from app.models.lead import Lead, LeadInteraction
from app.models.campaign import Campaign, CampaignSequence
from app.models.client import Client
from app.models.email import SentEmail, EmailTemplate
from app.models.integration import Integration
from app.models.analytics import AnalyticsEvent, DailyStats


async def get_db():
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
