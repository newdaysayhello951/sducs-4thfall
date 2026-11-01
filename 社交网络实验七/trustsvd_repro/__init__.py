"""Independent, equation-based reproduction of Guo et al. (AAAI 2015)."""
import os

# Prevent nested BLAS threads from oversubscribing CPU during parallel folds.
# Explicit user settings are preserved. This runs before NumPy in the CLI.
for _name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ.setdefault(_name,'1')
