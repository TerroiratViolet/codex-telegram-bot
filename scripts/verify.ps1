$ErrorActionPreference = "Stop"

$python = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Missing .venv. Follow README section 3 to create it first."
}

& $python -m ruff check .
& $python -m pytest
& $python -m schedule_bot --smoke-test "/start"

Write-Host "All local acceptance checks passed."

