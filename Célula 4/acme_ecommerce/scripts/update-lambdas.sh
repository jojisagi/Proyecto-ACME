#!/bin/bash

# Script para actualizar solo las funciones Lambda

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Actualizar Funciones Lambda${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Variables
REGION=${AWS_REGION:-us-east-1}
LAMBDA_BUCKET="ecommerce-lambda-code-$(aws sts get-caller-identity --query Account --output text)"

# Verificar que el bucket existe
if ! aws s3 ls "s3://$LAMBDA_BUCKET" 2>&1 > /dev/null; then
    echo -e "${YELLOW}⚠ El bucket $LAMBDA_BUCKET no existe. Ejecuta ./scripts/deploy.sh primero.${NC}"
    exit 1
fi

echo -e "${GREEN}[1/3] Empaquetando funciones Lambda...${NC}"

# App Server Lambda
echo "Empaquetando app-server..."
cd lambdas/app-server
zip -r ../../app-server.zip index.py > /dev/null 2>&1
cd ../..
echo "✓ app-server.zip creado"

# Process Order Lambda
echo "Empaquetando process-order..."
cd lambdas/process-order
zip -r ../../process-order.zip index.py > /dev/null 2>&1
cd ../..
echo "✓ process-order.zip creado"

echo ""
echo -e "${GREEN}[2/3] Subiendo a S3...${NC}"

# Subir a S3
aws s3 cp app-server.zip s3://$LAMBDA_BUCKET/app-server.zip --region $REGION
echo "✓ app-server.zip subido"

aws s3 cp process-order.zip s3://$LAMBDA_BUCKET/process-order.zip --region $REGION
echo "✓ process-order.zip subido"

echo ""
echo -e "${GREEN}[3/3] Actualizando funciones Lambda...${NC}"

# Actualizar Lambda app-server
aws lambda update-function-code \
  --function-name app-server \
  --s3-bucket $LAMBDA_BUCKET \
  --s3-key app-server.zip \
  --region $REGION > /dev/null
echo "✓ app-server actualizado"

# Actualizar Lambda process-order
aws lambda update-function-code \
  --function-name process-order \
  --s3-bucket $LAMBDA_BUCKET \
  --s3-key process-order.zip \
  --region $REGION > /dev/null
echo "✓ process-order actualizado"

# Limpiar archivos ZIP locales
rm -f app-server.zip process-order.zip
echo ""
echo -e "${GREEN}✓ Archivos temporales limpiados${NC}"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}¡Funciones Lambda actualizadas!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Las funciones Lambda han sido actualizadas con el código más reciente."
echo -e "Los cambios están disponibles inmediatamente."
