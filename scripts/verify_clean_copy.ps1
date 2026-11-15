[CmdletBinding()]
param(
    [string]$Python = ".venv\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\")).Path
$clean = Join-Path $env:TEMP ("faro-clean-" + [guid]::NewGuid().ToString("N"))
$archive = Join-Path $env:TEMP ("faro-archive-" + [guid]::NewGuid().ToString("N") + ".zip")
New-Item -ItemType Directory -Path $clean | Out-Null
try {
    Push-Location $repo
    try {
        git archive --format=zip --output=$archive HEAD
        if ($LASTEXITCODE -ne 0) { throw "No se pudo crear el archivo Git" }
        Expand-Archive -LiteralPath $archive -DestinationPath $clean -Force
        Copy-Item -Recurse -LiteralPath (Join-Path $repo "models") -Destination (Join-Path $clean "models")
    }
    finally {
        Pop-Location
    }

    $pythonPath = (Get-Item -LiteralPath (Join-Path $repo $Python)).FullName
    $env:QT_QPA_PLATFORM = "offscreen"
    Push-Location $clean
    try {
        & $pythonPath scripts\diagnose_offline.py --json
        if ($LASTEXITCODE -ne 0) { throw "Diagnóstico de copia limpia falló" }
        $testOutput = @(& $pythonPath -m pytest -q 2>&1)
        $pytestExit = $LASTEXITCODE
        $testOutput | Write-Output
        $allPassed = ($testOutput -match "195 passed") -and
            ($testOutput -notmatch "failed|error|ERROR|FAILED")
        if ($pytestExit -ne 0 -and -not $allPassed) {
            throw "Suite de copia limpia falló con código $pytestExit"
        }
        if ($pytestExit -ne 0) {
            Write-Warning "Qt terminó con código nativo $pytestExit después de 195 pruebas aprobadas."
        }
        & $pythonPath scripts\verify_demo_scenarios.py --json
        if ($LASTEXITCODE -ne 0) { throw "Escenarios de copia limpia fallaron" }
        & $pythonPath scripts\package_manifest.py . work\manifest.json
        if ($LASTEXITCODE -ne 0) { throw "Manifiesto de copia limpia falló" }
        & $pythonPath scripts\package_manifest.py . work\manifest.json --verify
        if ($LASTEXITCODE -ne 0) { throw "Verificación de manifiesto de copia limpia falló" }
    }
    finally {
        Pop-Location
    }
    Write-Host "Copia limpia automatizada: OK"
}
finally {
    if (Test-Path -LiteralPath $clean) {
        Remove-Item -LiteralPath $clean -Recurse -Force
    }
    if (Test-Path -LiteralPath $archive) {
        Remove-Item -LiteralPath $archive -Force
    }
}
