from typing import Optional, List, Dict, Any
from app.core.config import settings
import json
import re
import logging

logger = logging.getLogger(__name__)


class AIOrchestrator:
    def __init__(self):
        self.openai_available = bool(settings.OPENAI_API_KEY)
        self.anthropic_available = bool(settings.ANTHROPIC_API_KEY)

    async def _call_openai(self, system_prompt: str, user_prompt: str, model: str = "gpt-4", temperature: float = 0.7, max_tokens: int = 1000) -> str:
        if not self.openai_available:
            return self._fallback_response(system_prompt, user_prompt)
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"OpenAI call failed: {e}")
            return self._fallback_response(system_prompt, user_prompt)

    async def _call_anthropic(self, system_prompt: str, user_prompt: str, model: str = "claude-3-opus-20240229", max_tokens: int = 1000) -> str:
        if not self.anthropic_available:
            return self._fallback_response(system_prompt, user_prompt)
        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            response = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return response.content[0].text if response.content else ""
        except Exception as e:
            logger.error(f"Anthropic call failed: {e}")
            return self._fallback_response(system_prompt, user_prompt)

    def _fallback_response(self, system_prompt: str, user_prompt: str) -> str:
        try:
            prompt_lower = user_prompt.lower()

            if "score" in prompt_lower or "lead" in prompt_lower:
                lead_json = self._extract_lead_json(user_prompt)
                if lead_json:
                    score, reasoning = self._rule_score(lead_json)
                    return json.dumps({
                        "score": round(score, 2),
                        "is_qualified": score >= 0.5,
                        "reasoning": reasoning,
                        "pain_points": self._infer_pain_points(lead_json),
                        "industry_fit": self._infer_industry_fit(lead_json),
                        "recommended_action": "contact" if score >= 0.7 else "nurture" if score >= 0.4 else "discard",
                    })

            if "message" in prompt_lower or "body" in prompt_lower:
                name = self._extract_name(user_prompt)
                return json.dumps({
                    "subject": f"Helping {name or 'your business'} grow",
                    "body": f"Hi {name or 'there'},\n\nI came across your business and noticed you're doing great work in your industry.\n\nWe help companies streamline their lead generation and automate outreach to close more deals faster.\n\nWould you be open to a 15-minute chat this week to see if we can help?\n\nBest regards,\nMohammed Idrees",
                    "call_to_action": "schedule a 15-minute call",
                    "variants": [
                        f"Quick question for {name}" if name else "Quick question",
                        f"Helping {name or 'your company'} scale outreach",
                    ],
                })

            return json.dumps({"response": "I understand your request. Let me help you with that."})
        except Exception:
            return json.dumps({
                "score": 0.5,
                "is_qualified": True,
                "reasoning": "AI service unavailable. Using rule-based fallback.",
                "pain_points": ["growing their business", "finding more customers", "automating outreach"],
                "message": "Hi there,\n\nI came across your business and wanted to reach out.\n\nWe help companies automate their lead generation and outreach.\n\nWould you be open to a quick chat this week?\n\nBest,\nMohammed Idrees",
            })

    def _extract_lead_json(self, text: str) -> Optional[Dict[str, Any]]:
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            return json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError):
            return None

    def _extract_name(self, text: str) -> Optional[str]:
        patterns = [
            r'"name"\s*:\s*"([^"]+)"',
            r"name[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                return m.group(1)
        return None

    def _rule_score(self, lead: dict) -> tuple:
        score = 0.5
        reasons = []

        has_email = bool(lead.get("email"))
        has_phone = bool(lead.get("phone"))
        has_website = bool(lead.get("website") or lead.get("linkedin_url"))
        has_position = bool(lead.get("position") or lead.get("title"))
        industry = (lead.get("industry") or "").lower()
        location = (lead.get("location") or "").lower()

        if has_email:
            score += 0.15
            reasons.append("has email")
        if has_phone:
            score += 0.1
            reasons.append("has phone")
        if has_website:
            score += 0.1
            reasons.append("has online presence")
        if has_position:
            score += 0.1
            reasons.append("has position/title")

        high_value_industries = {"technology", "finance", "healthcare", "real estate", "consulting", "software", "saas"}
        if industry in high_value_industries:
            score += 0.1
            reasons.append(f"high-value industry: {industry}")

        major_cities = {"dubai", "riyadh", "jeddah", "doha", "abu dhabi", "kuwait", "muscat", "cairo"}
        if location in major_cities:
            score += 0.05
            reasons.append("major market location")

        score = max(0.0, min(1.0, score))
        reasoning = "; ".join(reasons) if reasons else "insufficient data for scoring"
        return score, reasoning

    def _infer_pain_points(self, lead: dict) -> list:
        pains = []
        industry = (lead.get("industry") or "").lower()
        position = (lead.get("position") or lead.get("title") or "").lower()

        if "ceo" in position or "founder" in position or "owner" in position:
            pains.append("scaling the business efficiently")
            pains.append("finding more qualified leads")
        if "marketing" in position:
            pains.append("improving marketing ROI")
            pains.append("generating more qualified leads")
        if "sales" in position:
            pains.append("meeting revenue targets")
            pains.append("automating sales outreach")
        if "real estate" in industry:
            pains.append("finding qualified buyers/sellers")
        if "tech" in industry or "software" in industry:
            pains.append("standing out in a crowded market")

        if not pains:
            pains = ["growing their business", "finding more customers", "automating outreach"]
        return pains

    def _infer_industry_fit(self, lead: dict) -> str:
        industry = (lead.get("industry") or "").lower()
        high_fit = {"technology", "software", "saas", "real estate", "finance", "healthcare", "consulting"}
        medium_fit = {"retail", "ecommerce", "education", "manufacturing", "hospitality"}
        if industry in high_fit:
            return "high"
        if industry in medium_fit:
            return "medium"
        return "low" if industry else "unknown"

    async def score_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""You are an expert lead qualification AI. Analyze this lead and provide a score from 0.0 to 1.0.

Lead Data: {json.dumps(lead_data, indent=2)}

Respond with JSON:
{{
  "score": 0.0-1.0,
  "is_qualified": true/false,
  "reasoning": "why this lead is or isn't qualified",
  "pain_points": ["list of potential pain points"],
  "industry_fit": "high/medium/low",
  "recommended_action": "contact/nurture/discard"
}}"""
        return await self._call_openai(
            "You are a lead qualification expert. Output ONLY valid JSON.",
            prompt,
            temperature=0.3,
        )

    async def generate_message(self, lead_data: Dict[str, Any], channel: str = "email", language: str = "en", tone: str = "professional") -> Dict[str, Any]:
        prompt = f"""Generate a personalized {channel} message for this lead.
Language: {language}
Tone: {tone}

Lead Data: {json.dumps(lead_data, indent=2)}

Respond with JSON:
{{
  "subject": "email subject line (if email)",
  "body": "message body with placeholders filled",
  "call_to_action": "what action to take",
  "variants": ["2-3 alternative subject lines or openings for A/B testing"]
}}"""
        lang_instruction = "Write in English." if language == "en" else f"Write in {language}."
        return await self._call_openai(
            f"You are an expert copywriter who creates high-converting outreach messages. {lang_instruction} Output ONLY valid JSON.",
            prompt,
            temperature=0.8,
        )

    async def generate_follow_up(self, original_message: str, lead_data: Dict[str, Any], step: int = 1, response_received: bool = False) -> Dict[str, Any]:
        prompt = f"""Generate follow-up message #{step}.

Original message: {original_message}
Lead Data: {json.dumps(lead_data, indent=2)}
Response received: {response_received}

Respond with JSON:
{{
  "subject": "follow-up subject",
  "body": "follow-up message body",
  "timing": "suggested send timing in days from now"
}}"""
        return await self._call_openai(
            "You are an expert sales sequence writer. Output ONLY valid JSON.",
            prompt,
            temperature=0.7,
        )

    async def analyze_sentiment(self, message: str) -> Dict[str, Any]:
        prompt = f"""Analyze the sentiment of this message:

Message: {message}

Respond with JSON:
{{
  "sentiment": "positive/negative/neutral",
  "intent": "interested/not_interested/meeting_request/question/complaint",
  "urgency": "high/medium/low",
  "suggested_reply": "how to respond to this message",
  "should_auto_reply": true/false
}}"""
        return await self._call_openai(
            "You are a communication analysis expert. Output ONLY valid JSON.",
            prompt,
            temperature=0.3,
        )

    async def auto_reply(self, incoming_message: str, lead_data: Dict[str, Any], conversation_history: List[Dict] = None) -> Dict[str, Any]:
        history = json.dumps(conversation_history or [])
        prompt = f"""Generate an appropriate auto-reply to this incoming message.

Incoming message: {incoming_message}
Lead Data: {json.dumps(lead_data, indent=2)}
Conversation History: {history}

Respond with JSON:
{{
  "reply": "the auto-reply message",
  "tone": "professional/friendly/formal",
  "next_action": "wait_for_reply/schedule_call/send_info/end_conversation",
  "should_send": true/false
}}"""
        return await self._call_openai(
            "You are an expert sales communication AI. Output ONLY valid JSON.",
            prompt,
            temperature=0.6,
        )

    async def translate_message(self, message: str, target_language: str) -> str:
        prompt = f"""Translate this message to {target_language}. Preserve all formatting, line breaks, and the professional tone.

Message: {message}

Translation:"""
        result = await self._call_openai(
            f"You are a professional translator. Translate to {target_language}. Output ONLY the translation.",
            prompt,
            temperature=0.3,
            max_tokens=2000,
        )
        return result

    async def detect_tech_stack(self, website_url: str) -> List[str]:
        prompt = f"""Based on this website URL, identify the likely tech stack (CMS, frameworks, analytics tools, etc.).
URL: {website_url}

Respond with a JSON array of technology names found.

Example: ["WordPress", "Google Analytics", "Yoast SEO", "WooCommerce", "PHP"]"""
        return await self._call_openai(
            "You are a web technology detection expert. Output ONLY a valid JSON array.",
            prompt,
            temperature=0.3,
        )
