"""
Prefect flow entrypoints for orchestrating the end-to-end content pipeline.
"""
import json
import sqlite3
from pathlib import Path

from prefect import flow, get_run_logger

from src.orchestrator.tasks import (
    task_generate_from_brief,
    task_quality_gate,
    task_publish,
)
from src.publisher.storage import DB_PATH
from src.publisher.telemetry import fetch_views
from src.common.config import settings


@flow(name="ai-content-orchestrator")
def ai_content_orchestrator_flow(
    brief: str = "AI content orchestrator for WordPress.com",
    model_a: str = settings.MODEL_PRIMARY,
    model_b: str = settings.MODEL_SECONDARY,
    auto_publish: bool = True,
    tone: str | None = None,
):
    """
    Run the three high-level stages: generate, quality gate, (optionally) publish.

    Prefect wraps each delegated task so the UI still shows individual retries,
    while this function keeps the control flow simple for CLI/Streamlit callers.
    The optional `tone` hint is forwarded to the LLM comparison prompt so editors
    can enforce voice/brand guidance.
    """
    # 1) generate
    result_generate = task_generate_from_brief(brief, model_a, model_b, tone)
    if isinstance(result_generate, dict):
        optimized_path = result_generate.get("path")
    else:
        optimized_path = result_generate

    # 2) quality gate
    result_quality = task_quality_gate(optimized_path)
    if isinstance(result_quality, dict):
        final_path = result_quality.get("path")
    else:
        final_path = result_quality

    # 3) publish (optional)
    if auto_publish:
        publish_res = task_publish(final_path, status="publish")
        url = publish_res.get("url") if isinstance(publish_res, dict) else publish_res
        return {"status": "published", "url": url, "final_path": final_path}
    else:
        return {"status": "ready", "final_path": final_path}


@flow(name="post-engagement-telemetry")
def post_engagement_telemetry_flow(limit: int = 20):
    """
    Collects engagement metrics for recent published posts.
    """
    logger = get_run_logger()
    if not DB_PATH.exists():
        logger.info("No published_posts table yet; skipping telemetry.")
        return

    site = settings.WP_DOTCOM_SITE
    if not site:
        logger.warning("WP_DOTCOM_SITE is not configured; cannot fetch telemetry.")
        return

    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT wp_id, title FROM published_posts ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()

    if not rows:
        logger.info("No published posts to collect telemetry for.")
        return

    for wp_id, title in rows:
        try:
            views = fetch_views(post_id=wp_id, site=site)
            logger.info(f"Recorded {views} views for post '{title}' (wp_id={wp_id}).")
        except Exception as exc:
            logger.warning(f"Failed to fetch telemetry for wp_id={wp_id}: {exc}")


if __name__ == "__main__":
    import argparse
    from distutils.util import strtobool

    parser = argparse.ArgumentParser(description="Run the AI content orchestrator flow.")
    parser.add_argument(
        "--brief",
        default="AI content orchestrator for WordPress.com",
        help="Content brief or working title for the draft.",
    )
    parser.add_argument(
        "--model-a",
        default=settings.MODEL_PRIMARY,
        help=f"Primary model to compare (default: {settings.MODEL_PRIMARY}).",
    )
    parser.add_argument(
        "--model-b",
        default=settings.MODEL_SECONDARY,
        help=f"Secondary model to compare (default: {settings.MODEL_SECONDARY}).",
    )
    parser.add_argument(
        "--auto-publish",
        default="true",
        help="Whether to publish automatically (true/false).",
    )
    parser.add_argument(
        "--tone",
        default=None,
        help="Optional tone hint (practical, technical, authoritative, friendly, ...).",
    )

    args = parser.parse_args()
    ai_content_orchestrator_flow(
        brief=args.brief,
        model_a=args.model_a,
        model_b=args.model_b,
        auto_publish=bool(strtobool(args.auto_publish)),
        tone=args.tone,
    )
