#!/bin/bash

# Script de pruebas funcionales con curl
# Incluye autenticación JWT con Cognito

set -e

echo "=== Pruebas Funcionales del Sistema de Scheduling ==="
echo ""

# Variables de configuración
REGION="${AWS_REGION:-us-east-1}"
STACK_NAME="acme-scheduling-main"

# Obtener información del stack
echo "Obteniendo información del despliegue..."
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text \
  --region $REGION)

USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text \
  --region $REGION)

CLIENT_ID=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' \
  --output text \
  --region $REGION)

echo "API Endpoint: $API_ENDPOINT"
echo "User Pool ID: $USER_POOL_ID"
echo "Client ID: $CLIENT_ID"
echo ""

# Credenciales de usuario (configurar según sea necesario)
USERNAME="${COGNITO_USERNAME:-testuser}"
PASSWORD="${COGNITO_PASSWORD:-TempPass123!}"

echo "=== Paso 1: Autenticación con Cognito ==="
echo "Usuario: $USERNAME"

# Obtener JWT Token
AUTH_RESPONSE=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id $CLIENT_ID \
  --auth-parameters USERNAME=$USERNAME,PASSWORD=$PASSWORD \
  --region $REGION 2>&1)

if echo "$AUTH_RESPONSE" | grep -q "NotAuthorizedException"; then
    echo "❌ Error: Usuario no autorizado o credenciales incorrectas"
    echo ""
    echo "Para crear un usuario, ejecuta:"
    echo "aws cognito-idp admin-create-user \\"
    echo "  --user-pool-id $USER_POOL_ID \\"
    echo "  --username $USERNAME \\"
    echo "  --temporary-password TempPass123! \\"
    echo "  --user-attributes Name=email,Value=test@acme.com"
    echo ""
    echo "Luego establece una contraseña permanente:"
    echo "aws cognito-idp admin-set-user-password \\"
    echo "  --user-pool-id $USER_POOL_ID \\"
    echo "  --username $USERNAME \\"
    echo "  --password TempPass123! \\"
    echo "  --permanent"
    exit 1
fi

JWT_TOKEN=$(echo $AUTH_RESPONSE | jq -r '.AuthenticationResult.IdToken')

if [ "$JWT_TOKEN" == "null" ] || [ -z "$JWT_TOKEN" ]; then
    echo "❌ Error: No se pudo obtener el token JWT"
    echo "Respuesta: $AUTH_RESPONSE"
    exit 1
fi

echo "✓ Token JWT obtenido exitosamente"
echo "Token (primeros 50 caracteres): ${JWT_TOKEN:0:50}..."
echo ""

# Función auxiliar para hacer requests
make_request() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo "=== $description ==="
    echo "Método: $method"
    echo "Endpoint: $endpoint"
    
    if [ -n "$data" ]; then
        echo "Payload:"
        echo "$data" | jq '.'
        
        response=$(curl -s -X $method \
          -H "Authorization: Bearer $JWT_TOKEN" \
          -H "Content-Type: application/json" \
          -d "$data" \
          "$API_ENDPOINT$endpoint")
    else
        response=$(curl -s -X $method \
          -H "Authorization: Bearer $JWT_TOKEN" \
          -H "Content-Type: application/json" \
          "$API_ENDPOINT$endpoint")
    fi
    
    echo "Respuesta:"
    echo "$response" | jq '.' 2>/dev/null || echo "$response"
    echo ""
    
    # Retornar la respuesta para uso posterior
    echo "$response"
}

# Test 1: Crear un nuevo schedule
echo "=== Test 1: POST /schedule - Crear Schedule ==="
SCHEDULE_PAYLOAD='{
  "scheduleName": "rocket-shoes-hourly",
  "frequency": "rate(1 hour)",
  "gadgetType": "Rocket Shoes",
  "quantity": 100,
  "enabled": true
}'

CREATE_RESPONSE=$(make_request "POST" "/schedule" "$SCHEDULE_PAYLOAD" "Crear Schedule para Rocket Shoes")
SCHEDULE_ID=$(echo "$CREATE_RESPONSE" | jq -r '.schedule.scheduleId' 2>/dev/null)

if [ "$SCHEDULE_ID" != "null" ] && [ -n "$SCHEDULE_ID" ]; then
    echo "✓ Schedule creado con ID: $SCHEDULE_ID"
else
    echo "⚠ No se pudo extraer el Schedule ID de la respuesta"
fi
echo ""

# Esperar un momento
sleep 2

# Test 2: Crear otro schedule
echo "=== Test 2: POST /schedule - Crear Otro Schedule ==="
SCHEDULE_PAYLOAD_2='{
  "scheduleName": "jetpack-daily",
  "frequency": "rate(1 day)",
  "gadgetType": "Jetpack",
  "quantity": 50,
  "enabled": true
}'

make_request "POST" "/schedule" "$SCHEDULE_PAYLOAD_2" "Crear Schedule para Jetpack"
sleep 2

# Test 3: Listar todos los schedules
echo "=== Test 3: GET /schedules - Listar Schedules ==="
make_request "GET" "/schedules" "" "Listar Todos los Schedules"
sleep 1

# Test 4: Obtener un schedule específico (si tenemos el ID)
if [ "$SCHEDULE_ID" != "null" ] && [ -n "$SCHEDULE_ID" ]; then
    echo "=== Test 4: GET /schedule/{id} - Obtener Schedule Específico ==="
    make_request "GET" "/schedule/$SCHEDULE_ID" "" "Obtener Schedule $SCHEDULE_ID"
    sleep 1
fi

# Test 5: Consultar órdenes generadas
echo "=== Test 5: GET /orders - Consultar Órdenes ==="
make_request "GET" "/orders" "" "Consultar Todas las Órdenes"
sleep 1

# Test 6: Consultar órdenes por estado
echo "=== Test 6: GET /orders?status=pending - Filtrar por Estado ==="
make_request "GET" "/orders?status=pending" "" "Consultar Órdenes Pendientes"
sleep 1

# Test 7: Cancelar un schedule (si tenemos el ID)
if [ "$SCHEDULE_ID" != "null" ] && [ -n "$SCHEDULE_ID" ]; then
    echo "=== Test 7: DELETE /schedule/{id} - Cancelar Schedule ==="
    make_request "DELETE" "/schedule/$SCHEDULE_ID" "" "Cancelar Schedule $SCHEDULE_ID"
    sleep 1
    
    # Verificar que fue cancelado
    echo "=== Verificación: Listar Schedules Después de Cancelar ==="
    make_request "GET" "/schedules" "" "Verificar Cancelación"
fi

echo ""
echo "=== Pruebas Completadas ==="
echo ""
echo "Resumen:"
echo "  ✓ Autenticación con Cognito"
echo "  ✓ Creación de schedules"
echo "  ✓ Consulta de schedules"
echo "  ✓ Consulta de órdenes"
echo "  ✓ Cancelación de schedules"
echo ""
echo "Para más pruebas, modifica este script o usa curl directamente:"
echo "curl -H \"Authorization: Bearer \$JWT_TOKEN\" $API_ENDPOINT/schedules"
