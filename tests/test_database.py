"""Tests for Database repository covering SQLite CRUD and mocked MySQL PyMySQL calls."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from app.db import Database


def test_sqlite_full_crud_and_video_recommendations(tmp_path: Path):
    db_file = tmp_path / "test_mental_health.db"
    db = Database({"DB_BACKEND": "sqlite", "SQLITE_PATH": str(db_file)})

    assert db.backend == "sqlite"
    all_videos = db.list_videos()
    assert len(all_videos) == 15

    uid = db.create_user("Asha Verma", "asha_v", "asha@example.com", "hashed_pw")
    user = db.get_user_by_username("asha_v")
    assert user is not None
    assert user["id"] == uid
    assert user["email"] == "asha@example.com"

    session = db.create_session(uid, "Morning Check-In")
    sid = session["id"]
    assert len(db.get_user_sessions(uid)) == 1

    recs_first = db.get_recommended_videos("negative", emotion="anxiety", limit=2)
    assert len(recs_first) == 2
    assert all(v["sentiment"] == "negative" for v in recs_first)
    assert any(v["emotion_tag"] == "anxiety" for v in recs_first)

    msg_id = db.add_message(
        session_id=sid,
        user_id=uid,
        sender="user",
        message_text="I feel anxious",
        sentiment="negative",
        sentiment_score=-0.6,
        emotion="anxiety",
        detected_intent="mood_anxious",
        engine_used="rasa",
    )
    db.add_sentiment_log(uid, sid, msg_id, "negative", -0.6, "anxiety", "initial")

    bot_vids = [v["id"] for v in recs_first]
    db.add_message(
        session_id=sid,
        user_id=uid,
        sender="bot",
        message_text="Take a deep breath.",
        sentiment="negative",
        sentiment_score=-0.6,
        emotion="anxiety",
        detected_intent="mood_anxious",
        engine_used="rasa",
        recommended_video_ids=bot_vids,
    )

    recent_ids = db.get_session_recent_video_ids(sid, uid)
    assert set(recent_ids) == set(bot_vids)

    recs_next = db.get_recommended_videos("negative", emotion="anxiety", exclude_ids=recent_ids, limit=2)
    assert len(recs_next) == 2
    assert all(v["id"] not in recent_ids for v in recs_next)

    messages = db.get_session_messages(sid, uid)
    assert len(messages) == 2
    assert len(messages[1]["videos"]) == 2

    logs = db.get_user_sentiment_logs(uid, session_id=sid)
    assert len(logs) == 1
    assert logs[0]["emotion"] == "anxiety"

    assert db.delete_session(sid, uid) is True
    assert db.get_session(sid, uid) is None


def test_mysql_mode_uses_pymysql_dict_cursor():
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        {
            "id": 1,
            "title": "How to cope with anxiety",
            "channel": "TEDx Talks",
            "youtube_id": "WWloIAQpMcQ",
            "url": "https://www.youtube.com/watch?v=WWloIAQpMcQ",
            "sentiment": "negative",
            "emotion_tag": "anxiety",
            "duration_label": "15 min",
            "description": "Test desc",
        }
    ]

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)

    with patch("app.db.pymysql.connect", return_value=mock_conn) as mock_connect:
        db = Database(
            {
                "DB_BACKEND": "mysql",
                "MYSQL_HOST": "127.0.0.1",
                "MYSQL_PORT": 3306,
                "MYSQL_USER": "root",
                "MYSQL_PASSWORD": "",
                "MYSQL_DATABASE": "mental_health_chatbot",
            }
        )
        assert db.backend == "mysql"
        vids = db.list_videos(sentiment="negative")
        assert len(vids) == 1
        assert vids[0]["youtube_id"] == "WWloIAQpMcQ"
        assert mock_connect.called
        executed_sql = [call.args[0] for call in mock_cursor.execute.call_args_list]
        assert any("SELECT id, title, channel" in sql and "%s" in sql for sql in executed_sql)
