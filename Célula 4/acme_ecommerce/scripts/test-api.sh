#!/bin/bash

# Script para probar el API Gateway con curl
# Uso: ./scripts/test-api.sh <API_GATEWAY_URL>

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar que se proporcionó la URL
if [ -z "$1" ]; then
    echo -e "${RED}Error: Debe proporcionar la URL del API Gateway${NC}"
    echo "Uso: $0 <API_GATEWAY_URL>"
    echo "Ejemplo: $0 https://abc123.execute-api.us-east-1.amazonaws.com/prod"
    exit 1
fi

API_URL="$1"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Probando API E-commerce${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Test 1: Health Check
echo -e "${GREEN}[Test 1] Health Check${NC}"
curl -X GET "${API_URL}/health" \
  -H "Content-Type: application/json" \
  -w "\nStatus: %{http_code}\n\n"

sleep 1

# Test 2: Crear nueva orden
echo -e "${GREEN}[Test 2] Crear nueva orden${NC}"
ORDER_RESPONSE=$(curl -s -X POST "${API_URL}/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "customerId": "cust-test-001",
    "customerName": "Test User",
    "customerEmail": "test@example.com",
    "items": [
      {
        "productId": "prod-101",
        "name": "Laptop HP 15",
        "quantity": 1,
        "price": 299.99
      }
    ],
    "totalAmount": 299.99,
    "paymentMethod": "credit_card",
    "shippingAddress": {
      "street": "Calle Test 123",
      "city": "Madrid",
      "state": "Madrid",
      "zipCode": "28001",
      "country": "España"
    }
  }' \
  -w "\nStatus: %{http_code}\n")

echo "$ORDER_RESPONSE"
echo ""

# Extraer orderId de la respuesta
ORDER_ID=$(echo "$ORDER_RESPONSE" | grep -o '"orderId":"[^"]*"' | cut -d'"' -f4)
echo -e "Order ID creado: ${BLUE}${ORDER_ID}${NC}"
echo ""

sleep 2

# Test 3: Obtener todas las órdenes
echo -e "${GREEN}[Test 3] Obtener todas las órdenes${NC}"
curl -X GET "${API_URL}/orders" \
  -H "Content-Type: application/json" \
  -w "\nStatus: %{http_code}\n\n"

sleep 1

# Test 4: Obtener orden específica
if [ ! -z "$ORDER_ID" ]; then
    echo -e "${GREEN}[Test 4] Obtener orden específica: ${ORDER_ID}${NC}"
    curl -X GET "${API_URL}/orders/${ORDER_ID}" \
      -H "Content-Type: application/json" \
      -w "\nStatus: %{http_code}\n\n"
else
    echo -e "${RED}[Test 4] Saltado - No se pudo obtener ORDER_ID${NC}"
    echo ""
fi

sleep 1

# Test 5: Crear orden con múltiples items
echo -e "${GREEN}[Test 5] Crear orden con múltiples items${NC}"
curl -X POST "${API_URL}/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "customerId": "cust-test-002",
    "customerName": "María Test",
    "customerEmail": "maria.test@example.com",
    "items": [
      {
        "productId": "prod-201",
        "name": "Mouse Inalámbrico",
        "quantity": 2,
        "price": 24.99
      },
      {
        "productId": "prod-202",
        "name": "Teclado Mecánico",
        "quantity": 1,
        "price": 79.99
      }
    ],
    "totalAmount": 129.97,
    "paymentMethod": "paypal",
    "shippingAddress": {
      "street": "Av. Test 456",
      "city": "Barcelona",
      "state": "Cataluña",
      "zipCode": "08001",
      "country": "España"
    }
  }' \
  -w "\nStatus: %{http_code}\n\n"

sleep 1

# Test 6: Buscar órdenes por cliente
echo -e "${GREEN}[Test 6] Buscar órdenes por cliente${NC}"
curl -X GET "${API_URL}/orders?customerId=cust-test-001" \
  -H "Content-Type: application/json" \
  -w "\nStatus: %{http_code}\n\n"

sleep 1

# Test 7: Intentar crear orden sin datos requeridos (debe fallar)
echo -e "${GREEN}[Test 7] Crear orden sin datos requeridos (debe fallar)${NC}"
curl -X POST "${API_URL}/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "customerName": "Test Incompleto"
  }' \
  -w "\nStatus: %{http_code}\n\n"

sleep 1

# Test 8: Buscar orden inexistente (debe retornar 404)
echo -e "${GREEN}[Test 8] Buscar orden inexistente (debe retornar 404)${NC}"
curl -X GET "${API_URL}/orders/order-nonexistent" \
  -H "Content-Type: application/json" \
  -w "\nStatus: %{http_code}\n\n"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Pruebas completadas${NC}"
echo -e "${BLUE}========================================${NC}"
