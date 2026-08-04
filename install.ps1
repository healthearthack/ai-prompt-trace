param(
  [Parameter(Mandatory=$true)][string]$Actor,
  [string]$Marker = 'PT',
  [ValidateSet('path-only','command-hash')][string]$Capture = 'command-hash',
  [switch]$AcceptConsent
)
$ErrorActionPreference = 'Stop'
# The consent notice is the trailhead gate. Copying the map is not permission to
# follow a traveler; they must deliberately open this gate first.
Write-Host 'PROMPT TRACE CONSENT' -ForegroundColor Yellow
Write-Host "Records: actor, time, working path, Git project/remote/branch/commit, workflow, exit code$(if($Capture -eq 'command-hash'){', and a one-way command hash'})."
Write-Host 'Never records by default: raw commands, prompts, output, keystrokes, clipboard, environment values, file contents, or credentials.'
Write-Host 'Storage is local. The PowerShell prompt will visibly show your chosen marker while enabled.'
if (-not $AcceptConsent) {
  $answer = Read-Host 'Type I CONSENT to enable tracing'
  if ($answer -cne 'I CONSENT') { throw 'Consent not granted. Nothing was installed.' }
}
$installRoot = Join-Path $env:LOCALAPPDATA 'PromptTrace\app'
# Place the trail keeper in the user's private local station, not in whichever
# project happened to contain the installer today.
New-Item -ItemType Directory -Force -Path $installRoot | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'prompt_trace.py') -Destination (Join-Path $installRoot 'prompt_trace.py') -Force
python (Join-Path $installRoot 'prompt_trace.py') init --actor $Actor --marker $Marker --capture $Capture --consent

$profilePath = $PROFILE.CurrentUserAllHosts
New-Item -ItemType Directory -Force -Path (Split-Path $profilePath) | Out-Null
if (-not (Test-Path $profilePath)) { New-Item -ItemType File -Path $profilePath | Out-Null }
$start = '# >>> prompt-trace >>>'
$end = '# <<< prompt-trace <<<'
# Marker fences let a later install replace only its own garden plot in the
# PowerShell profile, leaving every neighboring user customization untouched.
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
  # PowerShell rings this bell after a command finishes. We stamp each history ID
  # once, so repainting the prompt cannot scatter duplicate breadcrumbs.
  `$history = Get-History -Count 1 -ErrorAction SilentlyContinue
  if (`$history -and `$history.Id -ne `$global:PromptTraceLastHistoryId) {
    `$global:PromptTraceLastHistoryId = `$history.Id
    if (`$global:PromptTraceCapture -eq 'command-hash') {
      # Fold the command into a one-way fingerprint: later it can prove a match,
      # while the ledger itself never learns the words that made the fingerprint.
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
# The visible marker is the porch light: users can always see that the keeper is awake.
Write-Host "Prompt Trace is installed. Open a new PowerShell window to see $Marker beside the prompt." -ForegroundColor Green
Write-Host "Ledger: $(Join-Path $env:LOCALAPPDATA 'PromptTrace\breadcrumbs.jsonl')"
