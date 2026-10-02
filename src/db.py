import sqlite3
from contextlib import contextmanager
from pathlib import Path

from flask import current_app, g


def connect(path):
    connection = sqlite3.connect(path, timeout=10, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.create_function("casefold", 1, str.casefold, deterministic=True)
    return connection


def get_db():
    if "database" not in g:
        g.database = connect(current_app.config["DATABASE"])
    return g.database


def close_db(_error=None):
    connection = g.pop("database", None)
    if connection is not None:
        connection.close()


@contextmanager
def transaction(connection):
    connection.execute("BEGIN IMMEDIATE")
    try:
        yield
        connection.commit()
    except BaseException:
        connection.rollback()
        raise


def initialize_database(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    migrations = sorted(Path(__file__).with_name("sql").glob("*.sql"))
    connection = connect(path)
    try:
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version > len(migrations):
            raise RuntimeError(f"Unsupported database schema version: {version}")
        for migration in migrations[version:]:
            connection.executescript(migration.read_text(encoding="utf-8"))
    finally:
        connection.close()
