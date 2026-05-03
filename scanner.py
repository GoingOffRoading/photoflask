"""Scans a directory tree for image files and persists them to the database."""

import os

from db import get_db, init_db, insert_photo

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"}


def scan_directory(directory):
    """Walk *directory*, insert any image files found, and return a summary dict.

    Returns:
        {
            "scanned": int,   # total image files found
            "added":   int,   # new records inserted
            "skipped": int,   # duplicates that were already in the DB
        }
    """
    directory = os.path.abspath(directory)
    conn = get_db()
    init_db(conn)

    scanned = added = skipped = 0
    for root, _dirs, files in os.walk(directory):
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in IMAGE_EXTENSIONS:
                continue
            scanned += 1
            full_path = os.path.join(root, fname)
            if insert_photo(full_path, fname, conn):
                added += 1
            else:
                skipped += 1

    conn.close()
    return {"scanned": scanned, "added": added, "skipped": skipped}
