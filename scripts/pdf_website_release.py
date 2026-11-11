"""Select signed PDF releases and update only their existing news entry."""
import base64,json,pathlib,re
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

ROOT='https://github.com/aheinen1971-cmd/pdf-digital/releases'
TEXT=dict(zip('de en fr es nl it pt-PT pl cs da sv-SE nb-NO fi tr uk el ja ko ar he'.split(),[
 'Die neue Version ist verfügbar. Die Änderungen findest du in den Versionshinweisen.',
 'The new version is available. See the release notes for the changes.',
 'La nouvelle version est disponible. Consultez les notes de version pour connaître les changements.',
 'La nueva versión está disponible. Consulta los cambios en las notas de la versión.',
 'De nieuwe versie is beschikbaar. Bekijk de wijzigingen in de releaseopmerkingen.',
 'La nuova versione è disponibile. Consulta le note di rilascio per le modifiche.',
 'A nova versão está disponível. Consulte as notas da versão para conhecer as alterações.',
 'Nowa wersja jest dostępna. Zmiany opisano w informacjach o wydaniu.',
 'Nová verze je k dispozici. Změny najdete v poznámkách k vydání.',
 'Den nye version er tilgængelig. Se ændringerne i udgivelsesnoterne.',
 'Den nya versionen är tillgänglig. Läs om ändringarna i versionsinformationen.',
 'Den nye versjonen er tilgjengelig. Se endringene i versjonsnotatene.',
 'Uusi versio on saatavilla. Muutokset löytyvät julkaisutiedoista.',
 'Yeni sürüm kullanıma hazır. Değişiklikler için sürüm notlarına bakın.',
 'Нова версія вже доступна. Перелік змін наведено у примітках до випуску.',
 'Η νέα έκδοση είναι διαθέσιμη. Δείτε τις αλλαγές στις σημειώσεις έκδοσης.',
 '新しいバージョンが利用できます。変更内容はリリースノートをご覧ください。',
 '새 버전을 사용할 수 있습니다. 변경 사항은 릴리스 노트를 확인하세요.',
 'الإصدار الجديد متاح. راجع ملاحظات الإصدار للاطلاع على التغييرات.',
 'הגרסה החדשה זמינה. השינויים מפורטים בהערות הגרסה.'
]))

def verified_pdf(release,read):
    tag=release.get('tag_name','')
    if release.get('draft') or release.get('prerelease') or not re.fullmatch(r'v\d+\.\d+\.\d+',tag):raise ValueError('Regular PDF version required')
    v=tag[1:];assets={a['name']:a for a in release['assets']}
    package=assets[f'PDF-Werkbank-{v}-Windows.zip'];sig=assets[f'PDF-Werkbank-{v}-Signatur.json']
    for a in [package,sig]:
        if a.get('state')!='uploaded' or a['browser_download_url']!=ROOT+'/download/'+tag+'/'+a['name']:raise ValueError('Unexpected PDF asset')
    if not re.fullmatch(r'sha256:[a-f0-9]{64}',package.get('digest','')):raise ValueError('Missing PDF package digest')
    raw=read(sig['browser_download_url'])
    if len(raw)>8192:raise ValueError('Oversized signature metadata')
    manifest=json.loads(raw);payload=base64.b64decode(manifest['payload'],validate=True)
    key=load_pem_public_key(pathlib.Path(__file__).with_name('pdf-release-public.pem').read_bytes())
    key.verify(base64.b64decode(manifest['signature'],validate=True),payload,padding.PKCS1v15(),hashes.SHA256())
    lines=payload.decode('ascii').split('\n')
    if len(lines)!=6 or lines[:4]!=['PDF-Werkbank-Update-v1',v,package['digest'][7:],str(package['size'])] or lines[5] or not re.fullmatch(r'[a-f0-9]{64}',lines[4]) or manifest.get('sha256')!=lines[4]:raise ValueError('PDF signature metadata mismatch')
    return v

def rewrite_pdf_news(source,version):
    if not re.fullmatch(r'\d+\.\d+\.\d+',version):raise ValueError('Invalid PDF version')
    blocks=list(re.finditer(r'<section\b[^>]*\bid="rosavio-news"[^>]*>.*?</section>',source,re.S))
    if len(blocks)!=1:raise ValueError('Unique news section required')
    b=blocks[0];matches=list(re.finditer(r'(<h3><bdi>PDF Digital )(\d+\.\d+\.\d+)([^<]*</bdi></h3>)<p>.*?</p>',b[0],re.S))
    if len(matches)!=1:raise ValueError('Unique PDF news entry required')
    m=matches[0];old=m[2]
    if tuple(map(int,version.split('.')))<tuple(map(int,old.split('.'))):raise ValueError('Refusing PDF news downgrade')
    if version==old:return source
    lang=re.search(r'<html\b[^>]*\blang="([^"]+)"',source)[1]
    content=b[0][:m.start()]+m[1]+version+m[3]+'<p>'+TEXT[lang]+'</p>'+b[0][m.end():]
    oldlink=ROOT+'/tag/v'+old
    if content.count(oldlink)!=1:raise ValueError('Unique PDF release link required')
    content=content.replace(oldlink,ROOT+'/tag/v'+version)
    return source[:b.start()]+content+source[b.end():]
