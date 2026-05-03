"""Tests for photoflask – db helpers, scanner, and Flask routes."""

import os
import sys
import tempfile
import pytest

# Allow importing app modules from the project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import db as database
import scanner as photo_scanner
from app import app as flask_app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_db(tmp_path, monkeypatch):
    """Redirect DATABASE to a temporary file for each test."""
    db_file = str(tmp_path / "test.db")
    monkeypatch.setattr(database, "DATABASE", db_file)
    database.init_db()
    yield db_file


@pytest.fixture()
def client(tmp_db, tmp_path, monkeypatch):
    """Flask test client with an isolated DB and photos directory."""
    photos_dir = tmp_path / "photos"
    photos_dir.mkdir()
    monkeypatch.setattr("app.PHOTO_DIR", str(photos_dir))
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c, photos_dir


# ---------------------------------------------------------------------------
# DB helper tests
# ---------------------------------------------------------------------------

class TestDb:
    def test_init_creates_table(self, tmp_db):
        conn = database.get_db()
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='photos'"
        ).fetchone()
        conn.close()
        assert tables is not None

    def test_insert_and_retrieve(self, tmp_db):
        database.insert_photo("/some/path/a.jpg", "a.jpg")
        photos = database.get_all_photos()
        assert len(photos) == 1
        assert photos[0]["filename"] == "a.jpg"

    def test_insert_duplicate_ignored(self, tmp_db):
        database.insert_photo("/some/path/a.jpg", "a.jpg")
        database.insert_photo("/some/path/a.jpg", "a.jpg")
        assert len(database.get_all_photos()) == 1

    def test_get_photo_by_id(self, tmp_db):
        database.insert_photo("/some/path/b.jpg", "b.jpg")
        photos = database.get_all_photos()
        photo_id = photos[0]["id"]
        row = database.get_photo_by_id(photo_id)
        assert row is not None
        assert row["filename"] == "b.jpg"

    def test_get_photo_by_id_missing(self, tmp_db):
        assert database.get_photo_by_id(9999) is None


# ---------------------------------------------------------------------------
# Scanner tests
# ---------------------------------------------------------------------------

class TestScanner:
    def test_scan_finds_images(self, tmp_db, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        (photos_dir / "cat.jpg").write_bytes(b"fake-jpg")
        (photos_dir / "dog.png").write_bytes(b"fake-png")
        (photos_dir / "readme.txt").write_text("not an image")

        result = photo_scanner.scan_directory(str(photos_dir))

        assert result["scanned"] == 2
        assert result["added"] == 2
        assert result["skipped"] == 0

    def test_scan_skips_duplicates(self, tmp_db, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        (photos_dir / "cat.jpg").write_bytes(b"fake-jpg")

        photo_scanner.scan_directory(str(photos_dir))
        result = photo_scanner.scan_directory(str(photos_dir))

        assert result["scanned"] == 1
        assert result["added"] == 0
        assert result["skipped"] == 1

    def test_scan_recurses_subdirectories(self, tmp_db, tmp_path):
        photos_dir = tmp_path / "photos"
        sub = photos_dir / "sub"
        sub.mkdir(parents=True)
        (sub / "nested.jpg").write_bytes(b"fake-jpg")

        result = photo_scanner.scan_directory(str(photos_dir))
        assert result["scanned"] == 1
        assert result["added"] == 1

    def test_scan_empty_directory(self, tmp_db, tmp_path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        result = photo_scanner.scan_directory(str(empty_dir))
        assert result == {"scanned": 0, "added": 0, "skipped": 0}


# ---------------------------------------------------------------------------
# Flask route tests
# ---------------------------------------------------------------------------

class TestRoutes:
    def test_index_empty(self, client):
        c, _ = client
        resp = c.get("/")
        assert resp.status_code == 200
        assert b"No photos" in resp.data

    def test_scan_route_adds_photos(self, client):
        c, photos_dir = client
        (photos_dir / "sample.jpg").write_bytes(b"fake-jpg")
        resp = c.get("/scan")
        assert resp.status_code == 200
        assert b"sample.jpg" in resp.data
        assert b"added" in resp.data.lower() or b"Scan complete" in resp.data

    def test_index_shows_photos_after_scan(self, client):
        c, photos_dir = client
        (photos_dir / "flower.png").write_bytes(b"fake-png")
        c.get("/scan")
        resp = c.get("/")
        assert b"flower.png" in resp.data

    def test_photo_detail_404(self, client):
        c, _ = client
        resp = c.get("/photo/9999")
        assert resp.status_code == 404

    def test_serve_photo_404(self, client):
        c, _ = client
        resp = c.get("/serve/9999")
        assert resp.status_code == 404

    def test_serve_photo_missing_file(self, client, tmp_db):
        """Record exists in DB but file has been deleted from disk."""
        c, photos_dir = client
        img_path = photos_dir / "gone.jpg"
        img_path.write_bytes(b"fake-jpg")
        c.get("/scan")
        img_path.unlink()
        photos = database.get_all_photos()
        assert len(photos) == 1
        resp = c.get(f"/serve/{photos[0]['id']}")
        assert resp.status_code == 404
