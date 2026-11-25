"""Configuration settings for the Mental Health Chatbot Flask application."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Application configuration loaded from environment variables."""

    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-mental-health-chatbot-secret-key")
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))

    DB_BACKEND = os.getenv("DB_BACKEND", "auto").strip().lower()
    MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "mental_health_chatbot")

    _raw_sqlite = os.getenv("SQLITE_PATH", "instance/mental_health.db")
    SQLITE_PATH = str(
        Path(_raw_sqlite)
        if Path(_raw_sqlite).is_absolute()
        else (BASE_DIR / _raw_sqlite)
    )

    RASA_URL = os.getenv("RASA_URL", "http://127.0.0.1:5005").rstrip("/")
    RASA_ACTION_URL = os.getenv("RASA_ACTION_URL", "http://127.0.0.1:5055").rstrip("/")
    RASA_TIMEOUT_SECONDS = float(os.getenv("RASA_TIMEOUT_SECONDS", "8"))

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
