"""Compare shipped Linux icons with original Rosavio artwork, including small sizes."""
import json, pathlib, sys
from PIL import Image, ImageDraw
package=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
generator=pathlib.Path(__file__).with_name('create-icons.py').read_text()
scope={};exec(compile(generator.split('root = pathlib.Path(sys.argv[1])')[0],'<Rosavio icon generator>','exec'),scope)
checks=[]
for size in [16,32,48,64,128]:
    icon=package/f'browser/chrome/icons/default/default{size}.png'
    with Image.open(icon) as image:actual=image.convert('RGBA')
    expected=scope['icon'](size)
    if actual.size!=(size,size) or actual.tobytes()!=expected.tobytes():
        raise SystemExit('Shipped Linux icon does not match original Rosavio artwork: '+str(icon))
    checks.append({'size':size,'matchesOriginalArtwork':True,'file':str(icon)})
canvas=Image.new('RGB',(420,190),'#fff5f5');draw=ImageDraw.Draw(canvas)
draw.text((12,12),'Rosavio Linux: shipped 16 / 32 / 128 px icons',fill='#402029')
for x,size in [(24,16),(100,32),(230,128)]:
    with Image.open(package/f'browser/chrome/icons/default/default{size}.png') as im:canvas.paste(im,(x,45),im)
    draw.text((x,178),str(size)+' px',fill='#402029')
canvas.save(out/'icons.png')
(out/'report.json').write_text(json.dumps({'passed':True,'checks':checks},indent=2))
print('Original colored Rosavio Linux icons verified at 16,32,48,64,128 pixels.')
