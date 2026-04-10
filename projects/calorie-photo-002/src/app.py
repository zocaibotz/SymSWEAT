from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = os.getenv("CALORIE_DB_PATH", "data/calorie_records.db")

app = FastAPI(title="Calorie Photo Tracker")


def _db_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS meal_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            food_label TEXT NOT NULL,
            calories REAL NOT NULL,
            sugar_g REAL NOT NULL,
            recorded_at_utc TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def estimate_food_metrics(filename: str) -> tuple[str, float, float]:
    name = (filename or "").lower()
    if "banana" in name:
        return "banana", 105.0, 14.0
    if "rice" in name:
        return "rice", 206.0, 0.1
    if "apple" in name:
        return "apple", 95.0, 19.0
    return "mixed_food", 250.0, 8.0


class AnalyzeResponse(BaseModel):
    food_label: str
    calories: float
    sugar_g: float
    recorded_at_utc: str
    summary: str


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/analyze-photo", response_model=AnalyzeResponse)
async def analyze_photo(photo: UploadFile = File(...)):
    food_label, calories, sugar_g = estimate_food_metrics(photo.filename)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    conn = _db_conn()
    conn.execute(
        "INSERT INTO meal_records (food_label, calories, sugar_g, recorded_at_utc) VALUES (?, ?, ?, ?)",
        (food_label, calories, sugar_g, ts),
    )
    conn.commit()
    conn.close()

    summary = f"Recorded {food_label}: {calories:.0f} kcal, {sugar_g:.1f}g sugar at {ts}"
    return AnalyzeResponse(
        food_label=food_label,
        calories=calories,
        sugar_g=sugar_g,
        recorded_at_utc=ts,
        summary=summary,
    )
