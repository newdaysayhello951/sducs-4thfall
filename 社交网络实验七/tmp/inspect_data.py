from pathlib import Path
import re,zipfile,hashlib,json
for name in ['librec_datasets','epinions_alchemy','flixster_author']:
 print('\nPAGE',name)
 s=Path('dataset_check/'+name+'.html').read_text(encoding='utf-8')
 for href,label in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>',s,re.S):
  label=re.sub('<[^>]+>','',label)
  if name!='flixster_author' or any(x in (href+label).lower() for x in ['flixster','drive.google','docs.google','dataset']):print(href,label[:100])
for p in Path('dataset_check').glob('*.zip'):
 print('\nZIP',p.name)
 with zipfile.ZipFile(p) as z:
  print(z.namelist())
  for n in z.namelist():
   if not n.endswith('/'):
    d=z.read(n);print(n,len(d),len(d.splitlines()),hashlib.sha256(d).hexdigest())
    if n.lower().endswith('ratings.txt'):
     rows=[x.split() for x in d.decode().splitlines() if x.strip()];print('users',len(set(x[0] for x in rows)),'items',len(set(x[1] for x in rows)))
    if p.name=='filmtrust_author.zip':
     dest=Path('datasets/filmtrust')/Path(n).name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(d)
