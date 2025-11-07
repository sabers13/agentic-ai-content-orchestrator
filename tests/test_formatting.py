import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


from src.publisher.formatting import (
    ensure_markdown_toc,
    extract_introduction_excerpt,
    render_html,
)


def test_normalizes_h2_labels_and_makes_heading():
    src = "H2: Introduction\nThis is intro."
    html = render_html(src, post_title="Demo")
    assert '<h3 id="introduction">' in html


def test_injects_toc_when_missing():
    src = "## Intro\nText\n### Sub\nMore"
    html = render_html(src, post_title="Demo")
    assert "<h3>Table of Contents</h3>" in html
    assert '<li><a href="#intro">Intro</a>' in html
    assert '<ul>' in html
    assert '<li><a href="#sub">Sub</a></li>' in html


def test_faq_questions_are_bold_not_heading():
    src = "## FAQs\nWhat is this?\nThis is an answer."
    html = render_html(src, post_title="Demo")
    assert "<h4>FAQs</h4>" in html
    assert "<strong>What is this?</strong>" in html
    assert "<h3>What is this?" not in html


def test_title_like_lines_become_h2():
    src = """Computer 101

Introduction
Computers power everything.

What Is a Computer?
It is a device...
"""
    html = render_html(src, post_title="Computer 101")
    assert '<h3 id="what-is-a-computer">What Is a Computer?</h3>' in html


def test_toc_handles_promoted_headings():
    src = """Introduction
Text

Hardware vs. Software
Details
"""
    html = render_html(src, post_title="Computer 101")
    assert "<h3>Table of Contents</h3>" in html
    assert '<li><a href="#introduction">Introduction</a>' in html
    assert '<li><a href="#hardware-vs-software">Hardware vs. Software</a></li>' in html


def test_h2_h3_labels_are_converted():
    src = "  H2: Benefits and Limitations\nh3 - Benefits\n- Speed"
    html = render_html(src, post_title="Content Creation with AI")
    assert '<h3 id="benefits-and-limitations">' in html
    assert '<h4 id="benefits">' in html
    assert "<li>Speed</li>" in html


def test_intro_keyword_promoted():
    src = "Intro\nThis is the beginning."
    html = render_html(src, post_title="Content Creation with AI")
    assert '<h3 id="intro">' in html
    assert "Table of Contents" in html


def test_preamble_is_removed_before_toc():
    src = """Title: Foo
Proposed SEO title: Foo
Proposed meta description: Bar
Suggested slug: foo
Excerpt: short summary

Introduction
Body
## Next
### Child
"""
    html = render_html(src, post_title="Foo")
    assert "Proposed SEO title" not in html
    assert html.startswith("<h3>Table of Contents</h3>")
    assert '<a href="#child">' in html


def test_markdown_h3_outputs_h4():
    src = "## Parent\n### Child"
    html = render_html(src, post_title="Something Else")
    assert '<h3 id="parent">' in html
    assert '<h4 id="child">' in html


def test_intro_contributes_to_toc():
    src = "Intro\nBody text\n\nMain Section\nDetails"
    html = render_html(src, post_title="Trip")
    assert "<h3>Table of Contents</h3>" in html
    assert '<li><a href="#intro">Intro</a>' in html
    assert '<li><a href="#main-section">Main Section</a></li>' in html


def test_title_after_h2_demoted_to_subheading():
    src = "Main Section\n\nSub Topic\nMore details."
    html = render_html(src, post_title="Trip")
    assert '<h3 id="main-section">' in html
    assert '<h4 id="sub-topic">' in html


def test_optional_seo_tail_removed():
    src = """Main Content
Details go here.

Optional SEO Enhancements for WordPress
Add more keywords."""
    html = render_html(src, post_title="Trip")
    assert "Optional SEO Enhancements" not in html


def test_ensure_markdown_toc_adds_missing_toc():
    src = """Intro
Welcome text.

## Main Section
Content

### Details
More info

## Conclusion
Wrap up

## FAQs
**Q1?**
Answer.
"""
    markdown = ensure_markdown_toc(src)
    assert "Table of Contents" not in markdown
    assert markdown.splitlines()[0] == "Intro"
    assert "## Main Section" in markdown
    assert "### Details" in markdown


def test_ensure_markdown_toc_keeps_existing():
    src = """Table of Contents
- [Intro](#intro)

## Intro
Body text
"""
    markdown = ensure_markdown_toc(src)
    assert "Table of Contents" not in markdown
    assert markdown.startswith("## Intro")


def test_ensure_markdown_toc_strips_preface():
    src = """Title: Sample
Proposed SEO title: Sample

Introduction
Body text
"""
    markdown = ensure_markdown_toc(src)
    assert "Table of Contents" not in markdown
    assert markdown.startswith("Introduction")
    assert "Proposed SEO title" not in markdown


def test_extract_introduction_excerpt_strips_markdown():
    src = """## Table of Contents
- [Intro](#introduction)

## Introduction
Welcome to **AI tools** for [marketing](https://example.com).

- Bullet insight

## Main Section
Body text
"""
    excerpt = extract_introduction_excerpt(src)
    assert excerpt == "Welcome to AI tools for marketing. Bullet insight"


def test_extract_introduction_excerpt_missing_heading_returns_blank():
    src = """## Table of Contents
- [Intro](#intro)

## Overview
Text
"""
    assert extract_introduction_excerpt(src) == ""
