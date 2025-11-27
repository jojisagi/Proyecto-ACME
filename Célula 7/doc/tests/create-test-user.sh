#!/bin/bash

# Script para crear usuario de prueba en Cognito

USER_POOL_ID=${1:-"YOUR_USER_POOL_ID"}
EMAIL=${2:-"test@example.com"}
PASSWORD=${3:-"TestPassword123!"}

echo "Creando usuario de prueba en Cognito..."
echo "User Pool ID: ${USER_POOL_ID}"
echo "Email: ${EMAIL}"
echo ""

# Registrar usuario
echo "Paso 1: Registrando usuario..."
CLIENT_ID=$(aws cognito-idp describe-user-pool-clients \
  --user-pool-id ${USER_POOL_ID} \
  --max-results 1 \
  --query 'UserPoolClients[0].ClientId' \
  --output text)

aws cognito-idp sign-up \
  --client-id ${CLIENT_ID} \
  --username ${EMAIL} \
  --password ${PASSWORD} \
  --user-attributes Name=email,Value=${EMAIL}

echo "✓ Usuario registrado"
echo ""

# Confirmar usuario (solo para desarrollo/testing)
echo "Paso 2: Confirmando usuario (bypass verificación email)..."
aws cognito-idp admin-confirm-sign-up \
  --user-pool-id ${USER_POOL_ID} \
  --username ${EMAIL}

echo "✓ Usuario confirmado"
echo ""

# Obtener token
echo "Paso 3: Obteniendo token de autenticación..."
RESPONSE=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id ${CLIENT_ID} \
  --auth-parameters USERNAME=${EMAIL},PASSWORD=${PASSWORD} \
  --query 'AuthenticationResult.[IdToken,AccessToken]' \
  --output text)

ID_TOKEN=$(echo ${RESPONSE} | awk '{print $1}')
ACCESS_TOKEN=$(echo ${RESPONSE} | awk '{print $2}')

echo "✓ Token obtenido"
echo ""
echo "========================================="
echo "Usuario de prueba creado exitosamente"
echo "========================================="
echo ""
echo "Email: ${EMAIL}"
echo "Password: ${PASSWORD}"
echo ""
echo "ID Token (usar en Authorization header):"
echo "${ID_TOKEN}"
echo ""
echo "Para probar el API:"
echo "export ID_TOKEN=\"${ID_TOKEN}\""
echo ""
echo "curl -X POST \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -H \"Authorization: Bearer \${ID_TOKEN}\" \\"
echo "  -d '{\"gadgetId\": \"gadget-001\"}' \\"
echo "  \"YOUR_API_ENDPOINT/vote\""
