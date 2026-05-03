"""Flask application for photoflask – scan a directory and browse photos."""

import os

from flask import Flask, abort, redirect, render_template, send_file, url_for

import db as database
import scanner as photo_scanner

app = Flask(__name__)

# Directory that will be scanned for photos.  Override via env var.
PHOTO_DIR = os.environ.get("PHOTO_DIR", os.path.join(os.path.dirname(__file__), "photos"))


@app.before_request
def ensure_db():
    """Make sure the database and table exist before the first request."""
    database.init_db()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Gallery view – list all photos stored in the database."""
    photos = database.get_all_photos()
    return render_template("index.html", photos=photos)


@app.route("/scan")
def scan():
    """Trigger a scan of PHOTO_DIR, then redirect back to the gallery."""
    result = photo_scanner.scan_directory(PHOTO_DIR)
    photos = database.get_all_photos()
    return render_template("index.html", photos=photos, scan_result=result)


@app.route("/photo/<int:photo_id>")
def photo_detail(photo_id):
    """Detail page for a single photo."""
    photo = database.get_photo_by_id(photo_id)
    if photo is None:
        abort(404)
    return render_template("photo.html", photo=photo)


@app.route("/serve/<int:photo_id>")
def serve_photo(photo_id):
    """Serve the raw image file."""
    photo = database.get_photo_by_id(photo_id)
    if photo is None:
        abort(404)
    filepath = photo["filepath"]
    if not os.path.isfile(filepath):
        abort(404)
    return send_file(filepath)


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug)
