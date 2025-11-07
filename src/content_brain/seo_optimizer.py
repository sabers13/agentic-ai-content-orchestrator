# src/content_brain/seo_optimizer.py
import re
from pathlib import Path
import json

def load_draft(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_optimized(draft: dict, out_dir: str = "data/optimized") -> str:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    slug = draft.get("slug", "draft")
    out_path = Path(out_dir) / f"{slug}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(draft, f, ensure_ascii=False, indent=2)
    return str(out_path)

def compute_seo_score(draft: dict) -> tuple[int, dict]:
    title = draft.get("title", "") or ""
    seo = draft.get("seo", {}) or {}
    primary_kw = seo.get("primary_keyword") or (draft.get("keywords") or [None])[0]
    content = draft.get("content", "") or ""

    score = 100
    details: dict[str, str | int] = {}

    # --- Title length ---
    title_len = len(title)
    if not (45 <= title_len <= 65):
        score -= 8
        details["title_length"] = "suboptimal"
    else:
        details["title_length"] = "ok"

    # --- Primary keyword in title ---
    if primary_kw:
        pk = primary_kw.lower()
        if pk and pk not in title.lower():
            score -= 10
            details["primary_kw_in_title"] = "missing"
        else:
            details["primary_kw_in_title"] = "ok"
    else:
        details["primary_kw_in_title"] = "unknown"

    # --- Word count ---
    word_count = len(re.findall(r"\b\w+\b", content))
    if word_count < 600:
        score -= 15
        details["word_count"] = f"low ({word_count})"
    elif word_count < 1000:
        score -= 5
        details["word_count"] = f"medium ({word_count})"
    else:
        details["word_count"] = f"good ({word_count})"

    # --- Section count (## headings) ---
    sections = re.findall(r"^##\s+", content, flags=re.MULTILINE)
    section_count = len(sections)
    if section_count < 4:
        score -= 12
        details["sections"] = f"too_few ({section_count})"
    elif section_count > 8:
        score -= 5
        details["sections"] = f"too_many ({section_count})"
    else:
        details["sections"] = f"ok ({section_count})"

    # --- Keyword usage in body ---
    if primary_kw:
        pk = primary_kw.lower()
        body_low = content.lower()
        occurrences = body_low.count(pk)
        details["primary_kw_in_body"] = occurrences
        if occurrences < 2:
            score -= 10
        elif occurrences > 8:
            score -= 5  # possible keyword stuffing
    else:
        details["primary_kw_in_body"] = "unknown"

    # --- Link presence (basic) ---
    links = re.findall(r"\((https?://[^)]+)\)", content)
    if not links:
        score -= 8
        details["links"] = "missing"
    else:
        details["links"] = f"{len(links)}"

    # --- Image hints / alt text suggestion ---
    details["image_alt_text"] = "Add descriptive alt text to any images with the primary keyword."

    # Clamp score
    score = max(0, min(100, score))
    return score, details

def optimize_draft(draft: dict) -> dict:
    score, details = compute_seo_score(draft)
    draft["seo"] = draft.get("seo", {})
    draft["seo"]["seo_score"] = score
    draft["seo"]["analysis"] = details
    # also add meta fields that publisher could map
    draft["seo"]["meta_title"] = draft["title"][:60]
    draft["seo"]["meta_description"] = f"{draft['title']} – an AI automation / WordPress content guide."
    return draft
