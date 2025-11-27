#!/bin/bash

###############################################################################
# Script de Pruebas Funcionales - Acme Image Handler API
# Célula 3
###############################################################################

set -e

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Variables (configurar según el ambiente)
API_URL="${API_URL:-https://your-api-id.execute-api.us-east-1.amazonaws.com/sandbox}"
COGNITO_DOMAIN="${COGNITO_DOMAIN:-your-cognito-domain}"
CLIENT_ID="${CLIENT_ID:-your-client-id}"
USERNAME="${USERNAME:-test@example.com}"
PASSWORD="${PASSWORD:-TestPassword123!}"

print_test() {
    echo -e "${YELLOW}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_section() {
    echo ""
    echo "========================================="
    echo "$1"
    echo "========================================="
}

# Verificar que las variables estén configuradas
if [[ "$API_URL" == *"your-api"* ]] || [[ "$COGNITO_DOMAIN" == *"your-cognito"* ]]; then
    print_error "Por favor configura las variables de ambiente:"
    echo "  export API_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com/sandbox"
    echo "  export COGNITO_DOMAIN=your-cognito-domain"
    echo "  export CLIENT_ID=your-client-id"
    echo "  export USERNAME=test@example.com"
    echo "  export PASSWORD=YourPassword123!"
    exit 1
fi

print_section "Acme Image Handler - Pruebas Funcionales"
echo "API URL: $API_URL"
echo "Cognito Domain: $COGNITO_DOMAIN"
echo "Username: $USERNAME"

# ==================== TEST 1: Obtener Token JWT ====================
print_section "TEST 1: Autenticación con Cognito"
print_test "Obteniendo token JWT..."

AUTH_RESPONSE=$(curl -s -X POST "https://${COGNITO_DOMAIN}.auth.us-east-1.amazoncognito.com/oauth2/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&client_id=${CLIENT_ID}&username=${USERNAME}&password=${PASSWORD}")

if echo "$AUTH_RESPONSE" | grep -q "access_token"; then
    JWT_TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.access_token')
    print_success "Token JWT obtenido exitosamente"
    echo "Token: ${JWT_TOKEN:0:50}..."
else
    print_error "Error obteniendo token JWT"
    echo "Response: $AUTH_RESPONSE"
    exit 1
fi

# ==================== TEST 2: Listar Imágenes ====================
print_section "TEST 2: Listar Imágenes (GET /images)"
print_test "Listando todas las imágenes..."

LIST_RESPONSE=$(curl -s -X GET "${API_URL}/images" \
  -H "Authorization: Bearer ${JWT_TOKEN}")

if echo "$LIST_RESPONSE" | grep -q "images"; then
    IMAGE_COUNT=$(echo "$LIST_RESPONSE" | jq -r '.count')
    print_success "Imágenes listadas exitosamente"
    echo "Total de imágenes: $IMAGE_COUNT"
    echo "$LIST_RESPONSE" | jq '.'
else
    print_error "Error listando imágenes"
    echo "Response: $LIST_RESPONSE"
fi

# ==================== TEST 3: Obtener URL de Carga ====================
print_section "TEST 3: Obtener URL de Carga (POST /upload-url)"
print_test "Solicitando URL firmada para subir imagen..."

GADGET_ID="TEST-GADGET-$(date +%s)"
UPLOAD_RESPONSE=$(curl -s -X POST "${API_URL}/upload-url" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"gadgetId\": \"${GADGET_ID}\", \"filename\": \"test-image.jpg\"}")

if echo "$UPLOAD_RESPONSE" | grep -q "uploadUrl"; then
    UPLOAD_URL=$(echo "$UPLOAD_RESPONSE" | jq -r '.uploadUrl')
    S3_KEY=$(echo "$UPLOAD_RESPONSE" | jq -r '.key')
    print_success "URL de carga obtenida exitosamente"
    echo "Gadget ID: $GADGET_ID"
    echo "S3 Key: $S3_KEY"
    echo "Upload URL: ${UPLOAD_URL:0:100}..."
else
    print_error "Error obteniendo URL de carga"
    echo "Response: $UPLOAD_RESPONSE"
fi

# ==================== TEST 4: Subir Imagen (Opcional) ====================
print_section "TEST 4: Subir Imagen de Prueba"
print_test "Creando imagen de prueba..."

# Crear una imagen de prueba simple
TEST_IMAGE="test-upload.jpg"
if command -v convert &> /dev/null; then
    convert -size 800x600 xc:blue -pointsize 48 -fill white \
        -gravity center -annotate +0+0 "Test Image\n${GADGET_ID}" \
        "$TEST_IMAGE"
    print_success "Imagen de prueba creada: $TEST_IMAGE"
    
    print_test "Subiendo imagen a S3..."
    UPLOAD_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "$UPLOAD_URL" \
        -H "Content-Type: image/jpeg" \
        --data-binary "@${TEST_IMAGE}")
    
    if [ "$UPLOAD_STATUS" == "200" ]; then
        print_success "Imagen subida exitosamente (HTTP $UPLOAD_STATUS)"
        echo "Esperando procesamiento (10 segundos)..."
        sleep 10
    else
        print_error "Error subiendo imagen (HTTP $UPLOAD_STATUS)"
    fi
    
    rm -f "$TEST_IMAGE"
else
    print_error "ImageMagick no está instalado, saltando prueba de subida"
    echo "Instala con: brew install imagemagick"
fi

# ==================== TEST 5: Listar Imágenes por Gadget ====================
print_section "TEST 5: Listar Imágenes por Gadget ID"
print_test "Listando imágenes del gadget: $GADGET_ID..."

GADGET_RESPONSE=$(curl -s -X GET "${API_URL}/images?gadgetId=${GADGET_ID}" \
  -H "Authorization: Bearer ${JWT_TOKEN}")

if echo "$GADGET_RESPONSE" | grep -q "images"; then
    GADGET_IMAGE_COUNT=$(echo "$GADGET_RESPONSE" | jq -r '.count')
    print_success "Imágenes del gadget listadas: $GADGET_IMAGE_COUNT"
    echo "$GADGET_RESPONSE" | jq '.'
else
    print_error "Error listando imágenes del gadget"
    echo "Response: $GADGET_RESPONSE"
fi

# ==================== TEST 6: Obtener Imagen Específica ====================
print_section "TEST 6: Obtener Imagen Específica (GET /images/{imageId})"

if [ "$GADGET_IMAGE_COUNT" -gt 0 ]; then
    IMAGE_ID=$(echo "$GADGET_RESPONSE" | jq -r '.images[0].imageId')
    print_test "Obteniendo imagen: $IMAGE_ID..."
    
    IMAGE_RESPONSE=$(curl -s -X GET "${API_URL}/images/${IMAGE_ID}" \
      -H "Authorization: Bearer ${JWT_TOKEN}")
    
    if echo "$IMAGE_RESPONSE" | grep -q "signedUrls"; then
        print_success "Imagen obtenida exitosamente"
        echo "Versiones disponibles:"
        echo "$IMAGE_RESPONSE" | jq -r '.signedUrls | keys[]'
        echo ""
        echo "Metadatos completos:"
        echo "$IMAGE_RESPONSE" | jq '.'
    else
        print_error "Error obteniendo imagen"
        echo "Response: $IMAGE_RESPONSE"
    fi
else
    print_error "No hay imágenes para probar"
fi

# ==================== RESUMEN ====================
print_section "Resumen de Pruebas"
print_success "Pruebas completadas"
echo ""
echo "Comandos útiles para pruebas manuales:"
echo ""
echo "# Obtener token:"
echo "curl -X POST https://${COGNITO_DOMAIN}.auth.us-east-1.amazoncognito.com/oauth2/token \\"
echo "  -H 'Content-Type: application/x-www-form-urlencoded' \\"
echo "  -d 'grant_type=password&client_id=${CLIENT_ID}&username=${USERNAME}&password=${PASSWORD}'"
echo ""
echo "# Listar imágenes:"
echo "curl -H 'Authorization: Bearer <JWT>' ${API_URL}/images"
echo ""
echo "# Obtener URL de carga:"
echo "curl -H 'Authorization: Bearer <JWT>' -H 'Content-Type: application/json' \\"
echo "  -d '{\"gadgetId\": \"TEST-001\"}' ${API_URL}/upload-url"
echo ""
