"""Pack a fixed-layout Kindle EPUB from generated page HTML."""

from __future__ import annotations

import html
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMG_SRC = re.compile(r'(src=")(\.\./\.\./assets/[^"]+)(")')
FONT_URL = re.compile(r'url\("\.\./\.\./assets/fonts/book/([^"]+)"\)')


def _esc(text: str) -> str:
    return html.escape("" if text is None else str(text), quote=True)


def _page_title(page_html: str, fallback: str) -> str:
    m = re.search(r'<section class="([^"]+)"', page_html)
    classes = m.group(1).split() if m else []
    if "cover" in classes:
        return "Cover"
    labels = {
        "title": "Title",
        "copyright": "Copyright",
        "meet": "Meet Pip",
        "how": "How to read this book",
        "review": "Pip's alphabet",
        "certificate": "The End",
    }
    for cls, label in labels.items():
        if cls in classes:
            return label
    if "letter-left" in classes:
        am = re.search(r'aria-label="([^"]+)"', page_html)
        if am:
            return am.group(1).split()[0]
        return "Letter"
    if "letter-right" in classes:
        wm = re.search(r'class="scene-word display">([^<]+)', page_html)
        return wm.group(1) if wm else "Word"
    return fallback


def _rewrite_images(page_html: str, copied: dict[str, str], img_dir: Path) -> str:
    def repl(match: re.Match) -> str:
        rel = match.group(2)
        if rel not in copied:
            asset = ROOT / rel.replace("../../", "")
            if not asset.exists():
                return match.group(0)
            name = "_".join(asset.relative_to(ROOT / "assets").parts)
            dest = img_dir / name
            dest.write_bytes(asset.read_bytes())
            copied[rel] = f"img/{name}"
        return f'{match.group(1)}{copied[rel]}{match.group(3)}'

    return IMG_SRC.sub(repl, page_html)


def export_kindle_epub(
    *,
    pages: list[str],
    css: str,
    meta: dict,
    author: str,
    publisher: str,
    dest: Path,
) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    work = dest.parent / ".epub-build"
    if work.exists():
        for child in work.rglob("*"):
            if child.is_file():
                child.unlink()
        for child in sorted(work.rglob("*"), reverse=True):
            if child.is_dir():
                child.rmdir()
    oebps = work / "OEBPS"
    img_dir = oebps / "img"
    font_dir = oebps / "fonts"
    page_dir = oebps / "pages"
    meta_inf = work / "META-INF"
    for folder in (img_dir, font_dir, page_dir, meta_inf):
        folder.mkdir(parents=True, exist_ok=True)

    copied: dict[str, str] = {}
    css = FONT_URL.sub(r'url("fonts/\1")', css)
    book_fonts = ROOT / "assets" / "fonts" / "book"
    for woff in book_fonts.glob("*.woff2"):
        if woff.name in css:
            (font_dir / woff.name).write_bytes(woff.read_bytes())

    lang = meta.get("language_code", "en")
    title = meta.get("title", "Pip's Alphabet")
    rewritten_pages = []
    for page in pages:
        rewritten_pages.append(_rewrite_images(page, copied, img_dir))

    spine_items = []
    manifest_items = []
    nav_lis = []
    for i, page in enumerate(rewritten_pages, start=1):
        name = f"p{i:03d}.xhtml"
        label = _page_title(page, f"Page {i}")
        body = f"""<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{_esc(lang)}" lang="{_esc(lang)}">
<head>
  <meta charset="utf-8"/>
  <title>{_esc(label)}</title>
  <meta name="viewport" content="width=2550, height=2550"/>
  <link rel="stylesheet" type="text/css" href="../styles.css"/>
</head>
<body class="script-{_esc(meta.get("script", "latin"))} edition-kindle epub">
{page}
</body>
</html>
"""
        (page_dir / name).write_text(body, encoding="utf-8")
        pid = f"p{i:03d}"
        manifest_items.append(
            f'    <item id="{pid}" href="pages/{name}" media-type="application/xhtml+xml"/>'
        )
        spine_items.append(f'    <itemref idref="{pid}"/>')
        nav_lis.append(f'        <li><a href="pages/{name}">{_esc(label)}</a></li>')

    cover_rel = next((href for href in copied.values() if "cover-art" in href), None)
    cover_item = ""
    meta_cover = ""
    if cover_rel:
        cover_item = f'    <item id="cover-image" href="{cover_rel}" media-type="image/png" properties="cover-image"/>\n'
        meta_cover = '    <meta name="cover" content="cover-image"/>\n'

    img_manifest = []
    for href in sorted(set(copied.values())):
        ext = Path(href).suffix.lower()
        mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".svg": "image/svg+xml"}.get(ext, "application/octet-stream")
        iid = "img-" + Path(href).stem.replace(".", "-")
        if "cover-art" in href:
            continue
        img_manifest.append(f'    <item id="{iid}" href="{href}" media-type="{mime}"/>')

    font_manifest = []
    for woff in sorted(font_dir.glob("*.woff2")):
        fid = "font-" + woff.stem.replace(".", "-")
        font_manifest.append(
            f'    <item id="{fid}" href="fonts/{woff.name}" media-type="font/woff2"/>'
        )

    (oebps / "styles.css").write_text(css, encoding="utf-8")

    nav = f"""<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{_esc(lang)}">
<head>
  <meta charset="utf-8"/>
  <title>Contents</title>
</head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>Contents</h1>
    <ol>
{chr(10).join(nav_lis)}
    </ol>
  </nav>
</body>
</html>
"""
    (oebps / "nav.xhtml").write_text(nav, encoding="utf-8")

    opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">pip-alphabet-{_esc(lang)}-kindle</dc:identifier>
    <dc:title>{_esc(title)}</dc:title>
    <dc:language>{_esc(lang)}</dc:language>
    <dc:creator>{_esc(author)}</dc:creator>
    <dc:publisher>{_esc(publisher)}</dc:publisher>
    <dc:description>{_esc(meta.get("tagline", ""))}</dc:description>
    <meta property="dcterms:modified">2026-09-14T00:00:00Z</meta>
    <meta property="rendition:layout">pre-paginated</meta>
    <meta property="rendition:orientation">portrait</meta>
    <meta property="rendition:spread">none</meta>
{meta_cover}  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="css" href="styles.css" media-type="text/css"/>
{cover_item}{chr(10).join(manifest_items)}
{chr(10).join(img_manifest)}
{chr(10).join(font_manifest)}
  </manifest>
  <spine>
{chr(10).join(spine_items)}
  </spine>
</package>
"""
    (oebps / "content.opf").write_text(opf, encoding="utf-8")
    (meta_inf / "container.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
""",
        encoding="utf-8",
    )

    if dest.exists():
        dest.unlink()
    with zipfile.ZipFile(dest, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        for file in sorted(work.rglob("*")):
            if file.is_file():
                zf.write(file, file.relative_to(work).as_posix(), compress_type=zipfile.ZIP_DEFLATED)

    # Cleanup staging dir
    for child in sorted(work.rglob("*"), reverse=True):
        if child.is_file():
            child.unlink()
        elif child.is_dir():
            child.rmdir()
    if work.exists():
        work.rmdir()
