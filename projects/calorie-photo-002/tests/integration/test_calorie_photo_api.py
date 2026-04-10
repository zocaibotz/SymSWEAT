import io
import os
import sqlite3
from fastapi.testclient import TestClient

# set db path before app import
DB_PATH = "/tmp/calorie-photo-002-test.db"
os.environ["CALORIE_DB_PATH"] = DB_PATH

from src.app import app


def test_analyze_photo_records_to_sqlite_and_returns_summary():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    client = TestClient(app)
    resp = client.post(
        "/analyze-photo",
        files={"photo": ("banana.jpg", io.BytesIO(b"fake-image"), "image/jpeg")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["food_label"] == "banana"
    assert data["calories"] == 105.0
    assert data["sugar_g"] == 14.0
    assert "Recorded banana" in data["summary"]

    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT food_label, calories, sugar_g, recorded_at_utc FROM meal_records ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()

    assert row is not None
    assert row[0] == "banana"
    assert float(row[1]) == 105.0
    assert float(row[2]) == 14.0
    assert row[3].endswith("Z")
