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
        connection.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                recommendation_id INTEGER PRIMARY KEY,
                value INTEGER NOT NULL CHECK (value IN (-1, 1)),
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (recommendation_id) REFERENCES recommendations(id)
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


def save_rating(url: str, value: int) -> bool:
    if type(value) is not int or value not in (-1, 1):
        raise ValueError("Rating must be +1 or -1.")

    connection = sqlite3.connect(DB_PATH)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        row = connection.execute(
            "SELECT id FROM recommendations WHERE url = ?",
            (url,),
        ).fetchone()
        if row is None:
            return False

        connection.execute(
            """
            INSERT INTO ratings (recommendation_id, value)
            VALUES (?, ?)
            ON CONFLICT(recommendation_id) DO UPDATE SET
                value = excluded.value,
                updated_at = CURRENT_TIMESTAMP
            """,
            (row[0], value),
        )
        connection.commit()
        return True
    finally:
        connection.close()


def get_rating(url: str) -> int | None:
    connection = sqlite3.connect(DB_PATH)
    try:
        row = connection.execute(
            """
            SELECT ratings.value
            FROM ratings
            JOIN recommendations
                ON recommendations.id = ratings.recommendation_id
            WHERE recommendations.url = ?
            """,
            (url,),
        ).fetchone()
        return None if row is None else row[0]
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
