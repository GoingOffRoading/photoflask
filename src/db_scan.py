import os
from datetime import datetime

from db_operations import (
    add_photo_by_filepath,
    check_photo_record_exists_by_filepath,
    delete_photo_by_filepath,
    get_photos_not_last_touched,
    update_photo_timestamp,
)


def _process_photo_files(directory, scan_timestamp, db_filename="photoflask.db"):
    processed_files = 0

    for root, _, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)

            if check_photo_record_exists_by_filepath(filepath, db_filename=db_filename):
                update_photo_timestamp(filepath, scan_timestamp, db_filename=db_filename)
            else:
                add_photo_by_filepath(filepath, db_filename=db_filename, last_touched=scan_timestamp)

            processed_files += 1

    return processed_files


def _cleanup_outdated_photos(scan_timestamp, db_filename="photoflask.db"):
    outdated_photos = get_photos_not_last_touched(scan_timestamp, db_filename=db_filename)

    deleted_count = 0
    for filepath in outdated_photos:
        delete_photo_by_filepath(filepath, db_filename=db_filename)
        deleted_count += 1

    return deleted_count


def sync_photos(directory="C:/Photos", db_filename="photoflask.db"):
    scan_timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    if not os.path.isdir(directory):
        return {
            "scan_timestamp": scan_timestamp,
            "processed_files": 0,
            "deleted_records": 0,
            "message": f"Directory not found: {directory}",
        }

    processed_files = _process_photo_files(directory, scan_timestamp, db_filename=db_filename)
    deleted_count = _cleanup_outdated_photos(scan_timestamp, db_filename=db_filename)

    return {
        "scan_timestamp": scan_timestamp,
        "processed_files": processed_files,
        "deleted_records": deleted_count,
        "message": "Sync complete",
    }