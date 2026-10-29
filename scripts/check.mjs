// Checks the built site in dist/ before every review. No dependencies.
// Run after a build: `npm run build && node scripts/check.mjs`
//   1. Every internal link, image and #anchor resolves.
//   2. Visible words have no em dashes or semicolons.
//   3. Text colours meet WCAG AA contrast in both themes (from the tokens).
//   4. Page weight: JavaScript, images, and the home page's first load on a phone.
//   5. Lists any sample content still waiting for real words.
import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { join, dirname, extname } from 'node:path';

const DIST = 'dist';
const BASE = (process.env.BASE_PATH ?? (process.env.BIZCARE_LIVE === '1' ? '/' : '/bizcare-web/')).replace(/\/?$/, '/');
let failures = 0;
const fail = (msg) => {
  failures++;
  console.log(`  ✗ ${msg}`);
};
const ok = (msg) => console.log(`  ✓ ${msg}`);

const walk = (dir) =>
  readdirSync(dir).flatMap((n) => {
    const p = join(dir, n);
    return statSync(p).isDirectory() ? walk(p) : [p];
  });
const files = walk(DIST);
const pages = files.filter((f) => f.endsWith('.html'));
const html = Object.fromEntries(pages.map((p) => [p, readFileSync(p, 'utf8')]));
const decode = (s) =>
  s
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#(\d+);/g, (_, n) => String.fromCharCode(Number(n)))
    .replace(/&#x([0-9a-f]+);/gi, (_, n) => String.fromCharCode(parseInt(n, 16)));

// ---------- 1. Links ----------
console.log('\nLinks and anchors');
const ids = Object.fromEntries(pages.map((p) => [p, new Set([...html[p].matchAll(/\sid="([^"]+)"/g)].map((m) => m[1]))]));
const resolve = (url) => {
  let path = url.split('#')[0].split('?')[0];
  if (!path.startsWith(BASE)) return null;
  path = decodeURIComponent(path.slice(BASE.length));
  const candidates = [join(DIST, path), join(DIST, path, 'index.html')];
  return candidates.find((c) => existsSync(c) && statSync(c).isFile()) ?? false;
};
let links = 0;
for (const page of pages) {
  const refs = [...html[page].matchAll(/\s(?:href|src)="([^"]+)"/g), ...html[page].matchAll(/\ssrcset="([^"]+)"/g)].flatMap(
    (m) => (m[0].includes('srcset') ? m[1].split(',').map((s) => s.trim().split(/\s+/)[0]) : [m[1]]),
  );
  for (const ref of refs) {
    if (/^(https?:|mailto:|tel:|data:)/.test(ref)) continue;
    links++;
    if (ref.startsWith('#')) {
      if (ref.length > 1 && !ids[page].has(ref.slice(1))) fail(`${page}: missing anchor ${ref}`);
      continue;
    }
    const target = resolve(ref);
    if (target === null) fail(`${page}: link outside the site base ${ref}`);
    else if (target === false) fail(`${page}: broken link ${ref}`);
    else if (ref.includes('#') && target.endsWith('.html')) {
      const anchor = ref.split('#')[1];
      if (anchor && !ids[target].has(anchor)) fail(`${page}: missing anchor ${ref}`);
    }
  }
}
if (!failures) ok(`${links} internal links across ${pages.length} pages resolve`);

// ---------- 2. Wording ----------
console.log('\nWording (no em dashes or semicolons)');
const before = failures;
for (const page of pages) {
  const text = decode(
    html[page]
      .replace(/<script[\s\S]*?<\/script>/g, ' ')
      .replace(/<style[\s\S]*?<\/style>/g, ' ')
      .replace(/<[^>]+>/g, ' '),
  );
  const attrs = [...html[page].matchAll(/\s(?:alt|title|aria-label|content|placeholder)="([^"]*)"/g)]
    .map((m) => decode(m[1]))
    .filter((v) => !/^(width=|text\/|#[0-9a-f]{3,6}$)/i.test(v));
  for (const chunk of [text, ...attrs]) {
    const hit = chunk.match(/.{0,30}[—;].{0,30}/);
    if (hit) fail(`${page}: "${hit[0].trim()}"`);
  }
}
if (failures === before) ok('visible text is clean');

// ---------- 3. Contrast ----------
console.log('\nContrast (WCAG AA: 4.5 for text, 3 for large text and icons)');
const css = readFileSync('src/styles/global.css', 'utf8');
const rootBlock = css.slice(css.indexOf(':root {'), css.indexOf('\n}', css.indexOf(':root {')));
const t = Object.fromEntries([...rootBlock.matchAll(/(--[\w-]+):\s*(#[0-9a-f]{6})/gi)].map((m) => [m[1], m[2]]));
const lum = (hex) => {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255).map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
const ratio = (a, b) => {
  const [x, y] = [lum(a), lum(b)].sort((m, n) => n - m);
  return (x + 0.05) / (y + 0.05);
};
// Light bands, dark bands, and the teal in both.
const pairs = [
  ['--ink', '--bg', 4.5], ['--ink-2', '--bg', 4.5], ['--ink-3', '--bg', 4.5], ['--ink-2', '--bg-soft', 4.5], ['--ink-3', '--bg-soft', 4.5],
  ['--teal', '--bg', 4.5], ['--teal', '--bg-soft', 4.5], ['--white', '--teal', 4.5], ['--white', '--teal-hover', 4.5],
  ['--d-ink', '--d-bg', 4.5], ['--d-ink-2', '--d-bg', 4.5], ['--d-ink-3', '--d-bg', 4.5], ['--d-ink-2', '--d-surface', 4.5], ['--d-ink-3', '--d-surface', 4.5],
  ['--teal-bright', '--d-bg', 4.5], ['--teal-bright', '--d-surface', 4.5], ['--teal', '--d-bg', 3],
  ['--whatsapp', '--bg', 3], ['--sample', '--sample-bg', 4.5], ['--danger', '--bg', 4.5],
];
let worst = Infinity;
for (const [fg, bg, need] of pairs) {
  if (!t[fg] || !t[bg]) {
    fail(`${fg} or ${bg} is not a token`);
    continue;
  }
  const r = ratio(t[fg], t[bg]);
  worst = Math.min(worst, r / need);
  if (r < need) fail(`${fg} on ${bg} is ${r.toFixed(2)}, needs ${need}`);
}
if (worst >= 1) ok(`${pairs.length} pairs pass on white and on black`);

// ---------- 4. Weight ----------
console.log('\nPage weight');
const size = (f) => statSync(f).size;
const kb = (n) => `${(n / 1024).toFixed(0)} KB`;
const js = files.filter((f) => f.endsWith('.js'));
const jsTotal = js.reduce((s, f) => s + size(f), 0);
// Small scripts are inlined into each page, so count those per page as well.
const inlineJs = (page) =>
  [...html[page].matchAll(/<script(?![^>]*\bsrc=)(?![^>]*ld\+json)[^>]*>([\s\S]*?)<\/script>/g)].reduce((s, m) => s + Buffer.byteLength(m[1]), 0);
const heaviest = pages.map((p) => [p, inlineJs(p)]).sort((a, b) => b[1] - a[1])[0];
const perPage = jsTotal + heaviest[1];
(perPage <= 20 * 1024 ? ok : fail)(
  `JavaScript: ${kb(jsTotal)} in files, plus at most ${kb(heaviest[1])} inline (${heaviest[0]}), so ${kb(perPage)} at most per page (budget 20 KB)`,
);
const modern = files.filter((f) => /\.(avif|webp)$/.test(f));
const heavy = modern.filter((f) => size(f) > 150 * 1024);
(heavy.length ? fail : ok)(
  heavy.length ? `images over 150 KB: ${heavy.map((f) => `${f} ${kb(size(f))}`).join(', ')}` : `all ${modern.length} AVIF and WebP images are under 150 KB`,
);
const fallbacks = files.filter((f) => /_astro\/.*\.(jpe?g|png)$/.test(f) && size(f) > 150 * 1024);
if (fallbacks.length) console.log(`  · ${fallbacks.length} JPEG or PNG fallbacks over 150 KB, only for browsers without AVIF or WebP`);

// Home on a phone (390 px wide, 2x screen): HTML, CSS, scripts, the font and the eager images.
const home = join(DIST, 'index.html');
const h = html[home];
const local = (u) => join(DIST, decodeURIComponent(u.slice(BASE.length)));
let first = size(home);
for (const m of h.matchAll(/<link[^>]+href="([^"]+\.(?:css|woff2))"/g)) first += size(local(m[1]));
for (const m of h.matchAll(/<script[^>]+src="([^"]+)"/g)) first += size(local(m[1]));
for (const m of h.matchAll(/<picture>([\s\S]*?)<\/picture>/g)) {
  if (/loading="lazy"/.test(m[1])) continue;
  const avif = m[1].match(/type="image\/avif"[^>]*srcset="([^"]+)"|srcset="([^"]+)"[^>]*type="image\/avif"/);
  const set = (avif?.[1] ?? avif?.[2] ?? '').split(',').map((s) => s.trim().split(/\s+/));
  const pick = set.map(([u, w]) => [u, parseInt(w)]).sort((a, b) => a[1] - b[1]).find(([, w]) => w >= 780) ?? set.at(-1);
  if (pick?.[0]) first += size(local(pick[0]));
}
(first <= 600 * 1024 ? ok : fail)(`home page first load on a phone: ${kb(first)} (budget 600 KB)`);

// ---------- 5. Samples ----------
console.log('\nSample content (the live build refuses these)');
const samples = walk('src/data')
  .filter((f) => /\.(ya?ml|json)$/.test(f))
  .flatMap((f) =>
    readFileSync(f, 'utf8')
      .split('\n')
      .map((l, i) => (/^\s*"?sample"?\s*:\s*true\b/.test(l) ? `${f}:${i + 1}` : null))
      .filter(Boolean),
  );
console.log(samples.length ? `  · ${samples.length} waiting: ${samples.join(', ')}` : '  ✓ none');

console.log(failures ? `\n${failures} problem(s) found.\n` : '\nAll checks passed.\n');
process.exit(failures ? 1 : 0);
