from typing import Dict, Any
from app.services.ai_orchestrator import AIOrchestrator
import json


class AILeadScorer:
    def __init__(self):
        self.ai = AIOrchestrator()

    async def score(self, lead) -> Dict[str, Any]:
        lead_data = {
            "name": lead.name,
            "company": lead.company,
            "website": lead.website,
            "email": lead.email,
            "phone": lead.phone,
            "industry": lead.industry,
            "location": lead.location,
            "company_size": lead.company_size,
            "position": lead.position,
            "source": lead.source,
            "tags": lead.tags,
            "existing_score": lead.score,
        }
        try:
            result = await self.ai.score_lead(lead_data)
            if isinstance(result, str):
                result = json.loads(result)
            return {
                "score": min(1.0, max(0.0, result.get("score", 0.5))),
                "is_qualified": result.get("is_qualified", True),
                "reasoning": result.get("reasoning", ""),
                "pain_points": result.get("pain_points", []),
                "industry_fit": result.get("industry_fit", "medium"),
                "recommended_action": result.get("recommended_action", "contact"),
            }
        except Exception as e:
            return {
                "score": 0.5,
                "is_qualified": True,
                "reasoning": f"AI scoring error: {str(e)}",
                "pain_points": [],
                "industry_fit": "medium",
                "recommended_action": "contact",
            }


class RuleBasedScorer:
    WEIGHTS = {
        "has_website": 15,
        "has_email": 25,
        "has_phone": 10,
        "has_position": 10,
        "has_company": 10,
        "has_linkedin": 10,
        "has_industry": 5,
        "has_location": 5,
        "is_company_name": 10,
    }

    QUALIFIED_THRESHOLD = 60

    @staticmethod
    def _get(lead, key: str, default=None):
        if isinstance(lead, dict):
            return lead.get(key, default)
        return getattr(lead, key, default)

    def score(self, lead) -> Dict[str, Any]:
        score = 0
        reasons = []

        website = self._get(lead, "website", "")
        if website and len(website) > 10:
            score += self.WEIGHTS["has_website"]
            reasons.append("Has website")

        email = self._get(lead, "email", "")
        if email and "@" in email:
            score += self.WEIGHTS["has_email"]
            reasons.append("Has email")
            if any(x in email.lower() for x in ["contact", "sales", "hello", "info"]):
                score += 5
                reasons.append("Business email")

        if self._get(lead, "phone"):
            score += self.WEIGHTS["has_phone"]
            reasons.append("Has phone")

        if self._get(lead, "position"):
            score += self.WEIGHTS["has_position"]
            reasons.append("Has position")

        if self._get(lead, "company"):
            score += self.WEIGHTS["has_company"]
            reasons.append("Has company")

        if self._get(lead, "linkedin_url"):
            score += self.WEIGHTS["has_linkedin"]
            reasons.append("Has LinkedIn")

        if self._get(lead, "industry"):
            score += self.WEIGHTS["has_industry"]
            reasons.append("Has industry")

        if self._get(lead, "location") or self._get(lead, "city") or self._get(lead, "country"):
            score += self.WEIGHTS["has_location"]
            reasons.append("Has location")

        name = self._get(lead, "name", "")
        company_indicators = ["agency", "solutions", "consulting", "services", "tech", "digital", "group", "llc", "inc", "corp", "company", "ltd", "limited"]
        if name and any(x in name.lower() for x in company_indicators):
            score += self.WEIGHTS["is_company_name"]
            reasons.append("Company name detected")

        personal_indicators = ["linkedin", "facebook", "profile", "resume", "cv"]
        if name and any(x in name.lower() for x in personal_indicators):
            score -= 20
            reasons.append("Personal profile detected (penalty)")

        return {
            "score": max(0, score),
            "is_qualified": score >= self.QUALIFIED_THRESHOLD,
            "reasons": reasons,
        }
