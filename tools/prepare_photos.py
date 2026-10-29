"""Copies the old site's city and workplace photos into the project, resized.

Usage: python3 -I tools/prepare_photos.py SOURCE_DIR   (needs Pillow)
SOURCE_DIR is the downloaded old-site folder (source-images/current-site).
"""
import sys
from pathlib import Path

from PIL import Image, ImageOps

Image.MAX_IMAGE_PIXELS = None
src = Path(sys.argv[1])
root = Path(__file__).resolve().parent.parent

CITIES = {
    'peshawar': 'Peshawar', 'malakand': 'Malakand', 'islamabad': 'Islamabad', 'gujrat': 'Gujrat',
    'gujranwala': 'Gujranwala', 'lahore': 'Lahore', 'sargodha': 'Sargodha', 'faisalabad': 'Faisalabad',
    'sahiwal': 'Sahiwal', 'di-khan': 'DI_Khan', 'multan': 'Multan', 'bahawalpur': 'Bahawalpur',
    'balochistan': 'Balochistan', 'sindh': 'Sindh',
}
PHOTOS = {
    'office': 'hero-bg.jpg', 'workspace': 'about.jpg', 'software-desk': 'business-service.jpg',
    'whatsapp': 'whatssapp-service.jpg', 'marketing': 'digital-marketing-service.jpg',
}


def save(path_in, path_out, longest):
    im = Image.open(path_in)
    im.draft('RGB', (longest * 2, longest * 2))
    im = ImageOps.exif_transpose(im).convert('RGB')
    im.thumbnail((longest, longest), Image.LANCZOS)
    path_out.parent.mkdir(parents=True, exist_ok=True)
    im.save(path_out, quality=86, optimize=True, progressive=True)
    return im.size


for rid, name in CITIES.items():
    print(rid, save(src / f'gallery/{name}.jpg', root / f'src/assets/regions/{rid}.jpg', 1400))
for pid, name in PHOTOS.items():
    print(pid, save(src / name, root / f'src/assets/photos/{pid}.jpg', 2400))
