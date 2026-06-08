import os
from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    APP_NAME: str = "OpenLeads AI"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/openleads")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")

    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: Optional[str] = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")

    TWILIO_ACCOUNT_SID: Optional[str] = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: Optional[str] = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: Optional[str] = os.getenv("TWILIO_PHONE_NUMBER")

    LINKEDIN_EMAIL: Optional[str] = os.getenv("LINKEDIN_EMAIL")
    LINKEDIN_PASSWORD: Optional[str] = os.getenv("LINKEDIN_PASSWORD")

    WHATSAPP_API_KEY: Optional[str] = os.getenv("WHATSAPP_API_KEY")
    WHATSAPP_PHONE_ID: Optional[str] = os.getenv("WHATSAPP_PHONE_ID")

    STRIPE_SECRET_KEY: Optional[str] = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = os.getenv("STRIPE_WEBHOOK_SECRET")
    PAYPAL_CLIENT_ID: Optional[str] = os.getenv("PAYPAL_CLIENT_ID")
    PAYPAL_CLIENT_SECRET: Optional[str] = os.getenv("PAYPAL_CLIENT_SECRET")

    HUBSPOT_CLIENT_ID: Optional[str] = os.getenv("HUBSPOT_CLIENT_ID")
    HUBSPOT_CLIENT_SECRET: Optional[str] = os.getenv("HUBSPOT_CLIENT_SECRET")
    SALESFORCE_CLIENT_ID: Optional[str] = os.getenv("SALESFORCE_CLIENT_ID")
    SALESFORCE_CLIENT_SECRET: Optional[str] = os.getenv("SALESFORCE_CLIENT_SECRET")
    PIPEDRIVE_API_TOKEN: Optional[str] = os.getenv("PIPEDRIVE_API_TOKEN")
    ZOHO_CLIENT_ID: Optional[str] = os.getenv("ZOHO_CLIENT_ID")
    ZOHO_CLIENT_SECRET: Optional[str] = os.getenv("ZOHO_CLIENT_SECRET")

    CLEARBIT_API_KEY: Optional[str] = os.getenv("CLEARBIT_API_KEY")
    HUNTER_API_KEY: Optional[str] = os.getenv("HUNTER_API_KEY")
    APOLLO_API_KEY: Optional[str] = os.getenv("APOLLO_API_KEY")
    GOOGLE_SEARCH_API_KEY: Optional[str] = os.getenv("GOOGLE_SEARCH_API_KEY")
    GOOGLE_SEARCH_ENGINE_ID: Optional[str] = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

    N8N_WEBHOOK_URL: Optional[str] = os.getenv("N8N_WEBHOOK_URL")
    ZAPIER_WEBHOOK_URL: Optional[str] = os.getenv("ZAPIER_WEBHOOK_URL")

    DOMAIN: str = os.getenv("DOMAIN", "openleads.ai")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")

    CORS_ORIGINS: List[str] = ["*"]

    DAILY_EMAIL_LIMIT: int = 50
    DAILY_LINKEDIN_LIMIT: int = 30
    DAILY_WHATSAPP_LIMIT: int = 100
    DAILY_SMS_LIMIT: int = 50

    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
