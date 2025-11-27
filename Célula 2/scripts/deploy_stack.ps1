# Script PowerShell para desplegar los stacks de CloudFormation

$ErrorActionPreference = "Stop"

Write-Host "=== Desplegando Sistema de Scheduling de Órdenes de Compra ===" -ForegroundColor Cyan
Write-Host ""

# Variables
$IAM_STACK_NAME = "acme-scheduling-iam"
$MAIN_STACK_NAME = "acme-scheduling-main"
$REGION = if ($env:AWS_REGION) { $env:AWS_REGION } else { "us-east-1" }
$ENVIRONMENT = if ($env:ENVIRONMENT) { $env:ENVIRONMENT } else { "production" }

Write-Host "Configuración:" -ForegroundColor Yellow
Write-Host "  Región: $REGION"
Write-Host "  Ambiente: $ENVIRONMENT"
Write-Host ""

# Paso 1: Desplegar Stack de IAM
Write-Host "=== Paso 1: Desplegando Stack de IAM ===" -ForegroundColor Cyan
$iamTemplate = Join-Path $PSScriptRoot "..\iac\iam_stack.yml"

aws cloudformation deploy `
  --template-file $iamTemplate `
  --stack-name $IAM_STACK_NAME `
  --capabilities CAPABILITY_NAMED_IAM `
  --region $REGION `
  --no-fail-on-empty-changeset

Write-Host "✓ Stack de IAM desplegado" -ForegroundColor Green
Write-Host ""

# Esperar a que el stack esté completo
Write-Host "Esperando a que el stack de IAM esté completo..." -ForegroundColor Yellow
try {
    aws cloudformation wait stack-create-complete --stack-name $IAM_STACK_NAME --region $REGION 2>$null
} catch {
    aws cloudformation wait stack-update-complete --stack-name $IAM_STACK_NAME --region $REGION 2>$null
}

Write-Host "✓ Stack de IAM completado" -ForegroundColor Green
Write-Host ""

# Paso 2: Empaquetar Lambdas
Write-Host "=== Paso 2: Empaquetando Lambdas ===" -ForegroundColor Cyan
& (Join-Path $PSScriptRoot "package_lambdas.ps1")
Write-Host ""

# Paso 3: Crear bucket S3 para artefactos (si no existe)
$accountId = (aws sts get-caller-identity --query Account --output text)
$BUCKET_NAME = "acme-scheduling-artifacts-$accountId"

Write-Host "=== Paso 3: Verificando bucket S3 para artefactos ===" -ForegroundColor Cyan
Write-Host "Bucket: $BUCKET_NAME"

$bucketExists = $false
try {
    aws s3 ls "s3://$BUCKET_NAME" 2>$null
    $bucketExists = $true
} catch {
    $bucketExists = $false
}

if (-not $bucketExists) {
    Write-Host "Creando bucket S3..." -ForegroundColor Yellow
    aws s3 mb "s3://$BUCKET_NAME" --region $REGION
    Write-Host "✓ Bucket creado" -ForegroundColor Green
} else {
    Write-Host "✓ Bucket ya existe" -ForegroundColor Green
}
Write-Host ""

# Paso 4: Subir artefactos Lambda a S3
Write-Host "=== Paso 4: Subiendo artefactos Lambda a S3 ===" -ForegroundColor Cyan
$distDir = Join-Path $PSScriptRoot "..\dist"

aws s3 cp (Join-Path $distDir "scheduler_manager.zip") "s3://$BUCKET_NAME/lambdas/scheduler_manager.zip"
aws s3 cp (Join-Path $distDir "order_executor.zip") "s3://$BUCKET_NAME/lambdas/order_executor.zip"

Write-Host "✓ Artefactos subidos" -ForegroundColor Green
Write-Host ""

# Paso 5: Desplegar Stack Principal
Write-Host "=== Paso 5: Desplegando Stack Principal ===" -ForegroundColor Cyan
$mainTemplate = Join-Path $PSScriptRoot "..\iac\main_stack.yml"

aws cloudformation deploy `
  --template-file $mainTemplate `
  --stack-name $MAIN_STACK_NAME `
  --parameter-overrides Environment=$ENVIRONMENT `
  --region $REGION `
  --no-fail-on-empty-changeset

Write-Host "✓ Stack principal desplegado" -ForegroundColor Green
Write-Host ""

# Esperar a que el stack esté completo
Write-Host "Esperando a que el stack principal esté completo..." -ForegroundColor Yellow
try {
    aws cloudformation wait stack-create-complete --stack-name $MAIN_STACK_NAME --region $REGION 2>$null
} catch {
    aws cloudformation wait stack-update-complete --stack-name $MAIN_STACK_NAME --region $REGION 2>$null
}

Write-Host "✓ Stack principal completado" -ForegroundColor Green
Write-Host ""

# Paso 6: Actualizar código de Lambdas
Write-Host "=== Paso 6: Actualizando código de funciones Lambda ===" -ForegroundColor Cyan

Write-Host "Actualizando scheduler_manager..." -ForegroundColor Yellow
aws lambda update-function-code `
  --function-name acme-scheduler-manager `
  --s3-bucket $BUCKET_NAME `
  --s3-key lambdas/scheduler_manager.zip `
  --region $REGION | Out-Null

Write-Host "Actualizando order_executor..." -ForegroundColor Yellow
aws lambda update-function-code `
  --function-name acme-order-executor `
  --s3-bucket $BUCKET_NAME `
  --s3-key lambdas/order_executor.zip `
  --region $REGION | Out-Null

Write-Host "✓ Funciones Lambda actualizadas" -ForegroundColor Green
Write-Host ""

# Paso 7: Obtener outputs del stack
Write-Host "=== Paso 7: Información del Despliegue ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "API Endpoint:" -ForegroundColor Yellow
$apiEndpoint = aws cloudformation describe-stacks `
  --stack-name $MAIN_STACK_NAME `
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' `
  --output text `
  --region $REGION
Write-Host $apiEndpoint

Write-Host ""
Write-Host "User Pool ID:" -ForegroundColor Yellow
$userPoolId = aws cloudformation describe-stacks `
  --stack-name $MAIN_STACK_NAME `
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' `
  --output text `
  --region $REGION
Write-Host $userPoolId

Write-Host ""
Write-Host "User Pool Client ID:" -ForegroundColor Yellow
$clientId = aws cloudformation describe-stacks `
  --stack-name $MAIN_STACK_NAME `
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' `
  --output text `
  --region $REGION
Write-Host $clientId

Write-Host ""
Write-Host "=== Despliegue Completado Exitosamente ===" -ForegroundColor Green
Write-Host ""
Write-Host "Siguiente paso: Crear un usuario en Cognito y ejecutar las pruebas"
Write-Host "Comando: .\curl_tests.ps1"
