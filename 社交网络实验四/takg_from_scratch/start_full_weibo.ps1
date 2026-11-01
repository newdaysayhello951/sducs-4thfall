$ErrorActionPreference = 'Stop'
$TaskPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
$RunDirectory = Join-Path $PSScriptRoot 'runs/weibo_takg_seed9527'
New-Item -ItemType Directory -Path $RunDirectory -Force | Out-Null

$Arguments = @('-X', 'utf8', 'run.py', 'all', '--config', 'configs/weibo_full.json')
if (Test-Path -LiteralPath (Join-Path $RunDirectory 'last.pt')) {
    $Arguments += '--resume'
}

$Process = Start-Process -FilePath $TaskPython `
    -ArgumentList $Arguments `
    -WorkingDirectory $PSScriptRoot `
    -RedirectStandardOutput (Join-Path $RunDirectory 'stdout.log') `
    -RedirectStandardError (Join-Path $RunDirectory 'stderr.log') `
    -WindowStyle Hidden `
    -PassThru

[ordered]@{
    pid = $Process.Id
    started_at = (Get-Date).ToString('o')
    run_name = 'weibo_takg_seed9527'
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $RunDirectory 'process.json') -Encoding UTF8

Get-Content -LiteralPath (Join-Path $RunDirectory 'process.json') -Raw -Encoding UTF8
