#!/usr/bin/env python3
"""Build a print-ready KDP alphabet book from a language content file.

Usage:
    python3 src/build.py --lang en
    python3 src/build.py --lang hi --pdf
    python3 src/build.py --lang es --pdf
"""

from __future__ import annotations

import argparse
import html
import json
import random
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEMES = ("coral", "honey", "sage", "sky", "plum", "peach")


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def e(text) -> str:
    return html.escape("" if text is None else str(text), quote=True)


def font_faces(rel_fonts: str) -> str:
    faces = [
        ("Nunito", 400, "nunito-latin-400-normal.woff2"),
        ("Nunito", 600, "nunito-latin-600-normal.woff2"),
        ("Nunito", 700, "nunito-latin-700-normal.woff2"),
        ("Nunito", 800, "nunito-latin-800-normal.woff2"),
        ("Nunito", 400, "nunito-latin-ext-400-normal.woff2"),
        ("Nunito", 700, "nunito-latin-ext-700-normal.woff2"),
        ("Fredoka", 500, "fredoka-latin-500-normal.woff2"),
        ("Fredoka", 600, "fredoka-latin-600-normal.woff2"),
        ("Fredoka", 700, "fredoka-latin-700-normal.woff2"),
        ("Fredoka", 500, "fredoka-latin-ext-500-normal.woff2"),
        ("Fredoka", 700, "fredoka-latin-ext-700-normal.woff2"),
        ("Baloo 2", 400, "baloo-2-latin-400-normal.woff2"),
        ("Baloo 2", 700, "baloo-2-latin-700-normal.woff2"),
        ("Baloo 2", 400, "baloo-2-devanagari-400-normal.woff2"),
        ("Baloo 2", 700, "baloo-2-devanagari-700-normal.woff2"),
        ("Baloo Paaji 2", 400, "baloo-paaji-2-latin-400-normal.woff2"),
        ("Baloo Paaji 2", 700, "baloo-paaji-2-latin-700-normal.woff2"),
        ("Baloo Paaji 2", 400, "baloo-paaji-2-gurmukhi-400-normal.woff2"),
        ("Baloo Paaji 2", 700, "baloo-paaji-2-gurmukhi-700-normal.woff2"),
    ]
    css = []
    for family, weight, filename in faces:
        path = ROOT / "assets" / "fonts" / "book" / filename
        if not path.exists():
            continue
        css.append(
            f"""@font-face {{
  font-family: "{family}";
  font-style: normal;
  font-weight: {weight};
  font-display: block;
  src: url("{rel_fonts}/{filename}") format("woff2");
}}"""
        )
    return "\n".join(css)


PAW = """<svg class="paw" viewBox="0 0 24 24" aria-hidden="true"><circle cx="7" cy="7" r="2.2" fill="currentColor"/><circle cx="12" cy="5" r="2.2" fill="currentColor"/><circle cx="17" cy="7" r="2.2" fill="currentColor"/><ellipse cx="12" cy="15.5" rx="5.2" ry="4.2" fill="currentColor"/></svg>"""


class BookBuilder:
    def __init__(self, content: dict, config: dict, lang: str):
        self.content = content
        self.config = config
        self.lang = lang
        self.meta = content["meta"]
        self.front = content["front"]
        self.back = content.get("back") or {}
        self.letters = content["letters"]
        self.activities = content["activities"]
        self.cert = content["certificate"]
        self.script = self.meta.get("script", "latin")
        self.pages: list[str] = []
        self.n = 0  # 1-based printed page number
        self.asset = "../../assets"
        self.scenes = ROOT / "assets" / "illustrations" / "scenes"
        self.objects = ROOT / "assets" / "illustrations" / "objects"
        self.by_letter = {item["letter"]: item for item in self.letters}

    def side(self) -> str:
        return "recto" if self.n % 2 == 1 else "verso"

    def theme_for(self, index: int) -> str:
        item = self.letters[index]
        return item.get("theme") or THEMES[index % len(THEMES)]

    def start_page(self, extra: str = "", theme: str | None = None, numbered: bool = True) -> str:
        self.n += 1
        classes = ["page", self.side()]
        if extra:
            classes.extend(extra.split())
        if theme:
            classes.append(f"theme-{theme}")
        if not numbered:
            classes.append("unnumbered")
        folio = (
            f'<div class="folio">{PAW}{self.n}</div>'
            if numbered
            else ""
        )
        return f'<section class="{" ".join(classes)}" data-page="{self.n}">{folio}'

    def end_page(self) -> str:
        return "</section>"

    def resolve_image(self, stem: str) -> Path | None:
        if not stem:
            return None
        name = Path(stem).stem
        candidates = [
            self.scenes / f"scene-{name}.png",
            self.scenes / f"{name}.png",
            self.scenes / f"scene-{name}.jpg",
            self.objects / f"{name}.png",
            self.objects / f"{stem}",
            self.scenes / stem,
        ]
        for path in candidates:
            if path.exists():
                return path
        return None

    def img_src(self, stem: str) -> str | None:
        path = self.resolve_image(stem)
        if not path:
            return None
        return f"{self.asset}/illustrations/{path.parent.name}/{path.name}"

    def mascot_src(self, which: str = "pip-wave.png") -> str:
        return f"{self.asset}/illustrations/mascot/{which}"

    def cover_src(self) -> str:
        return f"{self.asset}/illustrations/cover-art.png"

    def fallback_scene(self, letter: str) -> str:
        return f"""<div class="fallback-scene">
  <div class="big display">{e(letter)}</div>
  <img src="{self.mascot_src()}" alt="">
</div>"""

    def scene_html(self, item: dict, alt: str) -> str:
        src = self.img_src(item.get("image", ""))
        if src:
            return f'<img src="{src}" alt="{e(alt)}">'
        return self.fallback_scene(item.get("uppercase") or item["letter"])

    def pip_sticker(self, item: dict) -> str:
        pip = item.get("pip") or {"x": 54, "y": 42, "scale": 1, "rotate": 0}
        x, y = pip.get("x", 54), pip.get("y", 42)
        scale = pip.get("scale", 1)
        rot = pip.get("rotate", 0)
        size = 1.55 * float(scale)
        return (
            f'<img class="pip-sticker" src="{self.mascot_src()}" alt="" '
            f'style="left:{x}%;top:{y}%;width:{size:.2f}in;height:{size:.2f}in;'
            f'transform:translate(-50%,-50%) rotate({rot}deg);">'
        )

    def cover_block(self, is_wrap_front: bool = False) -> str:
        meta = self.meta
        return f"""
<div class="bleed-wash"></div>
<img class="cover-art" src="{self.cover_src()}" alt="">
<div class="cover-scrim"></div>
<div class="cover-band">
  <p class="kicker">{e(meta.get("series", ""))}</p>
  <h1 class="cover-title display">{e(meta["title"])}</h1>
  <p class="cover-sub">{e(meta.get("subtitle", ""))}</p>
  <span class="cover-age">{e(meta.get("age", ""))}</span>
</div>
<p class="cover-tag">{e(meta.get("tagline", ""))}</p>
"""

    def add_cover(self) -> None:
        html_page = (
            self.start_page("cover", theme="coral", numbered=False)
            + self.cover_block()
            + self.end_page()
        )
        self.pages.append(html_page)

    def cover_back_block(self) -> str:
        meta = self.meta
        cfg = self.config
        back = self.back
        headline = back.get("headline") or meta.get("subtitle") or meta["title"]
        blurb = back.get("blurb") or meta.get("tagline", "")
        closing = back.get("closing") or meta.get("tagline", "")
        bullets = back.get("bullets") or []
        bullet_html = ""
        if bullets:
            items = "".join(f"<li>{e(item)}</li>" for item in bullets)
            bullet_html = f'<ul class="cover-back-bullets">{items}</ul>'
        return f"""
<div class="bleed-wash cover-back-wash"></div>
<img class="cover-back-mascot" src="{self.mascot_src()}" alt="">
<div class="cover-back-safe">
  <p class="kicker">{e(meta.get("series", ""))}</p>
  <h1 class="cover-back-title display">{e(meta["title"])}</h1>
  <p class="cover-back-headline">{e(headline)}</p>
  <p class="cover-back-blurb">{e(blurb)}</p>
  {bullet_html}
  <p class="cover-back-closing">{e(closing)}</p>
  <span class="cover-age">{e(meta.get("age", ""))}</span>
  <div class="cover-back-imprint">
    {e(cfg.get("author", ""))}<br>
    {e(cfg.get("publisher", ""))}<br>
    {e(cfg.get("edition", "First edition"))} · {e(cfg.get("year", 2026))}
  </div>
  <div class="cover-back-barcode" aria-hidden="true">
    <span>ISBN / barcode</span>
  </div>
</div>
"""

    def add_cover_back(self) -> None:
        html_page = (
            self.start_page("cover cover-back", theme="coral", numbered=False)
            + self.cover_back_block()
            + self.end_page()
        )
        self.pages.append(html_page)

    def add_title(self) -> None:
        cfg = self.config
        self.pages.append(
            self.start_page("title", theme="coral")
            + f"""
<div class="safe">
  <p class="kicker">{e(self.meta.get("series", ""))}</p>
  <h1 class="page-heading display">{e(self.meta["title"])}</h1>
  <p class="lede">{e(self.meta.get("subtitle", ""))}</p>
  <hr class="rule">
  <p class="body-copy">{e(self.front.get("copyright_line", ""))}</p>
  <div class="imprint">
    {e(self.meta.get("mascot", "Pip"))} &amp; {e(cfg.get("author", "Anshul Thakur"))}<br>
    {e(cfg.get("publisher", ""))}<br>
    {e(cfg.get("edition", "First edition"))} · {e(cfg.get("year", 2026))}
  </div>
</div>
"""
            + self.end_page()
        )

    def add_copyright(self) -> None:
        cfg = self.config
        self.pages.append(
            self.start_page("copyright", theme="honey")
            + f"""
<div class="safe">
  <h1 class="page-heading display">{e(self.meta["title"])}</h1>
  <p class="body-copy">
    Copyright © {e(cfg.get("year", 2026))} {e(cfg.get("author", "Anshul Thakur"))}.
    All rights reserved. No part of this book may be reproduced without permission,
    except for brief quotations in reviews.
  </p>
  <p class="body-copy" style="margin-top:0.28in">
    Illustrations and layout are original to this edition.
    Typefaces: Nunito, Fredoka, Baloo 2 and Baloo Paaji 2 (SIL Open Font License).
  </p>
  <div class="imprint">
    {e(cfg.get("publisher", ""))}<br>
    Paperback · {e(self.meta.get("language", ""))} · {e(self.meta.get("age", ""))}<br>
    Printed via Amazon KDP · Trim 8.5 × 8.5 in
  </div>
</div>
"""
            + self.end_page()
        )

    def add_belongs(self) -> None:
        f = self.front
        self.pages.append(
            self.start_page("belongs", theme="sage")
            + f"""
<div class="safe">
  <h1 class="page-heading display">{e(f["belongs_title"])}</h1>
  <div class="belongs-card">
    <div class="field">
      <label>{e(f["belongs_name_label"])}</label>
      <div class="line"></div>
    </div>
    <div class="field">
      <label>{e(f["belongs_age_label"])}</label>
      <div class="line"></div>
    </div>
    <p class="body-copy" style="margin-top:0.35in">{e(f["belongs_note"])}</p>
  </div>
</div>
"""
            + self.end_page()
        )

    def add_meet(self) -> None:
        f = self.front
        self.pages.append(
            self.start_page("meet", theme="peach")
            + f"""
<div class="safe">
  <h1 class="page-heading display">{e(f["meet_title"])}</h1>
  <div class="meet-row">
    <img class="pip-spot" src="{self.mascot_src()}" alt="{e(self.meta.get("mascot", "Pip"))}">
    <div>
      <p class="lede">{e(f["meet_body"])}</p>
      <p class="sentence">{e(f["meet_prompt"])}</p>
    </div>
  </div>
</div>
"""
            + self.end_page()
        )

    def add_how(self) -> None:
        f = self.front
        steps = "".join(
            f"""<article class="step">
  <div class="step-n">{e(s["n"])}</div>
  <h3 class="display">{e(s["title"])}</h3>
  <p>{e(s["text"])}</p>
</article>"""
            for s in f["how_steps"]
        )
        self.pages.append(
            self.start_page("how", theme="sky")
            + f"""
<div class="safe">
  <h1 class="page-heading display">{e(f["how_title"])}</h1>
  <p class="lede">{e(f["how_intro"])}</p>
  <div class="steps">{steps}</div>
</div>
"""
            + self.end_page()
        )

    def ensure_next_is_verso(self) -> None:
        """Letter spreads start on a left-hand (even) page."""
        if (self.n + 1) % 2 == 1:
            mascot = e(self.meta.get("mascot", "Pip"))
            self.pages.append(
                self.start_page("begin", theme="coral")
                + f"""
<div class="bleed-wash"></div>
<div class="safe" style="align-items:center;justify-content:center;text-align:center">
  <img class="pip-spot" src="{self.mascot_src()}" alt="">
  <h1 class="page-heading display" style="margin-top:0.28in">{e(mascot)}</h1>
  <p class="lede">{e(self.front.get("meet_prompt", ""))}</p>
</div>
"""
                + self.end_page()
            )

    def add_letter_spread(self, index: int) -> None:
        item = self.letters[index]
        theme = self.theme_for(index)
        upper = item.get("uppercase") or item["letter"]
        lower = item.get("lowercase") or ""
        lower_html = f'<span class="lower">{e(lower)}</span>' if lower else ""
        self.pages.append(
            self.start_page("letter-left", theme=theme)
            + f"""
<div class="bleed-wash"></div>
<div class="safe">
  <div class="letter-stage">
    <div class="letter-halo"></div>
    <div class="giant-letter display" aria-label="{e(upper)} {e(lower)}">
      <span class="upper">{e(upper)}</span>{lower_html}
    </div>
    {self.pip_sticker(item)}
  </div>
  <div class="letter-meta">
    <p class="word-xl display">{e(item["word"])}</p>
    <p class="pron">{e(item.get("pronunciation", ""))}</p>
    <p class="sentence">{e(item["sentence"])}</p>
  </div>
</div>
"""
            + self.end_page()
        )
        trace_letters = "".join(
            f'<span class="trace">{e(ch)}</span>'
            for ch in (upper, lower)
            if ch
        )
        alt = f"{self.meta.get('mascot', 'Pip')} — {item['word']}"
        self.pages.append(
            self.start_page("letter-right", theme=theme)
            + f"""
<div class="bleed-wash"></div>
<div class="safe">
  <div class="scene-frame">
    {self.scene_html(item, alt)}
  </div>
  <div class="scene-caption">
    <p class="scene-word display">{e(item["word"])}</p>
    <p class="fact">{e(item["fact"])}</p>
    <div class="mini-trace">
      <span class="trace-hint">Trace</span>
      {trace_letters}
    </div>
  </div>
</div>
"""
            + self.end_page()
        )

    def chunk(self, items: list, size: int) -> list[list]:
        return [items[i : i + size] for i in range(0, len(items), size)]

    def add_tracing(self) -> None:
        act = self.activities
        letters = self.letters
        # Prefer uppercase; if no lowercase exists, still trace the letterform.
        upper_items = [it.get("uppercase") or it["letter"] for it in letters]
        lower_items = [it.get("lowercase") for it in letters if it.get("lowercase")]
        groups = [("tracing_upper_label", upper_items)]
        if lower_items:
            groups.append(("tracing_lower_label", lower_items))
        for label_key, glyphs in groups:
            for chunk in self.chunk(glyphs, 12):
                cells = "".join(
                    f'<div class="trace-cell"><span>{e(g)}</span></div>' for g in chunk
                )
                self.pages.append(
                    self.start_page("tracing", theme="honey")
                    + f"""
<div class="bleed-wash"></div>
<div class="safe">
  <h1 class="page-heading display">{e(act["tracing_title"])}</h1>
  <p class="lede">{e(act["tracing_intro"])}</p>
  <p class="pron">{e(act.get(label_key, ""))}</p>
  <div class="trace-grid">{cells}</div>
</div>
"""
                    + self.end_page()
                )

    def add_review(self) -> None:
        act = self.activities
        chips = "".join(
            f'<div class="alpha-chip"><span class="ch">{e(it.get("uppercase") or it["letter"])}</span>'
            f'<span class="wd">{e(it["word"])}</span></div>'
            for it in self.letters
        )
        dense = " dense" if len(self.letters) > 30 else ""
        self.pages.append(
            self.start_page("review", theme="sage")
            + f"""
<div class="bleed-wash"></div>
<div class="safe">
  <h1 class="page-heading display">{e(act["review_title"])}</h1>
  <p class="lede">{e(act["review_intro"])}</p>
  <p class="body-copy">{e(act["review_prompt"])}</p>
  <div class="alpha-grid{dense}">{chips}</div>
</div>
"""
            + self.end_page()
        )

    def add_matching(self) -> None:
        act = self.activities
        sets = act.get("matching_sets")
        if not sets:
            pairs = act.get("matching_pairs")
            if pairs:
                sets = self.chunk(pairs, 5)
            else:
                keys = [it["letter"] for it in self.letters]
                sets = self.chunk(keys, 5)
        title = act.get("matching_title", "Match with Pip")
        intro = act.get("matching_intro", "Draw a line from each letter to its picture.")
        for page_i, wanted in enumerate(sets):
            items = [self.by_letter[k] for k in wanted if k in self.by_letter]
            if len(items) < 3:
                continue
            rng = random.Random(f"{self.meta.get('language_code', 'en')}-match-{page_i}")
            pictures = items[:]
            rng.shuffle(pictures)
            left = "".join(
                f'<div class="match-letter"><div class="bubble">{e(it.get("uppercase") or it["letter"])}</div>'
                f'<div class="dot-line"></div></div>'
                for it in items
            )
            right_bits = []
            for it in pictures:
                src = self.img_src(it.get("image", ""))
                pic = (
                    f'<img src="{src}" alt="{e(it["word"])}">'
                    if src
                    else f'<div class="bubble">{e(it.get("uppercase") or it["letter"])}</div>'
                )
                right_bits.append(
                    f'<div class="match-pic">{pic}<span class="wd" style="font-weight:800">{e(it["word"])}</span></div>'
                )
            part = f" · {page_i + 1}" if len(sets) > 1 else ""
            self.pages.append(
                self.start_page("matching", theme="plum")
                + f"""
<div class="bleed-wash"></div>
<div class="safe">
  <h1 class="page-heading display">{e(title)}{e(part)}</h1>
  <p class="lede">{e(intro)}</p>
  <div class="match">
    <div class="match-col">{left}</div>
    <div class="match-col">{"".join(right_bits)}</div>
  </div>
</div>
"""
                + self.end_page()
            )

    def add_match_pip(self) -> None:
        """Match each letter to Pip’s scene — ‘Match Pip’ game."""
        act = self.activities
        title = act.get("match_pip_title", "Match Pip")
        intro = act.get(
            "match_pip_intro",
            "Pip is busy! Draw a line from each letter to the picture of Pip.",
        )
        keys = act.get("match_pip_letters") or [it["letter"] for it in self.letters]
        sets = self.chunk([k for k in keys if k in self.by_letter], 4)
        for page_i, wanted in enumerate(sets):
            items = [self.by_letter[k] for k in wanted]
            if len(items) < 3:
                continue
            rng = random.Random(f"{self.meta.get('language_code', 'en')}-pip-{page_i}")
            pictures = items[:]
            rng.shuffle(pictures)
            left = "".join(
                f'<div class="match-letter"><div class="bubble">{e(it.get("uppercase") or it["letter"])}</div>'
                f'<div class="dot-line"></div></div>'
                for it in items
            )
            right_bits = []
            for it in pictures:
                src = self.img_src(it.get("image", ""))
                pic = (
                    f'<img src="{src}" alt="{e(it.get("action") or it["word"])}">'
                    if src
                    else f'<div class="bubble">{e(it.get("uppercase") or it["letter"])}</div>'
                )
                caption = it.get("word") or ""
                right_bits.append(
                    f'<div class="match-pic match-pip-pic">{pic}'
                    f'<span class="wd match-pip-cap">{e(caption)}</span></div>'
                )
            part = f" · {page_i + 1}" if len(sets) > 1 else ""
            self.pages.append(
                self.start_page("matching match-pip", theme="peach")
                + f"""
<div class="bleed-wash"></div>
<div class="safe">
  <h1 class="page-heading display">{e(title)}{e(part)}</h1>
  <p class="lede">{e(intro)}</p>
  <div class="match">
    <div class="match-col">{left}</div>
    <div class="match-col">{"".join(right_bits)}</div>
  </div>
</div>
"""
                + self.end_page()
            )

    def add_find_letter(self) -> None:
        """Circle the letter that matches the prompt."""
        act = self.activities
        title = act.get("find_title", "Find the letter")
        intro = act.get("find_intro", "Circle the letter Pip is looking for.")
        keys = [it["letter"] for it in self.letters]
        sets = self.chunk(keys, 6)
        rng_base = self.meta.get("language_code", "en")
        for page_i, wanted in enumerate(sets):
            rows = []
            for j, key in enumerate(wanted):
                it = self.by_letter[key]
                target = it.get("uppercase") or it["letter"]
                pool = [self.by_letter[k] for k in keys if k != key]
                rng = random.Random(f"{rng_base}-find-{page_i}-{j}")
                decoys = rng.sample(pool, min(3, len(pool)))
                choices = [target] + [
                    (d.get("uppercase") or d["letter"]) for d in decoys
                ]
                rng.shuffle(choices)
                cells = "".join(
                    f'<div class="find-choice"><span>{e(ch)}</span></div>' for ch in choices
                )
                rows.append(
                    f'<div class="find-row">'
                    f'<div class="find-prompt"><span class="bubble small">{e(target)}</span>'
                    f'<span class="wd">{e(it["word"])}</span></div>'
                    f'<div class="find-choices">{cells}</div></div>'
                )
            part = f" · {page_i + 1}" if len(sets) > 1 else ""
            self.pages.append(
                self.start_page("find-letter", theme="sky")
                + f"""
<div class="bleed-wash"></div>
<div class="safe">
  <h1 class="page-heading display">{e(title)}{e(part)}</h1>
  <p class="lede">{e(intro)}</p>
  <div class="find-game">{"".join(rows)}</div>
</div>
"""
                + self.end_page()
            )

    def add_what_next(self) -> None:
        """Fill in the missing letter in a short sequence."""
        act = self.activities
        title = act.get("sequence_title", "What comes next?")
        intro = act.get(
            "sequence_intro",
            "Say the letters out loud. Write the missing one in the empty box.",
        )
        letters = self.letters
        puzzles = []
        for i in range(len(letters) - 3):
            window = letters[i : i + 4]
            puzzles.append(window)
        # Keep a manageable set: every other sequence, max 12
        puzzles = puzzles[::2][:12]
        for page_i, chunk in enumerate(self.chunk(puzzles, 5)):
            rows = []
            for j, window in enumerate(chunk):
                blank_at = (page_i + j) % 3 + 1  # blank positions 1,2, or 3 (not first)
                cells = []
                for k, it in enumerate(window):
                    glyph = it.get("uppercase") or it["letter"]
                    if k == blank_at:
                        cells.append('<div class="seq-cell blank"><span></span></div>')
                    else:
                        cells.append(f'<div class="seq-cell"><span>{e(glyph)}</span></div>')
                rows.append(f'<div class="seq-row">{"".join(cells)}</div>')
            part = f" · {page_i + 1}"
            self.pages.append(
                self.start_page("sequence", theme="honey")
                + f"""
<div class="bleed-wash"></div>
<div class="safe">
  <h1 class="page-heading display">{e(title)}{e(part)}</h1>
  <p class="lede">{e(intro)}</p>
  <div class="seq-game">{"".join(rows)}</div>
</div>
"""
                + self.end_page()
            )

    def add_odd_one_out(self) -> None:
        """Circle the picture that belongs with each letter (4 choices)."""
        act = self.activities
        title = act.get("odd_title", "Pick Pip’s picture")
        intro = act.get(
            "odd_intro",
            "Circle the picture that belongs with each letter.",
        )
        keys = [it["letter"] for it in self.letters]
        step = max(1, len(keys) // 12)
        chosen = keys[::step][:12]
        sets = self.chunk(chosen, 3)
        rng_base = self.meta.get("language_code", "en")
        for page_i, wanted in enumerate(sets):
            cards = []
            for j, key in enumerate(wanted):
                it = self.by_letter[key]
                target = it.get("uppercase") or it["letter"]
                others = [self.by_letter[k] for k in keys if k != key]
                rng = random.Random(f"{rng_base}-odd-{page_i}-{j}")
                choices = [it] + rng.sample(others, min(3, len(others)))
                rng.shuffle(choices)
                thumbs = []
                for ch in choices:
                    src = self.img_src(ch.get("image", ""))
                    if src:
                        thumbs.append(
                            f'<div class="odd-choice"><img src="{src}" alt="">'
                            f'<span class="wd">{e(ch["word"])}</span></div>'
                        )
                    else:
                        thumbs.append(
                            f'<div class="odd-choice"><div class="bubble small">'
                            f'{e(ch.get("uppercase") or ch["letter"])}</div>'
                            f'<span class="wd">{e(ch["word"])}</span></div>'
                        )
                cards.append(
                    f'<div class="odd-card">'
                    f'<div class="odd-letter"><span class="bubble">{e(target)}</span></div>'
                    f'<div class="odd-choices">{"".join(thumbs)}</div></div>'
                )
            part = f" · {page_i + 1}"
            self.pages.append(
                self.start_page("odd-one", theme="sage")
                + f"""
<div class="bleed-wash"></div>
<div class="safe">
  <h1 class="page-heading display">{e(title)}{e(part)}</h1>
  <p class="lede">{e(intro)}</p>
  <div class="odd-game">{"".join(cards)}</div>
</div>
"""
                + self.end_page()
            )

    def add_write_practice(self) -> None:
        """Extra dotted-letter practice rows."""
        act = self.activities
        title = act.get("write_title", "Write with Pip")
        intro = act.get(
            "write_intro",
            "Trace each letter, then write it again in the empty boxes.",
        )
        glyphs = [it.get("uppercase") or it["letter"] for it in self.letters]
        for page_i, chunk in enumerate(self.chunk(glyphs, 6)):
            rows = []
            for g in chunk:
                practice = "".join(
                    f'<div class="write-box"><span class="ghost">{e(g)}</span></div>' for _ in range(3)
                )
                empty = "".join('<div class="write-box empty"></div>' for _ in range(3))
                rows.append(
                    f'<div class="write-row">'
                    f'<div class="write-model"><span>{e(g)}</span></div>'
                    f'{practice}{empty}</div>'
                )
            part = f" · {page_i + 1}"
            self.pages.append(
                self.start_page("write-practice", theme="coral")
                + f"""
<div class="bleed-wash"></div>
<div class="safe">
  <h1 class="page-heading display">{e(title)}{e(part)}</h1>
  <p class="lede">{e(intro)}</p>
  <div class="write-game">{"".join(rows)}</div>
</div>
"""
                + self.end_page()
            )

    def add_certificate(self) -> None:
        c = self.cert
        celebrate = f"{self.asset}/illustrations/mascot/pip-celebrate.png"
        if not (ROOT / "assets/illustrations/mascot/pip-celebrate.png").exists():
            celebrate = self.mascot_src()
        # Certificate looks better on a right-hand page.
        if self.side() == "verso":
            self.pages.append(
                self.start_page("closing", theme="coral")
                + f"""
<div class="bleed-wash"></div>
<div class="safe" style="align-items:center;justify-content:center;text-align:center">
  <img class="pip-spot" src="{celebrate}" alt="">
  <p class="closing-note display" style="margin-top:0.35in">{e(c.get("closing", ""))}</p>
</div>
"""
                + self.end_page()
            )
        self.pages.append(
            self.start_page("certificate", theme="coral")
            + f"""
<div class="bleed-wash"></div>
<div class="safe">
  <div class="cert-frame">
    <p class="kicker">{e(c["kicker"])}</p>
    <h1 class="cert-title display">{e(c["title"])}</h1>
    <p class="cert-body">{e(c["body"])}</p>
    <img class="cert-photo" src="{celebrate}" alt="">
    <div class="cert-fields">
      <div class="field"><label>{e(c["name_label"])}</label><div class="line"></div></div>
      <div class="field"><label>{e(c["date_label"])}</label><div class="line"></div></div>
    </div>
    <p class="stamp">{e(c["stamp"])}</p>
  </div>
</div>
"""
            + self.end_page()
        )

    def build_pages(self, include_cover: bool) -> None:
        if include_cover:
            self.add_cover()
        self.add_title()
        self.add_copyright()
        self.add_belongs()
        self.add_meet()
        self.add_how()
        self.ensure_next_is_verso()
        for i in range(len(self.letters)):
            self.add_letter_spread(index=i)
        self.add_tracing()
        self.add_review()
        self.add_matching()
        self.add_match_pip()
        self.add_find_letter()
        self.add_what_next()
        self.add_odd_one_out()
        self.add_write_practice()
        self.add_certificate()
        # KDP interiors often prefer even page counts.
        if self.n % 2 == 1:
            self.pages.append(
                self.start_page("blank unnumbered", theme="coral", numbered=False)
                + '<div class="bleed-wash"></div>'
                + self.end_page()
            )
        # KDP paperback minimum is 72 pages; pad with activity blanks if short.
        while self.n < 80:
            theme = THEMES[self.n % len(THEMES)]
            self.pages.append(
                self.start_page("extra-play", theme=theme)
                + f"""
<div class="bleed-wash"></div>
<div class="safe" style="align-items:center;justify-content:center;text-align:center">
  <img class="pip-spot" src="{self.mascot_src()}" alt="">
  <h1 class="page-heading display" style="margin-top:0.28in">{e(self.activities.get("bonus_title", "Play with Pip"))}</h1>
  <p class="lede">{e(self.activities.get("bonus_intro", "Draw Pip. Trace a letter. Invent a new word!"))}</p>
  <div class="bonus-pad"></div>
</div>
"""
                + self.end_page()
            )

    def document(self, body: str, title: str) -> str:
        css_print = (ROOT / "styles" / "print.css").read_text(encoding="utf-8")
        fonts = font_faces("../../assets/fonts/book")
        return f"""<!DOCTYPE html>
<html lang="{e(self.meta.get("language_code", "en"))}">
<head>
<meta charset="utf-8">
<title>{e(title)}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
{fonts}
{css_print}
</style>
</head>
<body class="script-{e(self.script)}">
{body}
</body>
</html>
"""

    def cover_wrap_html(self, page_count: int) -> str:
        cfg = self.config
        paper = cfg.get("paper", "white")
        per = cfg["kdp_notes"]["spine_white_paper_in_per_page"] if paper == "white" else cfg["kdp_notes"]["spine_cream_paper_in_per_page"]
        # Match KDP cover calculator: bleed + back + spine + front + bleed
        spine = page_count * per
        bleed = 0.125
        trim = 8.5
        width = bleed + trim + spine + trim + bleed
        height = trim + bleed * 2
        # KDP UI shows wrap width to 3 decimals (e.g. 17.448"); keep spine precise.
        spine_css = f"{spine:.4f}"
        width_css = f"{width:.3f}"
        height_css = f"{height:.3f}"
        panel = f"{trim + bleed:.3f}"
        # Spine text is allowed at 79+ pages; keep type small enough for thin spines.
        spine_pt = 9 if spine < 0.25 else 11
        return f"""<!DOCTYPE html>
<html lang="{e(self.meta.get("language_code", "en"))}">
<head>
<meta charset="utf-8">
<title>Cover wrap — {e(self.meta["title"])}</title>
<style>
{font_faces("../../assets/fonts/book")}
{ (ROOT / "styles" / "print.css").read_text(encoding="utf-8") }
@page {{ size: {width_css}in {height_css}in; margin: 0; }}
.wrap {{
  width: {width_css}in;
  height: {height_css}in;
  display: flex;
  background: #f6efe3;
}}
.panel {{ position: relative; height: 100%; overflow: hidden; }}
.back {{ width: {panel}in; }}
.spine {{
  width: {spine_css}in;
  background: #d45d4a;
  color: #fffdf8;
  display: flex;
  align-items: center;
  justify-content: center;
}}
.spine span {{
  writing-mode: vertical-rl;
  transform: rotate(180deg);
  font-family: Fredoka, "Baloo 2", sans-serif;
  font-size: {spine_pt}pt;
  letter-spacing: 0.06em;
  white-space: nowrap;
}}
.front {{ width: {panel}in; }}
.panel.back {{
  background: #f8eee6;
}}
.panel.back .cover-back-safe {{
  position: absolute;
  inset: 0.35in 0.4in 0.35in 0.45in;
}}
.panel.back .cover-back-mascot {{
  right: 0.35in;
  bottom: 1.55in;
  width: 2.1in;
  height: 2.1in;
  opacity: 0.92;
}}
.panel.back .cover-back-barcode {{
  right: 0.05in;
  bottom: 0.05in;
}}
</style>
</head>
<body>
<div class="wrap">
  <div class="panel back">{self.cover_back_block()}</div>
  <div class="spine"><span>{e(self.meta["title"])} · {e(self.config.get("author", ""))}</span></div>
  <div class="panel front">{self.cover_block()}</div>
</div>
</body>
</html>
"""


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"  wrote {path.relative_to(ROOT)}")


def export_pdf(html_path: Path, pdf_path: Path) -> bool:
    """Export HTML to PDF. Prefer Playwright so CSS @page size (cover wrap) is honored."""
    script = ROOT / "scripts" / "pdf.cjs"
    if not script.exists():
        script = ROOT / "scripts" / "pdf.mjs"
    try:
        subprocess.run(["node", str(script), str(html_path), str(pdf_path)], check=True)
        print(f"  wrote {pdf_path.relative_to(ROOT)}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as err:
        print(f"  Playwright PDF failed: {err}")

    html_uri = html_path.resolve().as_uri()
    chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if chrome.exists():
        try:
            subprocess.run(
                [
                    str(chrome),
                    "--headless=new",
                    "--disable-gpu",
                    "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf_path}",
                    html_uri,
                ],
                check=True,
                capture_output=True,
            )
            print(f"  wrote {pdf_path.relative_to(ROOT)}")
            return True
        except subprocess.CalledProcessError as err:
            print(f"  Chrome PDF failed: {err}")

    print("  PDF export skipped or failed.")
    print("  Open the HTML in Chrome and Print → Save as PDF, margins None, background graphics On.")
    return False


def build(lang: str, make_pdf: bool, with_cover: bool) -> None:
    content_path = ROOT / "content" / f"{lang}.json"
    if not content_path.exists():
        available = [p.stem for p in (ROOT / "content").glob("*.json") if p.stem != "schema"]
        raise SystemExit(f"No content file for '{lang}'. Available: {', '.join(available)}")
    content = load_json(content_path)
    config = load_json(ROOT / "config" / "book.json")
    out = ROOT / "output" / lang
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    builder = BookBuilder(content, config, lang)
    builder.build_pages(include_cover=with_cover)
    interior = builder.document("\n".join(builder.pages), content["meta"]["title"])
    interior_path = out / "interior.html"
    write(interior_path, interior)

    # Standalone front + back covers (preview / hardcover panels)
    cover_builder = BookBuilder(content, config, lang)
    cover_builder.pages = []
    cover_builder.n = 0
    cover_builder.add_cover()
    write(out / "cover-front.html", cover_builder.document("\n".join(cover_builder.pages), content["meta"]["title"] + " — cover"))

    back_builder = BookBuilder(content, config, lang)
    back_builder.pages = []
    back_builder.n = 0
    back_builder.add_cover_back()
    write(out / "cover-back.html", back_builder.document("\n".join(back_builder.pages), content["meta"]["title"] + " — back cover"))

    wrap = builder.cover_wrap_html(page_count=builder.n)
    write(out / "cover-wrap.html", wrap)

    meta_out = {
        "language": content["meta"]["language"],
        "title": content["meta"]["title"],
        "page_count": builder.n,
        "trim": "8.5in × 8.5in",
        "pdf_page": "8.75in × 8.75in (includes 0.125in bleed)",
        "letters": len(builder.letters),
        "spine_in_white_paper": round(builder.n * config["kdp_notes"]["spine_white_paper_in_per_page"], 4),
    }
    write(out / "build-info.json", json.dumps(meta_out, indent=2, ensure_ascii=False))
    print(f"\n{content['meta']['title']}: {builder.n} pages, {len(builder.letters)} letters.")

    if make_pdf:
        export_pdf(interior_path, out / "interior.pdf")
        export_pdf(out / "cover-front.html", out / "cover-front.pdf")
        export_pdf(out / "cover-back.html", out / "cover-back.pdf")
        export_pdf(out / "cover-wrap.html", out / "cover-wrap.pdf")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Pip's Alphabet for KDP")
    parser.add_argument("--lang", default="en", help="content file stem: en, hi, pa, es, fr")
    parser.add_argument("--pdf", action="store_true", help="also export PDF via Playwright")
    parser.add_argument("--no-cover", action="store_true", help="omit illustrated cover from interior")
    args = parser.parse_args()
    build(args.lang, make_pdf=args.pdf, with_cover=not args.no_cover)


if __name__ == "__main__":
    main()
