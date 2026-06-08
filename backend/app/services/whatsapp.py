from typing import Optional, Dict, Any, List
from app.core.config import settings
import requests
import logging

logger = logging.getLogger(__name__)


class WhatsAppService:
    def __init__(self):
        self.api_key = settings.WHATSAPP_API_KEY
        self.phone_id = settings.WHATSAPP_PHONE_ID
        self.daily_limit = 100
        self.sent_today = 0

    async def send_message(self, to_number: str, message: str) -> Dict[str, Any]:
        if not self.api_key or not self.phone_id:
            return {"success": False, "error": "WhatsApp not configured"}

        if self.sent_today >= self.daily_limit:
            return {"success": False, "error": "Daily limit reached"}

        try:
            url = f"https://graph.facebook.com/v17.0/{self.phone_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to_number,
                "type": "text",
                "text": {"body": message},
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            resp.raise_for_status()

            self.sent_today += 1
            return {
                "success": True,
                "to": to_number,
                "message_id": resp.json().get("messages", [{}])[0].get("id", ""),
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"WhatsApp send failed: {e}")
            return {"success": False, "error": str(e)}

    async def send_template(
        self, to_number: str, template_name: str, parameters: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        if not self.api_key or not self.phone_id:
            return {"success": False, "error": "WhatsApp not configured"}

        try:
            url = f"https://graph.facebook.com/v17.0/{self.phone_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to_number,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": "en"},
                    "components": [{"type": "body", "parameters": [{"type": "text", "text": p} for p in parameters]}],
                },
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            resp.raise_for_status()
            return {"success": True, "to": to_number}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
