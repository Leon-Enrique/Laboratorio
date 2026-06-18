param(
    [string]$OutputDir = ".\backups",
    [int]$Keep = 14
)

$ErrorActionPreference = "Stop"

# Cargar DATABASE_URL desde .env si existe
$envFile = Join-Path $PSScriptRoot ".." ".env"
$dbUrl = $env:DATABASE_URL
if (-not $dbUrl -and (Test-Path $envFile)) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*DATABASE_URL\s*=\s*(.+)\s*$') {
            $dbUrl = $matches[1].Trim()
        }
    }
}

if (-not $dbUrl) {
    Write-Error "Defina DATABASE_URL en el entorno o en .env"
}

if ($dbUrl -notmatch '^postgresql://([^:]+):([^@]+)@([^:/]+):(\d+)/(.+)$') {
    Write-Error "DATABASE_URL debe ser postgresql://usuario:clave@host:puerto/base"
}

$user = $matches[1]
$pass = $matches[2]
$host = $matches[3]
$port = $matches[4]
$db = $matches[5]

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outPath = Join-Path (Resolve-Path $OutputDir) "laboratorio_db_$timestamp.sql"

New-Item -ItemType Directory -Force -Path (Split-Path $outPath) | Out-Null

$env:PGPASSWORD = $pass
Write-Host "Respaldando $db en $host:$port -> $outPath"

& pg_dump -h $host -p $port -U $user -F p -f $outPath $db
if ($LASTEXITCODE -ne 0) {
    Write-Error "pg_dump falló. Instale PostgreSQL client tools y verifique credenciales."
}

Write-Host "Backup OK: $outPath"

# Rotación simple
Get-ChildItem (Join-Path (Split-Path $outPath) "laboratorio_db_*.sql") |
    Sort-Object LastWriteTime -Descending |
    Select-Object -Skip $Keep |
    ForEach-Object {
        Write-Host "Eliminando backup antiguo: $($_.Name)"
        Remove-Item $_.FullName -Force
    }
