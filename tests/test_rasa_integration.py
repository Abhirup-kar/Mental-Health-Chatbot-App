"""Unit tests for RasaClient webhook handling and local NLU fallback behavior."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import requests

from app.rasa_client import RasaClient


def test_rasa_client_parses_custom_action_payload():
    client = RasaClient("http://127.0.0.1:5005", timeout_seconds=2.0)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = [
        {
            "recipient_id": "user_1_session_1",
            "text": "Anxiety can feel heavy. Try box breathing.",
            "custom": {
                "sentiment": "negative",
                "score": -0.62,
                "confidence": 0.89,
                "emotion": "anxiety",
                "intent": "mood_anxious",
                "intent_confidence": 0.93,
                "is_crisis": False,
                "should_recommend_videos": True,
            },
        }
    ]

    with patch("app.rasa_client.requests.post", return_value=mock_resp):
        result = client.send_message("user_1_session_1", "I feel anxious")

    assert result["engine_used"] == "rasa"
    assert result["sentiment"] == "negative"
    assert result["emotion"] == "anxiety"
    assert result["intent"] == "mood_anxious"
    assert result["should_recommend_videos"] is True
    assert "box breathing" in result["reply_text"].lower()


def test_rasa_client_falls_back_gracefully_when_offline():
    client = RasaClient("http://127.0.0.1:59999", timeout_seconds=1.0)

    with patch("app.rasa_client.requests.post", side_effect=requests.ConnectionError("Connection refused")):
        result = client.send_message("user_1_session_2", "I feel happy and grateful today!")

    assert result["engine_used"] == "local_nlu_fallback"
    assert result["sentiment"] == "positive"
    assert result["should_recommend_videos"] is True
    assert result["reply_text"]
