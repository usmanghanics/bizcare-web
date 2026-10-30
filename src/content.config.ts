import { defineCollection, reference } from 'astro:content';
import { file, glob } from 'astro/loaders';
import { z } from 'astro/zod';
import { icons } from './lib/icons';

/** A Phosphor icon name from src/lib/icons.ts. */
const icon = z.enum(Object.keys(icons) as [keyof typeof icons, ...(keyof typeof icons)[]]);

/** One flat colour pair per product or app (see --tint-* in tokens.css). */
const tint = z.enum(['teal', 'blue', 'purple', 'orange', 'green', 'amber', 'red', 'forest']);

/** Plain words: no em dashes or semicolons anywhere a visitor reads. */
const words = z
  .string()
  .min(1)
  .refine((s) => !/[—;]/.test(s), { message: 'Use plain words: no em dashes or semicolons.' });

/** Drafted or stand-in content. Shown with a tag on the preview, refused by the live build. */
const sample = z.boolean().default(false);

const products = defineCollection({
  loader: glob({ pattern: '*.yaml', base: './src/data/products' }),
  schema: ({ image }) =>
    z.object({
      name: words,
      order: z.number(),
      industry: words,
      icon,
      tint,
      tagline: words,
      headline: words,
      line: words,
      proof: words.optional(),
      screen: z.object({
        src: image(),
        alt: words,
        frame: z.enum(['browser', 'window']),
        title: z.string(),
      }),
      highlights: z.array(words).length(3),
      fixes: z.array(z.object({ icon, problem: words, answer: words })).length(3),
      features: z.array(z.object({ icon, title: words, items: z.array(words).min(2).max(5) })).length(3),
      editions: z.array(z.object({ name: words, line: words })).optional(),
      faq: z.array(z.object({ q: words, a: words })).min(2),
      apps: z.array(reference('apps')).default([]),
    }),
});

const apps = defineCollection({
  loader: glob({ pattern: '*.yaml', base: './src/data/apps' }),
  schema: ({ image }) =>
    z.object({
      name: words,
      order: z.number(),
      kind: z.enum(['own', 'client']),
      client: words.optional(),
      icon,
      tint,
      status: z.enum(['live', 'soon']),
      tagline: words,
      headline: words,
      line: words,
      platforms: z.array(z.enum(['Android', 'iPhone', 'Web'])).min(1),
      links: z
        .object({ play: z.url().optional(), appStore: z.url().optional(), site: z.url().optional() })
        .default({}),
      features: z.array(z.object({ icon, title: words, line: words })).min(3).max(6),
      appIcon: image(),
      screens: z.array(z.object({ src: image(), alt: words })).min(1).max(3),
      poweredBy: reference('products').optional(),
    }),
});

const services = defineCollection({
  loader: glob({ pattern: '*.yaml', base: './src/data/services' }),
  schema: z.object({
    name: words,
    order: z.number(),
    icon,
    tagline: words,
    headline: words,
    line: words,
    features: z.array(z.object({ icon, title: words, line: words })).min(3).max(6),
    faq: z.array(z.object({ q: words, a: words })).default([]),
  }),
});

const quotes = defineCollection({
  loader: file('src/data/quotes.yaml'),
  schema: z.object({
    name: words,
    role: words,
    business: words,
    town: words,
    text: words,
    product: reference('products'),
    sample,
  }),
});

const team = defineCollection({
  loader: file('src/data/team.yaml'),
  schema: ({ image }) => z.object({ name: words, role: words, photo: image(), order: z.number() }),
});

const affiliations = defineCollection({
  loader: file('src/data/affiliations.yaml'),
  schema: z.object({ name: words, line: words, icon, url: z.url().optional(), order: z.number(), sample }),
});

const regions = defineCollection({
  loader: file('src/data/regions.yaml'),
  schema: ({ image }) =>
    z.object({ name: words, short: words, lat: z.number(), lon: z.number(), order: z.number(), photo: image() }),
});

const clients = defineCollection({
  loader: file('src/data/clients.json'),
  schema: ({ image }) =>
    z.object({
      name: words,
      town: words,
      region: reference('regions'),
      edition: z.enum(['cloud', 'desktop']),
      since: z.iso.date(),
      photo: image().optional(),
    }),
});

export const collections = { products, apps, services, quotes, team, affiliations, regions, clients };
