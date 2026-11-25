"""Unit tests for sentiment analysis, crisis detection, and communication pattern tracking."""

from __future__ import annotations

from shared.sentiment_engine import (
    analyze_communication_pattern,
    analyze_message,
    detect_crisis,
    generate_therapist_reply,
)


def test_positive_sentiment_detection():
    res = analyze_message(
        "I am feeling really happy, grateful, and hopeful today!",
        intent_name="mood_great",
        intent_confidence=0.9,
    )
    assert res["sentiment"] == "positive"
    assert res["score"] >= 0.15
    assert res["is_crisis"] is False
    assert res["should_recommend_videos"] is True


def test_negative_sentiments_across_emotions():
    cases = [
        ("I feel so anxious and worried about everything.", "mood_anxious", "anxiety"),
        ("Work has me completely stressed out and overwhelmed.", "mood_stressed", "stress"),
        ("I feel deeply sad, lonely, and hopeless today.", "mood_sad", "sadness"),
        ("I am furious and frustrated with how things went.", "mood_angry", "anger"),
        ("Insomnia is keeping me sleepless all night.", "sleep_issues", "sleep"),
    ]
    for text, intent, expected_emotion in cases:
        res = analyze_message(text, intent_name=intent, intent_confidence=0.85)
        assert res["sentiment"] == "negative", f"Failed negative check for: {text}"
        assert res["score"] <= -0.15
        assert res["emotion"] == expected_emotion
        assert res["should_recommend_videos"] is True


def test_neutral_checkin_recommends_videos():
    res = analyze_message(
        "Today was okay, just a normal routine day.",
        intent_name="mood_neutral",
        intent_confidence=0.8,
    )
    assert res["sentiment"] == "neutral"
    assert -0.15 < res["score"] < 0.15
    assert res["should_recommend_videos"] is True


def test_pure_greeting_is_neutral_without_videos():
    for greeting in ["hi", "hello", "good morning", "bye", "thanks"]:
        res = analyze_message(greeting, intent_name="greet", intent_confidence=0.95)
        assert res["sentiment"] == "neutral"
        assert res["score"] == 0.0
        assert res["should_recommend_videos"] is False


def test_negation_is_handled_accurately():
    res = analyze_message("I am not happy at all today.", intent_name="mood_sad", intent_confidence=0.75)
    assert res["sentiment"] == "negative"
    assert res["score"] <= -0.15


def test_crisis_detection_and_supportive_reply():
    msg = "I feel hopeless and want to kill myself tonight"
    assert detect_crisis(msg) is True
    res = analyze_message(msg, intent_name="crisis_self_harm", intent_confidence=0.95)
    assert res["is_crisis"] is True
    assert res["sentiment"] == "negative"
    assert res["emotion"] == "crisis"

    reply = generate_therapist_reply(msg, res)
    assert "988" in reply
    assert "741741" in reply
    assert "findahelpline.com" in reply


def test_communication_pattern_trends_and_streaks():
    improving = analyze_communication_pattern([
        {"sentiment": "negative", "score": -0.6, "emotion": "sadness"},
        {"sentiment": "negative", "score": -0.4, "emotion": "stress"},
        {"sentiment": "neutral", "score": 0.0, "emotion": "mindfulness"},
        {"sentiment": "positive", "score": 0.65, "emotion": "gratitude"},
    ])
    assert improving["trend"] == "improving"
    assert improving["total_messages"] == 4
    assert improving["consecutive_negative"] == 0

    declining = analyze_communication_pattern([
        {"sentiment": "positive", "score": 0.6, "emotion": "happiness"},
        {"sentiment": "negative", "score": -0.35, "emotion": "stress"},
        {"sentiment": "negative", "score": -0.55, "emotion": "anxiety"},
        {"sentiment": "negative", "score": -0.7, "emotion": "sadness"},
    ])
    assert declining["trend"] == "declining"
    assert declining["consecutive_negative"] == 3
    assert declining["dominant_sentiment"] == "negative"

    stable = analyze_communication_pattern([
        {"sentiment": "neutral", "score": 0.0, "emotion": "mindfulness"},
        {"sentiment": "neutral", "score": 0.05, "emotion": "calm"},
    ])
    assert stable["trend"] == "stable"
