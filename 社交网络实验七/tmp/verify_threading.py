import json,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path.cwd()))
from trustsvd_repro.experiment import run_one
args=json.loads(Path('results/gradient_descent/manifest.json').read_text(encoding='utf-8'))['arguments']
args.update(run='nogil_check',force=True)
r=run_one(('filmtrust','TrustSVD',5,0,args))
a=np.load('results/gradient_descent/filmtrust/TrustSVD_d5_fold0.npz')['prediction']
b=np.load('results/nogil_check/filmtrust/TrustSVD_d5_fold0.npz')['prediction']
print('bitwise_equal_after_threading_optimization',np.array_equal(a,b))
assert np.array_equal(a,b)
