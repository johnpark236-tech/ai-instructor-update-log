# One-time setup: run in your own Windows PowerShell, not GitHub-hosted Actions.
param([string]$Root = (Join-Path $env:USERPROFILE 'MannalCodexHourly'))
$ErrorActionPreference = 'Stop'
if (-not $IsWindows -and $PSVersionTable.PSEdition -eq 'Core') {
  if ($env:OS -ne 'Windows_NT') { throw 'This installer is for Windows only.' }
}
foreach ($app in @('git','python','codex')) {
  if (-not (Get-Command $app -ErrorAction SilentlyContinue)) {
    throw "Required executable '$app' is not installed or not in PATH."
  }
}
& codex login status | Out-Host
if ($LASTEXITCODE -ne 0) { throw 'Sign in using codex login (ChatGPT account), then retry.' }
New-Item -ItemType Directory -Force -Path $Root | Out-Null
$project = Join-Path $Root 'ai-instructor-update-log'
$news = Join-Path $Root 'mannal_news'
foreach ($info in @(
  @{ dir = $project; repo = 'ai-instructor-update-log' },
  @{ dir = $news; repo = 'mannal_news' }
)) {
  if (-not (Test-Path (Join-Path $info.dir '.git'))) {
    if (Test-Path $info.dir) { throw "Directory exists but is not a Git checkout: $($info.dir)" }
    & git clone ("https://github.com/johnpark236-tech/" + $info.repo + ".git") $info.dir
    if ($LASTEXITCODE -ne 0) { throw "Failed to clone $($info.repo)" }
  }
}
$engine = Join-Path $project 'automation\codex\hourly_publish.py'
if (-not (Test-Path $engine)) { throw 'Update/clone your AI instructor repository; automation files are missing.' }
& python -X utf8 $engine --self-test | Out-Host
if ($LASTEXITCODE -ne 0) { throw 'Configuration test failed.' }

$runner = Join-Path $project 'automation\codex\run-task.ps1'
$userId = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 55) -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$now = Get-Date
foreach ($item in @(
  @{ name = 'Mannal-Codex-AI-News'; kind = 'news'; minute = 5 },
  @{ name = 'Mannal-Codex-AI-Lessons'; kind = 'lesson'; minute = 35 }
)) {
  $start = Get-Date -Year $now.Year -Month $now.Month -Day $now.Day -Hour $now.Hour -Minute $item.minute -Second 0
  if ($start -le $now) { $start = $start.AddHours(1) }
  $trigger = New-ScheduledTaskTrigger -Once -At $start -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Days 3650)
  $arguments = '-NoLogo -NoProfile -ExecutionPolicy Bypass -File "' + $runner + '" -Kind ' + $item.kind + ' -Root "' + $Root + '"'
  $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $arguments -WorkingDirectory $project
  Register-ScheduledTask -TaskName $item.name -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
  Write-Host ("Scheduled " + $item.name + " every hour, first: " + $start.ToString('yyyy-MM-dd HH:mm'))
}
Write-Host 'Configured for the current signed-in Windows user. Keep the computer awake and the user session signed in.'
Write-Host ('Read results under ' + (Join-Path $env:USERPROFILE '.mannal-codex-hourly'))
Write-Host 'IMPORTANT: Existing ChatGPT hourly news task must be paused only after verifying local CLI publishes correctly.'
