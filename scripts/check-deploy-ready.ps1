# Verifica en TU PC que el proyecto está listo (no despliega a internet).
# Uso: .\scripts\check-deploy-ready.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "laboratorio-bioquimica-backend"
$Frontend = Join-Path $Root "laboratorio-bioquimica-web"

Write-Host ""
Write-Host "=== Genotipia: verificacion local pre-deploy ===" -ForegroundColor Cyan
Write-Host "Esto NO sube nada a internet. Solo comprueba tests y build." -ForegroundColor DarkGray
Write-Host ""

Write-Host "[1/2] Backend: pytest..." -ForegroundColor Yellow
Push-Location $Backend
$py = ".\venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    throw "No hay venv en backend. Ejecute: cd laboratorio-bioquimica-backend; python -m venv venv; pip install -r requirements.txt pytest"
}
$env:APP_ENV = "development"
$env:DATABASE_URL = "sqlite:///./check_deploy_ready.db"
$env:SECRET_KEY = "check_deploy_only"
$env:AUTO_MIGRATE = "true"
$env:RUN_DATA_BACKFILL = "false"
& $py -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "pytest fallo" }
Write-Host "  OK" -ForegroundColor Green
Pop-Location

Write-Host "[2/2] Frontend: build produccion..." -ForegroundColor Yellow
Push-Location $Frontend
npm run build -- --configuration=production
if ($LASTEXITCODE -ne 0) { throw "ng build fallo" }
Write-Host "  OK" -ForegroundColor Green
Pop-Location

Write-Host ""
Write-Host "Todo listo en local." -ForegroundColor Green
Write-Host "Cuando quiera publicar, lea: DEPLOY.md" -ForegroundColor Cyan
Write-Host ""
