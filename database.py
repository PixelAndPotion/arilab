"""
Database layer for ARI'Lab.

Persists every review attempt to SQLite so you can track your
improvement across sessions. The results table stores enough
information to analyse which categories you struggle with most
and whether your accuracy improves over time.

"""

import sqlite3
from datetime import datetime

DB_PATH = "arilab.db"


def init_db():
    """
    Creates the results table if it doesn't exist.
    Safe to call every time the application starts.
    """
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            challenge_id    TEXT NOT NULL,
            category        TEXT,
            difficulty      TEXT,
            points_earned   INTEGER,
            points_available INTEGER,
            grade           TEXT,
            user_answer     TEXT,
            answered_at     TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def log_result(challenge_id: str, category: str, difficulty: str,
               points_earned: int, points_avail: int,
               grade: str, user_answer: str):
    """
    Writes a single review attempt to the database.
    Called immediately after scoring so results are never lost
    even if the session is closed before the summary screen.
    """
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute("""
        INSERT INTO results
            (challenge_id, category, difficulty, points_earned,
             points_available, grade, user_answer, answered_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        challenge_id,
        category,
        difficulty,
        points_earned,
        points_avail,
        grade,
        user_answer,
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()


def get_session_summary() -> dict:
    """
    Returns aggregate statistics across all stored sessions.
    Useful for a future progress dashboard feature.
    """
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute("""
        SELECT category,
               COUNT(*) as attempts,
               SUM(points_earned) as earned,
               SUM(points_available) as available
        FROM results
        GROUP BY category
    """)
    rows   = c.fetchall()
    conn.close()
    return {
        row[0]: {
            "attempts":  row[1],
            "earned":    row[2],
            "available": row[3],
        }
        for row in rows
    }