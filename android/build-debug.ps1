$ErrorActionPreference = 'Stop'

& (Join-Path $PSScriptRoot 'prepare.ps1')

$gradle = Join-Path $PSScriptRoot 'gradlew.bat'
if (-not (Test-Path -LiteralPath $gradle)) {
    throw 'Falta Gradle Wrapper; genera el wrapper antes de compilar.'
}
& $gradle ':app:assembleDebug'
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host (Join-Path $PSScriptRoot 'app/build/outputs/apk/debug/app-debug.apk')
