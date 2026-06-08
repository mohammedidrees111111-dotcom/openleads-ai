"""Seed script to populate demo data for OpenLeads AI."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import async_session_factory, init_db
from app.models.user import User, UserRole, SubscriptionTier
from app.models.client import Client, ClientStatus
from app.models.lead import Lead
from app.models.campaign import Campaign, CampaignStatus, CampaignChannel
from app.core.security import get_password_hash
from datetime import datetime, timezone, timedelta
from sqlalchemy import select


async def seed():
    print("🌱 Seeding OpenLeads AI demo data...")
    await init_db()

    async with async_session_factory() as db:
        # Check if admin exists
        result = await db.execute(select(User).where(User.email == "mohammedidrees840@gmail.com"))
        existing = result.scalar_one_or_none()
        if existing:
            print("✅ Demo data already exists. Skipping.")
            return

        # Create admin user
        admin = User(
            email="mohammedidrees840@gmail.com",
            password_hash=get_password_hash("OpenLeads2024!"),
            name="Mohammed Idrees",
            company="OpenLeads AI",
            role=UserRole.ADMIN,
            subscription_tier=SubscriptionTier.ENTERPRISE,
            is_verified=True,
            is_active=True,
            paypal_email="mohammedidrees840@gmail.com",
        )
        db.add(admin)
        await db.flush()

        # Create demo clients
        clients_data = [
            {"name": "Ahmed Al-Rashid", "company": "Elite Properties Dubai", "email": "ahmed@eliteproperties.ae", "monthly_price": 599},
            {"name": "Sarah Khalid", "company": "TechVentures Saudi", "email": "sarah@techventures.sa", "monthly_price": 299},
            {"name": "Omar Hassan", "company": "Digital Solutions Qatar", "email": "omar@digitalsolutions.qa", "monthly_price": 1199},
        ]
        clients = []
        for c in clients_data:
            client = Client(
                agency_id=admin.id,
                status=ClientStatus.ACTIVE,
                subscription_tier=SubscriptionTier.GROWTH,
                subdomain=c["company"].lower().replace(" ", "-"),
                **c,
            )
            db.add(client)
            clients.append(client)
            admin.mrr += c["monthly_price"]

        await db.flush()

        # Create demo campaigns
        campaigns_data = [
            {"name": "Dubai Real Estate Q1", "channel": CampaignChannel.EMAIL, "target_keywords": ["real estate", "property"], "target_locations": ["Dubai"], "status": CampaignStatus.ACTIVE, "client_id": clients[0].id},
            {"name": "Saudi Tech Leaders", "channel": CampaignChannel.MULTI, "target_keywords": ["tech", "startup", "software"], "target_locations": ["Riyadh", "Jeddah"], "status": CampaignStatus.ACTIVE, "client_id": clients[1].id},
            {"name": "Qatar Business Growth", "channel": CampaignChannel.LINKEDIN, "target_keywords": ["business", "consulting"], "target_locations": ["Doha"], "status": CampaignStatus.DRAFT, "client_id": clients[2].id},
        ]
        for c in campaigns_data:
            campaign = Campaign(user_id=admin.id, **c)
            db.add(campaign)

        await db.flush()

        # Create demo leads
        leads_data = [
            {"name": "Abdullah Al-Faisal", "company": "Al-Faisal Holding", "email": "abdullah@alfaisal.com", "website": "alfaisal.com", "industry": "Real Estate", "location": "Dubai", "status": "qualified", "score": 85, "is_qualified": True, "client_id": clients[0].id, "source": "google"},
            {"name": "Nora Al-Saud", "company": "Saudia Tech", "email": "nora@saudiatech.com", "website": "saudiatech.com", "industry": "Technology", "location": "Riyadh", "status": "new", "score": 72, "is_qualified": True, "client_id": clients[1].id, "source": "linkedin"},
            {"name": "Khalid Al-Thani", "company": "Thani Group", "email": "khalid@thanigroup.qa", "website": "thanigroup.qa", "industry": "Consulting", "location": "Doha", "status": "contacted", "score": 45, "is_qualified": False, "client_id": clients[2].id, "source": "google"},
            {"name": "Layla Mahmoud", "company": "Layla's Beauty", "email": "layla@laylabeauty.com", "website": "laylabeauty.com", "industry": "Beauty", "location": "Jeddah", "status": "new", "score": 35, "is_qualified": False, "source": "google"},
            {"name": "Faisal Al-Qahtani", "company": "Qahtani Motors", "email": "faisal@qahtanimotors.com", "website": "qahtanimotors.com", "industry": "Automotive", "location": "Riyadh", "status": "converted", "score": 92, "is_qualified": True, "source": "referral"},
        ]
        for l in leads_data:
            lead = Lead(user_id=admin.id, **l)
            db.add(lead)

        await db.commit()

    print("✅ Demo data seeded successfully!")
    print(f"   • Admin: mohammedidrees840@gmail.com / OpenLeads2024!")
    print(f"   • 3 clients")
    print(f"   • 3 campaigns")
    print(f"   • 5 leads")
    print(f"   • MRR: ${admin.mrr}")


if __name__ == "__main__":
    asyncio.run(seed())
