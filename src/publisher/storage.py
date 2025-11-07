# src/publisher/storage.py
import sqlite3
from pathlib import Path
import json

DB_PATH = Path("data/runs.sqlite")

POSTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS published_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    wp_id INTEGER NOT NULL,
    wp_link TEXT NOT NULL,
    slug TEXT,
    title TEXT NOT NULL,
    source_file TEXT NOT NULL,
    raw_json TEXT NOT NULL
);
"""

POST_VIEWS_SCHEMA = """
CREATE TABLE IF NOT EXISTS post_views (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    site TEXT NOT NULL,
    views INTEGER NOT NULL,
    fetched_at TEXT NOT NULL
);
"""

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(POSTS_SCHEMA)
    conn.execute(POST_VIEWS_SCHEMA)
    conn.commit()
    conn.close()

def log_published(created_at: str, wp_id: int, wp_link: str,
                  slug: str, title: str, source_file: str, raw_json: dict):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO published_posts (
            created_at, wp_id, wp_link, slug, title, source_file, raw_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (created_at, wp_id, wp_link, slug, title, source_file, json.dumps(raw_json)),
    )
    conn.commit()
    conn.close()
