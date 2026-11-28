function videoFilename(title, height, suffix, extension) {
  let name = (title || mediaText('video')).normalize('NFC').replace(/[<>:"/\\|?*\u0000-\u001f\u007f\u202a-\u202e\u2066-\u2069]/g,' ').replace(/\s+/g,' ').trim();
  name = Array.from(name).slice(0,90).join('').replace(/^[. ]+|[. ]+$/g,'') || mediaText('video');
  const chars = Array.from(name);
  const bytes = c => { const n=c.codePointAt(0); return n<128 ? 1 : n<2048 ? 2 : n<65536 ? 3 : 4; };
  let length = chars.reduce((n,c)=>n+bytes(c),0);
  while(length>200) length-=bytes(chars.pop());
  name=chars.join('');
  if (/^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)/i.test(name)) name = '_'+name;
  return name + (Number.isInteger(height) && height > 0 ? ' – '+height+'p' : '') + suffix + '.' + extension;
}
