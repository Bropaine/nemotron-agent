import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "discovery.db"


def initialize_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY,
                url TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.commit()
    finally:
        connection.close()


def save_recommendation(url: str, title: str, reason: str) -> bool:
    connection = sqlite3.connect(DB_PATH)
    try:
        cursor = connection.execute(
            """
            INSERT INTO recommendations (url, title, reason)
            VALUES (?, ?, ?)
            ON CONFLICT(url) DO NOTHING
            """,
            (url, title, reason),
        )
        connection.commit()
        return cursor.rowcount == 1
    finally:
        connection.close()


def get_recommended_urls() -> set[str]:
    connection = sqlite3.connect(DB_PATH)
    try:
        rows = connection.execute(
            "SELECT url FROM recommendations"
        ).fetchall()
        return {row[0] for row in rows}
    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()
    saved = save_recommendation(
        "https://example.com",
        "Example Domain",
        "Local storage test.",
    )
    print("Saved new recommendation:", saved)
    print("Previously recommended:", get_recommended_urls())
