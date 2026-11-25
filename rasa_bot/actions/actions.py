"""Rasa custom actions for real-time sentiment analysis and therapist video guidance."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.sentiment_engine import (  # noqa: E402
    analyze_communication_pattern,
    analyze_message,
    generate_therapist_reply,
)


def _extract_history_from_tracker(tracker: Tracker) -> list[dict[str, Any]]:
    history: list[dict[str, Any]] = []
    for event in tracker.events:
        if event.get("event") == "user":
            text = event.get("text") or ""
            parse_data = event.get("parse_data") or {}
            intent_info = parse_data.get("intent") or {}
            analyzed = analyze_message(
                text,
                intent_name=intent_info.get("name"),
                intent_confidence=float(intent_info.get("confidence", 0.0) or 0.0),
            )
            if analyzed["should_recommend_videos"]:
                history.append(analyzed)
    return history


class ActionTherapistSentimentResponse(Action):
    """Analyze user emotion and communication pattern, then respond like a supportive therapist."""

    def name(self) -> Text:
        return "action_therapist_sentiment_response"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        latest = tracker.latest_message or {}
        user_text = str(latest.get("text") or "")
        intent_info = latest.get("intent") or {}
        intent_name = intent_info.get("name")
        intent_confidence = float(intent_info.get("confidence", 0.0) or 0.0)

        analysis = analyze_message(
            user_text,
            intent_name=intent_name,
            intent_confidence=intent_confidence,
        )
        history = _extract_history_from_tracker(tracker)
        pattern = analyze_communication_pattern(history)
        reply = generate_therapist_reply(
            user_text,
            analysis,
            pattern=pattern,
            intent_name=intent_name,
        )

        dispatcher.utter_message(
            text=reply,
            json_message={
                "sentiment": analysis["sentiment"],
                "score": analysis["score"],
                "confidence": analysis["confidence"],
                "emotion": analysis["emotion"],
                "intent": intent_name,
                "intent_confidence": round(intent_confidence, 4),
                "is_crisis": analysis["is_crisis"],
                "should_recommend_videos": analysis["should_recommend_videos"],
                "pattern": pattern,
            },
        )
        return [
            SlotSet("last_sentiment", analysis["sentiment"]),
            SlotSet("last_emotion", analysis["emotion"]),
        ]


class ActionRecommendVideo(Action):
    """Handle explicit requests for mental health video recommendations."""

    def name(self) -> Text:
        return "action_recommend_video"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        last_sentiment = tracker.get_slot("last_sentiment") or "neutral"
        last_emotion = tracker.get_slot("last_emotion") or "mindfulness"
        score_map = {"positive": 0.45, "neutral": 0.0, "negative": -0.45}

        if last_sentiment == "negative":
            reply = (
                "Here are calming, evidence-based video links selected for how you've been feeling. "
                "Take a slow breath and watch whichever one resonates most right now."
            )
        elif last_sentiment == "positive":
            reply = (
                "Here are uplifting mental-health videos matched to your positive mood to help reinforce gratitude and momentum."
            )
        else:
            reply = (
                "Here are gentle mindfulness and reflection videos curated for a balanced check-in."
            )

        dispatcher.utter_message(
            text=reply,
            json_message={
                "sentiment": last_sentiment,
                "score": score_map.get(last_sentiment, 0.0),
                "confidence": 0.85,
                "emotion": last_emotion,
                "intent": "request_video",
                "intent_confidence": 0.95,
                "is_crisis": False,
                "should_recommend_videos": True,
                "force_videos": True,
            },
        )
        return []
