# src/publisher/formatting.py
"""
Clean LLM markdown into consistent, WordPress-friendly HTML.
- Ensures <h3>/<h4> hierarchy (main/sub headings)
- Auto-generates exactly one Table of Contents
- Keeps only h3/h4/p/ul/li/strong
"""

from __future__ import annotations
import re
from html import escape
from typing import List, Tuple

import markdown as md
from bs4 import BeautifulSoup

PLAIN_BULLET_RE = re.compile(r"^(?:[-*•\u2013\u2014])\s+(.+)$")
MD_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
INTRO_HEADING_RE = re.compile(r"^##\s+introduction\b.*$", re.IGNORECASE | re.MULTILINE)
NEXT_SECTION_RE = re.compile(r"^\s*##\s+", re.IGNORECASE | re.MULTILINE)
SECTION_KEYWORDS = {"introduction", "conclusion"}
PREFACE_PREFIXES = (
    "title:",
    "proposed seo title:",
    "proposed seo",
    "meta description",
    "proposed meta description",
    "suggested slug",
    "excerpt",
    "seo enhancements",
)
FAQ_KEYWORDS = {"faq", "faqs", "frequently asked questions"}
TOC_MARKERS = {"table of contents", "toc"}
OPTIONAL_TAIL_PREFIXES = (
    "optional seo enhancements",
    "optional seo enhancements for wordpress",
    "seo enhancements",
    "seo suggestions",
)

def extract_introduction_excerpt(markdown_text: str) -> str:
    """
    Return plain-text excerpt spanning the Introduction section.
    """
    if not markdown_text:
        return ""

    intro_match = INTRO_HEADING_RE.search(markdown_text)
    if not intro_match:
        return ""

    remainder = markdown_text[intro_match.end():]
    next_heading = NEXT_SECTION_RE.search(remainder)
    section = remainder[: next_heading.start()] if next_heading else remainder
    section = section.strip()
    if not section:
        return ""

    html = md.markdown(section)
    soup = BeautifulSoup(html, "html.parser")
    clean_text = soup.get_text(separator=" ", strip=True)
    clean_text = re.sub(r"\s+([.,!?;:])", r"\1", clean_text)
    return re.sub(r"\s+", " ", clean_text).strip()

def _slugify(t: str) -> str:
    return re.sub(r"\s+", "-", re.sub(r"[^\w\s-]", "", t.strip().lower()))

def _looks_like_heading(line: str) -> bool:
    return line and len(line) < 80 and line[0].isupper() and not line.endswith(".")


def ensure_markdown_toc(text: str) -> str:
    """
    Normalize markdown, strip any model-generated TOC/preface/tail, but do not
    build a TOC. The HTML renderer will generate the single canonical TOC.
    """
    normalized = _normalize_markdown(text)
    lines = normalized.splitlines()
    output: List[str] = []
    skipping_toc = False

    for raw in lines:
        line = raw.strip()
        lower = line.lower()

        if not line:
            if skipping_toc:
                skipping_toc = False
            output.append("")
            continue

        if lower.startswith(PREFACE_PREFIXES):
            continue

        if lower.startswith(OPTIONAL_TAIL_PREFIXES):
            break

        if _normalize(line.lstrip("#")) in TOC_MARKERS:
            skipping_toc = True
            continue

        if skipping_toc and PLAIN_BULLET_RE.match(line):
            continue

        output.append(line)

    return "\n".join(output).strip()

def render_html(text: str, *, post_title: str | None = None) -> str:
    """
    Convert normalized markdown into a tightly controlled HTML subset.

    The renderer deliberately:
    - restricts headings to h3/h4 to match WP.com theme styles,
    - generates a single canonical Table of Contents at the top,
    - flattens ad-hoc FAQ sections into paragraph/question pairs.
    """
    text = _normalize_markdown(text)
    html: List[str] = []
    collected: List[Tuple[int, str, str]] = []
    faq_buffer: List[str] = []
    in_list = False
    in_faq = False
    prev_blank = True
    last_level = 0

    for raw in text.splitlines():
        line = raw.strip()
        lower = line.lower()

        if not line:
            if in_list:
                html.append("</ul>")
                in_list = False
            prev_blank = True
            continue

        if lower.startswith(PREFACE_PREFIXES):
            continue
        if lower.startswith(OPTIONAL_TAIL_PREFIXES):
            break

        if PLAIN_BULLET_RE.match(line) and not in_faq:
            if not in_list:
                html.append("<ul>")
                in_list = True
            bullet_text = PLAIN_BULLET_RE.sub(r"\1", line)
            html.append(f"<li>{escape(bullet_text)}</li>")
            prev_blank = False
            continue

        heading_match = MD_HEADING_RE.match(line)
        if heading_match:
            if in_list:
                html.append("</ul>")
                in_list = False
            level = len(heading_match.group(1))
            content = heading_match.group(2).strip()
            if _normalize(content) in FAQ_KEYWORDS:
                faq_buffer.append("<h4>FAQs</h4>")
                in_faq = True
                last_level = 4
                prev_blank = False
                continue
            slug = _slugify(content)
            lvl = 3 if level <= 2 else 4
            collected.append((lvl, content, slug))
            html.append(f"<h{lvl} id=\"{slug}\">{escape(content)}</h{lvl}>")
            last_level = lvl
            prev_blank = False
            continue

        if prev_blank and _looks_like_heading(line) and not in_faq:
            slug = _slugify(line)
            lvl = 4 if last_level == 3 else 3
            collected.append((lvl, line, slug))
            html.append(f"<h{lvl} id=\"{slug}\">{escape(line)}</h{lvl}>")
            last_level = lvl
            prev_blank = False
            continue

        if in_faq and line.endswith("?"):
            faq_buffer.append(f"<p><strong>{escape(line)}</strong></p>")
            prev_blank = False
            continue

        if in_list:
            html.append("</ul>")
            in_list = False
        target = faq_buffer if in_faq else html
        target.append(f"<p>{escape(line)}</p>")
        prev_blank = False

    if in_list:
        html.append("</ul>")

    if collected:
        toc: List[str] = ["<h3>Table of Contents</h3>", "<ul>"]
        top_open = False
        sub_open = False
        for lvl, title, slug in collected:
            if lvl == 3:
                if sub_open:
                    toc.append("</ul>")
                    sub_open = False
                if top_open:
                    toc.append("</li>")
                toc.append(f"<li><a href=\"#{slug}\">{escape(title)}</a>")
                top_open = True
            else:
                if not top_open:
                    toc.append("<li>")
                    top_open = True
                if not sub_open:
                    toc.append("<ul>")
                    sub_open = True
                toc.append(f"<li><a href=\"#{slug}\">{escape(title)}</a></li>")
        if sub_open:
            toc.append("</ul>")
        if top_open:
            toc.append("</li>")
        toc.append("</ul>")
        html = toc + html

    html.extend(faq_buffer)
    return "\n".join(html)

def _normalize(s: str) -> str:
    return re.sub(r"\s+"," ",s.strip().lower()) if s else ""

def _normalize_markdown(text: str) -> str:
    """Convert H2:/H3: style to markdown ##/###."""
    def repl(m: re.Match[str]) -> str:
        lvl=int(m.group(1)); title=m.group(2).strip()
        lvl=max(1,min(lvl,3))
        return "#"*lvl+" "+title
    text=re.sub(r"(?im)^\s*H([1-6])\s*[:\-]?\s+(.*)$",repl,text)
    text=re.sub(r"(?im)^\s*H([1-6])\s+(.*)$",repl,text)
    return text
