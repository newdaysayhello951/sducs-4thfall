import urllib.request,pathlib,re
out=pathlib.Path('dataset_check/retry')
u='https://web.archive.org/web/20131015031046id_/http://www.public.asu.edu:80/~jtang20/datasetcode/truststudy.htm'
try:
 with urllib.request.urlopen(u,timeout=30) as r:d=r.read()
 (out/'ciao_publisher_2013.html').write_bytes(d)
 for href,label in re.findall(r'<a[^>]+href=[\"\x27]([^\"\x27]+)[\"\x27][^>]*>(.*?)</a>',d.decode(errors='replace'),re.S):
  if any(s in href.lower() for s in ['ciao','zip','rar','readme','dropbox','drive']): print(href,re.sub('<[^>]+>','',label))
except Exception as e:print(type(e).__name__,str(e))
