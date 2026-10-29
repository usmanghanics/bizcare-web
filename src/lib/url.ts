/** The site's base path, e.g. "/" on bizcare.pk or "/bizcare-web/" on the preview. */
const base = import.meta.env.BASE_URL.replace(/\/?$/, '/');

/** An internal link that works on both the preview and the live site. */
export function u(path = '/') {
  if (/^(https?:|mailto:|tel:|#)/.test(path)) return path;
  return base + path.replace(/^\//, '');
}

/** True when `href` is the page being built, or a parent section of it. */
export function isCurrent(pathname: string, href: string, exact = false) {
  const here = pathname.replace(/\/?$/, '/');
  const target = u(href);
  return exact ? here === target : here.startsWith(target);
}
