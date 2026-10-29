import type { APIRoute } from 'astro';
import { LIVE } from '../lib/env';

/** The preview stays out of search engines. The live site lists its sitemap. */
export const GET: APIRoute = ({ site }) => {
  const body = LIVE
    ? `User-agent: *\nAllow: /\n\nSitemap: ${new URL(`${import.meta.env.BASE_URL}sitemap.xml`, site)}\n`
    : 'User-agent: *\nDisallow: /\n';
  return new Response(body, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
};
