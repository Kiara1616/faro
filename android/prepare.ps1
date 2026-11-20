$ErrorActionPreference = 'Stop'

$androidRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)
$projectRoot = [System.IO.Path]::GetFullPath((Join-Path $androidRoot '..'))
$pythonRoot = [System.IO.Path]::GetFullPath((Join-Path $androidRoot 'app/src/main/python'))
$pythonPrefix = $pythonRoot.TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar

function Reset-GeneratedDirectory([string] $name) {
    $target = [System.IO.Path]::GetFullPath((Join-Path $pythonRoot $name))
    if (-not $target.StartsWith($pythonPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "La ruta generada está fuera del módulo Android: $target"
    }
    if (Test-Path -LiteralPath $target) {
        Remove-Item -LiteralPath $target -Recurse -Force
    }
    return $target
}

$faroTarget = Reset-GeneratedDirectory 'faro'
New-Item -ItemType Directory -Path $faroTarget -Force | Out-Null
$modules = @(
    '__init__.py', 'audit.py', 'confirmation.py', 'controller.py', 'domain.py',
    'parser.py', 'plan.py', 'scenarios.py', 'simulator.py', 'voice_pipeline.py', 'web.py'
)
foreach ($module in $modules) {
    Copy-Item -LiteralPath (Join-Path $projectRoot "faro/$module") -Destination $faroTarget
}

foreach ($name in @('fixtures', 'web')) {
    $target = Reset-GeneratedDirectory $name
    Copy-Item -LiteralPath (Join-Path $projectRoot $name) -Destination $target -Recurse
}

Write-Host 'Fuentes y recursos de Faro preparados para Android.'
