import re
import requests
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from app.core.config import settings

logger = logging.getLogger(__name__)

PROFILE_ID_RE = re.compile(r"/in/([^/?#&]+)")


class LinkedInService:
    BASE = "https://www.linkedin.com"
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    def __init__(self):
        self.email = settings.LINKEDIN_EMAIL
        self.password = settings.LINKEDIN_PASSWORD
        self.daily_limit = 30
        self.sent_today = 0
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self._csrf_token = None
        self._authenticated = False

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------
    def _ensure_auth(self):
        if not self._authenticated:
            self._login()
        return self._authenticated

    def _login(self):
        if not self.email or not self.password:
            logger.warning("LinkedIn credentials not configured")
            return

        try:
            resp = self.session.get(
                urljoin(self.BASE, "/login"), timeout=15
            )
            soup = BeautifulSoup(resp.text, "lxml")
            csrf_input = soup.find("input", {"name": "loginCsrfParam"})
            csrf = csrf_input.get("value") if csrf_input else ""

            payload = {
                "session_key": self.email,
                "session_password": self.password,
                "loginCsrfParam": csrf,
                "trk": "guest_homepage-basic_sign-in-submit",
            }
            resp = self.session.post(
                urljoin(self.BASE, "/checkpoint/lg/login-submit"),
                data=payload,
                allow_redirects=True,
                timeout=15,
            )

            if "feed" in resp.url or "checkpoint" not in resp.url:
                self._authenticated = True
                self._csrf_token = self._extract_csrf(resp.text)
                logger.info("LinkedIn login successful")
            else:
                logger.error("LinkedIn login failed – check credentials")
        except requests.RequestException as e:
            logger.error(f"LinkedIn login network error: {e}")

    def _extract_csrf(self, html: str) -> Optional[str]:
        match = re.search(r'name="csrf-token"\s+content="([^"]+)"', html)
        return match.group(1) if match else None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _profile_id(self, url: str) -> Optional[str]:
        m = PROFILE_ID_RE.search(url)
        return m.group(1) if m else None

    def _voyager_get(self, path: str, params: dict = None) -> Optional[dict]:
        headers = {
            "csrf-token": self._csrf_token or "",
            "x-restli-protocol-version": "2.0.0",
        }
        try:
            resp = self.session.get(
                urljoin(self.BASE, path), headers=headers, params=params, timeout=15
            )
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as e:
            logger.error(f"Voyager GET {path} failed: {e}")
            return None

    def _voyager_post(self, path: str, payload: dict) -> Optional[dict]:
        headers = {
            "csrf-token": self._csrf_token or "",
            "x-restli-protocol-version": "2.0.0",
            "Content-Type": "application/json",
        }
        try:
            resp = self.session.post(
                urljoin(self.BASE, path), json=payload, headers=headers, timeout=15
            )
            resp.raise_for_status()
            return resp.json() if resp.text else {}
        except requests.RequestException as e:
            logger.error(f"Voyager POST {path} failed: {e}")
            return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def send_connection_request(self, profile_url: str, message: Optional[str] = None) -> Dict[str, Any]:
        if not self._ensure_auth():
            return {"success": False, "error": "LinkedIn not authenticated"}

        if self.sent_today >= self.daily_limit:
            return {"success": False, "error": "Daily limit reached"}

        profile_id = self._profile_id(profile_url)
        if not profile_id:
            return {"success": False, "error": "Invalid LinkedIn profile URL"}

        payload = {"emberEntityName": "growth/growthNormInvitation"}
        invitation = {
            "invitee": {"com.linkedin.voyager.growth.invitation.InviteeProfile": {"profileId": profile_id}},
        }
        if message:
            invitation["customMessage"] = message
        payload["invitation"] = invitation

        result = self._voyager_post("/voyager/api/growth/normInvitation", payload)
        if result is None:
            return {"success": False, "error": "Failed to send connection request"}

        self.sent_today += 1
        return {
            "success": True,
            "profile_url": profile_url,
            "profile_id": profile_id,
            "with_message": bool(message),
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }

    async def send_message(self, profile_url: str, message: str) -> Dict[str, Any]:
        if not self._ensure_auth():
            return {"success": False, "error": "LinkedIn not authenticated"}

        profile_id = self._profile_id(profile_url)
        if not profile_id:
            return {"success": False, "error": "Invalid LinkedIn profile URL"}

        # Create a conversation
        conv_payload = {
            "emberEntityName": "messaging/createConversation",
            "conversation": {
                "participants": [profile_id],
                "subject": "",
                "messages": [
                    {
                        "body": message,
                        "subject": "",
                    }
                ],
            },
        }
        result = self._voyager_post("/voyager/api/messaging/conversations", conv_payload)
        if result is None:
            return {"success": False, "error": "Failed to send message"}

        return {
            "success": True,
            "profile_url": profile_url,
            "profile_id": profile_id,
            "message_length": len(message),
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }

    async def search_profiles(self, keywords: List[str], location: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        if not self._ensure_auth():
            return []

        keyword_str = " ".join(keywords)
        params = {
            "keywords": keyword_str,
            "count": min(limit, 50),
            "start": 0,
        }
        if location:
            params["location"] = location

        data = self._voyager_get("/voyager/api/search/cluster", params)
        if not data:
            return []

        profiles = []
        try:
            elements = data.get("data", {}).get("elements", [])
            for element in elements:
                items = (element.get("items") or element.get("elements", []))
                for item in items:
                    entity = item.get("item", {}).get("entityResult", {}) if isinstance(item, dict) else {}
                    title = entity.get("title", {}).get("text", "")
                    subtitle = entity.get("subtitle", {}).get("text", "")
                    image = entity.get("image", {})
                    tracking = entity.get("trackingUrn", "")
                    public_id = tracking.split(":")[-1] if ":" in tracking else ""
                    profiles.append({
                        "name": title,
                        "headline": subtitle,
                        "public_id": public_id,
                        "url": f"{self.BASE}/in/{public_id}" if public_id else "",
                    })
                    if len(profiles) >= limit:
                        break
                if len(profiles) >= limit:
                    break
        except (KeyError, TypeError, IndexError) as e:
            logger.warning(f"Could not parse LinkedIn search results: {e}")

        return profiles

    async def get_profile_info(self, profile_url: str) -> Dict[str, Any]:
        if not self._ensure_auth():
            return {"url": profile_url, "error": "Not authenticated"}

        profile_id = self._profile_id(profile_url)
        if not profile_id:
            return {"url": profile_url, "error": "Invalid URL"}

        data = self._voyager_get(f"/voyager/api/identity/profiles/{profile_id}/profileView")
        if not data:
            return {"url": profile_url, "error": "Profile not found"}

        try:
            profile = data.get("profile", {})
            mini = profile.get("miniProfile", {})
            name = f"{mini.get('firstName', '')} {mini.get('lastName', '')}".strip()
            headline = mini.get("occupation", "")
            location_name = profile.get("locationName", "")
            company_info = (profile.get("position") or [{}])[0] if profile.get("position") else {}
            return {
                "url": profile_url,
                "public_id": profile_id,
                "name": name,
                "headline": headline,
                "company": company_info.get("companyName", ""),
                "position": company_info.get("title", ""),
                "location": location_name,
                "connections": 0,
            }
        except (KeyError, IndexError, TypeError) as e:
            logger.warning(f"Could not parse profile info: {e}")
            return {"url": profile_url, "error": "Parse error"}
