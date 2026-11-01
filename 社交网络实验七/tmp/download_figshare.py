import urllib.request,pathlib,hashlib,zipfile,re,json
out=pathlib.Path('dataset_check/retry')
u='https://ndownloader.figshare.com/files/9928717'
try:
 with urllib.request.urlopen(u,timeout=60) as r:d=r.read()
 p=out/'Flixster-figshare.zip';p.write_bytes(d)
 print('flixster_zip_bytes',len(d),'md5',hashlib.md5(d).hexdigest());assert hashlib.md5(d).hexdigest()=='867c0742cfec94591f12fdc6585cbaf9'
 with zipfile.ZipFile(p) as z:
  for f in z.infolist():
   print(f.filename,f.file_size)
   if pathlib.Path(f.filename).suffix.lower() in ['.txt','.csv','.dat','.arff']:
    with z.open(f) as stream: print('DATA_HEADER',repr(stream.read(220)))
except Exception as e:print('FIGSHARE_ERROR',str(e))
s=(out/'librec_dataset_listing.txt').read_text(encoding='utf-8')
for v in re.findall(r'"(?:name|path)":"([^"\n]+)"',s):
 if 'Dataset' in v or '/' not in v:print('LIBREC_DATA_ENTRY',v)
