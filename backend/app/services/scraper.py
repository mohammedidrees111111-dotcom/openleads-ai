import json
import logging
from typing import List, Dict, Any, Optional
import requests
import random
import time
import re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from app.core.config import settings

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

ARABIC_KEYWORDS = {
    "محامي": "lawyer", "طبيب": "doctor", "عيادة": "clinic", "مستشفى": "hospital",
    "مطعم": "restaurant", "كافيه": "cafe", "شركة": "company", "مكتب": "office",
    "وكالة": "agency", "تسويق": "marketing", "برمجة": "software", "تصميم": "design",
    "عقار": "real estate", "سياحة": "tourism", "فندق": "hotel",
    "تعليم": "education", "مدرسة": "school", "سيارات": "car dealership",
    "تجميل": "beauty salon", "صالون": "salon",
}

ARABIC_CITIES = {
    "الرياض": "Riyadh", "جدة": "Jeddah", "مكة": "Makkah", "الدمام": "Dammam",
    "الخبر": "Khobar", "دبي": "Dubai", "أبوظبي": "Abu Dhabi", "الشارقة": "Sharjah",
    "الدوحة": "Doha", "المنامة": "Manama", "الكويت": "Kuwait City",
    "مسقط": "Muscat", "عمان": "Amman", "القاهرة": "Cairo",
    "اسطنبول": "Istanbul",
}

SEARCH_RESULTS_CLASSES = ["g", "MjjYud", "Gx5Zad", "tF2Cxc"]


class GoogleScraper:
    def __init__(self):
        self.session = requests.Session()
        self._api_key = settings.GOOGLE_SEARCH_API_KEY
        self._engine_id = settings.GOOGLE_SEARCH_ENGINE_ID

    def get_ua(self):
        return random.choice(USER_AGENTS)

    def search(self, keyword: str, location: str, max_results: int = 10) -> List[Dict[str, Any]]:
        if self._api_key and self._engine_id:
            return self._search_api(keyword, location, max_results)
        return self._search_html(keyword, location, max_results)

    def _search_api(self, keyword: str, location: str, max_results: int = 10) -> List[Dict[str, Any]]:
        query = f"{keyword} {location}"
        try:
            resp = requests.get(
                "https://www.googleapis.com/customsearch/v1",
                params={
                    "key": self._api_key,
                    "cx": self._engine_id,
                    "q": query,
                    "num": min(max_results, 10),
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items", [])
            leads = []
            for item in items:
                title = item.get("title", "")
                link = item.get("link", "")
                snippet = item.get("snippet", "")
                if title and len(title) > 3:
                    lead = {
                        "name": title,
                        "website": link,
                        "email": self._find_email(link),
                        "phone": "",
                        "description": snippet,
                        "source": "google",
                        "status": "new",
                        "score": 0,
                        "location": location,
                    }
                    leads.append(lead)
            logger.info(f"Google API search for '{query}': {len(leads)} results")
            return leads
        except requests.RequestException as e:
            logger.error(f"Google API search failed: {e}")
            return []

    def _search_html(self, keyword: str, location: str, max_results: int = 10) -> List[Dict[str, Any]]:
        leads = []
        query = f"{keyword} {location}".replace(" ", "+")
        url = f"https://www.google.com/search?q={query}&num={min(max_results, 20)}"

        try:
            resp = self.session.get(
                url,
                headers={"User-Agent": self.get_ua(), "Accept": "text/html", "Accept-Language": "en-US,en;q=0.9"},
                timeout=15,
            )
            if resp.status_code != 200:
                logger.warning(f"Google search returned {resp.status_code}")
                return []

            soup = BeautifulSoup(resp.text, "lxml")
            results = []
            for cls_name in SEARCH_RESULTS_CLASSES:
                results = soup.find_all("div", {"class": cls_name})
                if results:
                    break

            if not results:
                results = soup.find_all("div", {"data-hveid": True})

            for r in results:
                lead = self._extract(r, location)
                if lead:
                    leads.append(lead)
                    if len(leads) >= max_results:
                        break

            logger.info(f"Google HTML search for '{query}': {len(leads)} results")
            time.sleep(random.uniform(3, 6))
        except requests.RequestException as e:
            logger.error(f"Google HTML search failed: {e}")
        except Exception as e:
            logger.warning(f"Google HTML parse error: {e}")

        return leads

    def _extract(self, result, location: str = "") -> Optional[Dict[str, Any]]:
        lead = {
            "name": "",
            "website": "",
            "email": "",
            "phone": "",
            "description": "",
            "source": "google",
            "status": "new",
            "score": 0,
            "location": location,
        }
        try:
            name_tag = result.find("h3")
            if not name_tag:
                name_tag = result.find(["span", "a", "div"], {"class": re.compile(r"title|heading|LC20lb")})
            if name_tag:
                lead["name"] = name_tag.get_text(strip=True)

            link_tag = result.find("a", href=True)
            if link_tag:
                href = link_tag["href"]
                if href.startswith("/url?q="):
                    href = href.split("/url?q=")[1].split("&")[0]
                if "http" in href and "google" not in href.lower():
                    lead["website"] = href.split("?")[0]

            cite = result.find("cite")
            if cite and not lead["website"]:
                url = cite.get_text(strip=True)
                if "http" in url and "google" not in url.lower():
                    lead["website"] = url

            snippet = result.find(["div", "span"], {"class": re.compile(r"snippet|st|VwiC3b")})
            if snippet:
                lead["description"] = snippet.get_text(strip=True)[:500]

            if lead["website"]:
                lead["email"] = self._find_email(lead["website"])
        except Exception as e:
            logger.debug(f"Extract error: {e}")

        return lead if lead["name"] and len(lead["name"]) > 3 else None

    def _find_email(self, website: str) -> str:
        try:
            if not website.startswith("http"):
                website = "https://" + website
            resp = self.session.get(
                website,
                headers={"User-Agent": self.get_ua(), "Accept": "text/html,application/xhtml+xml"},
                timeout=10,
                allow_redirects=True,
            )
            emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", resp.text)
            bad = {"example", "test", "noreply", "no-reply", "sentry"}
            emails = [e for e in emails if not any(x in e.split("@")[0].lower() for x in bad)]

            for priority in ["contact", "sales", "hello", "team", "info", "support"]:
                for e in emails:
                    if e.split("@")[0].lower().startswith(priority):
                        return e
            return emails[0] if emails else ""
        except requests.RequestException:
            logger.debug(f"Could not fetch {website} for email extraction")
        except Exception:
            logger.debug(f"Error extracting email from {website}")
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
