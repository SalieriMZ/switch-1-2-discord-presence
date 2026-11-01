# Arma build/runtime: Node portable (win-x64) + nxapi@next + bridge.mjs.
# Es lo que viaja dentro del .exe. Re-ejecutar con -Force para rehacerlo.
param(
    [string]$NodeLine = 'latest-v24.x',
    [switch]$Force
)
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$out = Join-Path $PSScriptRoot 'runtime'
$dl = Join-Path $PSScriptRoot 'work\download'

# Los archivos propios se actualizan siempre, también sobre un runtime ya armado.
function Copy-Own {
    Copy-Item (Join-Path $root 'runtime\package.json'), (Join-Path $root 'runtime\bridge.mjs'), (Join-Path $root 'runtime\discord-fix.mjs') $out
}

if ((Test-Path $out) -and -not $Force) {
    Copy-Own
    Write-Host "build/runtime ya existe (usa -Force para rehacerlo)."
    exit 0
}
if (Test-Path $out) { Remove-Item -Recurse -Force $out }
New-Item -ItemType Directory -Force $out, $dl | Out-Null

# Versión exacta y checksum desde el índice oficial.
$base = "https://nodejs.org/dist/$NodeLine"
$sums = (Invoke-WebRequest "$base/SHASUMS256.txt" -UseBasicParsing).Content -split "`n"
$line = $sums | Where-Object { $_ -match 'node-v[\d.]+-win-x64\.zip$' } | Select-Object -First 1
$hash, $zipName = $line -split '\s+'
$zip = Join-Path $dl $zipName

if (-not (Test-Path $zip) -or (Get-FileHash $zip -Algorithm SHA256).Hash -ne $hash.ToUpper()) {
    Write-Host "Descargando $zipName..."
    Invoke-WebRequest "$base/$zipName" -OutFile $zip -UseBasicParsing
    if ((Get-FileHash $zip -Algorithm SHA256).Hash -ne $hash.ToUpper()) { throw "Checksum inválido para $zipName" }
}

$extract = Join-Path $dl 'node-extract'
if (Test-Path $extract) { Remove-Item -Recurse -Force $extract }
Expand-Archive $zip $extract
$nodeDir = Get-ChildItem $extract -Directory | Select-Object -First 1
Move-Item $nodeDir.FullName (Join-Path $out 'node')

Copy-Own

$node = Join-Path $out 'node\node.exe'
$npm = Join-Path $out 'node\node_modules\npm\bin\npm-cli.js'
Push-Location $out
try {
    & $node $npm install --omit=dev --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { throw "npm install falló ($LASTEXITCODE)" }
} finally { Pop-Location }

Copy-Item (Join-Path $out 'node_modules\nxapi\LICENSE') (Join-Path $out 'NXAPI-LICENSE.txt')
# sharp trae binario precompilado (@img/sharp-win32-x64); su script "install" solo verifica, no hace falta.
$ver = (Get-Content (Join-Path $out 'node_modules\nxapi\package.json') -Raw | ConvertFrom-Json).version
Write-Host "Runtime listo en $out (nxapi $ver)"
