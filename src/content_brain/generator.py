"""
Utility helpers for producing scaffolds/outlines before the main LLM run.
"""
import csv
import json
from pathlib import Path
from datetime import datetime

TONES = {
    "practical": {
        "desc": "short, actionable, for busy readers",
        "temperature": 0.5,
    },
    "technical": {
        "desc": "detailed, assumes technical audience",
        "temperature": 0.4,
    },
    "authoritative": {
        "desc": "confident, expert tone",
        "temperature": 0.3,
    },
    "friendly": {
        "desc": "conversational, helpful",
        "temperature": 0.7,
    },
}

def load_topics_from_csv(path: str):
    """
    Parse a CSV file of briefs into a normalized list of topic dicts.
    """
    topics = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            topics.append({
                "title": row.get("title", "").strip(),
                "keywords": [k.strip() for k in row.get("keywords", "").split(",") if k.strip()],
                "tone": row.get("tone", "practical").strip(),
            })
    return topics

def load_topics_from_json(path: str):
    """
    Lightweight wrapper that keeps JSON topic inputs consistent.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def make_slug(title: str) -> str:
    """Create a URL-friendly slug with minimal assumptions."""
    return (
        title.lower()
        .replace(" ", "-")
        .replace("/", "-")
        .replace("--", "-")
    )

def build_outline(title: str, keywords: list[str]):
    """
    Provide a deterministic outline so draft builders know the expected sections.
    """
    return [
        {"heading": "Introduction", "notes": f"Explain why {title} matters."},
        {"heading": "Key Concepts", "notes": "Define core ideas; relate to WordPress + automation if relevant."},
        {"heading": "Step-by-step / Framework", "notes": "Actionable steps the reader can follow."},
        {"heading": "SEO / Practical Tips", "notes": f"Include keywords: {', '.join(keywords)}"},
        {"heading": "Conclusion / CTA", "notes": "Summarize and invite to read more posts."},
    ]

def build_draft(topic: dict):
    """
    Produce a JSON-ready draft skeleton that downstream stages can enrich.
    """
    title = topic["title"]
    keywords = topic.get("keywords", [])
    tone = topic.get("tone", "practical")
    tone_info = TONES.get(tone, TONES["practical"])
    slug = make_slug(title)

    outline = build_outline(title, keywords)

    draft = {
        "title": title,
        "slug": slug,
        "tone": tone,
        "tone_meta": tone_info,
        "keywords": keywords,
        "outline": outline,
        "sections": [
            {
                "id": "intro",
                "heading": "Introduction",
                "body": f"{title} is an important topic for creators who want to automate and scale. This article explains it in a {tone} tone.",
            },
            {
                "id": "body",
                "heading": "Main Content",
                "body": "Expand each outline point into 2–4 paragraphs. Add examples that fit WordPress.com and AI automation.",
            },
            {
                "id": "cta",
                "heading": "Next Steps",
                "body": "Add a CTA to explore related posts or to try the orchestrator.",
            },
        ],
        # SEO hook placeholder – Phase 5 will enrich this
        "seo": {
            "primary_keyword": keywords[0] if keywords else "",
            "secondary_keywords": keywords[1:] if len(keywords) > 1 else [],
        },
        "created_at": datetime.utcnow().isoformat() + "Z",
        "status": "draft-generated",
        "source": "content_brain",
    }
    return draft

def save_draft(draft: dict, out_dir: str = "data/drafts"):
    """
    Persist the generated draft to disk and return the absolute path.
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    slug = draft["slug"]
    out_path = Path(out_dir) / f"{slug}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(draft, f, ensure_ascii=False, indent=2)
    return str(out_path)
