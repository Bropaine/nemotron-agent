import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import discovery_store as store


with TemporaryDirectory() as directory:
    test_db = Path(directory) / "test.db"
    with patch.object(store, "DB_PATH", test_db):
        store.initialize_database()
        url = "https://example.com/test"
        assert store.save_recommendation(url, "Test", "Test reason")
        assert store.get_rating(url) is None

        assert store.save_rating(url, 1)
        assert store.get_rating(url) == 1
        assert store.save_rating(url, -1)
        assert store.get_rating(url) == -1
        assert store.save_rating(url, -1)

        assert not store.save_rating("https://example.com/unknown", 1)
        for invalid in (0, 2, True, "1"):
            try:
                store.save_rating(url, invalid)
            except ValueError:
                pass
            else:
                raise AssertionError(f"Accepted invalid rating: {invalid!r}")

        connection = sqlite3.connect(test_db)
        try:
            assert connection.execute("SELECT COUNT(*) FROM ratings").fetchone()[0] == 1
        finally:
            connection.close()

        store.initialize_database()
        assert store.get_rating(url) == -1

print("Passed: rating saved, changed, persisted, and validated without duplicates.")