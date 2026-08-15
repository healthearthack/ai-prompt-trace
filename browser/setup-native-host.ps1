param([Parameter(Mandatory=$true)][string]$ExtensionId)
$ErrorActionPreference = 'Stop'
if ($ExtensionId -notmatch '^[a-p]{32}$') { throw 'Chrome extension ID must be 32 letters from a through p.' }
$browserRoot = $PSScriptRoot
$hostScript = Join-Path $browserRoot 'native_host.py'
$python = (Get-Command python -ErrorAction Stop).Source
$launcher = Join-Path $browserRoot 'prompt-trace-native-host.bat'
Set-Content $launcher "@echo off`r`n`"$python`" `"$hostScript`"" -Encoding ascii
$manifestPath = Join-Path $browserRoot 'cloud.thepolka.prompt_trace.json'
$manifest = @{
  name = 'cloud.thepolka.prompt_trace'
  description = 'Prompt Trace local signed-ledger bridge'
  path = $launcher
  type = 'stdio'
  allowed_origins = @("chrome-extension://$ExtensionId/")
} | ConvertTo-Json -Depth 4
Set-Content $manifestPath $manifest -Encoding utf8
$browserKeys = @(
  'HKCU:\Software\Google\Chrome\NativeMessagingHosts\cloud.thepolka.prompt_trace',
  'HKCU:\Software\Microsoft\Edge\NativeMessagingHosts\cloud.thepolka.prompt_trace',
  'HKCU:\Software\BraveSoftware\Brave-Browser\NativeMessagingHosts\cloud.thepolka.prompt_trace'
)
foreach ($key in $browserKeys) {
  New-Item $key -Force | Out-Null
  Set-Item -Path $key -Value $manifestPath
}
Write-Host 'Browser companion configured for Chrome, Edge, and Brave.' -ForegroundColor Green
Write-Host "Native host: $manifestPath"
