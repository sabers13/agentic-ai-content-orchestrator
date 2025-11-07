# tests/test_smoke.py
import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def test_repo_structure():
    assert Path("src").exists()
    assert Path("data").exists()

def test_imports():
    # make sure our core modules import
    try:
        import src.llm_compare.evaluator  # noqa: F401
    except ModuleNotFoundError as exc:
        if exc.name == "openai":
            pytest.skip("openai package not installed")
        raise
    import src.quality_agent.quality_runner  # noqa: F401
    import src.publisher.wp_client  # noqa: F401
    import src.orchestrator.flows  # noqa: F401

def test_quality_runner_on_sample():
    # minimal fixture
    from src.quality_agent.quality_runner import evaluate_draft
    draft = {
        "title": "Test",
        "brief": "Test brief",
        "content": "This is a short test content about WordPress AI.",
        "seo_score": 75,
    }
    res = evaluate_draft(draft)
    assert "quality_score" in res
