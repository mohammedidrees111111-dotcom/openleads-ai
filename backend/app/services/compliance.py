from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import re
import hashlib
import requests
import logging

logger = logging.getLogger(__name__)


EU_COUNTRIES = {
    "at", "be", "bg", "hr", "cy", "cz", "dk", "ee", "fi", "fr", "de",
    "gr", "hu", "ie", "it", "lv", "lt", "lu", "mt", "nl", "pl", "pt",
    "ro", "sk", "si", "es", "se", "is", "li", "no", "ch",
}

GDPR_COUNTRY_CODES = {f".{cc}" for cc in EU_COUNTRIES}


class ComplianceService:
    @staticmethod
    def validate_gdpr(email: str, ip_address: Optional[str] = None) -> Dict[str, Any]:
        domain = email.split("@")[-1].lower() if "@" in email else ""
        tld = domain.split(".")[-1] if "." in domain else ""

        is_eu_domain = f".{tld}" in GDPR_COUNTRY_CODES
        is_eu_ip = False

        if ip_address:
            try:
                resp = requests.get(
                    f"http://ip-api.com/json/{ip_address}?fields=countryCode",
                    timeout=5,
                )
                if resp.status_code == 200:
                    cc = resp.json().get("countryCode", "").lower()
                    is_eu_ip = cc in EU_COUNTRIES
            except requests.RequestException:
                pass

        eu_related = is_eu_domain or is_eu_ip

        return {
            "consent_required": eu_related,
            "right_to_erasure": eu_related,
            "data_portability": eu_related,
            "lawful_basis": "consent" if eu_related else "legitimate_interest",
            "eu_related": eu_related,
            "eu_domain": is_eu_domain,
            "eu_ip": is_eu_ip,
        }

    @staticmethod
    def validate_can_spam(email_body: str, from_name: str, from_email: str) -> Dict[str, bool]:
        checks = {
            "has_unsubscribe_link": "unsubscribe" in email_body.lower() or "opt-out" in email_body.lower(),
            "has_physical_address": bool(re.search(r'\d+\s+[A-Za-z\s]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln)',
                                                    email_body, re.IGNORECASE)),
            "has_valid_from": bool(from_name and from_email),
            "subject_not_misleading": True,
        }
        checks["compliant"] = all(checks.values())
        return checks

    @staticmethod
    def generate_unsubscribe_hash(email: str, user_id: int) -> str:
        raw = f"{email}:{user_id}:openleads-unsubscribe-2024"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    @staticmethod
    def add_unsubscribe_link(body: str, email: str, user_id: int, base_url: str = "https://app.openleads.ai") -> str:
        hash_val = ComplianceService.generate_unsubscribe_hash(email, user_id)
        link = f"{base_url}/unsubscribe?email={email}&hash={hash_val}"
        footer = f"\n\n---\nTo unsubscribe, click here: {link}\nOpenLeads AI - Your Lead Generation Partner"
        return body + footer

    @staticmethod
    def validate_dmarc(domain: str) -> Dict[str, Any]:
        try:
            import dns.resolver
            records = dns.resolver.resolve(f"_dmarc.{domain}", "TXT")
            for record in records:
                if "v=DMARC1" in str(record):
                    return {"has_dmarc": True, "record": str(record)}
            return {"has_dmarc": False, "record": None}
        except ImportError:
            return {"has_dmarc": None, "record": "DNS check unavailable"}
        except Exception:
            return {"has_dmarc": False, "record": None}

    @staticmethod
    def validate_spf(domain: str) -> Dict[str, Any]:
        try:
            import dns.resolver
            records = dns.resolver.resolve(domain, "TXT")
            for record in records:
                if "v=spf1" in str(record):
                    return {"has_spf": True, "record": str(record)}
            return {"has_spf": False, "record": None}
        except ImportError:
            return {"has_spf": None, "record": "DNS check unavailable"}
        except Exception:
            return {"has_spf": False, "record": None}


class BounceHandler:
    BOUNCE_TYPES = {
        "hard": ["does not exist", "invalid", "unknown user", "no mailbox", "doesn't have an account"],
        "soft": ["try again", "temporarily", "over quota", "too many connections", "try later"],
        "spam": ["spam", "blocked", "blacklisted", "rejected"],
    }

    @staticmethod
    def classify_bounce(error_message: str) -> str:
        error_lower = error_message.lower()
        for category, patterns in BounceHandler.BOUNCE_TYPES.items():
            if any(p in error_lower for p in patterns):
                return category
        return "unknown"

    @staticmethod
    def should_retry(bounce_type: str, retry_count: int) -> bool:
        if bounce_type == "hard":
            return False
        if bounce_type == "spam":
            return False
        if bounce_type == "soft" and retry_count < 3:
            return True
        return False


class DomainWarmup:
    def __init__(self):
        self.warmup_days = 14
        self.daily_increase = {
            1: 5, 2: 5, 3: 10, 4: 10, 5: 15, 6: 15, 7: 20,
            8: 25, 9: 30, 10: 35, 11: 40, 12: 45, 13: 50, 14: 50,
        }

    def get_daily_limit(self, day: int) -> int:
        if day < 1:
            return 5
        if day > self.warmup_days:
            return 50
        return self.daily_increase.get(day, 50)

    def is_warmup_complete(self, days_active: int) -> bool:
        return days_active >= self.warmup_days

    def get_warmup_schedule(self) -> List[Dict[str, int]]:
        return [{"day": d, "limit": self.daily_increase.get(d, 50)} for d in range(1, self.warmup_days + 1)]
