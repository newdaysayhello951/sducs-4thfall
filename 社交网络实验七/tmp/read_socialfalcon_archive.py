import urllib.request,re,pathlib
u='https://web.archive.org/web/20150509110635id_/http://labs.fme.aegean.gr/ideal/socialfalcon-datasets/'
try:
 with urllib.request.urlopen(u,timeout=25) as r:d=r.read()
 pathlib.Path('dataset_check/retry/socialfalcon_historical_page.html').write_bytes(d)
 s=d.decode(errors='replace')
 print('PAGE_TITLE',re.findall(r'<title>(.*?)</title>',s,re.S))
 for href,label in re.findall(r'<a[^>]+href=[\"\x27]([^\"\x27]+)[\"\x27][^>]*>(.*?)</a>',s,re.S):
  if any(x in (href+label).lower() for x in ['flix','zip','rar','csv','drive','dropbox','dataset','download']):print(href,re.sub('<[^>]+>','',label))
except Exception as e:print(type(e).__name__,str(e))
