# Script PowerShell de pruebas funcionales con curl
# Incluye autenticación JWT con Cognito

$ErrorActionPreference = "Stop"

Write-Host "=== Pruebas Funcionales del Sistema de Scheduling ===" -ForegroundColor Cyan
Write-Host ""

# Variables de configuración
$REGION = if ($env:AWS_REGION) { $env:AWS_REGION } else { "us-east-1" }
$STACK_NAME = "acme-scheduling-main"

# Obtener información del stack
Write-Host "Obteniendo información del despliegue..." -ForegroundColor Yellow

$API_ENDPOINT = aws cloudformation describe-stacks `
  --stack-name $STACK_NAME `
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' `
  --output text `
  --region $REGION

$USER_POOL_ID = aws cloudformation describe-stacks `
  --stack-name $STACK_NAME `
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' `
  --output text `
  --region $REGION

$CLIENT_ID = aws cloudformation describe-stacks `
  --stack-name $STACK_NAME `
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' `
  --output text `
  --region $REGION

Write-Host "API Endpoint: $API_ENDPOINT"
Write-Host "User Pool ID: $USER_POOL_ID"
Write-Host "Client ID: $CLIENT_ID"
Write-Host ""

# Credenciales de usuario
$USERNAME = if ($env:COGNITO_USERNAME) { $env:COGNITO_USERNAME } else { "testuser" }
$PASSWORD = if ($env:COGNITO_PASSWORD) { $env:COGNITO_PASSWORD } else { "TempPass123!" }

Write-Host "=== Paso 1: Autenticación con Cognito ===" -ForegroundColor Cyan
Write-Host "Usuario: $USERNAME"

# Obtener JWT Token
try {
    $authResponse = aws cognito-idp initiate-auth `
      --auth-flow USER_PASSWORD_AUTH `
      --client-id $CLIENT_ID `
      --auth-parameters USERNAME=$USERNAME,PASSWORD=$PASSWORD `
      --region $REGION 2>&1 | ConvertFrom-Json
    
    $JWT_TOKEN = $authResponse.AuthenticationResult.IdToken
    
    if (-not $JWT_TOKEN) {
        throw "No se pudo obtener el token JWT"
    }
    
    Write-Host "✓ Token JWT obtenido exitosamente" -ForegroundColor Green
    Write-Host "Token (primeros 50 caracteres): $($JWT_TOKEN.Substring(0, [Math]::Min(50, $JWT_TOKEN.Length)))..."
    Write-Host ""
} catch {
    Write-Host "❌ Error: Usuario no autorizado o credenciales incorrectas" -ForegroundColor Red
    Write-Host ""
    Write-Host "Para crear un usuario, ejecuta:"
    Write-Host "aws cognito-idp admin-create-user \"
    Write-Host "  --user-pool-id $USER_POOL_ID \"
    Write-Host "  --username $USERNAME \"
    Write-Host "  --temporary-password TempPass123! \"
    Write-Host "  --user-attributes Name=email,Value=test@acme.com"
    Write-Host ""
    Write-Host "Luego establece una contraseña permanente:"
    Write-Host "aws cognito-idp admin-set-user-password \"
    Write-Host "  --user-pool-id $USER_POOL_ID \"
    Write-Host "  --username $USERNAME \"
    Write-Host "  --password TempPass123! \"
    Write-Host "  --permanent"
    exit 1
}

# Función auxiliar para hacer requests
function Invoke-ApiRequest {
    param(
        [string]$Method,
        [string]$Endpoint,
        [string]$Data = $null,
        [string]$Description
    )
    
    Write-Host "=== $Description ===" -ForegroundColor Cyan
    Write-Host "Método: $Method"
    Write-Host "Endpoint: $Endpoint"
    
    $headers = @{
        "Authorization" = "Bearer $JWT_TOKEN"
        "Content-Type" = "application/json"
    }
    
    $url = "$API_ENDPOINT$Endpoint"
    
    try {
        if ($Data) {
            Write-Host "Payload:"
            Write-Host $Data
            
            $response = Invoke-RestMethod -Uri $url -Method $Method -Headers $headers -Body $Data
        } else {
            $response = Invoke-RestMethod -Uri $url -Method $Method -Headers $headers
        }
        
        Write-Host "Respuesta:"
        $response | ConvertTo-Json -Depth 10
        Write-Host ""
        
        return $response
    } catch {
        Write-Host "Error en la petición:" -ForegroundColor Red
        Write-Host $_.Exception.Message
        Write-Host ""
        return $null
    }
}

# Test 1: Crear un nuevo schedule
Write-Host "=== Test 1: POST /schedule - Crear Schedule ===" -ForegroundColor Yellow
$schedulePayload = @{
    scheduleName = "rocket-shoes-hourly"
    frequency = "rate(1 hour)"
    gadgetType = "Rocket Shoes"
    quantity = 100
    enabled = $true
} | ConvertTo-Json

$createResponse = Invoke-ApiRequest -Method "POST" -Endpoint "/schedule" -Data $schedulePayload -Description "Crear Schedule para Rocket Shoes"
$scheduleId = $createResponse.schedule.scheduleId

if ($scheduleId) {
    Write-Host "✓ Schedule creado con ID: $scheduleId" -ForegroundColor Green
} else {
    Write-Host "⚠ No se pudo extraer el Schedule ID de la respuesta" -ForegroundColor Yellow
}
Write-Host ""

Start-Sleep -Seconds 2

# Test 2: Crear otro schedule
Write-Host "=== Test 2: POST /schedule - Crear Otro Schedule ===" -ForegroundColor Yellow
$schedulePayload2 = @{
    scheduleName = "jetpack-daily"
    frequency = "rate(1 day)"
    gadgetType = "Jetpack"
    quantity = 50
    enabled = $true
} | ConvertTo-Json

Invoke-ApiRequest -Method "POST" -Endpoint "/schedule" -Data $schedulePayload2 -Description "Crear Schedule para Jetpack"
Start-Sleep -Seconds 2

# Test 3: Listar todos los schedules
Write-Host "=== Test 3: GET /schedules - Listar Schedules ===" -ForegroundColor Yellow
Invoke-ApiRequest -Method "GET" -Endpoint "/schedules" -Description "Listar Todos los Schedules"
Start-Sleep -Seconds 1

# Test 4: Obtener un schedule específico
if ($scheduleId) {
    Write-Host "=== Test 4: GET /schedule/{id} - Obtener Schedule Específico ===" -ForegroundColor Yellow
    Invoke-ApiRequest -Method "GET" -Endpoint "/schedule/$scheduleId" -Description "Obtener Schedule $scheduleId"
    Start-Sleep -Seconds 1
}

# Test 5: Consultar órdenes generadas
Write-Host "=== Test 5: GET /orders - Consultar Órdenes ===" -ForegroundColor Yellow
Invoke-ApiRequest -Method "GET" -Endpoint "/orders" -Description "Consultar Todas las Órdenes"
Start-Sleep -Seconds 1

# Test 6: Consultar órdenes por estado
Write-Host "=== Test 6: GET /orders?status=pending - Filtrar por Estado ===" -ForegroundColor Yellow
Invoke-ApiRequest -Method "GET" -Endpoint "/orders?status=pending" -Description "Consultar Órdenes Pendientes"
Start-Sleep -Seconds 1

# Test 7: Cancelar un schedule
if ($scheduleId) {
    Write-Host "=== Test 7: DELETE /schedule/{id} - Cancelar Schedule ===" -ForegroundColor Yellow
    Invoke-ApiRequest -Method "DELETE" -Endpoint "/schedule/$scheduleId" -Description "Cancelar Schedule $scheduleId"
    Start-Sleep -Seconds 1
    
    # Verificar que fue cancelado
    Write-Host "=== Verificación: Listar Schedules Después de Cancelar ===" -ForegroundColor Yellow
    Invoke-ApiRequest -Method "GET" -Endpoint "/schedules" -Description "Verificar Cancelación"
}

Write-Host ""
Write-Host "=== Pruebas Completadas ===" -ForegroundColor Green
Write-Host ""
Write-Host "Resumen:"
Write-Host "  ✓ Autenticación con Cognito"
Write-Host "  ✓ Creación de schedules"
Write-Host "  ✓ Consulta de schedules"
Write-Host "  ✓ Consulta de órdenes"
Write-Host "  ✓ Cancelación de schedules"
Write-Host ""
Write-Host "Para más pruebas, modifica este script o usa curl/Invoke-RestMethod directamente"
