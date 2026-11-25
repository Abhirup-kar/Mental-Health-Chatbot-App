"""Rasa REST & NLU client with transparent local NLU fallback."""

from __future__ import annotations

import logging
from typing import Any

import requests

from app.fallback_nlu import LocalNLUFallback
from shared.sentiment_engine import (
    analyze_communication_pattern,
    analyze_message,
    generate_therapist_reply,
)

logger = logging.getLogger(__name__)


class RasaClient:
    """Client for communicating with Rasa REST webhook and NLU parse endpoints."""

    def __init__(self, rasa_url: str, timeout_seconds: float = 8.0) -> None:
        self.rasa_url = rasa_url.rstrip("/")
        self.timeout = timeout_seconds
        self.fallback_nlu = LocalNLUFallback()

    def check_health(self) -> bool:
        """Return True when the Rasa server responds on /status."""
        try:
            resp = requests.get(f"{self.rasa_url}/status", timeout=1.5)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def _parse_intent_via_rasa(self, message: str) -> tuple[str | None, float]:
        try:
            resp = requests.post(
                f"{self.rasa_url}/model/parse",
                json={"text": message},
                timeout=self.timeout,
            )
            if resp.status_code == 200:
                payload = resp.json() or {}
                intent = payload.get("intent") or {}
                return intent.get("name"), float(intent.get("confidence", 0.0) or 0.0)
        except requests.RequestException:
            pass
        return None, 0.0

    def send_message(
        self,
        sender_id: str,
        message: str,
        recent_history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Send a message to Rasa REST webhook, falling back to local NLU if Rasa is offline."""
        try:
            resp = requests.post(
                f"{self.rasa_url}/webhooks/rest/webhook",
                json={"sender": sender_id, "message": message},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            events = resp.json()
            if isinstance(events, list) and events:
                return self._process_rasa_events(events, message, recent_history)
            if isinstance(events, list) and not events:
                # Rasa returned no bot message (e.g. action_listen); enrich via /model/parse + therapist reply
                intent_name, intent_conf = self._parse_intent_via_rasa(message)
                return self._build_local_result(
                    message=message,
                    intent_name=intent_name,
                    intent_confidence=intent_conf,
                    recent_history=recent_history,
                    engine_used="rasa",
                )
        except requests.RequestException as exc:
            logger.info("Rasa unavailable (%s); using local NLU fallback.", exc)

        parsed = self.fallback_nlu.parse(message)
        return self._build_local_result(
            message=message,
            intent_name=parsed["name"],
            intent_confidence=float(parsed["confidence"]),
            recent_history=recent_history,
            engine_used="local_nlu_fallback",
        )

    def _process_rasa_events(
        self,
        events: list[dict[str, Any]],
        user_message: str,
        recent_history: list[dict[str, Any]] | None,
    ) -> dict[str, Any]:
        texts: list[str] = []
        custom_payload: dict[str, Any] = {}
        for event in events:
            if isinstance(event, dict):
                if event.get("text"):
                    texts.append(str(event["text"]))
                if isinstance(event.get("custom"), dict):
                    custom_payload.update(event["custom"])

        reply_text = "\n\n".join(texts).strip()
        if custom_payload and "sentiment" in custom_payload:
            return {
                "reply_text": reply_text
                or generate_therapist_reply(
                    user_message,
                    custom_payload,
                    pattern=analyze_communication_pattern(recent_history or []),
                    intent_name=custom_payload.get("intent"),
                ),
                "sentiment": custom_payload["sentiment"],
                "score": float(custom_payload.get("score", 0.0)),
                "confidence": float(custom_payload.get("confidence", 0.75)),
                "emotion": str(custom_payload.get("emotion", "neutral")),
                "intent": custom_payload.get("intent") or "nlu_fallback",
                "intent_confidence": float(custom_payload.get("intent_confidence", 0.0)),
                "is_crisis": bool(custom_payload.get("is_crisis", False)),
                "should_recommend_videos": bool(
                    custom_payload.get("should_recommend_videos", True)
                ),
                "engine_used": "rasa",
            }

        # Static Rasa response (e.g. utter_greet / utter_goodbye) without custom JSON
        intent_name, intent_conf = self._parse_intent_via_rasa(user_message)
        analysis = analyze_message(
            user_message,
            intent_name=intent_name,
            intent_confidence=intent_conf,
        )
        return {
            "reply_text": reply_text
            or generate_therapist_reply(
                user_message,
                analysis,
                pattern=analyze_communication_pattern(recent_history or []),
                intent_name=intent_name,
            ),
            "sentiment": analysis["sentiment"],
            "score": analysis["score"],
            "confidence": analysis["confidence"],
            "emotion": analysis["emotion"],
            "intent": intent_name or "unknown",
            "intent_confidence": round(intent_conf, 4),
            "is_crisis": analysis["is_crisis"],
            "should_recommend_videos": analysis["should_recommend_videos"],
            "engine_used": "rasa",
        }

    def _build_local_result(
        self,
        message: str,
        intent_name: str | None,
        intent_confidence: float,
        recent_history: list[dict[str, Any]] | None,
        engine_used: str,
    ) -> dict[str, Any]:
        analysis = analyze_message(
            message,
            intent_name=intent_name,
            intent_confidence=intent_confidence,
        )
        combined_history = list(recent_history or [])
        if analysis["should_recommend_videos"]:
            combined_history.append(analysis)
        pattern = analyze_communication_pattern(combined_history)
        reply_text = generate_therapist_reply(
            message,
            analysis,
            pattern=pattern,
            intent_name=intent_name,
        )
        return {
            "reply_text": reply_text,
            "sentiment": analysis["sentiment"],
            "score": analysis["score"],
            "confidence": analysis["confidence"],
            "emotion": analysis["emotion"],
            "intent": intent_name or "nlu_fallback",
            "intent_confidence": round(intent_confidence, 4),
            "is_crisis": analysis["is_crisis"],
            "should_recommend_videos": analysis["should_recommend_videos"],
            "engine_used": engine_used,
        }
