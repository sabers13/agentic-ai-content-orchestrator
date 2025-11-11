# 🧠 Agentic AI Content Workflow Engine

End-to-end system that compares LLMs, enforces content quality, and publishes winning drafts directly to WordPress.com. Built with Prefect flows, modular agents, and Streamlit dashboards so you can run the entire pipeline locally, in Docker, or on Prefect Cloud.

---

## Overview

- **A/B content generation** – `llm_compare` runs dual-model prompts (e.g., `gpt-5o` vs `gpt-5o-mini`) and stores structured telemetry.
- **Quality agent guardrails** – readability, SEO, relevance, and plagiarism gates with optional auto-revisions using GPT.
- **Publisher automation** – Markdown normalization, HTML rendering, and WordPress.com REST publishing with logging into SQLite.
- **Observability** – Streamlit dashboard (`src/dashboard/app.py`) surfaces service-level indicators, recent runs, and published posts.
- **Interactive runner** – `src/dashboard/run_pipeline_app.py` lets non-technical users walk through each pipeline step and open the resulting post.

---

## Core Architecture

```text
brief/topic
   │
   ├── llm_compare (src/llm_compare) ──> winner draft JSON in data/optimized/
   │       │
   │       └── metrics logged to SQLite (llm_runs table)
   │
   ├── quality_agent (src/quality_agent) ──> approves/revises into data/final/
   │
   ├── publisher (src/publisher)
   │       ├── formatting helpers → sanitized HTML
   │       └── wp_client → WordPress.com REST API + data/runs.sqlite (published_posts)
   │
   └── dashboards (src/dashboard) + Prefect flows (src/workflow engine)
```

Key flows live in `src/workflow engine/flows.py`:

- `ai-content-workflow engine` – generate → quality gate → publish (optional)
- `post-engagement-telemetry` – pulls view counts via WordPress Stats API for recent posts

---

## Repository Layout

```text
src/
├── common/            # shared config + helpers
├── content_brain/     # topic ingestion + outline/SEO helpers
├── llm_compare/       # model abstractions, evaluator, storage
├── workflow engine/      # Prefect flows + tasks
├── publisher/         # formatting, WordPress clients, storage
├── quality_agent/     # readability/relevance/plagiarism scoring
└── dashboard/         # Streamlit dashboard + pipeline runner UI
data/
├── topics/            # CSV/JSON topic briefs
├── drafts/, optimized/, final/  # pipeline artifacts
└── runs.sqlite        # central SQLite log (llm_runs, published_posts, post_views)
tests/                 # pytest suites (formatting, smoke, etc.)
```

---

## Getting Started

1. **Install system deps**
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Configure environment**
   - Copy `.env.example` → `.env`
   - Populate:
     - `OPENAI_API_KEY`
     - `WP_DOTCOM_BEARER` and `WP_DOTCOM_SITE`
     - `MODEL_PRIMARY`, `MODEL_SECONDARY`, quality thresholds, etc.
3. **Initialize data dirs**
   ```bash
   mkdir -p data/{drafts,optimized,final,runs} logs
   ```

---

## Running the Pipeline

### Prefect CLI
```bash
python -m src.workflow engine.flows --brief "AI content workflow engine for WordPress.com" \
    --model-a gpt-5o --model-b gpt-5o-mini --auto-publish true --tone practical
```
Add `--tone friendly` (or any descriptor) to nudge both models toward that writing voice.

### Streamlit dashboard
```bash
streamlit run src/dashboard/app.py
```
Shows SLO indicators, LLM runs, published posts, and the latest `data/final` artifacts.

### Guided pipeline runner
```bash
streamlit run src/dashboard/run_pipeline_app.py
```
Walks through each stage interactively, surfaces metrics, and links to the published post when auto-publish is on. Includes a tone selector plus custom text box so editors can enforce voice guidance without touching code.

---

## Configuration Notes

| Variable | Purpose |
|----------|---------|
| `MODEL_PRIMARY` / `MODEL_SECONDARY` | Names of the two models compared in `llm_compare`. |
| `Tone (runtime)` | Select via CLI `--tone` flag or Streamlit dropdown; omitted values default to a confident editorial voice. |
| `QUALITY_THRESHOLD`, `SEO_THRESHOLD` | Targets for dashboard SLO badges and gating. |
| `WP_DOTCOM_API_BASE`, `WP_DOTCOM_SITE` | WordPress REST endpoint and site handle. |
| `PREFECT_API_URL` | Set to empty (`""`) for local/Docker runs to avoid Prefect Cloud lookups. |

Place overrides in `.env`, or export them in your shell before running Prefect/Streamlit.

---

## Data & Storage

- **Artifacts:** JSON drafts live under `data/drafts`, `data/optimized`, `data/final`.
- **SQLite:** `data/runs.sqlite` contains:
  - `llm_runs` – metadata/telemetry for each comparison run.
  - `published_posts` – WordPress IDs, URLs, source file, timestamps.
  - `post_views` – optional engagement telemetry (Phase 15 enhancement).
- **Topics:** seed briefs in `data/topics/demo_topics.csv` or add your own CSV/JSON via `src/content_brain/generator.py`.

---

## Testing

Run targeted suites (example: formatting guardrails):
```bash
pytest tests/test_formatting.py
```
Or execute the full smoke tests before deployments:
```bash
pytest tests/test_smoke.py
```

---

## Troubleshooting

| Issue | Likely Fix |
|-------|------------|
| 401/403 from WordPress.com | Re-check `WP_DOTCOM_BEARER` token and `WP_DOTCOM_API_BASE`. |
| Draft rejected by quality gate | Lower `QUALITY_THRESHOLD` temporarily or run `scripts/simplify_draft.py` to trim the content. |
| Prefect API connection refused | Set `PREFECT_API_URL=""` in `.env` or Dockerfile to keep runs local. |
| Dashboard shows no data | Trigger at least one LLM compare run to create `data/runs.sqlite` tables. |
| Tags not visible on published posts | Some WordPress themes hide them; confirm via the WordPress editor. |

See `docs/TROUBLESHOOTING.md` for deeper fixes.

---

## Demo Run Snapshot (2025‑11‑05)

| Stage | Result | Artifact / Link |
|-------|--------|-----------------|
| LLM Compare | ✅ Winner: `gpt-5` | `data/runs/2025-11-05-gpt5.json` |
| Quality Agent | ✅ Quality 79.68 / SEO 75 | `data/final/ai-content-workflow engine-for-wordpress-com.json` |
| Publisher | ✅ Published | [View post](https://sabersojudi.wordpress.com/2025/11/05/ai-content-workflow engine-for-wordpress-com/) |
| Logging | ✅ Inserted | `data/runs.sqlite` → `published_posts` |

**Metrics:** Quality 79.68 · SEO 75 · Readability 51.49 · Relevance 80.52 · Plagiarism 0%  
**Latency:** LLM ~105 s · Total pipeline ~2 min 10 s  
**Environment:** WSL Ubuntu 22.04, Python 3.10 (venv)

---

## Roadmap Highlights

- Engagement telemetry flow + `post_views` table for daily stats.
- Title experimentation scaffold ready in `src/workflow engine/flows.py`.
- SLO indicators in Streamlit UI tied to `SEO_THRESHOLD` / `QUALITY_THRESHOLD`.

Contributions and experiments welcome—open an issue or PR describing the scenario you’re targeting.
