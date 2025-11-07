# scripts/extract_winner_to_draft.py
import json
from pathlib import Path
import sys
import re

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text

def main(src_path: str, out_path: str = None):
    data = json.loads(Path(src_path).read_text(encoding="utf-8"))

    brief = data["brief"]
    winner = data["winner"]
    model_key = "model_a" if data["model_a"]["model"] == winner else "model_b"
    content = data[model_key]["output"]

    title = brief  # simple mapping
    slug = slugify(brief)

    draft = {
        "title": title,
        "slug": slug,
        "brief": brief,
        "content": content,
        # we can guess SEO from the comparison scores
        "seo_score": max(
            data["scores"].get("model_a_seo", 60),
            data["scores"].get("model_b_seo", 60),
        ),
        "source": "llm_compare",
    }

    if out_path is None:
        out_path = f"data/optimized/{slug}.json"

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(draft, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] wrote draft → {out_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/extract_winner_to_draft.py <llm_run.json> [out.json]")
        sys.exit(1)
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else None
    main(src, dst)
