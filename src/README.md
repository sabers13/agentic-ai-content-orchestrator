# Agentic AI Content Orchestrator

Generates, scores, and publishes articles to a WordPress blog (WordPress.com or self-hosted) using an agentic pipeline with Prefect orchestration.

## Features (planned)
- Content Brain (topics, tone selector, structured drafts, SEO hooks)
- Quality Agent (readability, relevance, plagiarism-lite, SEO gate)
- Publisher Agent (basic) → WordPress REST
- Orchestrator (Prefect) → visual flow, retries, schedule
- Dashboard (Streamlit) → pipeline view, scores, model matchup
- SEO Optimizer, LLM comparison, CI/CD

## Getting Started
1. `python3 -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. copy `.env.example` → `.env` and fill your values
4. `python -m src.main`

## Repo Structure
- `src/content_brain`
- `src/quality_agent`
- `src/publisher`
- `src/orchestrator`
- `src/dashboard`
- `src/common`
- `docs/`
- `data/`
- `logs/`
