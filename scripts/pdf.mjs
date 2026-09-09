#!/usr/bin/env node
/**
 * Print a PDF from a book HTML file.
 * Uses CSS @page size when present (cover wrap), else 8.75in × 8.75in interior.
 * Usage: node scripts/pdf.mjs output/en/interior.html output/en/interior.pdf
 */
import { pathToFileURL } from "node:url";
import path from "node:path";
import fs from "node:fs";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);

function pageSizeFromHtml(html) {
  const atPage = html.match(/@page\s*\{[^}]*size:\s*([\d.]+)in\s+([\d.]+)in/i);
  if (atPage) {
    return { width: `${atPage[1]}in`, height: `${atPage[2]}in` };
  }
  const wrap = html.match(/\.wrap\s*\{[^}]*width:\s*([\d.]+)in[^}]*height:\s*([\d.]+)in/i);
  if (wrap) {
    return { width: `${wrap[1]}in`, height: `${wrap[2]}in` };
  }
  return { width: "8.75in", height: "8.75in" };
}

async function main() {
  const htmlPath = path.resolve(process.argv[2]);
  const pdfPath = path.resolve(process.argv[3]);
  if (!fs.existsSync(htmlPath)) {
    throw new Error(`HTML not found: ${htmlPath}`);
  }

  let chromium;
  try {
    ({ chromium } = require("playwright"));
  } catch {
    throw new Error("Playwright is not installed. Run: npm install playwright && npx playwright install chromium");
  }

  const html = fs.readFileSync(htmlPath, "utf8");
  const size = pageSizeFromHtml(html);

  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "networkidle" });
  await page.emulateMedia({ media: "print" });
  await page.pdf({
    path: pdfPath,
    width: size.width,
    height: size.height,
    printBackground: true,
    preferCSSPageSize: true,
    margin: { top: "0", right: "0", bottom: "0", left: "0" },
  });
  await browser.close();
  console.log(`PDF ${size.width} × ${size.height}`);
}

main().catch((err) => {
  console.error(err.message || err);
  process.exit(1);
});
