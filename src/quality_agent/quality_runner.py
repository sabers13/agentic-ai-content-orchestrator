# src/quality_agent/quality_runner.py
import os
from pathlib import Path
from typing import Dict, Any

from src.quality_agent.readability import readability_score
from src.quality_agent.relevance import relevance_score
from src.quality_agent.plagiarism import plagiarism_score
from src.quality_agent.utils import load_draft, save_json

SEO_THRESHOLD = int(os.environ.get("SEO_THRESHOLD", 70))
QUALITY_THRESHOLD = int(os.environ.get("QUALITY_THRESHOLD", 75))


def evaluate_draft(draft: Dict[str, Any]) -> Dict[str, Any]:
    content = draft.get("content", "")
    brief = draft.get("brief") or draft.get("title") or ""

    read_score = readability_score(content)
    rel_score = relevance_score(brief, content)
    plag_score = plagiarism_score(content)
    seo_score = draft.get("seo_score", 60)

    # give a small bonus to well-structured posts
    has_structure = ("##" in content) or ("H2:" in content) or ("H3:" in content)
    structure_bonus = 3 if has_structure else 0

    # slightly rebalanced weights
    quality_score = (
        read_score * 0.2
        + rel_score * 0.25
        + seo_score * 0.35
        + (100 - plag_score) * 0.2
    )

    quality_score = round(quality_score + structure_bonus, 2)

    passes = (
        seo_score >= SEO_THRESHOLD
        and quality_score >= QUALITY_THRESHOLD
        and plag_score <= 35.0
    )

    return {
        "passes": passes,
        "readability": read_score,
        "relevance": rel_score,
        "plagiarism": plag_score,
        "seo_score": seo_score,
        "quality_score": quality_score,
        "reasons": [] if passes else _failure_reasons(
            read_score,
            rel_score,
            plag_score,
            seo_score,
            quality_score,
        ),
    }


def _failure_reasons(read_s, rel_s, plag_s, seo_s, q_s):
    reasons = []
    if seo_s < SEO_THRESHOLD:
        reasons.append(f"SEO score {seo_s} < required {SEO_THRESHOLD}")
    if q_s < QUALITY_THRESHOLD:
        reasons.append(f"Quality score {q_s} < required {QUALITY_THRESHOLD}")
    if plag_s > 35.0:
        reasons.append(f"Plagiarism-lite overlap too high: {plag_s:.1f}%")
    # relaxed relevance floor
    if rel_s < 30:
        reasons.append(f"Relevance to brief low: {rel_s:.1f}")
    if read_s < 45:
        reasons.append(f"Readability low: {read_s:.1f}")
    return reasons


def process_file(
    input_path: str,
    final_dir: str = "data/final",
    rejected_dir: str = "data/rejected",
) -> Dict[str, Any]:
    draft = load_draft(input_path)
    result = evaluate_draft(draft)

    slug = draft.get("slug") or Path(input_path).stem

    if result["passes"]:
        out_path = Path(final_dir) / f"{slug}.json"
        draft["quality_meta"] = result
        save_json(draft, str(out_path))
    else:
        out_path = Path(rejected_dir) / f"{slug}.json"
        save_json(
            {
                "draft": draft,
                "quality_meta": result,
            },
            str(out_path),
        )

    return result
