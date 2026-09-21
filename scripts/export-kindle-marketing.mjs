#!/usr/bin/env node
/**
 * Export KDP A+ images + a 15s English Kindle showcase video.
 * Usage: node scripts/export-kindle-marketing.mjs
 */
import { pathToFileURL } from "node:url";
import path from "node:path";
import fs from "node:fs";
import { spawnSync } from "node:child_process";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const OUT = path.join(ROOT, "marketing", "en-kindle");
const IMG = path.join(OUT, "images");
const PAGES = path.join(OUT, "_pages");
const VIDEO = path.join(OUT, "video");

const ASSETS = path.join(ROOT, "assets", "illustrations");
const FONTS = path.join(ROOT, "assets", "fonts", "book");

function url(p) {
  return pathToFileURL(p).href;
}

function fontFace() {
  const faces = [
    ["Nunito", 400, "nunito-latin-400-normal.woff2"],
    ["Nunito", 600, "nunito-latin-600-normal.woff2"],
    ["Nunito", 700, "nunito-latin-700-normal.woff2"],
    ["Nunito", 800, "nunito-latin-800-normal.woff2"],
    ["Fredoka", 500, "fredoka-latin-500-normal.woff2"],
    ["Fredoka", 600, "fredoka-latin-600-normal.woff2"],
    ["Fredoka", 700, "fredoka-latin-700-normal.woff2"],
  ];
  return faces
    .map(
      ([family, weight, file]) => `@font-face {
  font-family: "${family}";
  font-style: normal;
  font-weight: ${weight};
  font-display: block;
  src: url("${url(path.join(FONTS, file))}") format("woff2");
}`
    )
    .join("\n");
}

const TOKENS = `
:root {
  --cream: #f6efe3;
  --cream-deep: #efe4d2;
  --ink: #3d342c;
  --ink-soft: #6a5e52;
  --coral: #d45d4a;
  --coral-deep: #a33f32;
  --sage: #5d9a6e;
  --honey: #d4a017;
  --sky: #4a8fbf;
  --white: #fffdf8;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 100%; height: 100%; overflow: hidden; }
body {
  font-family: Nunito, sans-serif;
  color: var(--ink);
  background: var(--cream);
  -webkit-font-smoothing: antialiased;
}
.display { font-family: Fredoka, sans-serif; font-weight: 600; letter-spacing: -0.02em; }
`;

function board(width, height, inner, extraCss = "") {
  return `<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
${fontFace()}
${TOKENS}
${extraCss}
</style></head>
<body>${inner}</body></html>`;
}

async function waitForAssets(page) {
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(async () => {
    const imgs = [...document.images];
    await Promise.all(
      imgs.map((img) => {
        if (img.complete && img.naturalWidth) return;
        return new Promise((res) => {
          img.addEventListener("load", res, { once: true });
          img.addEventListener("error", res, { once: true });
        });
      })
    );
  });
  await page.waitForTimeout(80);
}

async function screenshotHtml(page, html, dest, width, height, type = "png") {
  const tmp = path.join(OUT, "_board.html");
  fs.writeFileSync(tmp, html);
  await page.setViewportSize({ width, height });
  await page.goto(url(tmp), { waitUntil: "networkidle" });
  await waitForAssets(page);
  const opts = { path: dest, type, omitBackground: false };
  if (type === "jpeg") opts.quality = 92;
  await page.screenshot(opts);
}

async function captureBookPages(browser) {
  fs.mkdirSync(PAGES, { recursive: true });
  const ctx = await browser.newContext({
    viewport: { width: 900, height: 900 },
    deviceScaleFactor: 2,
  });
  const page = await ctx.newPage();

  async function shotFile(file, selector, dest) {
    await page.goto(url(file), { waitUntil: "networkidle" });
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(250);
    const el = page.locator(selector).first();
    await el.screenshot({ path: dest, type: "png" });
  }

  const cover = path.join(ROOT, "output", "en-kindle", "cover-front.html");
  const interior = path.join(ROOT, "output", "en-kindle", "interior.html");

  await shotFile(cover, "section.page.cover", path.join(PAGES, "cover.png"));

  const pages = {
    meet: 3,
    how: 4,
    aLeft: 5,
    aRight: 6,
    bLeft: 7,
    bRight: 8,
    cRight: 10,
    kLeft: 25,
    kRight: 26,
    rRight: 40,
    wRight: 50,
    review: 57,
    celebrate: 58,
  };
  for (const [name, n] of Object.entries(pages)) {
    await shotFile(
      interior,
      `section.page[data-page="${n}"]`,
      path.join(PAGES, `${name}.png`)
    );
  }
  await ctx.close();
}

function aPlusBoards() {
  const cover = url(path.join(PAGES, "cover.png"));
  const aLeft = url(path.join(PAGES, "aLeft.png"));
  const pip = url(path.join(ASSETS, "mascot", "pip-wave.png"));
  const pipC = url(path.join(ASSETS, "mascot", "pip-celebrate.png"));
  const art = url(path.join(ASSETS, "cover-art.png"));
  const apple = url(path.join(ASSETS, "scenes", "scene-apple.png"));
  const ball = url(path.join(ASSETS, "scenes", "scene-ball.png"));
  const kite = url(path.join(ASSETS, "scenes", "scene-kite.png"));
  const rainbow = url(path.join(ASSETS, "scenes", "scene-rainbow.png"));
  const whale = url(path.join(ASSETS, "scenes", "scene-whale.png"));
  const cat = url(path.join(ASSETS, "scenes", "scene-cat.png"));

  return {
    "01-logo-600x180.png": {
      w: 600,
      h: 180,
      html: board(
        600,
        180,
        `<div class="logo">
          <img src="${pip}" alt="">
          <div>
            <p class="kicker">Publisher</p>
            <h1 class="display">Infinity Hub</h1>
          </div>
        </div>`,
        `.logo { display:flex; align-items:center; gap:22px; height:100%; padding:18px 28px; background: #f8eee6; }
         img { width: 128px; height: 128px; object-fit: contain; }
         .kicker { font-size: 13px; font-weight: 800; letter-spacing: 0.22em; text-transform: uppercase; color: var(--coral-deep); }
         h1 { font-size: 42px; color: var(--coral); line-height: 1; margin-top: 2px; }`
      ),
    },
    "02-header-970x600.jpg": {
      w: 970,
      h: 600,
      type: "jpeg",
      html: board(
        970,
        600,
        `<div class="hero">
          <img class="bg" src="${art}" alt="">
          <div class="scrim"></div>
          <img class="page" src="${cover}" alt="">
        </div>`,
        `.hero { position:relative; width:100%; height:100%; background:#f6efe3; }
         .bg { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; object-position:50% 42%; filter:saturate(0.95); }
         .scrim { position:absolute; inset:0; background:
            linear-gradient(90deg, rgba(246,239,227,0.18) 0%, rgba(246,239,227,0.08) 40%, rgba(61,52,44,0.12) 100%); }
         .page { position:absolute; right:54px; top:50%; transform:translateY(-50%) rotate(3deg);
            width: 330px; height: 330px; object-fit:cover; border-radius: 18px;
            box-shadow: 0 22px 50px rgba(61,52,44,0.28); border: 6px solid #fffdf8; }`
      ),
    },
    "03-overlay-1940x600.jpg": {
      w: 1940,
      h: 600,
      type: "jpeg",
      html: board(
        1940,
        600,
        `<div class="strip">
          <img src="${apple}" alt=""><img src="${kite}" alt=""><img src="${rainbow}" alt=""><img src="${whale}" alt="">
        </div>`,
        `.strip { display:grid; grid-template-columns: repeat(4, 1fr); height:100%; gap: 10px; padding: 10px; background: #efe4d2; }
         img { width:100%; height:100%; object-fit:cover; border-radius: 18px; }`
      ),
    },
    "03-overlay-970x300.jpg": {
      w: 970,
      h: 300,
      type: "jpeg",
      html: board(
        970,
        300,
        `<div class="strip">
          <img src="${apple}" alt=""><img src="${kite}" alt=""><img src="${rainbow}" alt="">
        </div>`,
        `.strip { display:grid; grid-template-columns: repeat(3, 1fr); height:100%; gap: 8px; padding: 8px; background: #efe4d2; }
         img { width:100%; height:100%; object-fit:cover; border-radius: 14px; }`
      ),
    },
    "04-three-look-600x600.jpg": {
      w: 600,
      h: 600,
      type: "jpeg",
      html: board(
        600,
        600,
        `<img src="${aLeft}" alt="">`,
        `img { width:100%; height:100%; object-fit:cover; object-position:50% 42%; }`
      ),
    },
    "04-three-say-600x600.jpg": {
      w: 600,
      h: 600,
      type: "jpeg",
      html: board(600, 600, `<img src="${apple}" alt="">`, `img { width:100%; height:100%; object-fit:cover; }`),
    },
    "04-three-find-600x600.jpg": {
      w: 600,
      h: 600,
      type: "jpeg",
      html: board(600, 600, `<img src="${kite}" alt="">`, `img { width:100%; height:100%; object-fit:cover; }`),
    },
    "05-four-apple-220x220.jpg": {
      w: 220,
      h: 220,
      type: "jpeg",
      html: board(220, 220, `<img src="${apple}" alt="">`, `img { width:100%; height:100%; object-fit:cover; }`),
    },
    "05-four-ball-220x220.jpg": {
      w: 220,
      h: 220,
      type: "jpeg",
      html: board(220, 220, `<img src="${ball}" alt="">`, `img { width:100%; height:100%; object-fit:cover; }`),
    },
    "05-four-kite-220x220.jpg": {
      w: 220,
      h: 220,
      type: "jpeg",
      html: board(220, 220, `<img src="${kite}" alt="">`, `img { width:100%; height:100%; object-fit:cover; }`),
    },
    "05-four-rainbow-220x220.jpg": {
      w: 220,
      h: 220,
      type: "jpeg",
      html: board(220, 220, `<img src="${rainbow}" alt="">`, `img { width:100%; height:100%; object-fit:cover; }`),
    },
    "06-sidebar-main-300x400.jpg": {
      w: 300,
      h: 400,
      type: "jpeg",
      html: board(
        300,
        400,
        `<div class="card"><img src="${pip}" alt=""></div>`,
        `.card { width:100%; height:100%; background: radial-gradient(circle at 50% 38%, #f8eee6, #efe4d2);
           display:flex; align-items:center; justify-content:center; }
         img { width: 250px; height: 250px; object-fit: contain; }`
      ),
    },
    "06-sidebar-350x175.jpg": {
      w: 350,
      h: 175,
      type: "jpeg",
      html: board(
        350,
        175,
        `<img src="${art}" alt="">`,
        `img { width:100%; height:100%; object-fit:cover; object-position:50% 58%; }`
      ),
    },
    "07-single-left-600x180.jpg": {
      w: 600,
      h: 180,
      type: "jpeg",
      html: board(
        600,
        180,
        `<div class="row"><img src="${pipC}" alt=""><img src="${apple}" alt=""><img src="${kite}" alt=""></div>`,
        `.row { display:grid; grid-template-columns: 180px 1fr 1fr; height:100%; gap:8px; padding:8px; background:#efe4d2; }
         img { width:100%; height:100%; object-fit:cover; border-radius:12px; background:#f8eee6; object-position:center; }`
      ),
    },
    "08-video-poster-1920x1080.jpg": {
      w: 1920,
      h: 1080,
      type: "jpeg",
      html: board(
        1920,
        1080,
        `<div class="poster">
          <img class="bg" src="${art}" alt="">
          <div class="wash"></div>
          <div class="copy">
            <p class="kicker">Kindle eBook</p>
            <h1 class="display">Pip’s Alphabet</h1>
            <p class="sub">A letter adventure with Pip the fox</p>
            <p class="age">Ages 2–8 · Look · Say · Find Pip</p>
          </div>
          <img class="cover" src="${cover}" alt="">
        </div>`,
        `.poster { position:relative; width:100%; height:100%; }
         .bg { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }
         .wash { position:absolute; inset:0; background: linear-gradient(90deg, rgba(246,239,227,0.92) 0%, rgba(246,239,227,0.55) 46%, rgba(246,239,227,0.12) 100%); }
         .copy { position:absolute; left:90px; top:50%; transform:translateY(-50%); max-width: 820px; }
         .kicker { font-size: 22px; font-weight: 800; letter-spacing: 0.22em; text-transform: uppercase; color: var(--coral-deep); }
         h1 { font-size: 108px; line-height: 0.92; color: #c94b3a; margin: 10px 0 18px; }
         .sub { font-size: 32px; font-weight: 700; color: var(--ink); }
         .age { margin-top: 22px; font-size: 22px; font-weight: 800; color: var(--ink-soft); }
         .cover { position:absolute; right:110px; top:50%; transform:translateY(-50%) rotate(4deg); width: 520px; height: 520px;
            object-fit:cover; border-radius: 28px; border: 10px solid #fffdf8; box-shadow: 0 28px 70px rgba(61,52,44,0.3); }`
      ),
    },
    "08-video-poster-1464x600.jpg": {
      w: 1464,
      h: 600,
      type: "jpeg",
      html: board(
        1464,
        600,
        `<div class="poster">
          <img class="bg" src="${art}" alt="">
          <div class="wash"></div>
          <div class="copy">
            <p class="kicker">Kindle eBook</p>
            <h1 class="display">Pip’s Alphabet</h1>
            <p class="sub">Look, say, and find Pip — A to Z</p>
          </div>
          <img class="cover" src="${cover}" alt="">
        </div>`,
        `.poster { position:relative; width:100%; height:100%; }
         .bg { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; object-position:50% 40%; }
         .wash { position:absolute; inset:0; background: linear-gradient(90deg, rgba(246,239,227,0.92) 0%, rgba(246,239,227,0.5) 50%, rgba(246,239,227,0.1) 100%); }
         .copy { position:absolute; left:72px; top:50%; transform:translateY(-50%); }
         .kicker { font-size: 18px; font-weight: 800; letter-spacing: 0.22em; text-transform: uppercase; color: var(--coral-deep); }
         h1 { font-size: 84px; line-height: 0.92; color: #c94b3a; margin: 8px 0 12px; }
         .sub { font-size: 26px; font-weight: 700; }
         .cover { position:absolute; right:80px; top:50%; transform:translateY(-50%) rotate(3deg); width: 420px; height: 420px;
            object-fit:cover; border-radius: 24px; border: 8px solid #fffdf8; box-shadow: 0 22px 50px rgba(61,52,44,0.28); }`
      ),
    },
  };
}

function slideshowHtml() {
  const cover = url(path.join(PAGES, "cover.png"));
  const meet = url(path.join(PAGES, "meet.png"));
  const how = url(path.join(PAGES, "how.png"));
  const aLeft = url(path.join(PAGES, "aLeft.png"));
  const aRight = url(path.join(PAGES, "aRight.png"));
  const bRight = url(path.join(PAGES, "bRight.png"));
  const cRight = url(path.join(PAGES, "cRight.png"));
  const kRight = url(path.join(PAGES, "kRight.png"));
  const rRight = url(path.join(PAGES, "rRight.png"));
  const celebrate = url(path.join(PAGES, "celebrate.png"));
  const art = url(path.join(ASSETS, "cover-art.png"));
  const pip = url(path.join(ASSETS, "mascot", "pip-celebrate.png"));
  const apple = url(path.join(ASSETS, "scenes", "scene-apple.png"));
  const kite = url(path.join(ASSETS, "scenes", "scene-kite.png"));
  const rainbow = url(path.join(ASSETS, "scenes", "scene-rainbow.png"));
  const whale = url(path.join(ASSETS, "scenes", "scene-whale.png"));

  return `<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
${fontFace()}
${TOKENS}
body { background: #1c1713; }
.stage { position: relative; width: 1920px; height: 1080px; overflow: hidden; background: #f6efe3; }
.slide { position: absolute; inset: 0; opacity: 0; transition: opacity 0.35s ease; }
.slide.on { opacity: 1; }
.bg { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; filter: saturate(0.9); }
.wash { position:absolute; inset:0; }
.wash-left { background: linear-gradient(90deg, rgba(246,239,227,0.94) 0%, rgba(246,239,227,0.72) 42%, rgba(246,239,227,0.12) 100%); }
.wash-full { background: linear-gradient(180deg, rgba(246,239,227,0.2), rgba(246,239,227,0.55)); }
.copy { position:absolute; left: 96px; top: 50%; transform: translateY(-50%); max-width: 760px; z-index: 3; }
.kicker { font-size: 22px; font-weight: 800; letter-spacing: 0.22em; text-transform: uppercase; color: var(--coral-deep); margin-bottom: 12px; }
h1 { font-size: 92px; line-height: 0.92; color: #c94b3a; margin-bottom: 16px; }
.sub { font-size: 30px; font-weight: 700; }
.chip { display:inline-block; margin-top: 22px; padding: 10px 20px; border-radius: 999px; background: rgba(255,253,248,0.9); font-weight: 800; font-size: 20px; color: var(--coral-deep); }
.frame { position:absolute; border-radius: 28px; overflow:hidden; box-shadow: 0 28px 70px rgba(61,52,44,0.28); border: 10px solid #fffdf8; background: #fffdf8; }
.frame img { width:100%; height:100%; object-fit: cover; }
.book { right: 110px; top: 50%; transform: translateY(-50%) rotate(3deg); width: 540px; height: 540px; }
.spread { display:flex; gap: 22px; position:absolute; left: 50%; top: 50%; transform: translate(-50%, -54%); }
.spread .frame { position:relative; right:auto; top:auto; transform:none; width: 430px; height: 430px; }
.grid { position:absolute; left: 96px; right: 96px; top: 210px; display:grid; grid-template-columns: repeat(4, 1fr); gap: 22px; }
.grid .frame { position:relative; width:100%; height: 430px; transform:none; right:auto; top:auto; }
.caption { position:absolute; left: 0; right: 0; bottom: 54px; text-align:center; z-index: 4; }
.caption h2 { font-size: 48px; color: #c94b3a; }
.caption p { font-size: 24px; font-weight: 700; color: var(--ink-soft); margin-top: 6px; }
.end { position:relative; z-index: 5; display:flex; align-items:center; justify-content:center; gap: 56px; height:100%; padding: 0 80px; }
.end .text { max-width: 860px; background: rgba(246,239,227,0.88); padding: 36px 44px; border-radius: 28px; }
.end h1 { font-size: 72px; }
.pip { width: 360px; height: 360px; object-fit: contain; filter: drop-shadow(0 18px 24px rgba(61,52,44,0.2)); }
.zoom { animation: ken 2.6s linear forwards; }
@keyframes ken { from { transform: scale(1); } to { transform: scale(1.08); } }
.hero-cover.zoom { transform-origin: 60% 40%; }
</style></head>
<body>
<div class="stage">
  <div class="slide on" data-ms="2600" id="s1">
    <img class="bg zoom hero-cover" src="${art}" alt="">
    <div class="wash wash-left"></div>
    <div class="copy">
      <p class="kicker">Kindle eBook</p>
      <h1 class="display">Pip’s Alphabet</h1>
      <p class="sub">A letter adventure with Pip the fox</p>
      <span class="chip">Ages 2–8</span>
    </div>
    <div class="frame book"><img src="${cover}" alt=""></div>
  </div>
  <div class="slide" data-ms="2400" id="s2">
    <img class="bg" src="${art}" alt="" style="filter:blur(18px) saturate(0.8); transform:scale(1.2);">
    <div class="wash wash-full"></div>
    <div class="frame book" style="right:auto; left: 160px; transform: translateY(-50%) rotate(-3deg);"><img src="${meet}" alt=""></div>
    <div class="copy" style="left:auto; right: 120px; max-width: 640px;">
      <p class="kicker">Meet Pip</p>
      <h1 class="display">A small fox with a big curiosity</h1>
      <p class="sub">Pip climbs every letter — then acts out the word.</p>
    </div>
  </div>
  <div class="slide" data-ms="2500" id="s3">
    <div class="spread">
      <div class="frame"><img src="${aLeft}" alt=""></div>
      <div class="frame"><img src="${aRight}" alt=""></div>
    </div>
    <div class="caption">
      <h2 class="display">Giant letters. A picture for every word.</h2>
      <p>Look at A. Say Apple. Find Pip.</p>
    </div>
  </div>
  <div class="slide" data-ms="2500" id="s4">
    <div class="caption" style="top: 64px; bottom:auto;">
      <h2 class="display">26 illustrated letter adventures</h2>
    </div>
    <div class="grid">
      <div class="frame"><img src="${apple}" alt=""></div>
      <div class="frame"><img src="${bRight}" alt=""></div>
      <div class="frame"><img src="${kite}" alt=""></div>
      <div class="frame"><img src="${rainbow}" alt=""></div>
    </div>
  </div>
  <div class="slide" data-ms="2500" id="s5">
    <img class="bg" src="${art}" alt="" style="filter:blur(18px) saturate(0.8); transform:scale(1.2);">
    <div class="wash wash-full"></div>
    <div class="frame book" style="right:auto; left:50%; transform:translate(-50%,-58%) rotate(-1deg);"><img src="${how}" alt=""></div>
    <div class="caption">
      <h2 class="display">Look · Say · Find Pip · Discover</h2>
      <p>A read-together picture book — no tracing, just wonder.</p>
    </div>
  </div>
  <div class="slide" data-ms="2500" id="s6">
    <img class="bg" src="${whale}" alt="" style="object-position:50% 40%;">
    <div class="wash wash-left"></div>
    <div class="end">
      <img class="pip" src="${pip}" alt="">
      <div class="text">
        <p class="kicker">Now on Kindle</p>
        <h1 class="display">Come discover every letter with Pip</h1>
        <p class="sub">Pip’s Alphabet Adventures · Infinity Hub</p>
        <span class="chip">A to Z · Ages 2–8</span>
      </div>
    </div>
  </div>
</div>
<script>
(async () => {
  await document.fonts.ready;
  await Promise.all([...document.images].map((img) => {
    if (img.complete && img.naturalWidth) return;
    return new Promise((res) => {
      img.addEventListener("load", res, { once: true });
      img.addEventListener("error", res, { once: true });
    });
  }));
  const slides = [...document.querySelectorAll(".slide")];
  for (let i = 0; i < slides.length; i++) {
    slides.forEach((s) => s.classList.remove("on"));
    slides[i].classList.add("on");
    const ms = Number(slides[i].dataset.ms || 2500);
    await new Promise((r) => setTimeout(r, ms));
  }
  document.body.dataset.done = "1";
})();
</script>
</body></html>`;
}

function writeCopy() {
  const text = `# Pip’s Alphabet — English Kindle A+ pack

Upload folder: \`marketing/en-kindle/images\`
Video: \`marketing/en-kindle/video/pips-alphabet-en-kindle-15s.mp4\`

KDP A+ allows **up to 5 modules**. Amazon does not resize uploads — use the pixel sizes below. JPG/PNG, RGB, under 2 MB. Do not paste prices, reviews, “bestseller,” or “buy now.”

A+ images are **interior and collage art**, not a repeat of the storefront cover (Amazon asks for unique A+ visuals).

## Recommended 5-module layout

### 1. Standard Image Header with Text
- Image: \`02-header-970x600.jpg\` (970 × 600)
- Alt text: \`Pip the fox on a grassy hill holding a red apple, with the Pip’s Alphabet Kindle cover beside him.\`
- Headline: \`A letter adventure with Pip the fox\`
- Body: \`From A to Z, Pip climbs giant letters, acts out a new word, and hides in every picture. Look, say, and discover together — a read-aloud Kindle picture book for ages 2 to 8.\`

### 2. Standard Three Images and Text
- Images (600 × 600, recommended high-res):
  1. \`04-three-look-600x600.jpg\`
  2. \`04-three-say-600x600.jpg\`
  3. \`04-three-find-600x600.jpg\`
- Alt 1: \`Kindle page with a giant letter A and Pip the fox sitting on it.\`
- Headline 1: \`Look\`
- Body 1: \`Point to the giant letter. Say its name together.\`
- Alt 2: \`Pip the fox sitting in the grass taking a bite of a shiny red apple.\`
- Headline 2: \`Say\`
- Body 2: \`Say the sound, then say the word out loud. A short fun fact sits under every picture.\`
- Alt 3: \`Pip the fox running across a hill while flying an orange and green kite.\`
- Headline 3: \`Find Pip\`
- Body 3: \`Pip is in every scene. Where is Pip hiding this time, and what is Pip doing?\`

### 3. Standard Image & Text Overlay
- Prefer: \`03-overlay-1940x600.jpg\` (1940 × 600)
- Fallback if the module only accepts 970 × 300: \`03-overlay-970x300.jpg\`
- Leave baked-in image text empty — add the overlay in KDP:
- Alt text: \`Four interior scenes of Pip with an apple, a kite, a rainbow, and a whale.\`
- Headline: \`26 illustrated letter adventures\`
- Body: \`Each letter gets a playground page and a picture page. Pip tastes apples, flies kites, points at rainbows, and more — one discovery after another, all the way to Z.\`

### 4. Standard Four Images and Text
- Images (220 × 220):
  1. \`05-four-apple-220x220.jpg\`
  2. \`05-four-ball-220x220.jpg\`
  3. \`05-four-kite-220x220.jpg\`
  4. \`05-four-rainbow-220x220.jpg\`
- Alt 1: \`Pip hugging a big red apple.\` / Headline: \`A is for Apple\`
- Alt 2: \`Pip bouncing a striped ball.\` / Headline: \`B is for Ball\`
- Alt 3: \`Pip flying a kite on a windy hill.\` / Headline: \`K is for Kite\`
- Alt 4: \`Pip pointing up at a rainbow.\` / Headline: \`R is for Rainbow\`

### 5. Standard Single Image & Sidebar
- Main image: \`06-sidebar-main-300x400.jpg\` (300 × 400)
- Sidebar image: \`06-sidebar-350x175.jpg\` (350 × 175)
- Alt main: \`Pip the fox waving, wearing a sage-green knitted scarf.\`
- Alt sidebar: \`Pip sitting on a flower hill with a ball, a smiling sun, and a green kite.\`
- Headline: \`Meet Pip\`
- Body: \`Pip is a small fox with a very big curiosity. On every page Pip is discovering something new — and so is your little reader.\`
- Sidebar headline: \`How to read it\`
- Sidebar body:
  - Look at the giant letter
  - Say the sound and the word
  - Find Pip in the picture
  - Talk about the fun fact

## Optional extras

- Logo (use once): \`01-logo-600x180.png\` (600 × 180)
- Single left image: \`07-single-left-600x180.jpg\` (600 × 180; 600 × 600 is also accepted — this file is the minimum width)
- Video poster 16:9: \`08-video-poster-1920x1080.jpg\`
- Video poster wide: \`08-video-poster-1464x600.jpg\` (Premium A+ preview size, if a marketplace ever offers it)

## 15-second video

File: \`video/pips-alphabet-en-kindle-15s.mp4\`
- 1920 × 1080, H.264, ~15 seconds, silent (add music in ads if the campaign requires audio)
- Story: cover → Meet Pip → A/Apple spread → four scenes → how to read → end card

KDP **Standard A+ does not include a video module**. Use this file for:
- Amazon Ads / Sponsored Brands video
- Author Central, social, or a listing video field if your marketplace shows one
- Premium A+ video (Seller Central only — not typical for KDP books)

## A+ checklist

1. KDP → Marketing → A+ Content Manager → Create A+ Content
2. Add the five modules in the order above
3. Apply the Kindle ASIN (not the paperback)
4. Submit for review (often a few days)
`;
  fs.writeFileSync(path.join(OUT, "COPY.md"), text);
}

function findFfmpeg() {
  const candidates = ["ffmpeg", "/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg"];
  for (const c of candidates) {
    const r = spawnSync(c, ["-version"], { encoding: "utf8" });
    if (r.status === 0) return c;
  }
  return null;
}

async function recordVideo(browser) {
  fs.mkdirSync(VIDEO, { recursive: true });
  const htmlPath = path.join(OUT, "_slideshow.html");
  fs.writeFileSync(htmlPath, slideshowHtml());

  const ctx = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 1,
    recordVideo: { dir: VIDEO, size: { width: 1920, height: 1080 } },
  });
  const page = await ctx.newPage();
  await page.goto(url(htmlPath), { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForFunction(() => document.body.dataset.done === "1", null, {
    timeout: 20000,
  });
  await page.waitForTimeout(200);
  const v = page.video();
  await ctx.close();
  const webm = await v.path();
  const mp4 = path.join(VIDEO, "pips-alphabet-en-kindle-15s.mp4");
  const ffmpeg = findFfmpeg();
  if (!ffmpeg) {
    console.warn("ffmpeg not found; left WebM at", webm);
    return webm;
  }
  const r = spawnSync(
    ffmpeg,
    [
      "-y",
      "-i",
      webm,
      "-an",
      "-c:v",
      "libx264",
      "-crf",
      "18",
      "-pix_fmt",
      "yuv420p",
      "-vf",
      "scale=1920:1080,fps=30,trim=duration=15,setpts=PTS-STARTPTS",
      "-movflags",
      "+faststart",
      mp4,
    ],
    { encoding: "utf8" }
  );
  if (r.status !== 0) {
    console.error(r.stderr);
    throw new Error("ffmpeg failed");
  }
  try {
    fs.unlinkSync(webm);
  } catch {}
  return mp4;
}

async function main() {
  fs.mkdirSync(IMG, { recursive: true });
  fs.mkdirSync(PAGES, { recursive: true });
  fs.mkdirSync(VIDEO, { recursive: true });

  let chromium;
  try {
    ({ chromium } = require("playwright"));
  } catch {
    throw new Error("Playwright is not installed. Run: npm install playwright && npx playwright install chromium");
  }

  const browser = await chromium.launch();
  console.log("Capturing Kindle pages…");
  await captureBookPages(browser);

  console.log("Rendering A+ images…");
  const page = await browser.newPage();
  const boards = aPlusBoards();
  for (const [name, spec] of Object.entries(boards)) {
    if (!spec || !spec.html) continue;
    const dest = path.join(IMG, name);
    const type = spec.type === "jpeg" ? "jpeg" : "png";
    await screenshotHtml(page, spec.html, dest, spec.w, spec.h, type);
    const kb = Math.round(fs.statSync(dest).size / 1024);
    console.log(`  ${name}  ${spec.w}×${spec.h}  ${kb} KB`);
  }
  await page.close();

  writeCopy();
  console.log("Recording 15s video…");
  const videoPath = await recordVideo(browser);
  await browser.close();
  console.log("Wrote", videoPath);
  for (const extra of ["_board.html", "_slideshow.html"]) {
    try { fs.unlinkSync(path.join(OUT, extra)); } catch {}
  }
  console.log("Copy sheet:", path.join(OUT, "COPY.md"));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
