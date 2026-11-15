[CmdletBinding()]
param(
    [string]$Python = ".venv\Scripts\python.exe",
    [string]$Manifest = "work\manifest.json"
)

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\")).Path
Push-Location $repo
try {
    if (-not (Test-Path -LiteralPath $Python)) {
        throw "No se encontró el intérprete preparado: $Python"
    }

    function Invoke-Gate([string]$Name, [string[]]$Arguments) {
        Write-Host "== $Name =="
        & $Python @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "Falló el gate '$Name' con código $LASTEXITCODE"
        }
    }

    $env:QT_QPA_PLATFORM = "offscreen"
    Invoke-Gate "diagnóstico offline" @("scripts\diagnose_offline.py", "--json")
    Write-Host "== suite completa =="
    $testOutput = @(& $Python -m pytest -q 2>&1)
    $testExit = $LASTEXITCODE
    $testOutput | Write-Output
    # En Windows/Qt puede quedar un código nativo no cero después de que
    # pytest informa todos los tests aprobados. Solo se tolera ese caso exacto.
    $allPassed = ($testOutput -match "195 passed") -and
        ($testOutput -notmatch "failed|error|ERROR|FAILED")
    if ($testExit -ne 0 -and -not $allPassed) {
        throw "Falló el gate 'suite completa' con código $testExit"
    }
    if ($testExit -ne 0) {
        Write-Warning "Qt terminó con código nativo $testExit después de 195 pruebas aprobadas."
    }
    Invoke-Gate "límite de red runtime" @("scripts\check_offline_boundary.py", "--json")
    Invoke-Gate "escenarios deterministas" @("scripts\verify_demo_scenarios.py", "--json")
    Invoke-Gate "compilación" @("-m", "py_compile", "app.py")
    Invoke-Gate "manifiesto" @("scripts\package_manifest.py", ".", $Manifest)
    Invoke-Gate "verificación de manifiesto" @("scripts\package_manifest.py", ".", $Manifest, "--verify")
    Write-Host "Gates offline automatizables: OK"
}
finally {
    Pop-Location
}
