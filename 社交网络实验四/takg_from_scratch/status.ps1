$ErrorActionPreference = 'Stop'
$RunDirectory = Join-Path $PSScriptRoot 'runs/weibo_takg_seed9527'
$ProcessFile = Join-Path $RunDirectory 'process.json'
if (-not (Test-Path -LiteralPath $ProcessFile)) {
    Write-Output 'Full Weibo training has not been started.'
    exit 0
}
$Info = Get-Content -LiteralPath $ProcessFile -Raw -Encoding UTF8 | ConvertFrom-Json
[ordered]@{
    run_name = $Info.run_name
    pid = $Info.pid
    running = $null -ne (Get-Process -Id $Info.pid -ErrorAction SilentlyContinue)
    checkpoint = Test-Path -LiteralPath (Join-Path $RunDirectory 'last.pt')
    best_model = Test-Path -LiteralPath (Join-Path $RunDirectory 'best.pt')
    predictions = Test-Path -LiteralPath (Join-Path $RunDirectory 'predictions.txt')
    metrics = Test-Path -LiteralPath (Join-Path $RunDirectory 'metrics.json')
} | ConvertTo-Json
$StatusFile = Join-Path $RunDirectory 'status.json'
if (Test-Path -LiteralPath $StatusFile) {
    Get-Content -LiteralPath $StatusFile -Raw -Encoding UTF8
}
$LogFile = Join-Path $RunDirectory 'stdout.log'
if (Test-Path -LiteralPath $LogFile) {
    Get-Content -LiteralPath $LogFile -Tail 12 -Encoding UTF8
}
