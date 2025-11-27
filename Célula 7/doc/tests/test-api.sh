#!/bin/bash

# Script para probar el API Gateway con curl

# Configuración
API_ENDPOINT="https://YOUR-API-ID.execute-api.YOUR-REGION.amazonaws.com/prod"
USER_POOL_ID="YOUR-USER-POOL-ID"
CLIENT_ID="YOUR-CLIENT-ID"

echo "========================================="
echo "Test Suite - Sistema de Votación"
echo "========================================="
echo ""

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir resultados
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
    else
        echo -e "${RED}✗ $2${NC}"
    fi
}

# Test 1: Obtener resultados sin autenticación (debe funcionar)
echo -e "${YELLOW}Test 1: GET /results (sin autenticación)${NC}"
response=$(curl -s -w "\n%{http_code}" "${API_ENDPOINT}/results")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
    print_result 0 "Resultados obtenidos exitosamente"
    echo "$body" | python -m json.tool 2>/dev/null || echo "$body"
else
    print_result 1 "Error al obtener resultados (HTTP $http_code)"
    echo "$body"
fi

echo ""
echo "========================================="
echo ""

# Test 2: Intentar votar sin autenticación (debe fallar)
echo -e "${YELLOW}Test 2: POST /vote (sin autenticación - debe fallar)${NC}"
response=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"gadgetId": "gadget-001"}' \
    "${API_ENDPOINT}/vote")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "401" ] || [ "$http_code" = "403" ]; then
    print_result 0 "Correctamente rechazado sin autenticación (HTTP $http_code)"
else
    print_result 1 "Debería rechazar sin autenticación (HTTP $http_code)"
fi
echo "$body"

echo ""
echo "========================================="
echo ""

# Test 3: Votar con token (requiere autenticación)
echo -e "${YELLOW}Test 3: POST /vote (con autenticación)${NC}"
echo "Para probar con autenticación, necesitas:"
echo "1. Crear un usuario en Cognito"
echo "2. Obtener un token de autenticación"
echo ""
echo "Ejemplo de comando para autenticar:"
echo "aws cognito-idp initiate-auth \\"
echo "  --auth-flow USER_PASSWORD_AUTH \\"
echo "  --client-id ${CLIENT_ID} \\"
echo "  --auth-parameters USERNAME=user@example.com,PASSWORD=YourPassword123!"
echo ""
echo "Luego usar el IdToken en el header Authorization:"
echo ""

# Si tienes un token, descomenta y usa esto:
# TOKEN="YOUR_ID_TOKEN_HERE"
# response=$(curl -s -w "\n%{http_code}" \
#     -X POST \
#     -H "Content-Type: application/json" \
#     -H "Authorization: Bearer ${TOKEN}" \
#     -d '{"gadgetId": "gadget-001"}' \
#     "${API_ENDPOINT}/vote")
# http_code=$(echo "$response" | tail -n1)
# body=$(echo "$response" | head -n-1)
# 
# if [ "$http_code" = "201" ]; then
#     print_result 0 "Voto registrado exitosamente"
#     echo "$body" | python -m json.tool
# else
#     print_result 1 "Error al registrar voto (HTTP $http_code)"
#     echo "$body"
# fi

echo "curl -X POST \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -H \"Authorization: Bearer \$ID_TOKEN\" \\"
echo "  -d '{\"gadgetId\": \"gadget-001\"}' \\"
echo "  \"${API_ENDPOINT}/vote\""

echo ""
echo "========================================="
echo ""

# Test 4: Verificar CORS
echo -e "${YELLOW}Test 4: OPTIONS /vote (CORS preflight)${NC}"
response=$(curl -s -w "\n%{http_code}" \
    -X OPTIONS \
    -H "Origin: http://localhost:3000" \
    -H "Access-Control-Request-Method: POST" \
    "${API_ENDPOINT}/vote")
http_code=$(echo "$response" | tail -n1)

if [ "$http_code" = "200" ]; then
    print_result 0 "CORS configurado correctamente"
else
    print_result 1 "Error en configuración CORS (HTTP $http_code)"
fi

echo ""
echo "========================================="
echo "Tests completados"
echo "========================================="
