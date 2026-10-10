[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$BaseCheckout,
  [Parameter(Mandatory=$true)][string]$PrCheckout,
  [string]$RepoRoot = ''
)
if (-not $RepoRoot) {
  $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
  if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
  if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
  $RepoRoot = (Resolve-Path (Join-Path $scriptDir '..')).Path
}
$ErrorActionPreference = 'Stop'
$BaseSha = 'd65c8da504ca566d3b9590b798c72b9ab720ce59'
$PrSha = 'e24bff266a4fc2ab5046c18e8348f130c7d5625f'
$TaskRoot = Join-Path $RepoRoot 'corpus/expanded-deepeval-3338'
$RunStamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$OutRoot = Join-Path $env:TEMP "graderprobe-expanded-deepeval-raw-$RunStamp"
$Python = (Get-Command python -ErrorAction Stop).Source
function Assert-Revision([string]$Path,[string]$Expected,[string]$Label) {
  if (-not (Test-Path (Join-Path $Path '.git'))) { throw "$Label checkout is missing: $Path" }
  $sha = (& git -C $Path rev-parse HEAD).Trim()
  if ($LASTEXITCODE -ne 0) { throw "Could not read git HEAD for $Label" }
  if (-not $sha.StartsWith($Expected)) { throw "$Label revision mismatch: expected $Expected, got $sha. Do not continue." }
}
function Run-Side([string]$Label,[string]$Checkout,[string]$ExpectedSha,[string]$ExpectedVerdict,[int]$ExpectedExit) {
  Assert-Revision $Checkout $ExpectedSha $Label
  $env:PYTHONPATH = "$Checkout;$RepoRoot/src"
  $prov = & $Python -c "import deepeval, pathlib; print(pathlib.Path(deepeval.__file__).resolve())"
  if ($LASTEXITCODE -ne 0) { throw "Could not import DeepEval for $Label" }
  $provPath = ($prov | Select-Object -Last 1).Trim()
  $fullCheckout = [System.IO.Path]::GetFullPath($Checkout).TrimEnd('\') + '\'
  if (-not $provPath.StartsWith($fullCheckout,[System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Wrong DeepEval source imported for $($Label): $provPath; expected under $Checkout"
  }
  $out = Join-Path $OutRoot $Label
  New-Item -ItemType Directory -Force -Path $out | Out-Null
  $log = Join-Path $out 'audit.log'
  $prevEap = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  & $Python -m graderprobe audit $TaskRoot --out $out --workers 1 --task-workers 1 --execution-slots 1 *>&1 | Tee-Object -FilePath $log
  $code = $LASTEXITCODE
  $ErrorActionPreference = $prevEap
  if ($code -ne $ExpectedExit) { throw "$Label GraderProbe exit code $code; expected $ExpectedExit. Inspect $log" }
  $auditPath = Join-Path $out 'audit.json'
  if (-not (Test-Path $auditPath)) { throw "$Label audit.json missing" }
  $audit = Get-Content $auditPath -Raw | ConvertFrom-Json
  if ($audit.tasks.Count -ne 3) { throw "$Label expected 3 tasks, found $($audit.tasks.Count)" }
  foreach ($task in $audit.tasks) {
    if ($task.verdict -ne $ExpectedVerdict) { throw "$Label $($task.task_id) verdict $($task.verdict); expected $ExpectedVerdict" }
    if ($task.error) { throw "$Label task error: $($task.error)" }
  }
  Write-Host "$Label PASS: imported $provPath; 3 task verdicts = $ExpectedVerdict; exit=$code"
}
# Base must demonstrate the boundary failures; PR head must eliminate them.
Run-Side 'base' $BaseCheckout $BaseSha 'BOUNDARY_FAIL' 3
Run-Side 'pr_head' $PrCheckout $PrSha 'BOUNDARY_OK' 0
Write-Host "Raw local artifacts written under $OutRoot (do not publish raw logs)"
Write-Host "Next run: python tools/verify_expanded_graderprobe_results.py --results `"$OutRoot`""
Write-Host "Then sanitize to artifacts/phase7/expanded-deepeval-graderprobe/sanitized before commit/push."
