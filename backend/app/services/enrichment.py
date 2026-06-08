from typing import Optional, Dict, Any, List
from app.core.config import settings
import requests
import logging

logger = logging.getLogger(__name__)


class DataEnrichmentService:
    def __init__(self):
        self.clearbit_key = settings.CLEARBIT_API_KEY
        self.hunter_key = settings.HUNTER_API_KEY
        self.apollo_key = settings.APOLLO_API_KEY

    async def enrich(self, lead) -> Dict[str, Any]:
        result = {}
        domain = self._extract_domain(lead.website or lead.company or lead.name)

        if domain:
            if self.clearbit_key:
                clearbit_data = await self._clearbit_enrich(domain)
                if clearbit_data:
                    result.update(clearbit_data)

            if self.hunter_key and not lead.email:
                hunter_data = await self._hunter_enrich(domain)
                if hunter_data and hunter_data.get("email"):
                    result["email"] = hunter_data["email"]

            if self.apollo_key:
                apollo_data = await self._apollo_enrich(domain)
                if apollo_data:
                    result.update(apollo_data)

        return result

    def _extract_domain(self, text: str) -> Optional[str]:
        import re
        if not text:
            return None
        url_pattern = r"https?://(?:www\.)?([^/\s]+)"
        match = re.search(url_pattern, text)
        if match:
            return match.group(1)
        if "." in text and " " not in text:
            return text
        return None

    async def _clearbit_enrich(self, domain: str) -> Dict[str, Any]:
        try:
            resp = requests.get(
                f"https://company.clearbit.com/v2/companies/find?domain={domain}",
                auth=(self.clearbit_key, ""),
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "company": data.get("name"),
                    "industry": data.get("category", {}).get("industry"),
                    "company_size": data.get("metrics", {}).get("employees"),
                    "city": data.get("geo", {}).get("city"),
                    "country": data.get("geo", {}).get("country"),
                    "latitude": data.get("geo", {}).get("lat"),
                    "longitude": data.get("geo", {}).get("lng"),
                    "tech_stack": [
                        t.get("name") for t in data.get("tech", [])
                    ] if data.get("tech") else [],
                }
        except Exception as e:
            logger.warning(f"Clearbit enrichment failed for {domain}: {e}")
        return {}

    async def _hunter_enrich(self, domain: str) -> Dict[str, Any]:
        try:
            resp = requests.get(
                f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={self.hunter_key}",
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                emails = data.get("emails", [])
                if emails:
                    valid = [e for e in emails if e.get("position") and "ceo" in e.get("position", "").lower()]
                    if not valid:
                        valid = [e for e in emails if e.get("position") and "founder" in e.get("position", "").lower()]
                    if not valid:
                        valid = [e for e in emails if e.get("position")]
                    if not valid:
                        valid = [e for e in emails if e.get("type") == "generic"]
                    if valid:
                        return {
                            "email": valid[0].get("value"),
                            "position": valid[0].get("position"),
                            "name": valid[0].get("first_name", "") + " " + valid[0].get("last_name", ""),
                        }
        except Exception as e:
            logger.warning(f"Hunter enrichment failed for {domain}: {e}")
        return {}

    async def _apollo_enrich(self, domain: str) -> Dict[str, Any]:
        try:
            resp = requests.post(
                "https://api.apollo.io/v1/organizations/enrich",
                json={"domain": domain},
                headers={"x-api-key": self.apollo_key},
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json().get("organization", {})
                return {
                    "company": data.get("name"),
                    "industry": data.get("industry"),
                    "company_size": data.get("employee_count"),
                    "phone": data.get("phone"),
                    "city": data.get("city"),
                    "country": data.get("country"),
                }
        except Exception as e:
            logger.warning(f"Apollo enrichment failed for {domain}: {e}")
        return {}
