# src/llm_compare/evaluator.py
import time
from datetime import datetime
from textwrap import dedent
from typing import Dict, Optional

from openai import OpenAI

from src.common.config import settings
from src.llm_compare.models import LLMComparisonResult, LLMRunResult

MODEL_COST_PER_1K = {
    "gpt-5o-mini": 0.15,
    "gpt-5o": 5.00,
}
TONE_HINTS = {
    "practical": "direct, concise, action-oriented for busy operators",
    "technical": "precise, detail-heavy, assumes reader familiarity with developer tooling",
    "authoritative": "confident, expert voice with decisive recommendations",
    "friendly": "approachable, conversational, encouraging tone",
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    rate = MODEL_COST_PER_1K.get(model, 0.15)
    total_tokens = input_tokens + output_tokens
    return (total_tokens / 1000.0) * rate


def call_model(client: OpenAI, model: str, prompt: str) -> LLMRunResult:
    start = time.time()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    latency_ms = int((time.time() - start) * 1000)
    content = response.choices[0].message.content

    usage = getattr(response, "usage", None)
    input_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
    output_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
    cost_usd = estimate_cost(model, input_tokens, output_tokens)

    return LLMRunResult(
        model=model,
        prompt=prompt,
        output=content,
        latency_ms=latency_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
    )


def _heuristic_score(text: str) -> Dict[str, float]:
    length = len(text.split())
    clarity = 85 if length > 120 else 70
    coverage = 85 if "##" in text else 60
    return {
        "clarity": clarity,
        "coverage": coverage,
        "factuality": 80,
        "seo": 75,
        "tone": 75,
    }


def _tone_instruction(tone: Optional[str]) -> str:
    if not tone:
        return "Use a confident, helpful editorial tone that balances expertise with clarity."

    normalized = tone.strip().lower()
    descriptor = TONE_HINTS.get(normalized)
    if descriptor:
        return f"Adopt a {normalized} tone ({descriptor})."
    return f"Adopt a {tone.strip()} tone that fits modern WordPress.com editorial."


def compare_models(
    brief: str,
    model_a: str,
    model_b: str,
    tone: Optional[str] = None,
) -> LLMComparisonResult:
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing; set it before running comparisons.")

    client = OpenAI(api_key=api_key)

    tone_line = _tone_instruction(tone)

    prompt = dedent(
        f"""You are generating a WordPress.com-ready blog draft in **Markdown**.
The downstream formatter will **strip your TOC and rebuild it**, so follow this format exactly.
Topic/brief: {brief}
Tone guidance: {tone_line}

STRUCTURE RULES (very important):
1. Start with a "Table of Contents" heading (plain text, no `#`) followed immediately by a bulleted list.
2. Each bullet must link to a section that appears later, e.g. `- [Introduction](#introduction)`.
3. Use ONLY these heading levels in the body:
   - `##` for main sections (H2 logical level)
   - `###` for sub-sections (H3 logical level)
   - never output literal strings like `H2:` or `H3:`; always convert them to markdown headings instead.
4. Order of sections must be: Introduction → 3–4 main sections → Conclusion → FAQs.
5. In the **FAQs** section:
   - add a `## FAQs` heading
   - each question is a bold sentence in a paragraph, e.g. `**Can I use X?**`
   - the answer is the paragraph right after it
   - do NOT use headings for individual FAQ questions

HARD VALIDATION RULES (your output will be rejected if you break these):
- Do NOT output lines that start with `H1:`, `H2:`, or `H3:`.
- The string "Table of Contents" must come before `## Introduction`.
- All actual headings must be either `## ...` or `### ...`.
- `## FAQs` must be the last main section, after `## Conclusion`.

Example start (adapt titles to the topic):
Table of Contents
- [Introduction](#introduction)
- [Key Strategies](#key-strategies)
- [Conclusion](#conclusion)
- [FAQs](#faqs)

## Introduction
...content...

Return ONLY the markdown, no explanation."""
    )

    run_a = call_model(client, model_a, prompt)
    run_b = call_model(client, model_b, prompt)

    scores_a = _heuristic_score(run_a.output)
    scores_b = _heuristic_score(run_b.output)
    avg_a = sum(scores_a.values()) / len(scores_a)
    avg_b = sum(scores_b.values()) / len(scores_b)

    winner = model_a if avg_a >= avg_b else model_b

    scores = {f"model_a_{key}": value for key, value in scores_a.items()}
    scores.update({f"model_b_{key}": value for key, value in scores_b.items()})

    return LLMComparisonResult(
        brief=brief,
        model_a=run_a,
        model_b=run_b,
        scores=scores,
        winner=winner,
        created_at=datetime.utcnow().isoformat(),
        extra={"avg_a": avg_a, "avg_b": avg_b},
    )
