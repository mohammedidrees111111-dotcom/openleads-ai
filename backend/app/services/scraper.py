import json
import logging
from typing import List, Dict, Any, Optional
import requests
import random
import time
import re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse
from app.core.config import settings
try:
    from ddgs import DDGS
    HAS_DDG = True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        HAS_DDG = True
    except ImportError:
        HAS_DDG = False

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
]

ARABIC_KEYWORDS = {
    "\u0645\u062d\u0627\u0645\u064a": "lawyer", "\u0637\u0628\u064a\u0628": "doctor", "\u0639\u064a\u0627\u062f\u0629": "clinic", "\u0645\u0633\u062a\u0634\u0641\u0649": "hospital",
    "\u0645\u0637\u0639\u0645": "restaurant", "\u0643\u0627\u0641\u064a\u0647": "cafe", "\u0634\u0631\u0643\u0629": "company", "\u0645\u0643\u062a\u0628": "office",
    "\u0648\u0643\u0627\u0644\u0629": "agency", "\u062a\u0633\u0648\u064a\u0642": "marketing", "\u0628\u0631\u0645\u062c\u0629": "software", "\u062a\u0635\u0645\u064a\u0645": "design",
    "\u0639\u0642\u0627\u0631": "real estate", "\u0633\u064a\u0627\u062d\u0629": "tourism", "\u0641\u0646\u062f\u0642": "hotel",
    "\u062a\u0639\u0644\u064a\u0645": "education", "\u0645\u062f\u0631\u0633\u0629": "school", "\u0633\u064a\u0627\u0631\u0627\u062a": "car dealership",
    "\u062a\u062c\u0645\u064a\u0644": "beauty salon", "\u0635\u0627\u0644\u0648\u0646": "salon",
}

ARABIC_CITIES = {
    "\u0627\u0644\u0631\u064a\u0627\u0636": "Riyadh", "\u062c\u062f\u0629": "Jeddah", "\u0645\u0643\u0629": "Makkah", "\u0627\u0644\u062f\u0645\u0627\u0645": "Dammam",
    "\u0627\u0644\u062e\u0628\u0631": "Khobar", "\u062f\u0628\u064a": "Dubai", "\u0623\u0628\u0648\u0638\u0628\u064a": "Abu Dhabi", "\u0627\u0644\u0634\u0627\u0631\u0642\u0629": "Sharjah",
    "\u0627\u0644\u062f\u0648\u062d\u0629": "Doha", "\u0627\u0644\u0645\u0646\u0627\u0645\u0629": "Manama", "\u0627\u0644\u0643\u0648\u064a\u062a": "Kuwait City",
    "\u0645\u0633\u0642\u0637": "Muscat", "\u0639\u0645\u0627\u0646": "Amman", "\u0627\u0644\u0642\u0627\u0647\u0631\u0629": "Cairo",
    "\u0627\u0633\u0637\u0646\u0628\u0648\u0644": "Istanbul",
}


class GoogleScraper:
    def __init__(self):
        self.session = requests.Session()
        self._api_key = settings.GOOGLE_SEARCH_API_KEY
        self._engine_id = settings.GOOGLE_SEARCH_ENGINE_ID

    def get_ua(self):
        return random.choice(USER_AGENTS)

    def _headers(self):
        return {
            "User-Agent": self.get_ua(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

    def search(self, keyword: str, location: str, max_results: int = 10) -> List[Dict[str, Any]]:
        if HAS_DDG:
            result = self._search_ddg(keyword, location, max_results)
            if result:
                return result
        if self._api_key and self._api_key != "your-google-api-key" and self._engine_id and self._engine_id != "your-google-engine-id":
            result = self._search_api(keyword, location, max_results)
            if result:
                return result
        return self._search_html(keyword, location, max_results)

    def _search_api(self, keyword: str, location: str, max_results: int = 10) -> List[Dict[str, Any]]:
        query = f"{keyword} {location}"
        try:
            resp = requests.get(
                "https://www.googleapis.com/customsearch/v1",
                params={"key": self._api_key, "cx": self._engine_id, "q": query, "num": min(max_results, 10)},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            leads = []
            for item in data.get("items", []):
                title = item.get("title", "")
                link = item.get("link", "")
                if title and len(title) > 3 and link and not any(x in link for x in ["google.com", "youtube.com"]):
                    leads.append({
                        "name": title, "website": link, "email": self._extract_email_from_snippet(item.get("snippet", "")),
                        "phone": "", "description": item.get("snippet", ""), "source": "google", "status": "new", "score": 0, "location": location,
                    })
            logger.info(f"Google API: {len(leads)} results for '{query}'")
            return leads
        except Exception as e:
            logger.warning(f"Google API failed: {e}")
            return []

    def _search_ddg(self, keyword: str, location: str, max_results: int = 10) -> List[Dict[str, Any]]:
        query = f"{keyword} {location}"
        try:
            leads = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    title = r.get("title", "")
                    link = r.get("href", "")
                    snippet = r.get("body", "")
                    if title and len(title) > 3 and link and not any(x in link.lower() for x in ["duckduckgo.com", "google.com", "youtube.com"]):
                        leads.append({
                            "name": title, "website": link, "email": self._extract_email_from_snippet(snippet),
                            "phone": "", "description": snippet, "source": "duckduckgo", "status": "new", "score": 0, "location": location,
                        })
            logger.info(f"DDGS: {len(leads)} results for '{query}'")
            return leads
        except Exception as e:
            logger.warning(f"DDGS failed: {e}")
            return []

    def _search_html(self, keyword: str, location: str, max_results: int = 10) -> List[Dict[str, Any]]:
        query = f"{keyword} {location}".replace(" ", "+")
        url = f"https://www.google.com/search?q={query}&num={min(max_results, 20)}"
        try:
            resp = self.session.get(url, headers=self._headers(), timeout=15)
            if resp.status_code != 200:
                logger.warning(f"Google HTML returned {resp.status_code}")
                return []
            soup = BeautifulSoup(resp.text, "lxml")
            if "captcha" in resp.text.lower() or "unusual traffic" in resp.text.lower():
                logger.warning("Google CAPTCHA detected")
                return []
            leads = []
            for a_tag in soup.select("a[href^='/url?q=']"):
                href = a_tag["href"]
                match = re.search(r'/url\?q=([^&]+)', href)
                if not match:
                    continue
                link = match.group(1)
                if any(x in link.lower() for x in ["google.com", "youtube.com", "facebook.com", "instagram.com"]):
                    continue
                parent = a_tag.find_parent(["div", "span"])
                title = a_tag.get_text(strip=True) or (parent.find("h3").get_text(strip=True) if parent and parent.find("h3") else "")
                if not title or len(title) < 4:
                    title = a_tag.get_text(strip=True)
                snippet = ""
                if parent:
                    sp = parent.find(["div", "span"], {"class": re.compile(r"st|VwiC3b|snippet|BNeawe")})
                    if sp:
                        snippet = sp.get_text(strip=True)[:500]
                if title and len(title) > 3:
                    leads.append({
                        "name": title, "website": link.split("?")[0], "email": self._extract_email_from_snippet(snippet),
                        "phone": "", "description": snippet, "source": "google", "status": "new", "score": 0, "location": location,
                    })
                    if len(leads) >= max_results:
                        break
            logger.info(f"Google HTML: {len(leads)} results for '{query}'")
            time.sleep(random.uniform(3, 6))
            return leads
        except Exception as e:
            logger.warning(f"Google HTML error: {e}")
            return []

    @staticmethod
    def _extract_email_from_snippet(text: str) -> str:
        emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        bad = {"example", "test", "noreply", "no-reply", "sentry"}
        emails = [e for e in emails if not any(x in e.split("@")[0].lower() for x in bad)]
        return emails[0] if emails else ""

    def _find_email(self, website: str) -> str:
        try:
            if not website.startswith("http"):
                website = "https://" + website
            resp = self.session.get(website, headers=self._headers(), timeout=8, allow_redirects=True)
            emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", resp.text)
            bad = {"example", "test", "noreply", "no-reply", "sentry"}
            emails = [e for e in emails if not any(x in e.split("@")[0].lower() for x in bad)]
            for priority in ["contact", "sales", "hello", "team", "info", "support"]:
                for e in emails:
                    if e.split("@")[0].lower().startswith(priority):
                        return e
            return emails[0] if emails else ""
        except Exception:
            return ""

    @staticmethod
    def parse_input(user_input: str) -> Dict[str, Any]:
        user_input = user_input.strip().lower()
        has_arabic = bool(re.search(r"[\u0600-\u06FF]", user_input))
        keywords = []
        locations = []

        if has_arabic:
            for ar, en in ARABIC_KEYWORDS.items():
                if ar in user_input:
                    keywords.append(en)
            for ar, en in ARABIC_CITIES.items():
                if ar in user_input:
                    locations.append(en)
            if not keywords:
                keywords = ["company"]
            if not locations:
                locations = ["UAE", "Saudi Arabia"]
        else:
            words = user_input.split()
            countries = ["USA", "UK", "Canada", "Australia", "Germany", "France", "UAE", "Saudi Arabia", "Qatar", "Kuwait", "Egypt"]
            for country in countries:
                if country.lower() in user_input:
                    locations.append(country)
            if not locations and len(words) > 1:
                locations.append(words[-1].title())
                keywords = [" ".join(words[:-1])]
            else:
                keywords = [user_input]

        if not locations:
            locations = ["USA", "UK"]

        return {"keywords": keywords if keywords else [user_input], "locations": locations}
