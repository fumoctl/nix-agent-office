#!/usr/bin/env node
/**
 * Render Mermaid diagram sources to high-DPI PNGs for embedding in a .docx.
 *
 * Word cannot render Mermaid, so every diagram becomes a raster image at 3x scale
 * (≈288 dpi) — sharp in print, and small enough that the .docx stays a few MB.
 *
 * Usage:
 *   node render_mermaid.js diagrams/arch.mmd diagrams/er.mmd --out assets --scale 3
 *   node render_mermaid.js diagram.html --out assets            # pre-built HTML page
 *
 * A .mmd file may carry its own `%%{init: {...}}%%` theme directive; otherwise the
 * default theme below (navy/indigo, matching the report palette) is injected.
 * Output: <out>/<basename>.png, tightly cropped to the SVG.
 */
const path = require('path');
const fs = require('fs');
const os = require('os');

const PW = '/opt/computersetup/abacusai_computer/tools/html2pdf/node_modules/playwright';
let pwMod;
try {
  pwMod = require(fs.existsSync(PW) ? PW : 'playwright');
} catch (_) {
  pwMod = require('playwright-core');
}
const { chromium } = pwMod;

const args = process.argv.slice(2);
const inputs = args.filter((a) => !a.startsWith('--') && !isValue(a));
function isValue(a) {
  const flags = ['--out', '--scale', '--width', '--height', '--theme'];
  const i = args.indexOf(a);
  return i > 0 && flags.includes(args[i - 1]);
}
const opt = (name, dflt) => (args.includes(name) ? args[args.indexOf(name) + 1] : dflt);

const OUT = opt('--out', 'assets');
const SCALE = parseFloat(opt('--scale', '3'));
const WIDTH = parseInt(opt('--width', '1100'), 10);
const HEIGHT = parseInt(opt('--height', '900'), 10);
const THEME = opt('--theme', 'base');

const THEME_VARS = {
  base: {
    primaryColor: '#E7EEFB', primaryBorderColor: '#36519E', primaryTextColor: '#122641',
    lineColor: '#36519E', fontSize: '15px', clusterBkg: '#F5F7FB', clusterBorder: '#A6B6CC',
  },
  default: {}, dark: {}, forest: {}, neutral: {},
};

if (!inputs.length) {
  console.error('usage: node render_mermaid.js <file.mmd|file.html> [...] --out assets --scale 3');
  process.exit(1);
}
fs.mkdirSync(OUT, { recursive: true });

function pageFor(file) {
  const src = fs.readFileSync(file, 'utf8');
  if (file.endsWith('.html')) return { url: 'file://' + path.resolve(file), tmp: null };
  const init = src.includes('%%{init') ? '' :
    `%%{init: ${JSON.stringify({ theme: THEME, themeVariables: THEME_VARS[THEME] || {} })}}%%\n`;
  const html = `<!DOCTYPE html><html><head><meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
<style>body{margin:0;padding:16px;background:#fff;font-family:Arial,Helvetica,sans-serif}</style>
</head><body><pre class="mermaid">${init}${src}</pre>
<script>mermaid.initialize({startOnLoad:true});</script></body></html>`;
  const tmp = path.join(os.tmpdir(), 'mmd_' + path.basename(file) + '.html');
  fs.writeFileSync(tmp, html);
  return { url: 'file://' + tmp, tmp };
}

(async () => {
  const browser = await chromium.launch();
  for (const file of inputs) {
    const { url, tmp } = pageFor(file);
    const page = await browser.newPage({ deviceScaleFactor: SCALE, viewport: { width: WIDTH, height: HEIGHT } });
    await page.goto(url);
    await page.waitForSelector('.mermaid svg', { timeout: 30000 });
    await page.waitForTimeout(800); // let fonts settle before the screenshot
    const el = await page.$('.mermaid svg');
    const out = path.join(OUT, path.basename(file).replace(/\.(mmd|html)$/, '') + '.png');
    await el.screenshot({ path: out });
    const box = await el.boundingBox();
    console.log('ok', out, Math.round(box.width * SCALE) + 'x' + Math.round(box.height * SCALE));
    await page.close();
    if (tmp) fs.unlinkSync(tmp);
  }
  await browser.close();
})();
