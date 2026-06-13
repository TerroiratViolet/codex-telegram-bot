$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$systemPython = Join-Path $env:LOCALAPPDATA "Programs\Python\Python313\python.exe"

if (-not (Test-Path $systemPython)) {
    throw "Python 3.13 was not found. Install Python.Python.3.13 with winget."
}

if (-not (Test-Path $venvPython)) {
    & $systemPython -m venv (Join-Path $projectRoot ".venv")
}

& $venvPython -m pip install -r (Join-Path $projectRoot "requirements-dev.txt")
& (Join-Path $projectRoot "scripts\verify.ps1")

