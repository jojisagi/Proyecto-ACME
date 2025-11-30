# Script PowerShell para empaquetar funciones Lambda en archivos ZIP

Write-Host "=== Empaquetando Funciones Lambda ===" -ForegroundColor Cyan
Write-Host ""

# Crear directorio para los paquetes
$distDir = Join-Path $PSScriptRoot "..\dist"
if (-not (Test-Path $distDir)) {
    New-Item -ItemType Directory -Path $distDir | Out-Null
}

# Empaquetar Scheduler Manager
Write-Host "Empaquetando scheduler_manager..." -ForegroundColor Yellow
$schedulerDir = Join-Path $PSScriptRoot "..\src\scheduler_manager"
$schedulerZip = Join-Path $distDir "scheduler_manager.zip"

if (Test-Path $schedulerZip) {
    Remove-Item $schedulerZip -Force
}

Compress-Archive -Path (Join-Path $schedulerDir "app.py") -DestinationPath $schedulerZip
Write-Host "✓ scheduler_manager.zip creado" -ForegroundColor Green

# Empaquetar Order Executor
Write-Host "Empaquetando order_executor..." -ForegroundColor Yellow
$executorDir = Join-Path $PSScriptRoot "..\src\order_executor"
$executorZip = Join-Path $distDir "order_executor.zip"

if (Test-Path $executorZip) {
    Remove-Item $executorZip -Force
}

Compress-Archive -Path (Join-Path $executorDir "app.py") -DestinationPath $executorZip
Write-Host "✓ order_executor.zip creado" -ForegroundColor Green

Write-Host ""
Write-Host "=== Paquetes Lambda Creados ===" -ForegroundColor Cyan
Get-ChildItem $distDir -Filter "*.zip" | Format-Table Name, Length, LastWriteTime

Write-Host ""
Write-Host "✓ Empaquetado completado exitosamente" -ForegroundColor Green
Write-Host ""
Write-Host "Siguiente paso: Subir los ZIPs a S3 o desplegar directamente con CloudFormation"
