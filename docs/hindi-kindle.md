# पिप की वर्णमाला — Hindi Kindle e-book

Read-only children’s picture book for Amazon KDP **Kindle**. Kids look, say the sound, find Pip, and learn the word. There are **no write-in / trace / circle / draw-a-line** pages (Kindle screens cannot be written on).

| | |
| --- | --- |
| Title | पिप की वर्णमाला |
| Subtitle | अक्षरों की एक मज़ेदार यात्रा |
| Age | Ages 2–8 (Latin numerals on the cover) |
| Letters | 49 (अ–ज्ञ, including ऋ, अं, अः, ङ, ञ, ण) |
| Page size | 8.5 × 8.5 in (no bleed) |
| Typical page count | ~104 (see `output/hi-kindle/build-info.json`) |

## Build

```bash
# HTML + EPUB
python3 src/build.py --lang hi --format kindle --no-cover

# Also export PDF previews
python3 src/build.py --lang hi --format kindle --pdf --no-cover
```

Or via npm:

```bash
npm run build:hi:kindle
npm run pdf:hi:kindle
```

## Output (`output/hi-kindle/`)

| File | Use |
| --- | --- |
| `interior.html` | Browser preview (pages stacked vertically) |
| `cover-front.html` / `cover-front.pdf` | Storefront cover |
| `interior.pdf` | Optional proof PDF (not the KDP Kindle manuscript) |
| `pips-alphabet-kindle.epub` | **Upload this as the Kindle manuscript** |
| `build-info.json` | Page count and build notes |

## KDP Kindle upload

1. Build with `--format kindle` (add `--pdf` if you want cover/interior PDF proofs).
2. Manuscript: upload `pips-alphabet-kindle.epub`.
3. Cover: export `cover-front.html` to PNG/JPEG, or use `cover-front.pdf` converted to an image.
4. Book type: Kindle eBook (not paperback).
5. Language: Hindi. Age range: 2–8.
6. Proof on a Kindle device or Kindle Previewer / Kindle Create if you use those tools.

Do **not** upload the paperback interior PDF (`output/hi/interior.pdf`) as a Kindle manuscript — that file includes bleed, worksheets, and print padding.

## Page flow

1. Cover  
2. Title  
3. Copyright (Kindle eBook imprint)  
4. Meet Pip  
5. How to read this book (देखो → बोलो → पिप को ढूँढ़ो → खोजो)  
6. Letter + scene spreads for all 49 letters (no mini-trace strip)  
7. Alphabet review  
8. Celebration page (no name/date fill-in lines)

## Content sources

| File | Role |
| --- | --- |
| `content/hi.json` | Full Hindi book data (letters, words, facts, images) |
| `content/hi-kindle.json` | Kindle-only overlay (how-to copy, celebration, blurb) |
| `styles/kindle.css` | Square pages, no bleed/gutter, hide write-in UI |
| `src/build.py --format kindle` | Skips belongs-to, tracing, games, write practice, padding |
| `src/epub.py` | Packs fixed-layout EPUB |

Kindle copy is merged: `hi.json` + `hi-kindle.json`. The Hindi **paperback** build (`--lang hi` without `--format kindle`) is unchanged and still includes practice pages and games.

## Varnamala word list

| Letter | Word | Scene stem |
| --- | --- | --- |
| अ | अनार | pomegranate |
| आ | आम | mango |
| इ | इमली | tamarind |
| ई | ईख | sugarcane |
| उ | उल्लू | owl |
| ऊ | ऊन | wool |
| ऋ | ऋषि | rishi |
| ए | एड़ी | heel |
| ऐ | ऐनक | glasses |
| ओ | ओखली | mortar |
| औ | औरत | woman |
| अं | अंगूर | grapes |
| अः | अः | visarga |
| क | कुत्ता | dog |
| ख | खिलौना | toys |
| ग | गाय | cow |
| घ | घर | house |
| ङ | गंगा | river |
| च | चांद | moon |
| छ | छतरी | umbrella |
| ज | जहाज़ | ship |
| झ | झंडा | flag |
| ञ | चंचल | playful |
| ट | टोपी | hat |
| ठ | ठेला | cart |
| ड | डमरू | damru |
| ढ | ढोल | dhol |
| ण | बाण | arrow |
| त | तरबूज़ | watermelon |
| थ | थाली | thali |
| द | दूध | milk |
| ध | धनुष | bow |
| न | नाव | boat |
| प | पतंग | kite |
| फ | फल | fruit |
| ब | बिल्ली | cat |
| भ | भेड़ | sheep |
| म | मछली | fish |
| य | यज्ञ | yagya |
| र | रंग | colors |
| ल | लट्टू | spinning-top |
| व | वन | forest |
| श | शेर | lion |
| ष | षट्कोण | hexagon |
| स | सूरज | sun |
| ह | हवा | wind |
| क्ष | क्षीर | kheer |
| त्र | त्रिकोण | triangle |
| ज्ञ | ज्ञान | knowledge |

Scene files live at `assets/illustrations/scenes/scene-<stem>.png`. To change a letter’s picture, replace that PNG (or add a new stem) and set `"image": "<stem>"` on that letter in `content/hi.json`, then rebuild.

## Kindle vs paperback (Hindi)

| | Kindle | Paperback |
| --- | --- | --- |
| Command | `--lang hi --format kindle` | `--lang hi` |
| Output | `output/hi-kindle/` | `output/hi/` |
| Manuscript | EPUB | Interior PDF (8.75 in with bleed) |
| Write-in pages | No | Yes (trace, match, write, certificate lines) |
| Cover | Front only | Front + back + wrap |
| Min page padding | No | Pads toward KDP paperback minimum |

## Typography

Hindi / Devanagari uses **Baloo 2** (SIL OFL), embedded for commercial use. Keep the font files under `assets/fonts/book/`.

## Quick edit checklist

1. Edit words / facts / images in `content/hi.json`.  
2. Edit Kindle-only wording in `content/hi-kindle.json` if needed.  
3. Rebuild: `python3 src/build.py --lang hi --format kindle --pdf --no-cover`.  
4. Open `output/hi-kindle/interior.html` to proof.  
5. Upload EPUB + cover image to KDP.
