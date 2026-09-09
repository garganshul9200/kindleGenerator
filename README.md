# Pip's Alphabet — KDP paperback template

A print-ready children's alphabet book system for Amazon KDP.

Content lives in JSON. Layout lives in CSS. Swap the language file, rebuild, and you have a new edition — English, Hindi, Punjabi, Spanish, or French.

The complete English example is fully illustrated with a recurring mascot, **Pip the fox**, who climbs every letter and then acts out the word on the facing page.

## What you get

```
alphabet-book-kdp/
  content/           Language datasets (en, hi, pa, es, fr)
  config/book.json   Trim, bleed, gutter, imprint
  assets/
    fonts/book/      SIL OFL fonts (commercial-safe)
    illustrations/   Cover, mascot, letter scenes
  styles/print.css   8.5 × 8.5 in print layout
  src/build.py       HTML generator
  scripts/pdf.mjs    PDF exporter
  output/<lang>/     Built interior + covers
```

## Book structure

1. Cover
2. Title page
3. Copyright / imprint
4. This book belongs to
5. Meet Pip
6. How to use this book
7. Letter spreads (left = letter playground, right = illustrated scene)
8. Tracing practice
9. Alphabet review
10. Matching activity
11. Certificate

## Print specs (KDP paperback)

| Spec | Value |
| --- | --- |
| Trim | **8.5 × 8.5 in** (square picture book) |
| Bleed | 0.125 in on all sides |
| PDF page | **8.75 × 8.75 in** |
| Safe margin | 0.25 in from trim |
| Extra gutter | ~0.22 in on the binding edge |
| Interior | Color, white paper |
| Crop marks | **Do not include** (KDP rule) |
| Cover | Separate wrap PDF, calculated from page count |

KDP uploads two files: the interior PDF and a wraparound cover. This template builds both.

## Build the English example

```bash
cd alphabet-book-kdp
python3 src/build.py --lang en
```

Open `output/en/interior.html` in a browser to preview the full book (pages stack vertically).

### Print-ready PDF

```bash
npm install playwright
npx playwright install chromium
python3 src/build.py --lang en --pdf
```

That writes:

- `output/en/interior.pdf` — upload this as the KDP interior
- `output/en/cover-front.pdf` — front cover preview
- `output/en/cover-back.pdf` — back cover with blurb + barcode space
- `output/en/cover-wrap.pdf` — full wrap (back + spine + front)
- `output/en/cover-wrap.html` — full wrap HTML (edit blurb in `content/<lang>.json` → `back`)

For the KDP interior, prefer:

```bash
python3 src/build.py --lang en --pdf --no-cover
```

so page 1 of the PDF is the title page, not a second copy of the cover. The illustrated covers are still built as `cover-front` / `cover-back` / `cover-wrap`.

Chrome fallback (no Playwright): open `interior.html` → Print → Save as PDF → paper size **8.75in × 8.75in**, margins **None**, background graphics **On**.

## Other languages

```bash
python3 src/build.py --lang hi
python3 src/build.py --lang pa
python3 src/build.py --lang es
python3 src/build.py --lang fr
```

Each language file chooses its own words — they are **not** translations of Apple/Ball/Cat. Hindi `अ` is अनार, Spanish `A` is Árbol, French `A` is Avion, Punjabi `ੳ` is ਊਠ`.

English ships with a complete illustrated scene for every letter. Other languages reuse the closest scene where it still makes sense, and fall back to a letter-playground composition when a custom picture is missing. To illustrate a new language properly, drop files into `assets/illustrations/scenes/` named `scene-<stem>.png` and set `"image": "<stem>"` in that language's JSON.

## Content file format

`content/en.json` (and the others) follow `content/schema.json`. A letter looks like this:

```json
{
  "letter": "A",
  "uppercase": "A",
  "lowercase": "a",
  "word": "Apple",
  "pronunciation": "AP-ul",
  "sentence": "Apple starts with A.",
  "fact": "An apple is a crunchy fruit that grows on a tree.",
  "image": "apple",
  "action": "Pip takes a happy bite of a shiny red apple.",
  "pip": { "x": 52, "y": 46, "scale": 1, "rotate": -8 }
}
```

`pip` places the mascot sticker on the giant letter (percent of the letter stage). Change the word, sentence, fact, and image — the page design stays the same.

Front matter, tracing labels, matching pairs, and the certificate are all in the same JSON, so a Hindi or French edition is not an English book with swapped letters.

## Typography (commercial-safe)

All fonts are **SIL Open Font License** and may be embedded in a book you sell:

| Script | Display | Body |
| --- | --- | --- |
| English / Spanish / French | Fredoka | Nunito (latin + latin-ext) |
| Hindi / Devanagari | Baloo 2 | Baloo 2 |
| Punjabi / Gurmukhi | Baloo Paaji 2 | Baloo Paaji 2 |

Spanish Ñ/á and French É/ç/î use Nunito + Fredoka latin-ext. Do not substitute system “fun” fonts that you do not have a license to embed.

Before publishing, set `author` and `publisher` in `config/book.json`.

## KDP upload checklist

1. Build with `--no-cover --pdf`.
2. Note `page_count` and `spine_in_white_paper` in `output/<lang>/build-info.json`.
3. Interior PDF: 8.75 × 8.75 in, no crop marks, fonts embedded, bleed to the edge.
4. Cover: use KDP’s cover calculator, or finish `cover-wrap.html` at the spine width printed in `build-info.json`.
5. KDP paperback settings: trim **8.5 × 8.5 in**, **Bleed**, interior **Premium color** or **Standard color**, paper **White**.
6. Proof the printed copy. Check gutter on the binding edge of every spread, and confirm Hindi/Punjabi vowel signs are not clipped.

## Replacing illustrations

Scenes are 1:1 paintings of Pip with the object. Keep new art:

- Square, at least **2625 × 2625 px** (8.75 in at 300 dpi)
- Same fox: coral fur, cream belly, sage scarf
- No letters or words in the picture (type lives on the page)
- Muted, print-friendly color (avoid neon RGB)

Replace `assets/illustrations/cover-art.png` and `assets/illustrations/mascot/pip-wave.png` the same way.

## Design idea

This is not a worksheet stacked on clip-art.

On the **left** page the letter is a playground — cream fill, thick rounded stroke — and Pip sits on it like a sticker. On the **right** page Pip is *in* the world of the word: eating the apple, flying the kite, riding the whale. That repeating joke is the book.

## License notes

- **Fonts:** SIL OFL (Nunito, Fredoka, Baloo 2, Baloo Paaji 2). Keep the font files with the project.
- **Layout and content files:** yours to use for your own published editions.
- **Generated illustrations:** created for this template. Review Amazon’s and your own rights needs before a wide commercial release; commissioning a final illustration pass is the usual path to a bookstore-grade edition.
