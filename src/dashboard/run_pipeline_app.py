# src/dashboard/run_pipeline_app.py
"""
Streamlit front end for running the AI Content Orchestrator pipeline.
"""

import json
import sys
from pathlib import Path

import streamlit as st

# Ensure project root is on sys.path when run via `streamlit run`
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.orchestrator.tasks import task_generate_from_brief, task_quality_gate, task_publish
from src.common.config import settings


def run_pipeline(brief: str, model_a: str, model_b: str, auto_publish: bool, tone: str | None):
    """
    Execute the pipeline step by step, returning a summary dict.
    """
    status = {"steps": [], "status": "ready"}

    result_generate = task_generate_from_brief.fn(brief, model_a, model_b, tone)
    if isinstance(result_generate, str):
        optimized_path = result_generate
        metrics = {
            "model_a": model_a,
            "model_b": model_b,
            "tone": tone,
        }
    else:
        optimized_path = result_generate.get("path")
        metrics = {
            "model_a": model_a,
            "model_b": model_b,
            "winner": result_generate.get("winner"),
            "avg_a": result_generate.get("avg_a"),
            "avg_b": result_generate.get("avg_b"),
            "seo_score": result_generate.get("seo_score"),
            "quality_score": result_generate.get("quality_score"),
            "tone": tone,
        }
        status["steps"].append(("Draft generated", optimized_path, metrics))

    res_quality = task_quality_gate.fn(optimized_path)
    if isinstance(res_quality, str):
        final_path = res_quality
        quality_details = None
    else:
        final_path = res_quality["path"]
        quality_details = res_quality.get("quality_meta")
    if metrics is not None and quality_details:
        metrics["quality_score"] = quality_details.get("quality_score")
    status["steps"].append(("Passed quality gate", final_path, quality_details))

    if auto_publish:
        publish_details = task_publish.fn(final_path, status="publish")
        if isinstance(publish_details, dict):
            url = publish_details.get("url")
            publish_meta = publish_details
        else:
            url = publish_details
            publish_meta = {"url": url}
        status["steps"].append(("Published to WordPress.com", url, publish_meta))
        status["status"] = "published"
        status["url"] = url
    else:
        status["status"] = "ready"
        status["url"] = None

    status["final_path"] = final_path
    return status


def main():
    st.set_page_config(page_title="AI Content Orchestrator", page_icon="🧠", layout="centered")
    st.title("🧠 AI Content Orchestrator")
    st.write("Generate, review, and publish a WordPress.com post in a few clicks.")

    with st.form("run-orchestrator"):
        brief = st.text_input(
            "Content brief",
            value="AI content orchestrator for WordPress.com",
            help="Describe the topic or final title you want to publish.",
        )
        col1, col2 = st.columns(2)
        with col1:
            model_a = st.text_input("Primary model", value=settings.MODEL_PRIMARY)
        with col2:
            model_b = st.text_input("Secondary model", value=settings.MODEL_SECONDARY)
        tone_options = ["practical", "technical", "authoritative", "friendly", "custom"]
        tone_choice = st.selectbox(
            "Tone",
            tone_options,
            help="Select the writing voice to nudge the LLMs toward.",
            index=0,
        )
        tone_custom: str | None = None
        if tone_choice == "custom":
            tone_custom = st.text_input("Custom tone", value="", help="Describe the tone in your own words.")
        auto_publish = st.checkbox("Auto-publish to WordPress.com", value=True)

        submitted = st.form_submit_button("Run Pipeline 🚀")

    if submitted:
        if not brief.strip():
            st.error("Please provide a brief.")
            return

        if tone_choice == "custom":
            chosen_tone = tone_custom.strip() if tone_custom and tone_custom.strip() else None
        else:
            chosen_tone = tone_choice

        with st.status("Running orchestrator...", expanded=True) as status_box:
            try:
                result = run_pipeline(
                    brief.strip(),
                    model_a.strip(),
                    model_b.strip(),
                    auto_publish,
                    chosen_tone,
                )

                for step in result["steps"]:
                    if len(step) == 3:
                        label, value, meta = step
                    elif len(step) == 2:
                        label, value = step
                        meta = None
                    else:
                        label = step[0]
                        value = None
                        meta = None

                    if meta is None:
                        status_box.write(f"✅ {label}")
                        continue
                    if label == "Draft generated":
                        details = []
                        if meta.get("winner"):
                            details.append(f"winner: {meta['winner']}")
                        if meta.get("avg_a") is not None and meta.get("avg_b") is not None:
                            details.append(f"avg_a={meta['avg_a']:.1f}, avg_b={meta['avg_b']:.1f}")
                        if meta.get("seo_score") is not None:
                            details.append(f"initial_seo={meta['seo_score']}")
                        if meta.get("quality_score") is not None:
                            details.append(f"initial_quality={meta['quality_score']}")
                        if meta.get("tone"):
                            details.append(f"tone={meta['tone']}")
                        status_box.write(
                            "✅ Draft generated "
                            "(src/orchestrator/tasks.py::task_generate_from_brief) — "
                            f"{', '.join(details) if details else 'see JSON'}"
                        )
                    elif label == "Passed quality gate":
                        qm = meta or {}
                        status_box.write(
                            "✅ Passed quality gate "
                            "(src/orchestrator/tasks.py::task_quality_gate) "
                            f"(quality={qm.get('quality_score')}, "
                            f"readability={qm.get('readability')}, "
                            f"relevance={qm.get('relevance')}, "
                            f"plagiarism={qm.get('plagiarism')}%)"
                        )
                    elif label == "Published to WordPress.com":
                        status_box.write(
                            "✅ Published to WordPress.com "
                            "(src/orchestrator/tasks.py::task_publish) — "
                            f"{meta.get('url', 'success')} "
                            f"(wp_id={meta.get('wp_id')})"
                        )
                    else:
                        status_box.write(f"✅ {label}")

                status_box.update(label="Pipeline completed!", state="complete")
            except Exception as exc:
                status_box.update(label="Pipeline failed", state="error")
                st.exception(exc)
                return

        st.success("Pipeline finished successfully.")
        st.write(f"**Final draft:** `{result['final_path']}`")

        if result.get("url"):
            st.link_button("Open Published Post", result["url"])
        else:
            final_path = Path(result["final_path"])
            if final_path.exists():
                data = json.loads(final_path.read_text(encoding="utf-8"))
                st.json(data)


if __name__ == "__main__":
    main()
