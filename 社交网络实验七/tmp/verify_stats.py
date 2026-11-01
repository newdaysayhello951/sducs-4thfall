from pathlib import Path
import hashlib,json
stats={}
for folder in ['filmtrust','epinions_665k']:
 d=Path('datasets')/folder
 stats[folder]={}
 for p in d.glob('*.txt'):
  if 'readme' in p.name:continue
  b=p.read_bytes();rows=[x.split() for x in b.decode().splitlines() if x.strip()]
  s={'records':len(rows),'column1_unique':len({r[0] for r in rows}),'column2_unique':len({r[1] for r in rows}),'sha256':hashlib.sha256(b).hexdigest()}
  stats[folder][p.name]=s
print(json.dumps(stats,indent=2))
Path('dataset_check/verified_stats.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
p=Path('dataset_check/epinions_alchemy_archive.tgz')
if p.exists():p.unlink()
