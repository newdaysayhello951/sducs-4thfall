import urllib.request,pathlib,json
u='https://web.archive.org/web/20110415084158id_/http://www.cs.sfu.ca:80/~sja25/personal/datasets/'
try:
 with urllib.request.urlopen(u,timeout=25) as r:d=r.read()
 pathlib.Path('dataset_check/retry/flixster_old_page.html').write_bytes(d);print(d.decode(errors='replace'))
except Exception as e:print(type(e).__name__,str(e))
