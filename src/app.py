import os
import sqlite3
from flask import Flask, abort, redirect, render_template, request, send_file, url_for

from db_scan import sync_photos

app = Flask(__name__)

DB_FILENAME = "photoflask.db"


def _get_db_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, DB_FILENAME)


def get_all_photos():
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT Guid, FileName, FilePath, MediaType FROM photos ORDER BY FileName")
    rows = [
        {"guid": row[0], "name": row[1], "path": row[2], "type": row[3] or "unknown"}
        for row in cursor.fetchall()
    ]
    conn.close()
    return rows


@app.route("/")
def slideshow():
    photos = get_all_photos()
    selected_guid = request.args.get("photo")
    scan_message = request.args.get("scan_message")
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
        scan_message=scan_message,
    )


@app.post("/scan")
def scan():
    current_photo = request.form.get("current_photo")
    result = sync_photos()

    redirect_kwargs = {"scan_message": result["message"]}
    if current_photo:
        redirect_kwargs["photo"] = current_photo

    return redirect(url_for("slideshow", **redirect_kwargs))


@app.route("/image/<guid>")
def media(guid):
    photos = get_all_photos()
    matching_photo = next((photo for photo in photos if photo["guid"] == guid), None)
    if matching_photo is None:
        abort(404)

    filepath = matching_photo["path"]
    if not os.path.isfile(filepath):
        abort(404)

    # Handle range requests for video seeking
    range_header = request.headers.get("Range")
    file_size = os.path.getsize(filepath)

    if range_header:
        # Parse range header: "bytes=start-end"
        try:
            range_str = range_header.replace("bytes=", "")
            start, end = range_str.split("-")
            start = int(start) if start else 0
            end = int(end) if end else file_size - 1

            if start > end or end >= file_size:
                abort(416)  # Range Not Satisfiable

            with open(filepath, "rb") as f:
                f.seek(start)
                data = f.read(end - start + 1)

            response = app.response_class(
                data,
                206,  # Partial Content
                {
                    "Content-Range": f"bytes {start}-{end}/{file_size}",
                    "Content-Length": str(end - start + 1),
                    "Accept-Ranges": "bytes",
                },
            )
            return response
        except (ValueError, IndexError):
            pass

    return send_file(filepath)


if __name__ == "__main__":
    app.run(debug=True)
