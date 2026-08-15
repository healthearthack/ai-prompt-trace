param([switch]$CodexCli)
$ErrorActionPreference = 'Stop'

$installRoot = Join-Path $env:LOCALAPPDATA 'PromptTrace\app'
$server = Join-Path $installRoot 'mcp_server.py'
if (-not (Test-Path $server)) {
  throw "Prompt Trace MCP server is not installed at $server. Run setup-wizard.ps1 first."
}
$python = (Get-Command python -ErrorAction Stop).Source

if ($CodexCli) {
  $codex = Get-Command codex -ErrorAction Stop
  & $codex.Source mcp remove prompt-trace 2>$null
  & $codex.Source mcp add prompt-trace -- $python $server
  if ($LASTEXITCODE -ne 0) { throw 'Codex MCP registration failed.' }
  & $codex.Source mcp list
  exit
}

Write-Host 'Prompt Trace desktop integration is installed.' -ForegroundColor Green
Write-Host 'In the ChatGPT desktop app:' -ForegroundColor Cyan
Write-Host '  1. Open Settings > MCP servers > Add server.'
Write-Host '  2. Name: Prompt Trace'
Write-Host '  3. Connection: STDIO'
Write-Host "  4. Command: $python"
Write-Host "  5. Arguments: $server"
Write-Host '  6. Save, restart ChatGPT, then type /mcp to verify.'
