import urllib.request,urllib.parse,pathlib,json
u='https://web.archive.org/cdx/search/cdx?'+urllib.parse.urlencode({'url':'labs.fme.aegean.gr/ideal/wp-content/uploads/datasets/flixter/*','output':'json','filter':'statuscode:200','collapse':'urlkey'})
try:
 with urllib.request.urlopen(u,timeout=30) as r:d=r.read()
 pathlib.Path('dataset_check/retry/flixter_data_archive_index.json').write_bytes(d);print(d.decode())
except Exception as e:print(type(e).__name__,str(e))
