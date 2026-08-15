param(
  [Parameter(Mandatory=$true)][string]$DestinationFolder,
  [switch]$Archive
)
$ErrorActionPreference = 'Stop'
$configPath = Join-Path $env:LOCALAPPDATA 'PromptTrace\config.json'
if (-not (Test-Path $configPath)) { throw 'Prompt Trace is not configured for this Windows user.' }
$config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
$destination = [System.IO.Path]::GetFullPath($DestinationFolder)
New-Item -ItemType Directory -Force -Path $destination | Out-Null
$suffix = if ($Archive) { Get-Date -Format 'yyyyMMdd-HHmmss' } else { 'latest' }
$file = Join-Path $destination ("prompt-trace-{0}-{1}.csv" -f $config.actor, $suffix)
$temporary = "$file.tmp"
$cli = Join-Path $env:LOCALAPPDATA 'PromptTrace\app\prompt_trace.py'
python $cli export-csv $temporary
if ($LASTEXITCODE -ne 0) { throw 'Audit export failed.' }
Move-Item -LiteralPath $temporary -Destination $file -Force
Write-Host "Published sanitized audit export for $($config.actor): $file" -ForegroundColor Green
Write-Host 'Treat this file as confidential employee work data.' -ForegroundColor Yellow
