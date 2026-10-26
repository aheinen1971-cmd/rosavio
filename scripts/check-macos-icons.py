"""Compare native ICNS layers against original Rosavio artwork."""
import json,pathlib,plistlib,sys,tempfile
from PIL import Image,ImageDraw
app=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
info=plistlib.loads((app/'Contents/Info.plist').read_bytes());name=info['CFBundleIconFile']
if pathlib.Path(name).name!=name:raise SystemExit('Unsafe icon path')
if not name.endswith('.icns'):name+='.icns'
actual_path=app/'Contents/Resources'/name
scope={};generator=pathlib.Path(__file__).with_name('create-icons.py').read_text();exec(compile(generator.split('root = pathlib.Path(sys.argv[1])')[0],'<Rosavio artwork>','exec'),scope)
with tempfile.TemporaryDirectory() as temp:
 expected_path=pathlib.Path(temp)/'expected.icns';scope['icon'](1024).save(expected_path,format='ICNS')
 checks=[];canvas=Image.new('RGB',(420,200),'#fff5f5');draw=ImageDraw.Draw(canvas);draw.text((12,12),'Rosavio native ICNS: 16 / 32 / 128 px',fill='#402029')
 for x,size in [(24,16),(100,32),(230,128)]:
  with Image.open(actual_path) as im:
   im.size=(size,size);im.load();actual=im.convert('RGBA')
  with Image.open(expected_path) as im:
   im.size=(size,size);im.load();expected=im.convert('RGBA')
  if actual.size!=expected.size or actual.tobytes()!=expected.tobytes():raise SystemExit('Native ICNS artwork mismatch at '+str(size))
  canvas.paste(actual,(x,45),actual);draw.text((x,180),str(size)+' px',fill='#402029');checks.append({'size':size,'matchesOriginalArtwork':True})
 canvas.save(out/'icons.png')
(out/'report.json').write_text(json.dumps({'passed':True,'file':str(actual_path),'checks':checks},indent=2))
print('Original native colored Rosavio ICNS layers passed.')
