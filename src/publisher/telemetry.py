# src/publisher/telemetry.py
"""
Utilities for collecting engagement telemetry from WordPress.com.
"""

from __future__ import annotations

import datetime as dt
import sqlite3
from typing import Optional

import requests

from src.common.config import settings
from src.publisher.storage import DB_PATH, init_db

STATS_ENDPOINT = "https://public-api.wordpress.com/rest/v1.1/sites/{site}/stats/post/{post_id}"


def fetch_views(post_id: int, site: Optional[str] = None, timeout: int = 10) -> int:
    """
    Fetch view counts for a WordPress.com post and log them to SQLite.

    Returns the number of views reported by the API.
    """
    site = site or settings.WP_DOTCOM_SITE
    if not site:
        raise ValueError("WP_DOTCOM_SITE must be configured to collect telemetry.")

    headers = {"Content-Type": "application/json"}
    token = settings.WP_DOTCOM_BEARER
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = STATS_ENDPOINT.format(site=site, post_id=post_id)
    resp = requests.get(url, headers=headers, timeout=timeout)
    if not resp.ok:
        raise RuntimeError(f"Failed to fetch stats for post {post_id}: {resp.status_code} {resp.text}")

    payload = resp.json()
    views = int(payload.get("views", 0))
    log_post_views(post_id=post_id, site=site, views=views)
    return views


def log_post_views(post_id: int, site: str, views: int, fetched_at: Optional[dt.datetime] = None) -> None:
    """
    Persist a telemetry datapoint to SQLite.
    """
    init_db()
    fetched_at = fetched_at or dt.datetime.utcnow()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO post_views (post_id, site, views, fetched_at)
        VALUES (?, ?, ?, ?)
        """,
        (post_id, site, views, fetched_at.isoformat()),
    )
    conn.commit()
    conn.close()

