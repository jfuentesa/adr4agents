import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.db import connect, initialize_database


class DatabaseTests(unittest.TestCase):
    def test_upgrade_preserves_existing_data(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "upgrade.sqlite3")
            connection = connect(path)
            schema = Path(__file__).resolve().parents[1] / "src" / "sql" / "001_initial.sql"
            connection.executescript(schema.read_text(encoding="utf-8"))
            connection.execute("INSERT INTO projects (name) VALUES ('existing')")
            connection.close()
            initialize_database(path)
            initialize_database(path)
            connection = connect(path)
            try:
                self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 2)
                self.assertEqual(connection.execute("SELECT name FROM projects").fetchone()[0], "existing")
                columns = connection.execute("PRAGMA table_info(relations)").fetchall()
                self.assertIn("effective", [column["name"] for column in columns])
                self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
            finally:
                connection.close()

    def test_foreign_keys_are_enforced(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "foreign_keys.sqlite3")
            initialize_database(path)
            connection = connect(path)
            try:
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(
                        "INSERT INTO comments (decision_id, author, text, date) VALUES (999, 'Agent1', 'Text', '2026-10-02')"
                    )
            finally:
                connection.close()
