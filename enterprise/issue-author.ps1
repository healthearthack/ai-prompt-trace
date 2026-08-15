param(
  [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9]{1,8}$')][string]$AuthorId,
  [Parameter(Mandatory=$true)][ValidateLength(1,80)][string]$DisplayName,
  [Parameter(Mandatory=$true)][string]$Registry
)
$ErrorActionPreference = 'Stop'
$cli = Join-Path (Split-Path $PSScriptRoot -Parent) 'prompt_trace.py'
python $cli issue-id --actor $AuthorId.ToUpperInvariant() --display-name $DisplayName --registry $Registry
if ($LASTEXITCODE -ne 0) { throw 'Author ID issuance failed.' }
