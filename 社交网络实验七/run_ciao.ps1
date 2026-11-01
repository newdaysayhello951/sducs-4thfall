param([string]$Python = 'D:\anaconda\python.exe', [int]$Jobs = 2)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
& $Python prepare_ciao.py
if ($LASTEXITCODE -ne 0) { throw 'Ciao preparation failed.' }
& $Python -u -m trustsvd_repro.experiment --datasets ciao --allow-mismatch ciao --run ciao_original_gd --optimizer gd --maxiter 200 --jobs $Jobs
if ($LASTEXITCODE -ne 0) { throw 'Ciao training failed.' }
& $Python -m trustsvd_repro.report --run ciao_original_gd
if ($LASTEXITCODE -ne 0) { throw 'Ciao report failed.' }
& $Python -m trustsvd_repro.audit --run ciao_original_gd
if ($LASTEXITCODE -ne 0) { throw 'Ciao audit failed.' }
