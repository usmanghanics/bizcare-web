// @ts-check
import { defineConfig } from 'astro/config';
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

/**
 * Two builds:
 * - Preview (default): hidden from search engines, shows a "Sample" tag on
 *   drafted content, and includes the /design page.
 * - Live (BIZCARE_LIVE=1, `npm run build:live`): for bizcare.pk. Refuses to
 *   build while any data file still has `sample: true`.
 */
const LIVE = process.env.BIZCARE_LIVE === '1';
const SITE = process.env.SITE_URL ?? (LIVE ? 'https://bizcare.pk' : 'https://usmanghanics.github.io');
const BASE = process.env.BASE_PATH ?? (LIVE ? '/' : '/bizcare-web/');

/** Every data file that still holds drafted or sample content. */
function findSamples(dir) {
  const found = [];
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) {
      found.push(...findSamples(path));
    } else if (/\.(ya?ml|json)$/.test(name)) {
      readFileSync(path, 'utf8')
        .split('\n')
        .forEach((line, i) => {
          if (/^\s*"?sample"?\s*:\s*true\b/.test(line)) found.push(`${path}:${i + 1}`);
        });
    }
  }
  return found;
}

/** @returns {import('astro').AstroIntegration} */
function bizcare() {
  return {
    name: 'bizcare',
    hooks: {
      'astro:config:setup': ({ injectRoute, logger }) => {
        if (LIVE) {
          const samples = findSamples('src/data');
          if (samples.length) {
            throw new Error(
              `The live build stops while sample content remains. Replace these first:\n  ${samples.join('\n  ')}`,
            );
          }
          logger.info('Live build: no sample content found.');
        } else {
          injectRoute({ pattern: '/design', entrypoint: './src/design/DesignPage.astro' });
        }
      },
    },
  };
}

export default defineConfig({
  site: SITE,
  base: BASE,
  trailingSlash: 'always',
  build: { format: 'directory', inlineStylesheets: 'auto' },
  compressHTML: true,
  prefetch: { prefetchAll: true, defaultStrategy: 'hover' },
  integrations: [bizcare()],
  image: { responsiveStyles: false },
  vite: {
    define: { 'import.meta.env.BIZCARE_LIVE': JSON.stringify(LIVE ? '1' : '') },
  },
});
