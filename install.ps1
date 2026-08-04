param(
  [Parameter(Mandatory=$true)][string]$Actor,
  [string]$Marker = 'PT',
  [ValidateSet('path-only','command-hash')][string]$Capture = 'command-hash'
)
$ErrorActionPreference = 'Stop'
$installRoot = Join-Path $env:LOCALAPPDATA 'PromptTrace\app'
New-Item -ItemType Directory -Force -Path $installRoot | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'prompt_trace.py') -Destination (Join-Path $installRoot 'prompt_trace.py') -Force
python (Join-Path $installRoot 'prompt_trace.py') init --actor $Actor --marker $Marker --capture $Capture

$profilePath = $PROFILE.CurrentUserAllHosts
New-Item -ItemType Directory -Force -Path (Split-Path $profilePath) | Out-Null
if (-not (Test-Path $profilePath)) { New-Item -ItemType File -Path $profilePath | Out-Null }
$start = '# >>> prompt-trace >>>'
$end = '# <<< prompt-trace <<<'
$existing = Get-Content -LiteralPath $profilePath -Raw
if ($null -eq $existing) { $existing = '' }
$existing = [regex]::Replace($existing, "(?s)\r?\n?$([regex]::Escape($start)).*?$([regex]::Escape($end))\r?\n?", '')
$escapedCli = (Join-Path $installRoot 'prompt_trace.py').Replace("'", "''")
$block = @"
$start
`$global:PromptTraceCli = '$escapedCli'
`$global:PromptTraceMarker = '$($Marker.Replace("'", "''"))'
`$global:PromptTraceCapture = '$Capture'
function global:prompt-trace { python `$global:PromptTraceCli @args }
`$global:PromptTraceLastHistoryId = -1
function global:prompt {
  `$history = Get-History -Count 1 -ErrorAction SilentlyContinue
  if (`$history -and `$history.Id -ne `$global:PromptTraceLastHistoryId) {
    `$global:PromptTraceLastHistoryId = `$history.Id
    if (`$global:PromptTraceCapture -eq 'command-hash') {
      `$commandHash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes(`$history.CommandLine))).ToLower()
      python `$global:PromptTraceCli checkpoint --path `$PWD.Path --workflow powershell --command-hash `$commandHash --exit-code `$global:LASTEXITCODE --quiet 2>`$null
    } else {
      python `$global:PromptTraceCli checkpoint --path `$PWD.Path --workflow powershell --exit-code `$global:LASTEXITCODE --quiet 2>`$null
    }
  }
  "`e[32m`$global:PromptTraceMarker`e[0m PS `$(`$PWD.Path)> "
}
$end
"@
Set-Content -LiteralPath $profilePath -Value ($existing.TrimEnd() + "`r`n" + $block) -Encoding utf8
Write-Host 'Prompt Trace is installed. Open a new PowerShell window to see PT● beside the prompt.' -ForegroundColor Green
Write-Host "Ledger: $(Join-Path $env:LOCALAPPDATA 'PromptTrace\breadcrumbs.jsonl')"
