# src/publisher/cli.py
import argparse
import json
from datetime import datetime
from pathlib import Path

from src.publisher.wp_client import WordPressDotComClient
from src.publisher.storage import log_published
from src.publisher.formatting import render_html, extract_introduction_excerpt

def main():
    parser = argparse.ArgumentParser(description="Publish final article to WordPress.com")
    parser.add_argument("--input", required=True, help="Path to final JSON (from data/final/)")
    parser.add_argument("--status", default="publish", help="WP post status, e.g. publish|draft")
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    title = data.get("title", "Untitled")
    raw_content = data.get("content", "")
    excerpt = extract_introduction_excerpt(raw_content)
    content = render_html(raw_content, post_title=title if title else None)
    slug = data.get("slug")
    tags = data.get("tags")
    categories = data.get("categories")

    client = WordPressDotComClient()
    resp = client.create_post(
        title=title,
        content=content,
        slug=slug,
        status=args.status,
        tags=tags,
        categories=categories,
        excerpt=excerpt or None,
    )

    created_at = datetime.utcnow().isoformat()
    wp_id = resp["id"]
    wp_link = resp["link"]

    log_published(
        created_at=created_at,
        wp_id=wp_id,
        wp_link=wp_link,
        slug=slug,
        title=title,
        source_file=args.input,
        raw_json=resp,
    )

    print("[OK] Published to WordPress.com")
    print(f"ID: {wp_id}")
    print(f"URL: {wp_link}")

if __name__ == "__main__":
    main()
