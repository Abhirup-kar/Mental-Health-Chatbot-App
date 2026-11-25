"""End-to-end Flask route tests for registration, login, chat, analytics, and logout."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from app import create_app


@pytest.fixture()
def client(tmp_path: Path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DB_BACKEND": "sqlite",
            "SQLITE_PATH": str(tmp_path / "app_test.db"),
            "RASA_URL": "http://127.0.0.1:59999",
        }
    )
    with app.test_client() as test_client:
        yield test_client


def _register_and_login(client, username: str = "rahul_k", email: str = "rahul@example.com"):
    reg_resp = client.post(
        "/register",
        data={
            "full_name": "Rahul Kapoor",
            "username": username,
            "email": email,
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )
    assert reg_resp.status_code == 200
    assert b"Registration successful" in reg_resp.data

    login_resp = client.post(
        "/login",
        data={"username": username, "password": "password123"},
        follow_redirects=True,
    )
    assert login_resp.status_code == 200
    assert b"Rahul Kapoor" in login_resp.data


def test_landing_and_unauthenticated_protection(client):
    home = client.get("/")
    assert home.status_code == 200
    assert b"SereneMind" in home.data

    chat_redirect = client.get("/chat", follow_redirects=False)
    assert chat_redirect.status_code == 302
    assert "/login" in chat_redirect.headers["Location"]

    api_unauth = client.post("/api/chat", json={"message": "hello"})
    assert api_unauth.status_code == 401


def test_registration_validation_and_login_failures(client):
    bad_pw = client.post(
        "/register",
        data={
            "full_name": "Test User",
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "confirm_password": "different123",
        },
    )
    assert bad_pw.status_code == 400
    assert b"Passwords do not match" in bad_pw.data

    _register_and_login(client, username="unique_u", email="unique@example.com")
    client.get("/logout")

    dup = client.post(
        "/register",
        data={
            "full_name": "Another User",
            "username": "unique_u",
            "email": "other@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    )
    assert dup.status_code == 400
    assert b"already taken" in dup.data

    bad_login = client.post(
        "/login",
        data={"username": "unique_u", "password": "wrongpassword"},
    )
    assert bad_login.status_code == 401
    assert b"Invalid username or password" in bad_login.data


def test_full_chat_sentiment_video_persistence_and_analytics(client):
    _register_and_login(client)

    health = client.get("/api/health").get_json()
    assert health["status"] == "ok"
    assert health["database_backend"] == "sqlite"

    # Negative turn
    neg_resp = client.post(
        "/api/chat",
        json={"message": "I feel really anxious and stressed about exams."},
    )
    assert neg_resp.status_code == 200
    neg_data = neg_resp.get_json()
    session_id = neg_data["session_id"]
    assert neg_data["analysis"]["sentiment"] == "negative"
    assert len(neg_data["videos"]) >= 1
    assert all(v["sentiment"] == "negative" for v in neg_data["videos"])
    assert all(v["url"].startswith("https://www.youtube.com/watch?v=") for v in neg_data["videos"])

    # Neutral turn
    neu_resp = client.post(
        "/api/chat",
        json={"session_id": session_id, "message": "Today was okay, just a normal routine day."},
    )
    assert neu_resp.status_code == 200
    neu_data = neu_resp.get_json()
    assert neu_data["analysis"]["sentiment"] == "neutral"
    assert len(neu_data["videos"]) >= 1
    assert all(v["sentiment"] == "neutral" for v in neu_data["videos"])

    # Positive turn
    pos_resp = client.post(
        "/api/chat",
        json={"session_id": session_id, "message": "I feel really happy, grateful, and energized now!"},
    )
    assert pos_resp.status_code == 200
    pos_data = pos_resp.get_json()
    assert pos_data["analysis"]["sentiment"] == "positive"
    assert len(pos_data["videos"]) >= 1
    assert all(v["sentiment"] == "positive" for v in pos_data["videos"])

    # Verify history persistence
    hist = client.get(f"/api/sessions/{session_id}/messages").get_json()
    assert len(hist["messages"]) == 6
    assert hist["analytics"]["summary"]["total_messages"] == 3
    assert hist["analytics"]["summary"]["negative_count"] == 1
    assert hist["analytics"]["summary"]["neutral_count"] == 1
    assert hist["analytics"]["summary"]["positive_count"] == 1

    # Verify video library filter & analytics endpoint
    videos_pos = client.get("/api/videos?sentiment=positive").get_json()
    assert len(videos_pos["videos"]) == 3
    assert all(v["sentiment"] == "positive" for v in videos_pos["videos"])

    analytics = client.get(f"/api/analytics?session_id={session_id}").get_json()
    assert analytics["summary"]["trend"] == "improving"

    # Create and delete session
    new_sess = client.post("/api/sessions", json={"title": "Evening Reflection"}).get_json()
    del_resp = client.delete(f"/api/sessions/{new_sess['session']['id']}")
    assert del_resp.status_code == 200

    # Logout blocks subsequent API calls
    client.get("/logout")
    assert client.get("/api/sessions").status_code == 401


def test_chat_with_mocked_live_rasa_response(client):
    _register_and_login(client, username="maya_s", email="maya@example.com")

    fake_rasa_result = {
        "reply_text": "I hear how overwhelming today has felt. Let's take one steady breath together.",
        "sentiment": "negative",
        "score": -0.72,
        "confidence": 0.91,
        "emotion": "stress",
        "intent": "mood_stressed",
        "intent_confidence": 0.94,
        "is_crisis": False,
        "should_recommend_videos": True,
        "engine_used": "rasa",
    }

    with patch.object(client.application.extensions["rasa_client"], "send_message", return_value=fake_rasa_result):
        resp = client.post("/api/chat", json={"message": "I am overwhelmed by everything"})
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["engine_used"] == "rasa"
        assert body["analysis"]["sentiment"] == "negative"
        assert body["bot_message"]["message_text"] == fake_rasa_result["reply_text"]
        assert all(v["sentiment"] == "negative" for v in body["videos"])
