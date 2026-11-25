"""Entry point for running the Mental Health Chatbot Flask server."""

from __future__ import annotations

import os

from app import create_app

application = create_app()

if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", application.config.get("FLASK_PORT", 5000)))
    application.run(host="0.0.0.0", port=port, debug=False)
