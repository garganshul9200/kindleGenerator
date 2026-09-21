"""Export a Kindle-friendly Word manuscript (.docx) from book content."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent


def _set_run_font(run, name: str = "Nirmala UI", size_pt: float = 14, bold: bool = False) -> None:
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size_pt)
    run.bold = bold
    run.font.color.rgb = RGBColor(0x2C, 0x24, 0x1B)


def _add_para(
    doc: Document,
    text: str,
    *,
    size: float = 14,
    bold: bool = False,
    center: bool = False,
    space_after: float = 8,
    space_before: float = 0,
) -> None:
    p = doc.add_paragraph()
    if center:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    run = p.add_run(text)
    _set_run_font(run, size_pt=size, bold=bold)


def _page_break(doc: Document) -> None:
    p = doc.add_paragraph()
    p.add_run().add_break(WD_BREAK.PAGE)


def _add_image(doc: Document, path: Path | None, width_in: float = 5.2) -> None:
    if not path or not path.exists():
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(10)
    run = p.add_run()
    run.add_picture(str(path), width=Inches(width_in))


def _resolve_scene(stem: str) -> Path | None:
    if not stem:
        return None
    name = Path(stem).stem
    scenes = ROOT / "assets" / "illustrations" / "scenes"
    objects = ROOT / "assets" / "illustrations" / "objects"
    for path in (
        scenes / f"scene-{name}.png",
        scenes / f"{name}.png",
        scenes / f"scene-{name}.jpg",
        objects / f"{name}.png",
    ):
        if path.exists():
            return path
    return None


def export_kindle_docx(
    *,
    content: dict,
    config: dict,
    dest: Path,
) -> Path:
    """Write a read-only Kindle manuscript DOCX (no write-in activity pages)."""
    dest.parent.mkdir(parents=True, exist_ok=True)

    meta = content["meta"]
    front = content["front"]
    letters = content["letters"]
    activities = content["activities"]
    cert = content["certificate"]
    author = config.get("author", "")
    publisher = config.get("publisher", "")
    year = config.get("year", 2026)

    cover = ROOT / "assets" / "illustrations" / "cover-art.png"
    mascot = ROOT / "assets" / "illustrations" / "mascot" / "pip-wave.png"
    celebrate = ROOT / "assets" / "illustrations" / "mascot" / "pip-celebrate.png"
    if not celebrate.exists():
        celebrate = mascot

    doc = Document()
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(8.5)
    section.left_margin = Inches(0.7)
    section.right_margin = Inches(0.7)
    section.top_margin = Inches(0.6)
    section.bottom_margin = Inches(0.6)

    # --- Title ---
    _add_para(doc, meta.get("series", ""), size=12, center=True, space_after=4)
    _add_para(doc, meta["title"], size=32, bold=True, center=True, space_after=6)
    _add_para(doc, meta.get("subtitle", ""), size=16, center=True, space_after=12)
    _add_image(doc, cover if cover.exists() else mascot, width_in=4.8)
    _add_para(doc, meta.get("tagline", ""), size=13, center=True, space_before=8)
    _add_para(doc, f"{meta.get('mascot', 'Pip')} & {author}", size=12, center=True, space_before=10)
    _add_para(doc, f"{publisher} · {config.get('edition', 'First edition')} · {year}", size=11, center=True)
    _add_para(doc, f"Kindle eBook · {meta.get('language', '')} · {meta.get('age', '')}", size=11, center=True)
    _page_break(doc)

    # --- Copyright ---
    _add_para(doc, meta["title"], size=22, bold=True, center=True, space_after=14)
    _add_para(
        doc,
        f"Copyright © {year} {author}. All rights reserved. "
        "No part of this book may be reproduced without permission, "
        "except for brief quotations in reviews.",
        size=12,
        space_after=10,
    )
    _add_para(
        doc,
        "Illustrations and layout are original to this edition. "
        "Typefaces: Nunito, Fredoka, Baloo 2 and Baloo Paaji 2 (SIL Open Font License).",
        size=12,
        space_after=10,
    )
    _add_para(doc, front.get("copyright_line", ""), size=12, space_after=10)
    _add_para(doc, f"{publisher}\nKindle eBook · {meta.get('language', '')} · {meta.get('age', '')}", size=11)
    _page_break(doc)

    # --- Meet Pip ---
    _add_para(doc, front.get("meet_title", "Meet Pip"), size=24, bold=True, center=True, space_after=10)
    _add_image(doc, mascot, width_in=2.4)
    _add_para(doc, front.get("meet_body", ""), size=13, space_after=10)
    _add_para(doc, front.get("meet_prompt", ""), size=13, bold=True, center=True)
    _page_break(doc)

    # --- How to read ---
    _add_para(doc, front.get("how_title", "How to read"), size=24, bold=True, center=True, space_after=8)
    _add_para(doc, front.get("how_intro", ""), size=13, center=True, space_after=14)
    for step in front.get("how_steps", []):
        _add_para(doc, f"{step.get('n', '')}. {step.get('title', '')}", size=15, bold=True, space_after=2)
        _add_para(doc, step.get("text", ""), size=13, space_after=10)
    _page_break(doc)

    # --- Letters ---
    for item in letters:
        letter = item.get("uppercase") or item["letter"]
        word = item.get("word", "")
        _add_para(doc, letter, size=72, bold=True, center=True, space_after=4)
        _add_para(doc, word, size=28, bold=True, center=True, space_after=4)
        if item.get("pronunciation"):
            _add_para(doc, item["pronunciation"], size=12, center=True, space_after=6)
        if item.get("sentence"):
            _add_para(doc, item["sentence"], size=14, center=True, space_after=10)
        _add_image(doc, _resolve_scene(item.get("image", "")), width_in=5.0)
        if item.get("fact"):
            _add_para(doc, item["fact"], size=13, center=True, space_before=8, space_after=6)
        if item.get("action"):
            _add_para(doc, item["action"], size=12, center=True, space_after=4)
        _page_break(doc)

    # --- Review ---
    _add_para(doc, activities.get("review_title", "Alphabet"), size=24, bold=True, center=True, space_after=8)
    _add_para(doc, activities.get("review_intro", ""), size=13, center=True, space_after=6)
    _add_para(doc, activities.get("review_prompt", ""), size=13, center=True, space_after=14)
    # Compact letter grid as paragraphs
    chunk: list[str] = []
    for item in letters:
        chunk.append(f"{item.get('uppercase') or item['letter']} — {item.get('word', '')}")
        if len(chunk) == 4:
            _add_para(doc, "   ·   ".join(chunk), size=12, center=True, space_after=4)
            chunk = []
    if chunk:
        _add_para(doc, "   ·   ".join(chunk), size=12, center=True, space_after=4)
    _page_break(doc)

    # --- Celebration ---
    _add_para(doc, cert.get("kicker", ""), size=12, center=True, space_after=4)
    _add_para(doc, cert.get("title", ""), size=26, bold=True, center=True, space_after=10)
    _add_para(doc, cert.get("body", ""), size=13, center=True, space_after=12)
    _add_image(doc, celebrate, width_in=2.6)
    _add_para(doc, cert.get("stamp", ""), size=12, bold=True, center=True, space_before=8)
    if cert.get("closing"):
        _add_para(doc, cert["closing"], size=13, center=True, space_before=12)

    doc.save(dest)
    return dest
