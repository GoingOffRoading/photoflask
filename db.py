"""SQLite database helpers for photoflask."""

import sqlite3
import os

DATABASE = os.environ.get("DATABASE_PATH", "photos.db")


def get_db():
    """Return a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn=None):
    """Create the photos table if it does not already exist."""
    close = conn is None
    if conn is None:
        conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS photos (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            filename  TEXT    NOT NULL,
            filepath  TEXT    NOT NULL UNIQUE,
            added_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()
    if close:
        conn.close()


def insert_photo(filepath, filename, conn=None):
    """Insert a photo record, ignoring duplicates.  Returns True if inserted."""
    close = conn is None
    if conn is None:
        conn = get_db()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO photos (filepath, filename) VALUES (?, ?)",
            (filepath, filename),
        )
        conn.commit()
        inserted = conn.execute(
            "SELECT changes() AS c"
        ).fetchone()["c"] == 1
    finally:
        if close:
            conn.close()
    return inserted


def get_all_photos(conn=None):
    """Return all photo rows ordered by filename."""
    close = conn is None
    if conn is None:
        conn = get_db()
    rows = conn.execute(
        "SELECT * FROM photos ORDER BY filename"
    ).fetchall()
    if close:
        conn.close()
    return rows


def get_photo_by_id(photo_id, conn=None):
    """Return a single photo row or None."""
    close = conn is None
    if conn is None:
        conn = get_db()
    row = conn.execute(
        "SELECT * FROM photos WHERE id = ?", (photo_id,)
    ).fetchone()
    if close:
        conn.close()
    return row
