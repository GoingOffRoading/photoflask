import os
import sqlite3
import uuid


def _get_db_path(db_filename="photoflask.db"):
    # Return the absolute path to the SQLite database file in this folder.
    base_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
    return os.path.join(base_dir, db_filename)


def add_photo_by_filepath(filepath, db_filename="photoflask.db", last_touched=None):
    # Add a photo row to the photos table using Guid, FileName, FilePath, and LastTouched.
    db_path = _get_db_path(db_filename)
    file_name = os.path.basename(filepath)
    guid = uuid.uuid4().hex[:16]

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO photos (Guid, FileName, FilePath, LastTouched)
        VALUES (?, ?, ?, ?)
        """,
        (guid, file_name, filepath, last_touched),
    )

    conn.commit()
    conn.close()
    return guid


def check_photo_record_exists_by_filepath(filepath, db_filename="photoflask.db"):
    # Check if a photo row exists in the photos table by filepath.
    # Returns True if the filepath exists, False otherwise.
    db_path = _get_db_path(db_filename)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT 1
        FROM photos
        WHERE FilePath = ?
        LIMIT 1
        """,
        (filepath,),
    )

    exists = cursor.fetchone() is not None
    conn.close()
    return exists


def update_photo_timestamp(filepath, timestamp, db_filename="photoflask.db"):
    # Update the LastTouched timestamp for a photo by filepath.
    # Returns the number of rows updated.
    db_path = _get_db_path(db_filename)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE photos
        SET LastTouched = ?
        WHERE FilePath = ?
        """,
        (timestamp, filepath),
    )

    updated_rows = cursor.rowcount
    conn.commit()
    conn.close()
    return updated_rows


def delete_photo_by_filepath(filepath, db_filename="photoflask.db"):
    # Delete photo row(s) from the photos table by file path.
    db_path = _get_db_path(db_filename)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM photos
        WHERE FilePath = ?
        """,
        (filepath,),
    )

    deleted_rows = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted_rows


def get_photos_not_last_touched(last_touched_timestamp, db_filename="photoflask.db"):
    # Get all photo records that do not match the given LastTouched timestamp.
    # Returns a list of filepaths for records to be deleted.
    db_path = _get_db_path(db_filename)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT FilePath
        FROM photos
        WHERE LastTouched != ?
        """,
        (last_touched_timestamp,),
    )

    outdated_photos = [row[0] for row in cursor.fetchall()]
    conn.close()
    return outdated_photos


