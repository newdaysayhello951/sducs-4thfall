"""Run not-yet-started primary-model jobs with the existing manifest settings.

Does not change manifests or progress files and never overwrites a completed job.
Use only when the regular queue has not yet reached the TrustSVD jobs.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from trustsvd_repro.data import ROOT
from trustsvd_repro.experiment import run_one


if __name__=='__main__':
    args=json.loads((ROOT/'results/paper/manifest.json').read_text(encoding='utf-8'))['arguments']
    tasks=[('epinions','TrustSVD',d,f,args) for d in args['dims'] for f in args['folds']]
    with ThreadPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(run_one,t) for t in tasks]):
            result=future.result()
            print(result['dataset'],result['dim'],result['fold'],result['all'],result['seconds'],flush=True)
