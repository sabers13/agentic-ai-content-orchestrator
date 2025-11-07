# src/quality_agent/plagiarism.py
from pathlib import Path

def _ngrams(tokens, n=5):
    return {" ".join(tokens[i:i+n]) for i in range(len(tokens)-n+1)}

def load_existing_texts(final_dir: str = "data/final"):
    base = Path(final_dir)
    if not base.exists():
        return []
    texts = []
    for p in base.glob("*.json"):
        try:
            import json
            data = json.loads(p.read_text(encoding="utf-8"))
            texts.append(data.get("content", ""))
        except Exception:
            continue
    return texts

def plagiarism_score(content: str, final_dir: str = "data/final") -> float:
    """
    Returns % of ngrams that collide with existing ones.
    Lower is better.
    """
    tokens = content.split()
    this_ngrams = _ngrams(tokens, n=5)
    if not this_ngrams:
        return 0.0

    existing_texts = load_existing_texts(final_dir)
    existing_ngrams = set()
    for txt in existing_texts:
        existing_ngrams |= _ngrams(txt.split(), n=5)

    if not existing_ngrams:
        return 0.0

    overlap = this_ngrams & existing_ngrams
    return len(overlap) / len(this_ngrams) * 100.0
