"""
Streamlit dashboard that surfaces pipeline health, runs, and published posts.
"""
import json
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path("data/runs.sqlite")
FINAL_DIR = Path("data/final")

import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.common.config import settings

st.set_page_config(
    page_title="AI Content Orchestrator Dashboard",
    layout="wide",
)

st.title("📊 AI Content Orchestrator — Pipeline Dashboard")

# Simple health panel
st.sidebar.header("Health")
st.sidebar.success("SQLite OK" if DB_PATH.exists() else "SQLite missing")
st.sidebar.success("Final dir OK" if FINAL_DIR.exists() else "Final dir missing")

# SLO indicators derived from final drafts
seo_scores = []
quality_scores = []
if FINAL_DIR.exists():
    for p in FINAL_DIR.glob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        seo_val = data.get("seo_score")
        if isinstance(seo_val, (int, float)):
            seo_scores.append(seo_val)
        qm = data.get("quality_meta") or {}
        qs = qm.get("quality_score") if isinstance(qm, dict) else None
        if isinstance(qs, (int, float)):
            quality_scores.append(qs)

seo_avg = sum(seo_scores) / len(seo_scores) if seo_scores else None
quality_avg = sum(quality_scores) / len(quality_scores) if quality_scores else None

col_a, col_b = st.columns(2)
seo_ok = seo_avg is not None and seo_avg >= settings.SEO_THRESHOLD
quality_ok = quality_avg is not None and quality_avg >= settings.QUALITY_THRESHOLD
col_a.metric(
    "SEO SLO",
    f"{seo_avg:.1f}" if seo_avg is not None else "—",
    "✅" if seo_ok else "⚠️",
)
col_b.metric(
    "Quality SLO",
    f"{quality_avg:.1f}" if quality_avg is not None else "—",
    "✅" if quality_ok else "⚠️",
)

conn = None
if DB_PATH.exists():
    conn = sqlite3.connect(DB_PATH)
else:
    st.warning("No data/runs.sqlite found yet. Run a flow or LLM compare first.")

# --- LLM runs tab ---
st.subheader("🧠 LLM Comparison Runs")
llm_df = pd.DataFrame()
if conn is not None:
    try:
        llm_df = pd.read_sql_query("SELECT * FROM llm_runs ORDER BY id DESC LIMIT 50;", conn)
    except Exception:
        st.info("No llm_runs table yet. Trigger an LLM comparison to create it.")

if llm_df.empty:
    st.info("No LLM runs logged yet.")
else:
    llm_df = llm_df.copy()
    llm_df["brief_display"] = (
        llm_df["brief"]
        .astype(str)
        .str.strip()
        .replace({"nan": ""})
    )
    briefs = sorted({b for b in llm_df["brief_display"].tolist() if b})
    options = ["<all>"] + briefs
    selected_brief = st.selectbox("Filter by brief", options)
    filtered_df = llm_df
    if selected_brief != "<all>":
        filtered_df = llm_df[llm_df["brief_display"] == selected_brief]

    if filtered_df.empty:
        st.info("No runs match the selected brief.")
    else:
        filtered_df = filtered_df.copy()
        filtered_df["model_pair"] = filtered_df["model_a"] + " vs " + filtered_df["model_b"]
        st.dataframe(
            filtered_df[
                [
                    "id",
                    "created_at",
                    "brief_display",
                    "model_pair",
                    "winner",
                    "model_a_latency_ms",
                    "model_b_latency_ms",
                    "model_a_cost_usd",
                    "model_b_cost_usd",
                ]
            ]
        )

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total LLM runs", len(filtered_df))
        col2.metric(
            "Avg model A latency (ms)", f"{filtered_df['model_a_latency_ms'].mean():.0f}"
        )
        col3.metric(
            "Avg model B latency (ms)", f"{filtered_df['model_b_latency_ms'].mean():.0f}"
        )
        latest = filtered_df.iloc[0]
        col4.metric(
            "Latest run latency (ms)",
            f"A: {latest['model_a_latency_ms']} | B: {latest['model_b_latency_ms']}",
            help=f"Run ID {latest['id']} at {latest['created_at']}",
        )
        filtered_df.rename(columns={"brief_display": "brief"}, inplace=True)

st.markdown("---")

# --- Published posts tab ---
st.subheader("📰 Published Posts (WordPress.com)")
published_df = pd.DataFrame()
if conn is not None:
    try:
        published_df = pd.read_sql_query(
            "SELECT * FROM published_posts ORDER BY id DESC LIMIT 50;", conn
        )
    except Exception:
        st.info("No published_posts table yet. Publish once to create it.")

if not published_df.empty:
    st.dataframe(
        published_df[["id", "created_at", "title", "wp_link", "slug", "source_file"]]
    )
    for _, row in published_df.iterrows():
        st.markdown(f"- [{row['title']}]({row['wp_link']}) ({row['created_at']})")
else:
    st.write("No published posts logged.")

st.markdown("---")

# --- Recent finals from data/final ---
st.subheader("✅ Recently Approved Drafts")
if FINAL_DIR.exists():
    files = sorted(
        FINAL_DIR.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for p in files[:10]:
        data = json.loads(p.read_text(encoding="utf-8"))
        title = data.get("title", p.name)
        seo = data.get("seo_score", "—")
        qm = data.get("quality_meta", {})
        qs = qm.get("quality_score", "—")
        st.markdown(f"**{title}** — SEO: {seo}, Quality: {qs}  \n`{p}`")
else:
    st.write("No data/final/ directory yet.")

if conn is not None:
    conn.close()
