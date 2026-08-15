$ErrorActionPreference = 'Stop'
Clear-Host
Write-Host '===============================================' -ForegroundColor Cyan
Write-Host '       PROMPT TRACE INSTALLATION WIZARD' -ForegroundColor Cyan
Write-Host '===============================================' -ForegroundColor Cyan
Write-Host
Write-Host 'This wizard binds one issued author ID to this device signing identity.'
$displayName = (Read-Host 'Enter your full display name (example: Joe Spack)').Trim()
if (-not $displayName -or $displayName.Length -gt 80) { throw 'Display name must contain 1-80 characters.' }
$actor = (Read-Host 'Enter your unique author ID (1-8 letters or numbers)').Trim().ToUpperInvariant()
if ($actor -notmatch '^[A-Z0-9]{1,8}$') { throw 'Author ID must contain 1-8 alphanumeric characters only.' }

Write-Host
Write-Host 'For one device, press Enter to use the local registry.'
Write-Host 'For a team, enter a shared path such as C:\Users\Owner\OneDrive\PromptTrace\actors.json.'
$registry = (Read-Host 'Shared author registry path (optional)').Trim()
$enrollmentToken = ''
if ($registry) {
  $enrollmentToken = (Read-Host 'Enterprise enrollment token (press Enter for an open team registry)').Trim()
}

Write-Host
Write-Host 'CAPTURE NOTICE' -ForegroundColor Yellow
Write-Host 'After installation, completed PowerShell command text is sanitized, recorded, and signed.'
Write-Host 'Detected passwords, passcodes, PINs, API keys, authorization values, and tokens become **** before storage.'
Write-Host 'Explicit AI prompts can be recorded by piping them to: prompt-trace record --source ai-composer'
Write-Host 'Command output and unsubmitted keystrokes are not recorded. Pause tracing for sensitive work.'
$consent = Read-Host 'Type I CONSENT to continue'
if ($consent -cne 'I CONSENT') { throw 'Consent not granted. No device configuration was changed.' }

$arguments = @{ Actor = $actor; DisplayName = $displayName; AcceptConsent = $true }
if ($registry) { $arguments.Registry = $registry }
if ($enrollmentToken) { $arguments.EnrollmentToken = $enrollmentToken }
& (Join-Path $PSScriptRoot 'install.ps1') @arguments

Write-Host
Write-Host 'Installation complete.' -ForegroundColor Green
Write-Host 'Next: close PowerShell, open it again, enter a command, then run prompt-trace status.'
$exampleExport = Join-Path $HOME 'prompt-trace.csv'
Write-Host "Export with: prompt-trace-export $exampleExport"
Write-Host 'For ChatGPT desktop and Codex integration, run: .\register-mcp.ps1' -ForegroundColor Cyan
