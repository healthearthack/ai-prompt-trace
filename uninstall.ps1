$ErrorActionPreference = 'Stop'
$profilePath = $PROFILE.CurrentUserAllHosts
if (Test-Path $profilePath) {
  $content = Get-Content -LiteralPath $profilePath -Raw
  $content = [regex]::Replace($content, '(?s)\r?\n?\# >>> prompt-trace >>>.*?\# <<< prompt-trace <<<\r?\n?', '')
  Set-Content -LiteralPath $profilePath -Value $content -Encoding utf8
}
Write-Host 'Prompt Trace prompt helper removed. Signed breadcrumbs and identity remain in LocalAppData.'
