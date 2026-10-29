/** Company facts used across the site. One place to change them. */
export const company = {
  name: 'BizCare Software Solutions (Pvt.) Ltd.',
  short: 'BizCare',
  phone: '+92 301 1155505',
  phoneHref: 'tel:+923011155505',
  whatsapp: '923011155505',
  email: 'info@bizcare.pk',
  address: 'Al-Hamd Garden, Lahore, Pakistan',
  mapsHref: 'https://www.google.com/maps/search/?api=1&query=Al-Hamd+Garden+Lahore',
  // Kept from the current site so Search Console carries on after the swap.
  googleVerification: 'Zz72sKiOxXC4nKrsLL_vGFoS-0aczeb5X5NDhbRjMlQ',
};

/** Agreed 28 Oct 2026: the larger figure wherever the old site disagreed. */
export const numbers = [
  { value: '300+', label: 'Clients' },
  { value: '200+', label: 'Flour Mills' },
  { value: '70+', label: 'Cities' },
  { value: '7', label: 'Years' },
  { value: '20,000+', label: 'Hours of Support' },
];

/** A WhatsApp chat link, with an optional message already written. */
export function whatsappHref(text?: string) {
  const base = `https://wa.me/${company.whatsapp}`;
  return text ? `${base}?text=${encodeURIComponent(text)}` : base;
}
