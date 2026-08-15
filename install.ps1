param(
  [Parameter(Mandatory=$true)][string]$Actor,
  [string]$DisplayName = '',
  [string]$Registry = '',
  [string]$EnrollmentToken = '',
  [switch]$AcceptConsent
)
$ErrorActionPreference = 'Stop'

Write-Host 'PROMPT TRACE — DEVICE CONFIGURATION' -ForegroundColor Cyan
Write-Host 'This integration records completed PowerShell commands and explicitly submitted prompts.'
Write-Host 'It also records time, author ID, device signature ID, working path, Git context, and exit code.'
Write-Host 'It does not record command output, keystrokes before submission, clipboard data, or file contents.'
Write-Host 'Detected passwords, passcodes, PINs, authorization values, API keys, and tokens are replaced with **** before storage.' -ForegroundColor Green
Write-Host 'Automatic detection is defense-in-depth, not a guarantee. Pause tracing before handling sensitive material.' -ForegroundColor Yellow
if (-not $AcceptConsent) {
  $answer = Read-Host 'Type I CONSENT to configure exact-entry capture on this device'
  if ($answer -cne 'I CONSENT') { throw 'Consent not granted. Nothing was installed.' }
}

$installRoot = Join-Path $env:LOCALAPPDATA 'PromptTrace\app'
New-Item -ItemType Directory -Force -Path $installRoot | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'prompt_trace.py') -Destination (Join-Path $installRoot 'prompt_trace.py') -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'mcp_server.py') -Destination (Join-Path $installRoot 'mcp_server.py') -Force
$cli = Join-Path $installRoot 'prompt_trace.py'
$initArgs = @($cli, 'init', '--actor', $Actor, '--consent')
if ($DisplayName) { $initArgs += @('--display-name', $DisplayName) }
if ($Registry) { $initArgs += @('--registry', $Registry) }
if ($EnrollmentToken) { $initArgs += "--enrollment-token=$EnrollmentToken" }
python @initArgs
if ($LASTEXITCODE -ne 0) { throw 'Author registration failed.' }

$profilePath = $PROFILE.CurrentUserAllHosts
New-Item -ItemType Directory -Force -Path (Split-Path $profilePath) | Out-Null
if (-not (Test-Path $profilePath)) { New-Item -ItemType File -Path $profilePath | Out-Null }
$start = '# >>> prompt-trace-v4 >>>'
$end = '# <<< prompt-trace-v4 <<<'
$existing = Get-Content -LiteralPath $profilePath -Raw
if ($null -eq $existing) { $existing = '' }
$existing = [regex]::Replace($existing, '(?s)\r?\n?\# >>> prompt-trace(?:-v[234])? >>>.*?\# <<< prompt-trace(?:-v[234])? <<<\r?\n?', '')
$escapedCli = $cli.Replace("'", "''")
$block = @"
$start
`$global:PromptTraceCli = '$escapedCli'
`$global:PromptTraceEnabled = `$true
`$global:PromptTraceLastHistoryId = -1
function global:prompt-trace { python `$global:PromptTraceCli @args }
function global:prompt-trace-pause { `$global:PromptTraceEnabled = `$false; Write-Host 'Prompt Trace paused' -ForegroundColor Yellow }
function global:prompt-trace-resume { `$global:PromptTraceEnabled = `$true; Write-Host 'Prompt Trace resumed' -ForegroundColor Green }
function global:prompt-trace-export { param([string]`$Path = "`$HOME\prompt-trace.csv"); python `$global:PromptTraceCli export-csv `$Path }
function global:prompt {
  `$history = Get-History -Count 1 -ErrorAction SilentlyContinue
  if (`$global:PromptTraceEnabled -and `$history -and `$history.Id -ne `$global:PromptTraceLastHistoryId) {
    `$global:PromptTraceLastHistoryId = `$history.Id
    `$history.CommandLine | python `$global:PromptTraceCli record --source powershell --path `$PWD.Path --exit-code `$global:LASTEXITCODE --quiet 2>`$null
  }
  if (`$global:PromptTraceEnabled) {
    Write-Host "[PT:$Actor]" -NoNewline -ForegroundColor Magenta
  } else {
    Write-Host '[PT:PAUSED]' -NoNewline -ForegroundColor Yellow
  }
  " PS `$(`$PWD.Path)> "
}
$end
"@
Set-Content -LiteralPath $profilePath -Value ($existing.TrimEnd() + "`r`n" + $block) -Encoding utf8
Write-Host "Configured Prompt Trace for $Actor on this device." -ForegroundColor Green
Write-Host "Open a new PowerShell window. The prompt will show [PT:$Actor]."
Write-Host 'Safety controls: prompt-trace-pause, prompt-trace-resume, prompt-trace-export'
Write-Host 'Desktop integration: run .\register-mcp.ps1 and follow the displayed ChatGPT MCP settings.'
