from pathlib import Path
import json,sys
from concurrent.futures import ThreadPoolExecutor,as_completed
sys.path.insert(0,str(Path.cwd()))
from trustsvd_repro.experiment import run_one
args=json.loads(Path('results/gradient_descent/manifest.json').read_text(encoding='utf-8'))['arguments']
args['force']=True
tasks=[('filmtrust','SoReg',d,f,args) for d in (5,10) for f in range(5)]
with ThreadPoolExecutor(max_workers=2) as pool:
 for future in as_completed([pool.submit(run_one,t) for t in tasks]):
  r=future.result();print(r['dim'],r['fold'],r['all'],flush=True)
