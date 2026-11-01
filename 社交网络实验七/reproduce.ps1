param(
    [string]$Python = 'D:\anaconda\python.exe',
    [string]$Run = 'gradient_descent',
    [int]$Jobs = 2
)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
& $Python -m pytest -q tests
if ($LASTEXITCODE -ne 0) { throw 'Mathematical verification failed.' }
& $Python -u -m trustsvd_repro.experiment --run $Run --jobs $Jobs --optimizer gd
if ($LASTEXITCODE -ne 0) { throw 'An experiment failed; inspect results before continuing.' }
& $Python -m trustsvd_repro.report --run $Run
if ($LASTEXITCODE -ne 0) { throw 'Report generation failed.' }
& $Python -m trustsvd_repro.audit --run $Run
if ($LASTEXITCODE -ne 0) { throw 'Saved-result audit failed.' }
$audit = Get-Content -LiteralPath (Join-Path $PSScriptRoot "results/$Run/audit.json") -Raw | ConvertFrom-Json
if (-not $audit.complete_for_entire_paper) {
    Write-Output 'Partial reproduction only. The paper-specific Ciao and Flixster datasets remain unavailable; see the report.'
    exit 2
}
