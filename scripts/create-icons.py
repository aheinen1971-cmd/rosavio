"""Generate simple original Rosavio artwork for Windows branding resources."""
import math
import pathlib
import sys
from PIL import Image, ImageDraw

def icon(size):
    scale = 4
    n = size * scale
    im = Image.new('RGBA', (n, n))
    draw = ImageDraw.Draw(im)
    draw.rounded_rectangle((0, 0, n - 1, n - 1), radius=n * .23, fill='#111b30')
    for index in range(7):
        angle = index * math.tau / 7 - math.pi / 2
        cx = n * (.5 + .19 * math.cos(angle))
        cy = n * (.5 + .19 * math.sin(angle))
        r = n * .175
        draw.ellipse((cx-r, cy-r, cx+r, cy+r), fill=('#f582a2' if index % 2 else '#ea557e'))
    r = n * .12
    draw.ellipse((n*.5-r, n*.5-r, n*.5+r, n*.5+r), fill='#ffd4a5')
    return im.resize((size, size), Image.Resampling.LANCZOS)

root = pathlib.Path(sys.argv[1])
count = 0
for file in root.rglob('*'):
    if file.suffix.lower() == '.png':
        with Image.open(file) as old:
            width, height = old.size
        if width == height:
            icon(width).save(file)
        else:
            # Installer/header art: center the Rosavio mark on an original background.
            canvas = Image.new('RGBA', (width, height), '#111b30')
            mark = icon(min(width, height))
            canvas.alpha_composite(mark, ((width-mark.width)//2, (height-mark.height)//2))
            canvas.save(file)
        count += 1
    elif file.suffix.lower() == '.ico':
        icon(256).save(file, format='ICO', sizes=[(n,n) for n in (16,24,32,48,64,128,256)])
        count += 1
    elif file.suffix.lower() == '.svg':
        if 'wordmark' in file.name:
            artwork = '<svg xmlns="http://www.w3.org/2000/svg" width="180" height="60" viewBox="0 0 180 60"><text x="0" y="46" fill="#ea557e" font-family="Segoe UI, sans-serif" font-size="52" font-weight="700">Rosavio</text></svg>'
        else:
            petals = ''.join(f'<circle cx="{256+97*math.cos(i*math.tau/7-math.pi/2):.2f}" cy="{256+97*math.sin(i*math.tau/7-math.pi/2):.2f}" r="90" fill="{("#f582a2" if i%2 else "#ea557e")}"/>' for i in range(7))
            artwork = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><rect width="512" height="512" rx="118" fill="#111b30"/>{petals}<circle cx="256" cy="256" r="61" fill="#ffd4a5"/></svg>'
        file.write_text(artwork, encoding='utf-8')
        count += 1
print(f'Generated {count} Rosavio Windows branding images')
