import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';
import { u } from '../lib/url';

/** Every public page, for search engines. */
export const GET: APIRoute = async ({ site }) => {
  const [products, apps, services] = await Promise.all([
    getCollection('products'),
    getCollection('apps'),
    getCollection('services'),
  ]);
  const paths = [
    '/',
    '/products/',
    ...products.map((p) => `/products/${p.id}/`),
    '/apps/',
    ...apps.map((a) => `/apps/${a.id}/`),
    '/services/',
    ...services.map((s) => `/services/${s.id}/`),
    '/clients/',
    '/about/',
    '/careers/',
    '/contact/',
    '/privacy/',
    '/terms/',
  ];
  const urls = paths.map((p) => `  <url><loc>${new URL(u(p), site).href}</loc></url>`).join('\n');
  const body = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`;
  return new Response(body, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
};
