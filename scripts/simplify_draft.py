# scripts/simplify_draft.py
import json
from pathlib import Path
import textwrap
import sys
import re

def split_paragraphs(text: str):
    paras = [p.strip() for p in text.split("\n") if p.strip()]
    return paras

def shorten_sentence(sent: str, limit=22):
    words = sent.split()
    if len(words) <= limit:
        return sent
    return " ".join(words[:limit]) + "..."

def simplify_content(content: str) -> str:
    paras = split_paragraphs(content)
    new_paras = []
    for p in paras:
        # split on . ! ?
        parts = re.split(r'(?<=[.!?])\s+', p)
        short_parts = [shorten_sentence(s.strip()) for s in parts if s.strip()]
        new_paras.append(" ".join(short_parts))
    return "\n\n".join(new_paras)

def main(src, dst=None):
    data = json.loads(Path(src).read_text(encoding="utf-8"))
    content = data.get("content", "")
    brief = data.get("brief", "")

    simplified = simplify_content(content)

    # add a short intro to help relevance/seo
    intro = f"## Overview\nThis article explains: {brief}.\n"
    final_content = intro + "\n" + simplified

    data["content"] = final_content

    if dst is None:
        dst = src.replace(".json", ".simplified.json")

    Path(dst).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] wrote simplified draft → {dst}")

if __name__ == "__main__":
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else None
    main(src, dst)
