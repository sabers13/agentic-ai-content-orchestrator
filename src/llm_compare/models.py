# src/llm_compare/models.py
from dataclasses import dataclass
from typing import Optional, Dict, Any
import time

@dataclass
class LLMRunResult:
    model: str
    prompt: str
    output: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    cost_usd: float

@dataclass
class LLMComparisonResult:
    brief: str
    model_a: LLMRunResult
    model_b: LLMRunResult
    scores: Dict[str, float]  # clarity, coverage, factuality, seo, tone
    winner: str               # model name
    created_at: str           # isoformat
    extra: Dict[str, Any]
