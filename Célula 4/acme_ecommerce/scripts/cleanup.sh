#!/bin/bash

# Script para limpiar todos los recursos AWS

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Limpieza de Recursos E-commerce${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

REGION=${AWS_REGION:-us-east-1}
IAM_STACK_NAME="ecommerce-iam"
RESOURCES_STACK_NAME="ecommerce-resources"

# Confirmar
read -p "¿Estás seguro de que quieres eliminar todos los recursos? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Operación cancelada"
    exit 0
fi

# Vaciar buckets S3
echo -e "${BLUE}[1/4] Vaciando buckets S3...${NC}"

# Frontend bucket
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name $RESOURCES_STACK_NAME \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
  --output text \
  --region $REGION 2>/dev/null || echo "")

if [ ! -z "$BUCKET_NAME" ]; then
    aws s3 rm s3://$BUCKET_NAME --recursive --region $REGION
    echo -e "${GREEN}✓ Frontend bucket vaciado${NC}"
else
    echo -e "${YELLOW}⚠ Frontend bucket no encontrado${NC}"
fi

# Lambda code bucket
LAMBDA_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name $RESOURCES_STACK_NAME \
  --query "Stacks[0].Outputs[?OutputKey=='LambdaCodeBucketName'].OutputValue" \
  --output text \
  --region $REGION 2>/dev/null || echo "")

if [ ! -z "$LAMBDA_BUCKET" ]; then
    aws s3 rm s3://$LAMBDA_BUCKET --recursive --region $REGION
    echo -e "${GREEN}✓ Lambda code bucket vaciado${NC}"
else
    echo -e "${YELLOW}⚠ Lambda code bucket no encontrado${NC}"
fi
echo ""

# Eliminar stack de recursos
echo -e "${BLUE}[2/4] Eliminando stack de recursos...${NC}"
aws cloudformation delete-stack \
  --stack-name $RESOURCES_STACK_NAME \
  --region $REGION

echo "Esperando a que el stack se elimine..."
aws cloudformation wait stack-delete-complete \
  --stack-name $RESOURCES_STACK_NAME \
  --region $REGION

echo -e "${GREEN}✓ Stack de recursos eliminado${NC}"
echo ""

# Eliminar stack IAM
echo -e "${BLUE}[3/4] Eliminando stack IAM...${NC}"
aws cloudformation delete-stack \
  --stack-name $IAM_STACK_NAME \
  --region $REGION

echo "Esperando a que el stack se elimine..."
aws cloudformation wait stack-delete-complete \
  --stack-name $IAM_STACK_NAME \
  --region $REGION

echo -e "${GREEN}✓ Stack IAM eliminado${NC}"
echo ""

# Limpiar archivos locales
echo -e "${BLUE}[4/4] Limpiando archivos locales...${NC}"
rm -f app-server.zip process-order.zip
echo -e "${GREEN}✓ Archivos locales limpiados${NC}"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}¡Limpieza completada!${NC}"
echo -e "${GREEN}========================================${NC}"
