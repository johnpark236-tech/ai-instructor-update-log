# Task Scheduler entrypoint; runs only under the Windows user who signed into Codex.
param(
  [Parameter(Mandatory=$true)][ValidateSet('news','lesson')][string]$Kind,
  [Parameter(Mandatory=$true)][string]$Root
)
$ErrorActionPreference = 'Stop'
$project = Join-Path $Root 'ai-instructor-update-log'
$news = Join-Path $Root 'mannal_news'
$engine = Join-Path $project 'automation\codex\hourly_publish.py'
$logs = Join-Path $env:USERPROFILE '.mannal-codex-hourly'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$log = Join-Path $logs "$Kind-$stamp.log"
if (-not (Test-Path $engine)) { throw "Missing hourly_publish.py: $engine" }
try {
  & python -X utf8 $engine --kind $Kind --news-repo $news --lesson-repo $project *> $log
  if ($LASTEXITCODE -ne 0) { throw "Codex $Kind publisher failed (see $log)" }
} catch {
  Add-Content -Path $log -Value ("ERROR: " + $_.Exception.Message) -Encoding UTF8
  throw
}
