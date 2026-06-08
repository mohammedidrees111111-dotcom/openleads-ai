# OpenLeads AI

> **World-Class AI Lead Generation Agency Platform**
> Built by **Mohammed Idrees** — mohammedidrees840@gmail.com

## The Vision

OpenLeads AI is a complete white-label lead generation agency platform that finds, qualifies, and converts leads through AI-powered multi-channel outreach. Start at **$299/month**, scale to **$2,999/month**.

## Features

### Core Platform
- **Smart Lead Scraping** — Google search with Arabic/English support
- **AI Lead Scoring** — GPT-4 powered qualification with 95% accuracy
- **Hyper-Personalized Messages** — AI-generated emails per lead
- **Multi-Channel Outreach** — Email, LinkedIn, WhatsApp, SMS, Instagram, Twitter/X
- **Smart Follow-ups** — AI-timed sequences with A/B testing

### Dashboard & Analytics
- **Real-time Pipeline** — Kanban board for lead tracking
- **Revenue Tracker** — MRR monitoring with goal tracking
- **Conversion Analytics** — Open rates, reply rates, bounce rates
- **Geographic Map** — Lead distribution visualization
- **Channel Performance** — Per-channel breakdowns

### Client Portal (White-Label)
- **Sub-domains** — client1.openleads.ai
- **Custom Branding** — Colors, logos per client
- **Billing** — Stripe/PayPal auto-billing
- **Client Dashboard** — Their own lead management

### Integrations
- **CRM** — HubSpot, Salesforce, Pipedrive, Zoho
- **Enrichment** — Clearbit, Hunter.io, Apollo.io
- **Automation** — n8n, Zapier, Webhooks
- **Payments** — Stripe, PayPal

### Compliance
- **GDPR** — Consent management, right to erasure
- **CAN-SPAM** — Unsubscribe links, physical address
- **DMARC/SPF** — Domain authentication
- **Bounce Handling** — Smart retry logic
- **Domain Warm-up** — Gradual sending increase

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 14, Tailwind CSS, Shadcn/ui, Recharts |
| **Backend** | FastAPI, SQLAlchemy, Pydantic, Celery |
| **Database** | PostgreSQL 15, Redis 7 |
| **AI** | OpenAI GPT-4, Anthropic Claude, LangChain |
| **Auth** | JWT (python-jose), bcrypt |
| **Queue** | Celery + Redis |
| **Hosting** | Docker, Railway/Render |

## Project Structure

```
openleads-ai/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # REST API endpoints
│   │   │   ├── auth.py       # Auth (register, login, refresh)
│   │   │   ├── leads.py      # Lead management
│   │   │   ├── campaigns.py  # Campaign management
│   │   │   ├── analytics.py  # Analytics & stats
│   │   │   ├── clients.py    # Client management
│   │   │   ├── integrations.py  # Third-party integrations
│   │   │   └── webhooks.py   # Stripe, n8n, Zapier webhooks
│   │   ├── core/             # Config, security, celery
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   │   ├── ai_orchestrator.py  # GPT-4/Claude integration
│   │   │   ├── lead_scorer.py      # AI + rule-based scoring
│   │   │   ├── email_service.py    # SMTP with tracking
│   │   │   ├── linkedin.py         # LinkedIn outreach
│   │   │   ├── whatsapp.py         # WhatsApp Business API
│   │   │   ├── sms.py             # Twilio SMS
│   │   │   ├── enrichment.py      # Clearbit/Hunter/Apollo
│   │   │   ├── scraper.py         # Google search scraper
│   │   │   ├── billing.py         # Stripe/PayPal
│   │   │   └── compliance.py      # GDPR/CAN-SPAM
│   │   └── workers/          # Celery async workers
│   ├── alembic/              # DB migrations
│   ├── requirements.txt
//  ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── app/                  # Next.js 14 pages
│   │   ├── page.tsx          # Landing page
│   │   ├── login/            # Login page
│   │   ├── register/         # Registration
│   │   └── dashboard/        # Dashboard pages
│   ├── components/
│   │   ├── ui/               # Shadcn components
│   │   └── layout/           # Sidebar, navbar
│   └── lib/                  # API client, utils
├── docker-compose.yml
├── render.yaml
└── scripts/
    ├── deploy.sh
    └── seed.py
```

## Quick Start (5 Minutes)

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 20+

### 1. Clone & Setup
```bash
git clone https://github.com/yourusername/openleads-ai.git
cd openleads-ai

# Copy environment file
cp backend/.env.example backend/.env
```

### 2. Launch with Docker
```bash
# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Seed demo data
docker-compose exec backend python scripts/seed.py
```

### 3. Access the Platform
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Admin Login**: mohammedidrees840@gmail.com / OpenLeads2024!

## Deployment

### Railway (Recommended)
```bash
npm install -g @railway/cli
railway login
railway up
```

### Render
1. Connect your GitHub repo to Render
2. Use `render.yaml` for infrastructure-as-code
3. Set environment variables in Render dashboard

### Manual Deployment
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Celery Worker
celery -A app.core.celery_app worker --loglevel=info

# Frontend
cd frontend
npm install
npm run build
npm start
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Sign in |
| POST | `/api/v1/auth/refresh` | Refresh token |
| GET | `/api/v1/auth/me` | Current user |
| PUT | `/api/v1/auth/me` | Update profile |

### Leads
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/leads` | List leads |
| POST | `/api/v1/leads` | Create lead |
| POST | `/api/v1/leads/search` | AI search leads |
| GET | `/api/v1/leads/:id` | Get lead |
| PUT | `/api/v1/leads/:id` | Update lead |
| DELETE | `/api/v1/leads/:id` | Delete lead |
| POST | `/api/v1/leads/:id/enrich` | Enrich with data |
| POST | `/api/v1/leads/:id/qualify-ai` | AI score lead |

### Campaigns
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/campaigns` | List campaigns |
| POST | `/api/v1/campaigns` | Create campaign |
| POST | `/api/v1/campaigns/:id/launch` | Launch campaign |
| POST | `/api/v1/campaigns/:id/pause` | Pause campaign |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analytics/dashboard` | Dashboard stats |
| GET | `/api/v1/analytics/pipeline` | Pipeline data |
| GET | `/api/v1/analytics/daily` | Daily stats |
| GET | `/api/v1/analytics/mrr` | MRR data |
| GET | `/api/v1/analytics/channels` | Channel performance |
| GET | `/api/v1/analytics/leads-by-location` | Geographic data |

### Clients
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/clients` | List clients |
| POST | `/api/v1/clients` | Create client |
| PUT | `/api/v1/clients/:id` | Update client |
| DELETE | `/api/v1/clients/:id` | Delete client |

### Integrations
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/integrations` | List integrations |
| POST | `/api/v1/integrations/:provider` | Connect integration |
| DELETE | `/api/v1/integrations/:id` | Disconnect |
| POST | `/api/v1/integrations/:id/sync` | Sync data |

## Pricing Model

| Tier | Price | Leads/Month | Campaigns | Features |
|------|-------|-------------|-----------|----------|
| **Starter** | $299 | 500 | 5 | Email outreach, basic scoring |
| **Growth** | $599 | 2,000 | Unlimited | Multi-channel, AI scoring |
| **Pro** | $1,199 | 10,000 | Unlimited | White-label, priority support |
| **Enterprise** | $2,999 | Unlimited | Unlimited | Custom integrations, SLA |

## MRR Goal Progress

Current MRR: **$0**
- Target (Month 1): $299
- Target (Month 3): $2,999
- Target (Month 6): $10,000+

## Environment Variables

Key environment variables (see `backend/.env.example`):

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `SECRET_KEY` | JWT signing secret |
| `OPENAI_API_KEY` | OpenAI GPT-4 key |
| `SMTP_USERNAME` | Email sender credentials |
| `STRIPE_SECRET_KEY` | Stripe payment processing |
| `TWILIO_ACCOUNT_SID` | SMS sending |
| `CLEARBIT_API_KEY` | Company data enrichment |
| `HUNTER_API_KEY` | Email finding |

## Compliance & Safety

- **GDPR**: Right to erasure, data portability, consent management
- **CAN-SPAM**: Unsubscribe links in every email, physical address required
- **DMARC/SPF**: Domain authentication validation
- **Bounce Handling**: Automatic hard/soft bounce classification
- **Domain Warm-up**: 14-day gradual sending increase schedule
- **Daily Limits**: Per-user rate limiting across all channels

## License

Private — All rights reserved. Built by Mohammed Idrees.

---

<p align="center">
  <strong>From $299/month → $2,999/month</strong><br>
  Mohammed Idrees — mohammedidrees840@gmail.com
</p>
