"""One-off import of the client list from the old bizcare.pk city pages.

Usage: python3 import_clients.py SOURCE_DIR PROJECT_DIR
SOURCE_DIR holds clients-scraped.json and the downloaded gallery/ photos.
Writes PROJECT_DIR/src/data/clients.json and resized photos under
PROJECT_DIR/src/assets/clients/. Needs Pillow.
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageOps

src, project = Path(sys.argv[1]), Path(sys.argv[2])
scraped = json.loads((src / 'clients-scraped.json').read_text())
photos_out = project / 'src/assets/clients'
photos_out.mkdir(parents=True, exist_ok=True)

# The old pages' region keys, as the new site names them.
REGION = {
    'Bahawalpur': 'bahawalpur', 'Balochistan': 'balochistan', 'DI_Khan': 'di-khan',
    'Faisalabad': 'faisalabad', 'Gujranwala': 'gujranwala', 'Gujrat': 'gujrat',
    'Islamabad': 'islamabad', 'Lahore': 'lahore', 'Malakand': 'malakand', 'Multan': 'multan',
    'Peshawar': 'peshawar', 'Sahiwal': 'sahiwal', 'Sargodha': 'sargodha', 'Sindh': 'sindh',
}
# Spelling slips on the old pages.
FIX = {
    'Sardaryb Flour Mills': 'Sardaryab Flour Mills', 'ALi Ahmad Awan Flour Mills': 'Ali Ahmad Awan Flour Mills',
    'AL-Wahab Flour Mills': 'Al-Wahab Flour Mills', 'Feburary': 'February', 'Dādu': 'Dadu',
    'Lucky Marwat': 'Lakki Marwat',
}
# Photos the old site reuses for a different mill, or that no longer load.
NO_PHOTO = {'Shahzad Flour Mills', 'Miller and Baker Flour Mills'}


def fix(text):
    for a, b in FIX.items():
        text = text.replace(a, b)
    return text


def trim_white_sides(im):
    """Drop plain white bars on the left and right that some photos carry."""
    grey = im.convert('L')
    w, h = grey.size
    px = grey.load()
    def blank(x):
        return all(px[x, y] > 243 for y in range(0, h, max(1, h // 60)))
    left = 0
    while left < w // 3 and blank(left):
        left += 1
    right = w
    while right > w - w // 3 and blank(right - 1):
        right -= 1
    return im.crop((left, 0, right, h)) if left > 4 or w - right > 4 else im


def slug(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


out, seen = [], set()
for region, items in scraped.items():
    for it in items:
        parts = [p.strip() for p in fix(it['client']).split(',')]
        name, town = parts[0], ', '.join(parts[1:]) or parts[0]
        cid = slug(f'{name} {parts[1] if len(parts) > 1 else ""}')
        while cid in seen:
            cid += '-2'
        seen.add(cid)
        since = datetime.strptime(fix(it['date']).replace(',', ''), '%d %B %Y').date().isoformat()
        entry = {
            'id': cid, 'name': name, 'town': town, 'region': REGION[region],
            'edition': 'cloud' if 'Cloud' in it['category'] else 'desktop', 'since': since,
        }
        photo = src / it['image'].lstrip('/').replace('assets/img/', '').replace(' ', '_')
        if name not in NO_PHOTO and photo.exists():
            im = trim_white_sides(ImageOps.exif_transpose(Image.open(photo)).convert('RGB'))
            im.thumbnail((960, 960), Image.LANCZOS)
            im.save(photos_out / f'{cid}.jpg', quality=84, optimize=True, progressive=True)
            entry['photo'] = f'../assets/clients/{cid}.jpg'
        out.append(entry)

out.sort(key=lambda e: (e['region'], e['name']))
(project / 'src/data').mkdir(parents=True, exist_ok=True)
(project / 'src/data/clients.json').write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n')
print(len(out), 'clients,', sum('photo' in e for e in out), 'with photos,',
      sum(e['edition'] == 'cloud' for e in out), 'cloud')
