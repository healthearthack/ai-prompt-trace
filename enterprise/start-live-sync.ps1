param(
  [Parameter(Mandatory=$true)][string]$DestinationFolder,
  [ValidateRange(5,3600)][int]$IntervalSeconds = 15
)
$ErrorActionPreference = 'Stop'
Write-Host "Prompt Trace live audit sync started. Refresh interval: $IntervalSeconds seconds." -ForegroundColor Green
Write-Host 'Press Ctrl+C to stop. Keep this window open.' -ForegroundColor Yellow
while ($true) {
  & (Join-Path $PSScriptRoot 'publish-audit.ps1') -DestinationFolder $DestinationFolder
  Start-Sleep -Seconds $IntervalSeconds
}
