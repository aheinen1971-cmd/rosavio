function httpUrl(value, base) {
  const url = new URL(value, base);
  if (!['http:', 'https:'].includes(url.protocol)) throw Error('Diese Medienadresse wird nicht unterstützt.');
  return url.href;
}

async function readList(url, load) {
  const response = await load(url);
  if (!response.ok) throw Error('Wiedergabeliste nicht erreichbar (HTTP ' + response.status + ').');
  const lines = (await response.text()).trim().split(/\r?\n/).map(s => s.trim()).filter(Boolean);
  if (lines[0] !== '#EXTM3U') throw Error('Die Adresse liefert keine HLS-Wiedergabeliste.');
  return {base:response.url || url, lines};
}

function attributes(line) {
  const fields = {};
  for (const match of line.slice(line.indexOf(':')+1).matchAll(/(?:^|,)([A-Z0-9-]+)=("[^"]*"|[^,]*)/g)) {
    fields[match[1]] = match[2].replace(/^"|"$/g, '');
  }
  return fields;
}

function variantsOf({lines, base}) {
  const audioTracks = lines.filter(line => line.startsWith('#EXT-X-MEDIA:'))
    .map(attributes).filter(track => track.TYPE === 'AUDIO');
  const variants = [];
  let master = false;
  for (const [i, line] of lines.entries()) {
    if (!line.startsWith('#EXT-X-STREAM-INF:')) continue;
    master = true;
    const fields = attributes(line);
    if (!lines[i+1] || lines[i+1].startsWith('#')) continue;
    const group = audioTracks.filter(track => track['GROUP-ID'] === fields.AUDIO);
    const track = group.find(track => track.DEFAULT === 'YES') || group.find(track => track.AUTOSELECT === 'YES') || group[0];
    if (fields.AUDIO && !track) continue;
    const resolution = /^(\d+)x(\d+)$/i.exec(fields.RESOLUTION || '');
    variants.push({url:httpUrl(lines[i+1],base), audioURL:track?.URI ? httpUrl(track.URI,base) : null, height:Number(resolution?.[2] || 0), rate:Number(fields.BANDWIDTH) || 0});
  }
  if (master && !variants.length) throw Error('Eine gemeinsame Bild- und Tonspur wurde nicht gefunden.');
  return variants.sort((a,b) => b.height-a.height || b.rate-a.rate);
}

function mediaPlan({lines, base}) {
  if (lines.some(s => s.startsWith('#EXT-X-STREAM-INF:'))) throw Error('Verschachtelte Qualitätslisten werden nicht unterstützt.');
  if (!lines.includes('#EXT-X-ENDLIST')) throw Error('Diese Wiedergabeliste hat noch kein bestätigtes Ende.');
  if (lines.some(s => s.startsWith('#EXT-X-KEY:') && s !== '#EXT-X-KEY:METHOD=NONE')) throw Error('Verschlüsselte Wiedergabeliste.');
  const sections = parseMedia(lines, base);
  const times = lines.filter(s => s.startsWith('#EXTINF:')).map(s => {
    const m = /^#EXTINF:(\d+(?:\.\d+)?)(?:,|$)/.exec(s);
    return m ? Number(m[1]) : NaN;
  });
  return {sections, seconds:times.reduce((a,b) => a+b,0)};
}
