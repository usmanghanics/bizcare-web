"""Draws the favicon, the home screen icon and the share preview images.

Usage: python3 -I tools/brand_images.py   (from the project folder; needs Pillow)
Reads the traced logo from src/lib/logo.ts and the product and app files, and
writes public/favicon.svg, public/favicon-32.png, public/apple-touch-icon.png
and public/og/*.png (1200 x 630, for WhatsApp, Facebook and LinkedIn links).
"""
import re
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / 'public'
FONT = ROOT / 'tools/fonts/Manrope.ttf'
INK, INK2, ACCENT_INK, DOT, LINE, BAND = '#0d1b1e', '#4b5b5e', '#015e63', '#017e84', '#e2e8e8', '#f4f6f6'
# Share images sit on black, like the site's top bands.
BG, FG, FG2, TEAL_LIGHT, EDGE, STAGE = '#000000', '#ffffff', '#a6a6a6', '#2bb8bf', '#2a2a2a', '#111111'

logo_ts = (ROOT / 'src/lib/logo.ts').read_text()
MARK_D, WORD_D = re.findall(r"d: '([^']+)'", logo_ts)
MARK_W = float(re.search(r'mark = \{\s*width: ([\d.]+)', logo_ts).group(1))
WORD_W = float(re.search(r'word = \{\s*width: ([\d.]+)', logo_ts).group(1))
WORD_H = float(re.search(r'word = \{[^}]*height: ([\d.]+)', logo_ts).group(1))
GAP = float(re.search(r'gap = ([\d.]+)', logo_ts).group(1))
cx, cy, r = (float(v) for v in re.search(r'cx: ([\d.]+), cy: ([\d.]+), r: ([\d.]+)', logo_ts).groups())


def subpaths(d):
    """Flatten an absolute M/L/C/Z path into polygons."""
    toks = re.findall(r'[MLCZ]|-?\d+(?:\.\d+)?', d)
    polys, cur, i, cmd = [], [], 0, None
    while i < len(toks):
        t = toks[i]
        if t in 'MLCZ':
            cmd = t
            i += 1
            if t == 'Z':
                if cur:
                    polys.append(cur)
                cur = []
            continue
        if cmd == 'M':
            if cur:
                polys.append(cur)
            cur = [(float(toks[i]), float(toks[i + 1]))]
            i += 2
            cmd = 'L'
        elif cmd == 'L':
            cur.append((float(toks[i]), float(toks[i + 1])))
            i += 2
        elif cmd == 'C':
            x0, y0 = cur[-1]
            x1, y1, x2, y2, x3, y3 = (float(v) for v in toks[i:i + 6])
            for k in range(1, 13):
                t_ = k / 12
                a = (1 - t_) ** 3
                b = 3 * (1 - t_) ** 2 * t_
                c = 3 * (1 - t_) * t_ ** 2
                e = t_ ** 3
                cur.append((a * x0 + b * x1 + c * x2 + e * x3, a * y0 + b * y1 + c * y2 + e * y3))
            i += 6
    if cur:
        polys.append(cur)
    return polys


def shape_mask(d, size, scale, dx, dy):
    """Even-odd fill of a path into an L mask."""
    mask = Image.new('L', size, 0)
    for poly in subpaths(d):
        layer = Image.new('L', size, 0)
        ImageDraw.Draw(layer).polygon([(x * scale + dx, y * scale + dy) for x, y in poly], fill=255)
        mask = ImageChops.logical_xor(mask.convert('1'), layer.convert('1')).convert('L')
    return mask


def draw_logo(img, x, y, height, lockup=True, ink=INK):
    """Paint the logo onto img with its mark's top-left at (x, y)."""
    ss = 4
    width = MARK_W + (GAP + WORD_W if lockup else 0)
    w, h = int(width * height / 100) + 4, int(height) + 4
    size = (w * ss, h * ss)
    scale = height / 100 * ss
    mask = shape_mask(MARK_D, size, scale, 0, 0)
    if lockup:
        word = shape_mask(WORD_D, size, scale, (MARK_W + GAP) * scale, (100 - WORD_H) * scale)
        mask = ImageChops.lighter(mask, word)
    dot = Image.new('L', size, 0)
    ImageDraw.Draw(dot).ellipse([(cx - r) * scale, (cy - r) * scale, (cx + r) * scale, (cy + r) * scale], fill=255)
    mask = mask.resize((w, h), Image.LANCZOS)
    dot = dot.resize((w, h), Image.LANCZOS)
    img.paste(Image.new('RGB', (w, h), ink), (x, y), mask)
    img.paste(Image.new('RGB', (w, h), DOT), (x, y), dot)


def font(px, weight):
    f = ImageFont.truetype(str(FONT), px)
    f.set_variation_by_axes([weight])
    return f


def wrap(draw, text, f, max_w):
    lines, line = [], ''
    for word in text.split():
        trial = f'{line} {word}'.strip()
        if draw.textlength(trial, font=f) <= max_w:
            line = trial
        else:
            lines.append(line)
            line = word
    lines.append(line)
    return lines


def rounded(img, radius):
    mask = Image.new('L', img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius, fill=255)
    out = Image.new('RGBA', img.size)
    out.paste(img, (0, 0), mask)
    return out


def share_image(path, label, title, line, screen=None, phone=None):
    W, H = 1200, 630
    img = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(img)
    text_w = 560 if (screen or phone) else 1000
    draw_logo(img, 64, 56, 44, ink=FG)
    y = 168
    d.text((64, y), label.upper(), font=font(20, 750), fill=TEAL_LIGHT)
    y += 44
    tf = font(56 if len(title) < 40 else 48, 800)
    for ln in wrap(d, title, tf, text_w):
        d.text((62, y), ln, font=tf, fill=FG)
        y += int(tf.size * 1.08)
    y += 18
    lf = font(24, 500)
    for ln in wrap(d, line, lf, text_w)[:3]:
        d.text((64, y), ln, font=lf, fill=FG2)
        y += 36
    d.text((64, H - 70), 'bizcare.pk', font=font(22, 750), fill=TEAL_LIGHT)
    if screen:
        shot = Image.open(screen).convert('RGB')
        sw = 640
        shot = shot.resize((sw, int(shot.height * sw / shot.width)), Image.LANCZOS)
        bar = 34
        frame = Image.new('RGB', (sw + 2, shot.height + bar + 2), EDGE)
        inner = Image.new('RGB', (sw, bar), STAGE)
        frame.paste(inner, (1, 1))
        frame.paste(shot, (1, bar + 1))
        frame = rounded(frame, 16)
        img.paste(frame, (680, 150), frame)
    if phone:
        shot = Image.open(phone).convert('RGB')
        pw = 250
        shot = shot.resize((pw, int(shot.height * pw / shot.width)), Image.LANCZOS)
        shot = shot.crop((0, 0, pw, min(shot.height, 540)))
        body = Image.new('RGB', (pw + 16, shot.height + 16), '#1a1a1a')
        body = rounded(body, 40)
        body.paste(rounded(shot, 32), (8, 8), rounded(shot, 32))
        bg = Image.new('RGB', (440, H), STAGE)
        img.paste(bg, (W - 440, 0))
        img.paste(body, (W - 440 + (440 - body.width) // 2, 70), body)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, optimize=True)


def field(text, name):
    m = re.search(rf'^{name}: (.+)$', text, re.M)
    return m.group(1).strip() if m else ''


def main():
    # Favicon: the mark, dark ink on light tabs and light ink on dark ones.
    pad = 8
    side = 100 + 2 * pad
    ox = (side - MARK_W) / 2 - pad
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-ox:.2f} {-pad} {side} {side}">'
        '<style>.b{fill:#0d1b1e}@media (prefers-color-scheme:dark){.b{fill:#eaf1f1}}</style>'
        f'<path class="b" d="{MARK_D}"/><circle fill="#017e84" cx="{cx}" cy="{cy}" r="{r}"/></svg>\n'
    )
    (PUBLIC / 'favicon.svg').write_text(svg)

    for name, size, bg in (('favicon-32.png', 32, None), ('apple-touch-icon.png', 180, 'white')):
        big = 720
        img = Image.new('RGBA' if bg is None else 'RGB', (big, big), (0, 0, 0, 0) if bg is None else bg)
        h = int(big * (0.86 if bg is None else 0.62))
        draw_logo(img, int((big - MARK_W * h / 100) / 2), int((big - h) / 2), h, lockup=False)
        img.resize((size, size), Image.LANCZOS).save(PUBLIC / name, optimize=True)

    share_image(
        PUBLIC / 'og/default.png',
        'Software House, Lahore',
        'Software That Runs Pakistan’s Businesses',
        'ERP, point of sale and mobile apps. Trusted by 300+ businesses in 70+ cities.',
        screen=ROOT / 'src/assets/screens/bizcare-erp.jpg',
    )
    for f in sorted((ROOT / 'src/data/products').glob('*.yaml')):
        t = f.read_text()
        src = re.search(r'src: \.\./\.\./assets/screens/(\S+)', t).group(1)
        share_image(PUBLIC / f'og/products/{f.stem}.png', f"{field(t, 'name')} for {field(t, 'industry')}",
                    field(t, 'headline'), field(t, 'tagline'), screen=ROOT / 'src/assets/screens' / src)
    for f in sorted((ROOT / 'src/data/apps').glob('*.yaml')):
        t = f.read_text()
        src = re.search(r'src: \.\./\.\./assets/(apps/\S+)', t).group(1)
        share_image(PUBLIC / f'og/apps/{f.stem}.png', field(t, 'name'), field(t, 'headline'), field(t, 'tagline'),
                    phone=ROOT / 'src/assets' / src)
    print('brand images written to', PUBLIC)


main()
