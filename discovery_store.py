import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "discovery.db"


def migrate_rating_feedback(connection: sqlite3.Connection) -> None:
    columns = {
        row[1]
        for row in connection.execute("PRAGMA table_info(ratings)")
    }
    if "feedback_reason" not in columns:
        connection.execute(
            "ALTER TABLE ratings ADD COLUMN feedback_reason TEXT NOT NULL DEFAULT ''"
        )
    if "feedback_note" not in columns:
        connection.execute(
            "ALTER TABLE ratings ADD COLUMN feedback_note TEXT NOT NULL DEFAULT ''"
        )


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
        migrate_rating_feedback(connection)
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


FEEDBACK_REASONS = {
    "", "too_promotional", "wrong_topic", "too_basic", "too_advanced",
    "untrustworthy", "outdated", "already_familiar", "other",
}


def validate_feedback(reason: str, note: str) -> tuple[str, str]:
    if not isinstance(reason, str) or reason not in FEEDBACK_REASONS:
        raise ValueError("Unknown feedback reason.")
    if not isinstance(note, str):
        raise ValueError("Feedback note must be text.")
    note = note.strip()
    if len(note) > 500:
        raise ValueError("Feedback note must be 500 characters or fewer.")
    return reason, note


def save_rating(
        url: str,
        value: int,
        feedback_reason: str = "",
        feedback_note: str = "",
) -> bool:
    if type(value) is not int or value not in (-1, 1):
        raise ValueError("Rating must be +1 or -1.")
    feedback_reason, feedback_note = validate_feedback(
        feedback_reason, feedback_note
    )

    connection = sqlite3.connect(DB_PATH)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        row = connection.execute(
            "SELECT id FROM recommendations WHERE url = ?", (url,)
        ).fetchone()
        if row is None:
            return False

        connection.execute(
            """
            INSERT INTO ratings (
                recommendation_id, value, feedback_reason, feedback_note
            ) VALUES (?, ?, ?, ?)
            ON CONFLICT(recommendation_id) DO UPDATE SET
                value = excluded.value,
                feedback_reason = excluded.feedback_reason,
                feedback_note = excluded.feedback_note,
                updated_at = CURRENT_TIMESTAMP
            """,
            (row[0], value, feedback_reason, feedback_note),
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


def get_recent_feedback(limit: int = 6) -> list[dict]:
    if type(limit) is not int or not 1 <= limit <= 20:
        raise ValueError("Limit must be an integer between 1 and 20.")

    connection = sqlite3.connect(DB_PATH)
    try:
        rows = connection.execute(
            """
            SELECT recommendations.url,
                   recommendations.title,
                   recommendations.reason,
                   ratings.value,
                   ratings.feedback_reason,
                   ratings.feedback_note
            FROM ratings
            JOIN recommendations
                ON recommendations.id = ratings.recommendation_id
            ORDER BY ratings.updated_at DESC, recommendations.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [
            {
                "url": url,
                "title": title,
                "reason": reason,
                "rating": rating,
                "feedback_reason": feedback_reason,
                "feedback_note": feedback_note,
            }
            for url, title, reason, rating, feedback_reason, feedback_note in rows
        ]
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
