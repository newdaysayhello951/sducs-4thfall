import zipfile,json,pathlib
out=pathlib.Path('dataset_check/retry')
with zipfile.ZipFile(out/'Flixster-figshare.zip') as z:
 print(z.read('Flixster-dataset/readme.txt').decode(errors='replace'))
 counts={}
 for n in ['Flixster-dataset/data/nodes.csv','Flixster-dataset/data/edges.csv']:
  with z.open(n) as f:counts[n]=sum(bool(line.strip()) for line in f)
 print('ACTUAL_ROWS',counts)
 (out/'flixster_figshare_stats.json').write_text(json.dumps(counts,indent=2),encoding='utf-8')
