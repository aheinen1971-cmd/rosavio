"""Add a small translated status-page link; preserve every existing page element."""
import html,pathlib,re
LABELS=dict(zip('de en fr es nl it pt-PT pl cs da sv-SE nb-NO fi tr uk el ja ko ar he'.split(),['Statusseite','Status page','Page de statut','Página de estado','Statuspagina','Pagina di stato','Página de estado','Strona statusu','Stránka stavu','Statusside','Statussida','Statusside','Tilasivu','Durum sayfası','Сторінка стану','Σελίδα κατάστασης','ステータスページ','상태 페이지','صفحة الحالة','דף מצב']))
PATTERN=re.compile(r'<!-- rosavio-status-link -->.*?<!-- /rosavio-status-link -->',re.S)
def add(source):
 source=PATTERN.sub('',source)
 lang=re.search(r'<html\b[^>]*\blang="([^"]+)"',source)[1]
 label=html.escape(LABELS[lang])
 link='<!-- rosavio-status-link --><div style="margin:12px 0 18px;text-align:end"><a class="rosavio-status-link" href="status/" target="_blank" rel="noopener noreferrer" style="display:inline-flex;align-items:center;gap:6px;color:#7c1935;font-size:14px;font-weight:700;text-decoration:underline;text-underline-offset:4px">'+label+' <span aria-hidden="true">↗</span></a></div><!-- /rosavio-status-link -->'
 link=link.replace('href="status/"','href="status/?lang='+html.escape(lang,quote=True)+'"')
 result,n=re.subn(r'(<main\b)',lambda m:link+m[1],source,count=1)
 if n!=1:raise ValueError('Unique main element required')
 return result
def main():
 pages=list(pathlib.Path('docs').glob('*.html'))
 if len(pages)!=20:raise ValueError('Exactly twenty languages required')
 for path in pages:
  source=path.read_text(encoding='utf-8-sig');result=add(source)
  if add(result)!=result:raise ValueError('Not idempotent')
  if PATTERN.sub('',result)!=PATTERN.sub('',source):raise ValueError('Existing page changed')
  path.write_text(result,encoding='utf-8')
 print('20 localized status links added; all original page content preserved.')
if __name__=='__main__':main()
