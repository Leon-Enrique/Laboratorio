# Actualización en servidor Windows.
# Uso: .\scripts\deploy-update.ps1
# Ajuste $WebRoot según IIS o carpeta estática.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "laboratorio-bioquimica-backend"
$Frontend = Join-Path $Root "laboratorio-bioquimica-web"
$WebRoot = if ($env:WEB_ROOT) { $env:WEB_ROOT } else { "C:\inetpub\wwwroot\genotipia" }

Write-Host "==> 1. Git pull"
Set-Location $Root
git pull --ff-only

Write-Host "==> 2. Backend: deps + Alembic"
Set-Location $Backend
if (-not (Test-Path ".\venv")) {
  python -m venv venv
}
& .\venv\Scripts\Activate.ps1
pip install -q -r requirements.txt
alembic upgrade head

Write-Host "==> 3. Frontend: build producción"
Set-Location $Frontend
npm ci
npm run build -- --configuration=production

Write-Host "==> 4. Copiar sitio estático"
$dist = Join-Path $Frontend "dist\laboratorio-bioquimica-web\browser"
New-Item -ItemType Directory -Force -Path $WebRoot | Out-Null
robocopy $dist $WebRoot /MIR /NFL /NDL /NJH /NJS | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy falló con código $LASTEXITCODE" }

Write-Host "==> 5. Reiniciar API (si existe servicio genotipia-api)"
$svc = Get-Service -Name "genotipia-api" -ErrorAction SilentlyContinue
if ($svc) {
  Restart-Service genotipia-api
  Write-Host "Servicio genotipia-api reiniciado."
} else {
  Write-Host "Inicie manualmente: uvicorn app.main:app --host 127.0.0.1 --port 8000"
}

Write-Host "==> Deploy completado."
