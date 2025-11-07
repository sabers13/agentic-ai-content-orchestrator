"""
Prefect task definitions that back each stage of the orchestrator flow.
"""
import json
from datetime import datetime
from pathlib import Path

from openai import OpenAI
from prefect import task

from src.common.config import settings
from src.llm_compare.evaluator import compare_models
from src.llm_compare.storage import save_result
from src.publisher.formatting import (
    ensure_markdown_toc,
    extract_introduction_excerpt,
    render_html,
)
from src.quality_agent.quality_runner import process_file

QUALITY_MAX_REVISIONS = 2
REVISION_MODEL = "gpt-5o"
BAD_HEADING_MARKERS = ("H1:", "H2:", "H3:", "h1:", "h2:", "h3:")


@task(name="Generate draft via LLM compare")
def task_generate_from_brief(
    brief: str,
    model_a: str,
    model_b: str,
    tone: str | None = None,
) -> str:
    """
    Compare two LLMs, persist the run metadata, and normalize the winning draft.
    Optional `tone` guidance is forwarded to the LLM prompt when provided.

    Returns:
        Either a JSON summary dict (with `path`, metrics, and winner) or the raw
        optimized path if the downstream caller only needs the artifact.
    """
    result = compare_models(brief, model_a, model_b, tone=tone)
    save_result(result)

    winner = result.winner
    # `compare_models` keeps both structured outputs; choose the text from the winner.
    chosen = result.model_a if result.model_a.model == winner else result.model_b
    slug = brief.lower().replace(" ", "-")
    content_markdown = ensure_markdown_toc(chosen.output)

    # Base draft structure
    draft = {
        "title": brief,
        "slug": slug,
        "brief": brief,
        "tone": tone,
        "content": content_markdown,
        "source": "prefect_run",
    }

    # Compute a richer SEO score if the optimizer is available; otherwise keep the legacy heuristic.
    try:
        from src.content_brain.seo_optimizer import compute_seo_score

        score, analysis = compute_seo_score(draft)
        draft["seo_score"] = score
        draft["seo_analysis"] = analysis
        seo_meta = draft.setdefault("seo", {})
        seo_meta["seo_score"] = score
        seo_meta["analysis"] = analysis
        seo_meta["meta_title"] = (draft["title"] or "")[:60]
        seo_meta["meta_description"] = (
            f"{draft['title']} – {brief[:120]}" if draft.get("title") else brief[:120]
        )
    except Exception:
        draft["seo_score"] = max(
            result.scores.get("model_a_seo", 60),
            result.scores.get("model_b_seo", 60),
        )
    out_path = Path("data/optimized") / f"{slug}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(draft, indent=2, ensure_ascii=False), encoding="utf-8")
    summary = {
        "path": str(out_path),
        "winner": winner,
        "avg_a": result.extra.get("avg_a"),
        "avg_b": result.extra.get("avg_b"),
        "seo_score": draft.get("seo_score"),
        "quality_score": None,
        "tone": tone,
    }
    return summary


@task(name="Quality gate draft")
def task_quality_gate(draft_path: str) -> str:
    """
    Run the quality agent and optionally invoke iterative GPT revisions.
    """
    attempts = 0
    current_path = draft_path.get("path") if isinstance(draft_path, dict) else draft_path

    while attempts <= QUALITY_MAX_REVISIONS:
        # The quality runner copies the passing artifact into data/final automatically.
        res = process_file(current_path, "data/final", "data/rejected")
        if res["passes"]:
            draft_stem = Path(current_path).stem
            final_path = Path("data/final") / f"{draft_stem}.json"
            meta = {}
            if isinstance(res, dict):
                meta = res
            return {
                "path": str(final_path) if final_path.exists() else str(final_path),
                "quality_meta": meta,
            }

        attempts += 1
        if attempts > QUALITY_MAX_REVISIONS:
            raise ValueError(f"Quality gate failed after revisions: {res['reasons']}")

        current_path = _revise_draft_for_quality(current_path, res["reasons"], attempts)


@task(name="Publish to WordPress.com")
def task_publish(final_path: str, status: str = "publish") -> str:
    """
    Render sanitized HTML and push it to the WordPress.com REST API.
    """
    from src.publisher.storage import log_published
    from src.publisher.wp_client import WordPressDotComClient

    final_path = final_path.get("path") if isinstance(final_path, dict) else final_path
    data = json.loads(Path(final_path).read_text(encoding="utf-8"))
    title = data.get("title", "Untitled")
    content = data.get("content", "")
    excerpt = extract_introduction_excerpt(content)
    slug = data.get("slug")
    tags = data.get("tags")
    categories = data.get("categories")

    client = WordPressDotComClient()
    content_html = render_html(content, post_title=title)
    if any(marker in content for marker in BAD_HEADING_MARKERS):
        print("[publisher] normalized draft with legacy heading markers")
    resp = client.create_post(
        title=title,
        content=content_html,
        slug=slug,
        status=status,
        tags=tags,
        categories=categories,
        excerpt=excerpt or None,
    )

    created_at = datetime.utcnow().isoformat()
    log_published(
        created_at=created_at,
        wp_id=resp["id"],
        wp_link=resp["link"],
        slug=slug,
        title=title,
        source_file=final_path,
        raw_json=resp,
    )

    return {
        "url": resp["link"],
        "wp_id": resp["id"],
        "status": resp.get("status"),
    }


def _revise_draft_for_quality(draft_path: str, reasons: list[str], attempt: int) -> str:
    """
    Use GPT to revise the draft aiming to satisfy quality gate reasons.
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY missing; cannot auto-revise failed draft.")

    data = json.loads(Path(draft_path).read_text(encoding="utf-8"))
    original_content = data.get("content", "")
    reasons_text = "\n".join(f"- {reason}" for reason in reasons)

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    # Delegate the actual rewrite to a lighter-weight editing prompt so retries stay cheap.
    response = client.chat.completions.create(
        model=REVISION_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are an expert editor who improves drafts for WordPress.com readers.",
            },
            {
        "role": "user",
        "content": f"""The draft below failed a quality gate for these reasons:
{reasons_text}

Revise the draft to fix these issues:
- Improve readability (shorter sentences, clear structure).
- Boost SEO cues with H2/H3 headings and scannable bullets.
- Preserve the Table of Contents at the top using markdown bullets that mirror the final sections.
- Use `##` for section titles (H2) and `###` for sub-sections (H3); keep FAQ questions bold within paragraphs, not headings.
- Preserve accurate facts and the author's voice.
- Return the revised draft as markdown-style text only, no commentary.

Draft:
{original_content}
""",
            },
        ],
        temperature=0.4,
    )

    improved_content = response.choices[0].message.content.strip()
    data["content"] = ensure_markdown_toc(improved_content)
    data["quality_revision_attempt"] = attempt
    Path(draft_path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return draft_path
