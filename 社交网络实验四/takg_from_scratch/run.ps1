param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments)
$ErrorActionPreference = 'Stop'
$TaskPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $TaskPython)) {
    throw 'Missing .venv. Follow README.md to create the environment.'
}
Push-Location $PSScriptRoot
try {
    & $TaskPython -X utf8 (Join-Path $PSScriptRoot 'run.py') @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Command failed with exit code $LASTEXITCODE" }
} finally {
    Pop-Location
}
