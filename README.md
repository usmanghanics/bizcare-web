# bizcare.pk

The new BizCare Software Solutions website, built to replace the current bizcare.pk once approved. The plan is in `~/Desktop/BizCare-Website/`.

Astro 7.3.8 turns everything into plain HTML files ahead of time, so the server only hands over finished pages. No framework runs in the browser. Each page carries under 10 KB of JavaScript.

## Run It

```sh
npm install
npm run dev          # opens http://localhost:4321/ and reloads as you edit (Ctrl+C to stop)
npm run check        # type check, build, then every check below
npm run build:live   # the build for bizcare.pk (refuses sample content)
```

## Where Things Live

| What | Where |
|---|---|
| Company facts, phone, numbers | `src/data/site.ts` |
| Products (6), apps (3), services (2) | `src/data/products/`, `src/data/apps/`, `src/data/services/` (one YAML file each) |
| Clients (123, from the old city pages) | `src/data/clients.json` and `src/assets/clients/` |
| Map regions | `src/data/regions.yaml` |
| Quotes, team, affiliations | `src/data/quotes.yaml`, `team.yaml`, `affiliations.yaml` |
| Real product and app screens | `src/assets/screens/`, `src/assets/apps/` |
| Colours, type, shared styles | `src/styles/global.css` |
| Pages | `src/pages/` |
| Components | `src/components/` |

Every data file is checked against a schema (`src/content.config.ts`). A missing field, an unknown icon, an em dash or a semicolon stops the build with the file and line.

## Samples Never Go Live

Drafted quotes and stand-in affiliations carry `sample: true`. The preview shows them with a small "Sample" tag and stays hidden from search engines. `npm run build:live` refuses to finish while any remain, and lists each one. To replace one, put in the real words and set `sample: false`.

## Checks (`scripts/check.mjs`)

1. Every internal link, image and `#anchor` resolves.
2. No em dashes or semicolons in anything a visitor reads.
3. WCAG AA contrast for every text colour pair, in light and dark.
4. Page weight: JavaScript at most 20 KB a page, no AVIF or WebP image over 150 KB, and the home page's first load on a phone at most 600 KB.
5. Lists the sample content still waiting for real words.

## Preview on GitHub Pages

1. Create a repository (for example `bizcare-web`) and push this folder to `main`.
2. In the repository: Settings, Pages, Source: **GitHub Actions**.
3. Every push builds, checks and publishes `https://<username>.github.io/<repository>/`. The workflow sets the address itself (`.github/workflows/preview.yml`).

## Tools

| Tool | What it does |
|---|---|
| `tools/icons.py` | Writes `src/lib/icons.ts` from the Phosphor font (the same icons as the apps). Add a name to its list and run it. |
| `tools/brand_images.py` | Draws the favicon, home screen icon and share preview images into `public/`. Needs Pillow. |
| `tools/import_clients.py` | The one-off import of the old site's client list and photos. |
| `tools/webshot.swift` | Renders a built page offline with its scripts running, for design reviews: `swiftc -O tools/webshot.swift -o webshot`, then `./webshot dist/index.html 390 844 out.png --full`. Build with `BASE_PATH` set to the output folder's full path first, so file links resolve. |

The logo in `src/lib/logo.ts` is traced from the brand PNGs, because no vector file exists yet. Swap in the official SVG when it arrives.

## Credits

Manrope (SIL Open Font License). Phosphor Icons (MIT, `tools/phosphor/LICENSE-Phosphor.txt`). Product screens, client and team photos from the current bizcare.pk. App screens from the BizCareers, Makki AutoCare and Madadgar Kisan projects.
