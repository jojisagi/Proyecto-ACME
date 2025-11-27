#!/bin/bash

###############################################################################
# Script para Crear Usuario de Prueba en Cognito
# Célula 3 - Acme Image Handler
###############################################################################

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Parámetros
ENVIRONMENT=${1:-sandbox}
STACK_NAME="acme-image-handler-${ENVIRONMENT}"
AWS_PROFILE=${AWS_PROFILE:-$ENVIRONMENT}

echo "========================================="
echo "Crear Usuario de Prueba en Cognito"
echo "Ambiente: $ENVIRONMENT"
echo "Stack: $STACK_NAME"
echo "========================================="
echo ""

# Obtener User Pool ID del stack
print_info "Obteniendo User Pool ID..."
USER_POOL_ID=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --profile $AWS_PROFILE \
    --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
    --output text 2>/dev/null)

if [ -z "$USER_POOL_ID" ]; then
    print_error "No se pudo obtener el User Pool ID"
    echo "Verifica que el stack esté desplegado: $STACK_NAME"
    exit 1
fi

print_success "User Pool ID: $USER_POOL_ID"

# Solicitar datos del usuario
echo ""
read -p "Email del usuario: " USER_EMAIL
read -s -p "Password (mínimo 8 caracteres, mayúsculas, minúsculas, números y símbolos): " USER_PASSWORD
echo ""

# Validar password
if [ ${#USER_PASSWORD} -lt 8 ]; then
    print_error "Password debe tener al menos 8 caracteres"
    exit 1
fi

# Crear usuario
print_info "Creando usuario en Cognito..."

aws cognito-idp admin-create-user \
    --user-pool-id $USER_POOL_ID \
    --username $USER_EMAIL \
    --user-attributes \
        Name=email,Value=$USER_EMAIL \
        Name=email_verified,Value=true \
    --temporary-password "TempPass123!" \
    --message-action SUPPRESS \
    --profile $AWS_PROFILE > /dev/null

print_success "Usuario creado"

# Establecer password permanente
print_info "Estableciendo password permanente..."

aws cognito-idp admin-set-user-password \
    --user-pool-id $USER_POOL_ID \
    --username $USER_EMAIL \
    --password "$USER_PASSWORD" \
    --permanent \
    --profile $AWS_PROFILE > /dev/null

print_success "Password establecido"

# Obtener información adicional para pruebas
CLIENT_ID=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --profile $AWS_PROFILE \
    --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' \
    --output text)

COGNITO_DOMAIN=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --profile $AWS_PROFILE \
    --query 'Stacks[0].Outputs[?OutputKey==`UserPoolDomain`].OutputValue' \
    --output text)

API_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --profile $AWS_PROFILE \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text)

echo ""
echo "========================================="
print_success "Usuario creado exitosamente"
echo "========================================="
echo ""
echo "Credenciales:"
echo "  Email: $USER_EMAIL"
echo "  Password: ********"
echo ""
echo "Información del ambiente:"
echo "  User Pool ID: $USER_POOL_ID"
echo "  Client ID: $CLIENT_ID"
echo "  Cognito Domain: $COGNITO_DOMAIN"
echo "  API URL: $API_URL"
echo ""
echo "Para probar el API:"
echo ""
echo "# Obtener token JWT"
echo "curl -X POST https://${COGNITO_DOMAIN}.auth.us-east-1.amazoncognito.com/oauth2/token \\"
echo "  -H 'Content-Type: application/x-www-form-urlencoded' \\"
echo "  -d 'grant_type=password' \\"
echo "  -d 'client_id=${CLIENT_ID}' \\"
echo "  -d 'username=${USER_EMAIL}' \\"
echo "  -d 'password=YOUR_PASSWORD'"
echo ""
echo "# Listar imágenes"
echo "curl -H 'Authorization: Bearer <JWT_TOKEN>' ${API_URL}/images"
echo ""
echo "O ejecuta el script de pruebas:"
echo ""
echo "export API_URL='${API_URL}'"
echo "export COGNITO_DOMAIN='${COGNITO_DOMAIN}'"
echo "export CLIENT_ID='${CLIENT_ID}'"
echo "export USERNAME='${USER_EMAIL}'"
echo "export PASSWORD='YOUR_PASSWORD'"
echo "./tests/test-api.sh"
echo ""
