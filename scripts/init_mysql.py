"""Initialize the MySQL database schema and seed mental health video recommendations."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import Config  # noqa: E402
from app.db import Database  # noqa: E402


def main() -> int:
    cfg = {
        "DB_BACKEND": "mysql",
        "MYSQL_HOST": Config.MYSQL_HOST,
        "MYSQL_PORT": Config.MYSQL_PORT,
        "MYSQL_USER": Config.MYSQL_USER,
        "MYSQL_PASSWORD": Config.MYSQL_PASSWORD,
        "MYSQL_DATABASE": Config.MYSQL_DATABASE,
    }
    try:
        db = Database(cfg)
    except Exception as exc:
        print(f"Error initializing MySQL database: {exc}", file=sys.stderr)
        return 1

    videos = db.list_videos()
    print(
        f"MySQL schema initialized successfully in database '{Config.MYSQL_DATABASE}' "
        f"with {len(videos)} seeded videos."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
