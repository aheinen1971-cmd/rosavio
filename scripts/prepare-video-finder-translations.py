import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
data=json.loads((root/'scripts/video-finder-translations.json').read_text(encoding='utf-8'))
keys=data.pop('keys')
assert len(data)==20
for locale, values in data.items():
    assert len(keys)==len(values),locale
    file=root/'media/_locales'/locale/'messages.json'
    catalog=json.loads(file.read_text(encoding='utf-8'))
    catalog['media']={'message':'Video Finder'}
    catalog.update({key:{'message':value} for key,value in zip(keys,values)})
    file.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
