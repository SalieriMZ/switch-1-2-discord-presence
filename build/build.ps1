# Construye dist/NSO-Discord-RPC/ (NSO-Discord-RPC.exe + _internal/ + runtime/ con Node y nxapi).
# Es una carpeta, no un .exe único: arranca al instante porque no extrae nada en cada inicio.
#   powershell -ExecutionPolicy Bypass -File build\build.ps1 [-Zip] [-Clean]
#   -Zip    además crea dist/NSO-Discord-RPC-<versión>.zip para compartir
#   -Clean  recompila desde cero (borra la caché de PyInstaller)
param(
    [switch]$Zip,
    [switch]$Clean
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root '.venv\Scripts\python.exe'
$work = Join-Path $PSScriptRoot 'work'
$app = Join-Path $root 'dist\NSO-Discord-RPC'
$stage = Join-Path $work 'stage'

if (-not (Test-Path $py)) {
    py -m venv (Join-Path $root '.venv')
    & $py -m pip install -q pyside6 pyinstaller pytest
}

& (Join-Path $PSScriptRoot 'fetch-runtime.ps1')

$env:PYTHONPATH = Join-Path $root 'app'
$env:QT_QPA_PLATFORM = 'offscreen'
$icon = Join-Path $work 'icon.ico'
& $py (Join-Path $PSScriptRoot 'make_icon.py') $icon | Out-Null
Remove-Item Env:QT_QPA_PLATFORM

# PyInstaller arma la parte Python en una carpeta de paso; el runtime (Node + nxapi) no pasa por él.
$extra = @()
if ($Clean) { $extra += '--clean' }
& $py -m PyInstaller --noconfirm @extra --onedir --windowed `
    --name 'NSO-Discord-RPC' `
    --icon $icon `
    --paths (Join-Path $root 'app') `
    --exclude-module PySide6.QtWebEngineCore --exclude-module PySide6.QtQml --exclude-module PySide6.QtQuick `
    --exclude-module PySide6.Qt3DCore --exclude-module PySide6.QtMultimedia --exclude-module PySide6.QtPdf `
    --distpath $stage `
    --workpath (Join-Path $work 'pyinstaller') `
    --specpath $work `
    (Join-Path $PSScriptRoot 'launcher.py')
if ($LASTEXITCODE -ne 0) { throw "PyInstaller falló ($LASTEXITCODE)" }

# robocopy copia solo lo que cambió: recompilar tarda segundos, no copia de nuevo los >100 MB del runtime.
function Sync([string]$from, [string]$to, [string[]]$more) {
    robocopy $from $to /MIR /NFL /NDL /NJH /NJS /NP @more | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "robocopy falló ($LASTEXITCODE): $from -> $to" }
}
$old = Join-Path $root 'dist\NSO-Discord-RPC.exe'  # el .exe único de la versión anterior
if (Test-Path $old) { Remove-Item -Force $old }
Sync (Join-Path $stage 'NSO-Discord-RPC') $app @('/XD', (Join-Path $app 'runtime'))
Sync (Join-Path $PSScriptRoot 'runtime') (Join-Path $app 'runtime') @()
$global:LASTEXITCODE = 0

$exe = Join-Path $app 'NSO-Discord-RPC.exe'
$size = (Get-ChildItem $app -Recurse -File | Measure-Object Length -Sum).Sum / 1MB
Write-Host ("Listo: {0} (carpeta {1:N0} MB)" -f $exe, $size)

if ($Zip) {
    $ver = (& $py -c "import nso_rpc; print(nso_rpc.__version__)").Trim()
    $zipPath = Join-Path $root "dist\NSO-Discord-RPC-$ver.zip"
    if (Test-Path $zipPath) { Remove-Item -Force $zipPath }
    Compress-Archive -Path $app -DestinationPath $zipPath -CompressionLevel Fastest
    Write-Host ("Zip: {0} ({1:N0} MB)" -f $zipPath, ((Get-Item $zipPath).Length / 1MB))
}
