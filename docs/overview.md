# Agentic AI Content Orchestrator — One-Page Plan

**Goal:** Generate, score, and publish articles to WordPress on `blog.<domain>` via REST, orchestrated with Prefect, tracked in a dashboard.

## Architecture Modules
- content_brain · seo_optimizer · llm_compare · quality_agent · publisher · orchestrator (Prefect) · dashboard · common

## Data Flow
```mermaid
flowchart LR
  A[Topics] --> B(Content Brain)
  B --> C(SEO Optimizer)
  B --> D1(Model A) & D2(Model B)
  D1 & D2 --> E(LLM Comparison)
  E --> F(Quality Agent)
  F -->|pass| G(Publisher) --> H(WordPress)
  F -->|fail| I[Hold & Log]
  subgraph Orchestration
    J[Prefect Flow + Schedule]
  end
  J --> B --> C --> E --> F --> G
  H --> K(Dashboard)
