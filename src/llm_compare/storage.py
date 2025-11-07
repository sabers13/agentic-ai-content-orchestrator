# src/llm_compare/storage.py
import os
import json
import sqlite3
from typing import Any
from pathlib import Path

from src.llm_compare.models import LLMComparisonResult

DB_PATH = Path("data/runs.sqlite")
RUNS_DIR = Path("data/runs")

SCHEMA = """
CREATE TABLE IF NOT EXISTS llm_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    brief TEXT NOT NULL,
    model_a TEXT NOT NULL,
    model_b TEXT NOT NULL,
    winner TEXT NOT NULL,
    model_a_latency_ms INTEGER,
    model_b_latency_ms INTEGER,
    model_a_cost_usd REAL,
    model_b_cost_usd REAL,
    model_a_avg_score REAL,
    model_b_avg_score REAL,
    raw_json TEXT NOT NULL
);
"""

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(SCHEMA)
    conn.commit()
    conn.close()

def save_result(result: LLMComparisonResult):
    init_db()
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    # save json artifact
    fname = RUNS_DIR / f"llm_run_{result.created_at.replace(':','-')}.json"
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(_to_jsonable(result), f, indent=2, ensure_ascii=False)

    # save to sqlite
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO llm_runs (
            created_at, brief, model_a, model_b, winner,
            model_a_latency_ms, model_b_latency_ms,
            model_a_cost_usd, model_b_cost_usd,
            model_a_avg_score, model_b_avg_score,
            raw_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            result.created_at,
            result.brief,
            result.model_a.model,
            result.model_b.model,
            result.winner,
            result.model_a.latency_ms,
            result.model_b.latency_ms,
            result.model_a.cost_usd,
            result.model_b.cost_usd,
            result.extra.get("avg_a"),
            result.extra.get("avg_b"),
            json.dumps(_to_jsonable(result)),
        ),
    )
    conn.commit()
    conn.close()

def _to_jsonable(result: LLMComparisonResult) -> Any:
    return {
        "brief": result.brief,
        "created_at": result.created_at,
        "winner": result.winner,
        "scores": result.scores,
        "extra": result.extra,
        "model_a": {
            "model": result.model_a.model,
            "latency_ms": result.model_a.latency_ms,
            "cost_usd": result.model_a.cost_usd,
            "input_tokens": result.model_a.input_tokens,
            "output_tokens": result.model_a.output_tokens,
            "output": result.model_a.output,
        },
        "model_b": {
            "model": result.model_b.model,
            "latency_ms": result.model_b.latency_ms,
            "cost_usd": result.model_b.cost_usd,
            "input_tokens": result.model_b.input_tokens,
            "output_tokens": result.model_b.output_tokens,
            "output": result.model_b.output,
        },
    }
