$ErrorActionPreference = 'Stop'
$profilePath = $PROFILE.CurrentUserAllHosts
if (Test-Path $profilePath) {
  # Remove our fenced garden plot without uprooting the rest of the user's profile.
  $content = Get-Content -LiteralPath $profilePath -Raw
  $content = [regex]::Replace($content, '(?s)\r?\n?\# >>> prompt-trace(?:-v[234])? >>>.*?\# <<< prompt-trace(?:-v[234])? <<<\r?\n?', '')
  Set-Content -LiteralPath $profilePath -Value $content -Encoding utf8
}
# Taking down the trailhead sign stops future tracing, but does not burn the old
# signed journal. Provenance should disappear only through a separate deliberate act.
Write-Host 'Prompt Trace prompt helper removed. Signed breadcrumbs and identity remain in LocalAppData.'
