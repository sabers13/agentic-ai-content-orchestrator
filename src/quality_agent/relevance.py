# src/quality_agent/relevance.py
import re
from collections import Counter
import math

def _normalize(text: str):
    return re.findall(r"[a-zA-Z0-9]+", text.lower())

def _cosine(a: Counter, b: Counter) -> float:
    common = set(a.keys()) & set(b.keys())
    num = sum(a[t] * b[t] for t in common)
    den_a = math.sqrt(sum(v*v for v in a.values()))
    den_b = math.sqrt(sum(v*v for v in b.values()))
    if den_a == 0 or den_b == 0:
        return 0.0
    return num / (den_a * den_b)

def relevance_score(brief: str, content: str) -> float:
    """
    Hybrid relevance:
    1) keyword coverage from brief
    2) cosine fallback
    returns 0-100
    """
    brief_tokens = _normalize(brief)
    content_tokens = _normalize(content)

    if not brief_tokens or not content_tokens:
        return 0.0

    # 1) keyword coverage: how many brief words appear in content
    content_set = set(content_tokens)
    covered = sum(1 for t in brief_tokens if t in content_set)
    coverage_ratio = covered / len(brief_tokens)  # 0..1

    # 2) cosine (light)
    vec_brief = Counter(brief_tokens)
    vec_content = Counter(content_tokens)
    cos = _cosine(vec_brief, vec_content)  # 0..1

    # weight: coverage is more important for short briefs
    score = (coverage_ratio * 0.7 + cos * 0.3) * 100.0
    return score
