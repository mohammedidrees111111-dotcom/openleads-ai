from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import logging
import dkim
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD

    async def send(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        tracking_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not self.username or not self.password:
            return {"success": False, "error": "SMTP not configured"}

        try:
            msg = MIMEMultipart("alternative")
            sender = f"{from_name or 'OpenLeads AI'} <{self.username}>"
            msg["From"] = sender
            msg["To"] = to_email
            msg["Subject"] = subject
            if reply_to:
                msg["Reply-To"] = reply_to

            if tracking_id:
                tracking_pixel = f'<img src="{settings.BACKEND_URL}/api/v1/track/open/{tracking_id}" width="1" height="1" style="display:none" />'
                if body_html:
                    body_html += tracking_pixel
                else:
                    body_html = body_text.replace("\n", "<br>\n") + tracking_pixel

            msg.attach(MIMEText(body_text, "plain", "utf-8"))
            if body_html:
                msg.attach(MIMEText(body_html, "html", "utf-8"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            return {
                "success": True,
                "to": to_email,
                "subject": subject,
                "sent_at": datetime.now(timezone.utc).isoformat(),
            }
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failed")
            return {"success": False, "error": "SMTP authentication failed. Check your credentials."}
        except smtplib.SMTPRecipientsRefused as e:
            logger.error(f"Recipient refused: {e}")
            return {"success": False, "error": f"Recipient refused: {e}"}
        except smtplib.SMTPServerDisconnected:
            logger.error("SMTP server disconnected")
            return {"success": False, "error": "SMTP server disconnected"}
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return {"success": False, "error": str(e)}

    async def send_bulk(
        self,
        recipients: List[Dict[str, str]],
        subject_template: str,
        body_template: str,
        delay_between: int = 3,
    ) -> List[Dict[str, Any]]:
        import asyncio
        results = []
        for i, recipient in enumerate(recipients):
            subject = subject_template.format(**recipient)
            body = body_template.format(**recipient)
            result = await self.send(
                to_email=recipient["email"],
                subject=subject,
                body_text=body,
                from_name=recipient.get("from_name"),
            )
            results.append(result)
            if i < len(recipients) - 1:
                await asyncio.sleep(delay_between)
        return results

    async def verify_email(self, email: str) -> Dict[str, bool]:
        import re
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        format_valid = bool(re.match(pattern, email))

        if not format_valid:
            return {"valid": False, "reason": "Invalid format"}

        domain = email.split("@")[1]
        try:
            import dns.resolver
            records = dns.resolver.resolve(domain, "MX")
            return {"valid": len(records) > 0, "reason": "Domain accepts mail" if records else "No MX records"}
        except ImportError:
            return {"valid": format_valid, "reason": "DNS check unavailable (install dnspython)"}
        except Exception:
            return {"valid": False, "reason": "Domain does not exist"}
