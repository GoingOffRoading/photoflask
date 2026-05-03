import os
import sqlite3
from flask import Flask, abort, render_template, request, send_file

app = Flask(__name__)

DB_FILENAME = "photoflask.db"


def _get_db_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, DB_FILENAME)


def get_all_photos():
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT Guid, FileName, FilePath FROM photos ORDER BY FileName")
    rows = [
        {"guid": row[0], "name": row[1], "path": row[2]}
        for row in cursor.fetchall()
    ]
    conn.close()
    return rows


@app.route("/")
def slideshow():
    photos = get_all_photos()
    selected_guid = request.args.get("guid")
    selected_index = 0

    if selected_guid:
        for index, photo in enumerate(photos):
            if photo["guid"] == selected_guid:
                selected_index = index
                break

    return render_template(
        "slideshow.html",
        photos=photos,
        total=len(photos),
        initial_index=selected_index,
    )


@app.route("/image/<guid>")
def photo(guid):
    photos = get_all_photos()
    matching_photo = next((photo for photo in photos if photo["guid"] == guid), None)
    if matching_photo is None:
        abort(404)

    filepath = matching_photo["path"]
    if not os.path.isfile(filepath):
        abort(404)
    return send_file(filepath)


if __name__ == "__main__":
    app.run(debug=True)
