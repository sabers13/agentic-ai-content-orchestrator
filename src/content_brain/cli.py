# src/content_brain/cli.py
import json
from pathlib import Path
import typer
from . import seo_optimizer
from pathlib import Path


from .generator import (
    load_topics_from_csv,
    load_topics_from_json,
    build_draft,
    save_draft,
)

app = typer.Typer(help="Content Brain – generate structured drafts from topics.")


@app.command("from-file")
def generate_from_file(
    path: str = typer.Argument(..., help="Path to CSV or JSON topics file"),
    limit: int = typer.Option(0, help="Generate only N drafts (0=all)"),
):
    """Load topics from CSV or JSON and generate drafts."""
    p = Path(path)
    if not p.exists():
        typer.echo(f"❌ File not found: {path}")
        raise typer.Exit(code=1)

    topics = []
    if p.suffix.lower() == ".csv":
        topics = load_topics_from_csv(str(p))
    elif p.suffix.lower() == ".json":
        topics = load_topics_from_json(str(p))
    else:
        typer.echo("❌ Unsupported file format. Use .csv or .json")
        raise typer.Exit(code=1)

    count = 0
    for topic in topics:
        draft = build_draft(topic)
        out = save_draft(draft)
        typer.echo(f"✓ Draft saved -> {out}")
        count += 1
        if limit and count >= limit:
            break


@app.command("from_file")
def from_file_deprecated(
    path: str = typer.Argument(None),
    limit: int = typer.Option(
        None,
        help="Deprecated command renamed to from-file; this option is ignored.",
    ),
):
    """Friendly message for legacy command name with underscore."""
    message = (
        "Command renamed to 'from-file'. Please rerun as:\n"
        "python -m src.content_brain.cli from-file <path> [--limit N]"
    )
    typer.echo(message)
    raise typer.Exit(code=1)


@app.command("sample")
def sample():
    """Generate a single sample draft."""
    topic = {
        "title": "Sample AI Content Orchestrator Post",
        "keywords": ["ai", "wordpress", "automation"],
        "tone": "practical",
    }
    draft = build_draft(topic)
    out = save_draft(draft)
    typer.echo(f"✓ Draft saved -> {out}")
    typer.echo(json.dumps(draft, indent=2))

@app.command("seo-all")
def seo_all(
    src_dir: str = typer.Argument("data/drafts", help="Directory of generated drafts"),
    out_dir: str = typer.Argument("data/optimized", help="Where to save optimized drafts"),
):
    """Run SEO optimizer on all draft JSON files."""
    src_path = Path(src_dir)
    if not src_path.exists():
        typer.echo(f"❌ Source dir not found: {src_dir}")
        raise typer.Exit(code=1)

    for f in src_path.glob("*.json"):
        draft = seo_optimizer.load_draft(str(f))
        draft = seo_optimizer.optimize_draft(draft)
        out = seo_optimizer.save_optimized(draft, out_dir=out_dir)
        typer.echo(f"✓ SEO optimized -> {out}")

if __name__ == "__main__":
    app()
