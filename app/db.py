"""Database abstraction layer supporting MySQL (PyMySQL) and SQLite fallback."""

from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import pymysql
from pymysql.cursors import DictCursor

from shared.sentiment_engine import SEED_VIDEOS

logger = logging.getLogger(__name__)


def _decorate_video(row: dict[str, Any]) -> dict[str, Any]:
    video = dict(row)
    yt_id = video["youtube_id"]
    video["thumbnail_url"] = f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg"
    video["embed_url"] = f"https://www.youtube.com/embed/{yt_id}?rel=0"
    return video


class Database:
    """Repository wrapping MySQL (primary) or SQLite (local fallback / test) operations."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        requested = str(config.get("DB_BACKEND", "auto")).strip().lower()
        if requested not in {"auto", "mysql", "sqlite"}:
            raise ValueError(f"Unsupported DB_BACKEND: {requested}")

        self.backend = "sqlite"
        if requested in {"auto", "mysql"}:
            try:
                self._bootstrap_mysql()
                self.backend = "mysql"
            except Exception as exc:
                if requested == "mysql":
                    raise RuntimeError(f"MySQL connection failed: {exc}") from exc
                logger.warning(
                    "MySQL is not reachable (%s). Falling back to local SQLite database at %s.",
                    exc,
                    config.get("SQLITE_PATH"),
                )
                self.backend = "sqlite"

        self.init_schema()
        self.seed_videos()

    def _mysql_connect(self, include_db: bool = True) -> pymysql.connections.Connection:
        kwargs: dict[str, Any] = {
            "host": self.config.get("MYSQL_HOST", "127.0.0.1"),
            "port": int(self.config.get("MYSQL_PORT", 3306)),
            "user": self.config.get("MYSQL_USER", "root"),
            "password": self.config.get("MYSQL_PASSWORD", ""),
            "charset": "utf8mb4",
            "cursorclass": DictCursor,
            "connect_timeout": 2,
            "autocommit": False,
        }
        if include_db:
            kwargs["database"] = self.config.get("MYSQL_DATABASE", "mental_health_chatbot")
        return pymysql.connect(**kwargs)

    def _bootstrap_mysql(self) -> None:
        db_name = str(self.config.get("MYSQL_DATABASE", "mental_health_chatbot"))
        safe_db = "".join(ch for ch in db_name if ch.isalnum() or ch == "_")
        if not safe_db:
            raise ValueError("Invalid MYSQL_DATABASE name")
        conn = self._mysql_connect(include_db=False)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{safe_db}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            conn.commit()
        finally:
            conn.close()

    def _sqlite_connect(self) -> sqlite3.Connection:
        db_path = Path(str(self.config.get("SQLITE_PATH", "instance/mental_health.db")))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path), detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def _connection(self) -> Iterator[Any]:
        conn = self._mysql_connect() if self.backend == "mysql" else self._sqlite_connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _adapt_sql(self, sql: str) -> str:
        if self.backend == "sqlite":
            return sql.replace("%s", "?")
        return sql

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> int:
        adapted = self._adapt_sql(sql)
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(adapted, params)
            last_id = getattr(cur, "lastrowid", 0) or 0
            cur.close()
            return int(last_id)

    def fetch_one(self, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        adapted = self._adapt_sql(sql)
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(adapted, params)
            row = cur.fetchone()
            cur.close()
            return dict(row) if row is not None else None

    def fetch_all(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        adapted = self._adapt_sql(sql)
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(adapted, params)
            rows = cur.fetchall()
            cur.close()
            return [dict(r) for r in rows]

    def init_schema(self) -> None:
        if self.backend == "mysql":
            statements = [
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    full_name VARCHAR(120) NOT NULL,
                    username VARCHAR(60) NOT NULL UNIQUE,
                    email VARCHAR(160) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """,
                """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    title VARCHAR(160) NOT NULL DEFAULT 'New Check-In',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    CONSTRAINT fk_sessions_user FOREIGN KEY (user_id)
                        REFERENCES users(id) ON DELETE CASCADE,
                    INDEX idx_sessions_user_updated (user_id, updated_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """,
                """
                CREATE TABLE IF NOT EXISTS videos (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    channel VARCHAR(120) NOT NULL,
                    youtube_id VARCHAR(32) NOT NULL UNIQUE,
                    url VARCHAR(255) NOT NULL,
                    sentiment ENUM('positive', 'negative', 'neutral') NOT NULL,
                    emotion_tag VARCHAR(60) NOT NULL,
                    duration_label VARCHAR(40) NOT NULL,
                    description TEXT NOT NULL,
                    INDEX idx_videos_sentiment (sentiment, emotion_tag)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """,
                """
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id INT NOT NULL,
                    user_id INT NOT NULL,
                    sender ENUM('user', 'bot') NOT NULL,
                    message_text TEXT NOT NULL,
                    sentiment ENUM('positive', 'negative', 'neutral') DEFAULT NULL,
                    sentiment_score DECIMAL(5, 4) DEFAULT NULL,
                    emotion VARCHAR(60) DEFAULT NULL,
                    detected_intent VARCHAR(80) DEFAULT NULL,
                    engine_used VARCHAR(40) DEFAULT NULL,
                    recommended_video_ids TEXT DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_messages_session FOREIGN KEY (session_id)
                        REFERENCES chat_sessions(id) ON DELETE CASCADE,
                    CONSTRAINT fk_messages_user FOREIGN KEY (user_id)
                        REFERENCES users(id) ON DELETE CASCADE,
                    INDEX idx_messages_session_created (session_id, created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """,
                """
                CREATE TABLE IF NOT EXISTS sentiment_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    session_id INT NOT NULL,
                    message_id INT NOT NULL,
                    sentiment ENUM('positive', 'negative', 'neutral') NOT NULL,
                    score DECIMAL(5, 4) NOT NULL,
                    emotion VARCHAR(60) NOT NULL,
                    pattern_trend VARCHAR(40) NOT NULL DEFAULT 'stable',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_logs_user FOREIGN KEY (user_id)
                        REFERENCES users(id) ON DELETE CASCADE,
                    CONSTRAINT fk_logs_session FOREIGN KEY (session_id)
                        REFERENCES chat_sessions(id) ON DELETE CASCADE,
                    CONSTRAINT fk_logs_message FOREIGN KEY (message_id)
                        REFERENCES chat_messages(id) ON DELETE CASCADE,
                    INDEX idx_logs_user_created (user_id, created_at),
                    INDEX idx_logs_session_created (session_id, created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """,
            ]
        else:
            statements = [
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    username TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL DEFAULT 'New Check-In',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    youtube_id TEXT NOT NULL UNIQUE,
                    url TEXT NOT NULL,
                    sentiment TEXT NOT NULL CHECK (sentiment IN ('positive', 'negative', 'neutral')),
                    emotion_tag TEXT NOT NULL,
                    duration_label TEXT NOT NULL,
                    description TEXT NOT NULL
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    sender TEXT NOT NULL CHECK (sender IN ('user', 'bot')),
                    message_text TEXT NOT NULL,
                    sentiment TEXT DEFAULT NULL CHECK (sentiment IS NULL OR sentiment IN ('positive', 'negative', 'neutral')),
                    sentiment_score REAL DEFAULT NULL,
                    emotion TEXT DEFAULT NULL,
                    detected_intent TEXT DEFAULT NULL,
                    engine_used TEXT DEFAULT NULL,
                    recommended_video_ids TEXT DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS sentiment_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    sentiment TEXT NOT NULL CHECK (sentiment IN ('positive', 'negative', 'neutral')),
                    score REAL NOT NULL,
                    emotion TEXT NOT NULL,
                    pattern_trend TEXT NOT NULL DEFAULT 'stable',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
                    FOREIGN KEY (message_id) REFERENCES chat_messages(id) ON DELETE CASCADE
                )
                """,
            ]

        with self._connection() as conn:
            cur = conn.cursor()
            for stmt in statements:
                cur.execute(stmt)
            cur.close()

    def seed_videos(self) -> None:
        insert_prefix = "INSERT IGNORE INTO" if self.backend == "mysql" else "INSERT OR IGNORE INTO"
        sql = (
            f"{insert_prefix} videos "
            "(title, channel, youtube_id, url, sentiment, emotion_tag, duration_label, description) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        )
        adapted = self._adapt_sql(sql)
        with self._connection() as conn:
            cur = conn.cursor()
            for item in SEED_VIDEOS:
                cur.execute(
                    adapted,
                    (
                        item["title"],
                        item["channel"],
                        item["youtube_id"],
                        item["url"],
                        item["sentiment"],
                        item["emotion_tag"],
                        item["duration_label"],
                        item["description"],
                    ),
                )
            cur.close()

    # ---- User operations ----

    def create_user(self, full_name: str, username: str, email: str, password_hash: str) -> int:
        return self.execute(
            "INSERT INTO users (full_name, username, email, password_hash) VALUES (%s, %s, %s, %s)",
            (full_name, username, email, password_hash),
        )

    def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        return self.fetch_one(
            "SELECT id, full_name, username, email, password_hash, created_at FROM users WHERE username = %s",
            (username,),
        )

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        return self.fetch_one(
            "SELECT id, full_name, username, email, password_hash, created_at FROM users WHERE email = %s",
            (email,),
        )

    def get_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        return self.fetch_one(
            "SELECT id, full_name, username, email, created_at FROM users WHERE id = %s",
            (user_id,),
        )

    # ---- Session operations ----

    def create_session(self, user_id: int, title: str = "New Check-In") -> dict[str, Any]:
        session_id = self.execute(
            "INSERT INTO chat_sessions (user_id, title) VALUES (%s, %s)",
            (user_id, title[:160]),
        )
        row = self.get_session(session_id, user_id)
        assert row is not None
        return row

    def get_user_sessions(self, user_id: int) -> list[dict[str, Any]]:
        return self.fetch_all(
            "SELECT id, user_id, title, created_at, updated_at "
            "FROM chat_sessions WHERE user_id = %s ORDER BY updated_at DESC, id DESC",
            (user_id,),
        )

    def get_session(self, session_id: int, user_id: int) -> dict[str, Any] | None:
        return self.fetch_one(
            "SELECT id, user_id, title, created_at, updated_at "
            "FROM chat_sessions WHERE id = %s AND user_id = %s",
            (session_id, user_id),
        )

    def update_session_title(self, session_id: int, title: str) -> None:
        self.execute(
            "UPDATE chat_sessions SET title = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (title[:160], session_id),
        )

    def touch_session(self, session_id: int) -> None:
        self.execute(
            "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (session_id,),
        )

    def delete_session(self, session_id: int, user_id: int) -> bool:
        existing = self.get_session(session_id, user_id)
        if existing is None:
            return False
        self.execute(
            "DELETE FROM chat_sessions WHERE id = %s AND user_id = %s",
            (session_id, user_id),
        )
        return True

    # ---- Message & Sentiment Log operations ----

    def add_message(
        self,
        session_id: int,
        user_id: int,
        sender: str,
        message_text: str,
        sentiment: str | None = None,
        sentiment_score: float | None = None,
        emotion: str | None = None,
        detected_intent: str | None = None,
        engine_used: str | None = None,
        recommended_video_ids: list[int] | None = None,
    ) -> int:
        video_json = json.dumps(recommended_video_ids) if recommended_video_ids else None
        msg_id = self.execute(
            "INSERT INTO chat_messages "
            "(session_id, user_id, sender, message_text, sentiment, sentiment_score, "
            "emotion, detected_intent, engine_used, recommended_video_ids) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                session_id,
                user_id,
                sender,
                message_text,
                sentiment,
                sentiment_score,
                emotion,
                detected_intent,
                engine_used,
                video_json,
            ),
        )
        self.touch_session(session_id)
        return msg_id

    def get_session_messages(self, session_id: int, user_id: int) -> list[dict[str, Any]]:
        rows = self.fetch_all(
            "SELECT id, session_id, user_id, sender, message_text, sentiment, "
            "sentiment_score, emotion, detected_intent, engine_used, "
            "recommended_video_ids, created_at "
            "FROM chat_messages WHERE session_id = %s AND user_id = %s "
            "ORDER BY id ASC",
            (session_id, user_id),
        )
        all_vid_ids: list[int] = []
        parsed_ids: dict[int, list[int]] = {}
        for row in rows:
            raw_ids = row.get("recommended_video_ids")
            vid_ids: list[int] = []
            if raw_ids:
                try:
                    vid_ids = [int(v) for v in json.loads(raw_ids)]
                except (ValueError, TypeError):
                    vid_ids = []
            parsed_ids[row["id"]] = vid_ids
            all_vid_ids.extend(vid_ids)

        videos_by_id = {v["id"]: v for v in self.get_videos_by_ids(list(set(all_vid_ids)))}
        for row in rows:
            if row.get("sentiment_score") is not None:
                row["sentiment_score"] = float(row["sentiment_score"])
            row["videos"] = [
                videos_by_id[vid] for vid in parsed_ids.get(row["id"], []) if vid in videos_by_id
            ]
            row["created_at"] = str(row["created_at"]) if row.get("created_at") else None
        return rows

    def get_session_recent_video_ids(self, session_id: int, user_id: int) -> list[int]:
        rows = self.fetch_all(
            "SELECT recommended_video_ids FROM chat_messages "
            "WHERE session_id = %s AND user_id = %s AND sender = 'bot' AND recommended_video_ids IS NOT NULL "
            "ORDER BY id DESC LIMIT 6",
            (session_id, user_id),
        )
        seen: list[int] = []
        for row in rows:
            try:
                for vid in json.loads(row["recommended_video_ids"]):
                    if int(vid) not in seen:
                        seen.append(int(vid))
            except (ValueError, TypeError):
                continue
        return seen

    def add_sentiment_log(
        self,
        user_id: int,
        session_id: int,
        message_id: int,
        sentiment: str,
        score: float,
        emotion: str,
        pattern_trend: str = "stable",
    ) -> int:
        return self.execute(
            "INSERT INTO sentiment_logs "
            "(user_id, session_id, message_id, sentiment, score, emotion, pattern_trend) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (user_id, session_id, message_id, sentiment, score, emotion, pattern_trend),
        )

    def get_user_sentiment_logs(
        self,
        user_id: int,
        session_id: int | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        if session_id is not None:
            rows = self.fetch_all(
                "SELECT id, user_id, session_id, message_id, sentiment, score, emotion, pattern_trend, created_at "
                "FROM sentiment_logs WHERE user_id = %s AND session_id = %s "
                "ORDER BY id ASC LIMIT %s",
                (user_id, session_id, int(limit)),
            )
        else:
            rows = self.fetch_all(
                "SELECT id, user_id, session_id, message_id, sentiment, score, emotion, pattern_trend, created_at "
                "FROM sentiment_logs WHERE user_id = %s "
                "ORDER BY id ASC LIMIT %s",
                (user_id, int(limit)),
            )
        for row in rows:
            row["score"] = float(row["score"])
            row["created_at"] = str(row["created_at"]) if row.get("created_at") else None
        return rows

    # ---- Video operations ----

    def list_videos(self, sentiment: str | None = None) -> list[dict[str, Any]]:
        if sentiment in {"positive", "negative", "neutral"}:
            rows = self.fetch_all(
                "SELECT id, title, channel, youtube_id, url, sentiment, emotion_tag, duration_label, description "
                "FROM videos WHERE sentiment = %s ORDER BY id ASC",
                (sentiment,),
            )
        else:
            rows = self.fetch_all(
                "SELECT id, title, channel, youtube_id, url, sentiment, emotion_tag, duration_label, description "
                "FROM videos ORDER BY id ASC"
            )
        return [_decorate_video(r) for r in rows]

    def get_videos_by_ids(self, ids: list[int]) -> list[dict[str, Any]]:
        if not ids:
            return []
        placeholders = ", ".join(["%s"] * len(ids))
        rows = self.fetch_all(
            "SELECT id, title, channel, youtube_id, url, sentiment, emotion_tag, duration_label, description "
            f"FROM videos WHERE id IN ({placeholders})",
            tuple(int(i) for i in ids),
        )
        return [_decorate_video(r) for r in rows]

    def get_recommended_videos(
        self,
        sentiment: str,
        emotion: str | None = None,
        exclude_ids: list[int] | None = None,
        limit: int = 2,
    ) -> list[dict[str, Any]]:
        target_sentiment = sentiment if sentiment in {"positive", "negative", "neutral"} else "neutral"
        candidates = self.list_videos(sentiment=target_sentiment)
        if not candidates:
            candidates = self.list_videos()

        excluded = set(exclude_ids or [])
        fresh = [v for v in candidates if v["id"] not in excluded]
        pool = fresh if len(fresh) >= limit else candidates

        # Prioritize matching emotion_tag while keeping fresh non-repeated videos first.
        def sort_key(video: dict[str, Any]) -> tuple[int, int, int]:
            is_fresh = 0 if video["id"] not in excluded else 1
            emotion_match = 0 if (emotion and video["emotion_tag"] == emotion) else 1
            return (is_fresh, emotion_match, video["id"])

        ordered = sorted(pool, key=sort_key)
        return ordered[:limit]
