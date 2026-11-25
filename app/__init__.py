"""Flask application factory for the Mental Health Chatbot System."""

from __future__ import annotations

from typing import Any

from flask import Flask

from app.auth import auth_bp
from app.chat import chat_bp
from app.config import Config
from app.db import Database
from app.rasa_client import RasaClient


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    """Create and configure the Flask application instance."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    db = Database(app.config)
    rasa_client = RasaClient(
        rasa_url=str(app.config.get("RASA_URL", "http://127.0.0.1:5005")),
        timeout_seconds=float(app.config.get("RASA_TIMEOUT_SECONDS", 8)),
    )

    app.extensions["db"] = db
    app.extensions["rasa_client"] = rasa_client

    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)

    @app.after_request
    def add_security_headers(response: Any) -> Any:
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        return response

    return app
