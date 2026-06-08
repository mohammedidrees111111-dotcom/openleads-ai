from typing import Optional, Dict, Any
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class SMSService:
    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.from_number = settings.TWILIO_PHONE_NUMBER
        self.daily_limit = 50
        self.sent_today = 0

    async def send(self, to_number: str, message: str) -> Dict[str, Any]:
        if not self.account_sid or not self.auth_token or not self.from_number:
            return {"success": False, "error": "Twilio not configured"}

        if self.sent_today >= self.daily_limit:
            return {"success": False, "error": "Daily SMS limit reached"}

        try:
            from twilio.rest import Client
            client = Client(self.account_sid, self.auth_token)
            msg = client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number,
            )
            self.sent_today += 1
            return {"success": True, "to": to_number, "sid": msg.sid, "status": msg.status}
        except ImportError:
            # Fallback: use requests
            try:
                import requests
                from base64 import b64encode
                auth = b64encode(f"{self.account_sid}:{self.auth_token}".encode()).decode()
                resp = requests.post(
                    f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json",
                    data={"To": to_number, "From": self.from_number, "Body": message},
                    headers={"Authorization": f"Basic {auth}"},
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()
                self.sent_today += 1
                return {"success": True, "to": to_number, "sid": data.get("sid"), "status": data.get("status")}
            except Exception as e:
                return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"SMS send failed: {e}")
            return {"success": False, "error": str(e)}
