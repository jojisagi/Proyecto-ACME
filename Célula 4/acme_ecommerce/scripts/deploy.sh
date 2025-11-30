#!/bin/bash

# Script de despliegue completo para la arquitectura E-commerce

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Despliegue E-commerce AWS${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Variables
REGION=${AWS_REGION:-us-east-1}
IAM_STACK_NAME="ecommerce-iam"
RESOURCES_STACK_NAME="ecommerce-resources"

# Paso 1: Desplegar stack IAM
echo -e "${GREEN}[1/5] Desplegando stack IAM...${NC}"
aws cloudformation create-stack \
  --stack-name $IAM_STACK_NAME \
  --template-body file://cloudformation/iam-stack.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $REGION

echo "Esperando a que el stack IAM se complete..."
aws cloudformation wait stack-create-complete \
  --stack-name $IAM_STACK_NAME \
  --region $REGION

echo -e "${GREEN}✓ Stack IAM desplegado${NC}"
echo ""

# Paso 2: Crear bucket para código Lambda
echo -e "${GREEN}[2/6] Creando bucket para código Lambda...${NC}"
LAMBDA_BUCKET="ecommerce-lambda-code-$(aws sts get-caller-identity --query Account --output text)"

# Verificar si el bucket existe
if aws s3 ls "s3://$LAMBDA_BUCKET" 2>&1 | grep -q 'NoSuchBucket'; then
    aws s3 mb s3://$LAMBDA_BUCKET --region $REGION
    echo -e "${GREEN}✓ Bucket creado: $LAMBDA_BUCKET${NC}"
else
    echo -e "${YELLOW}⚠ Bucket ya existe: $LAMBDA_BUCKET${NC}"
fi
echo ""

# Paso 3: Empaquetar y subir Lambdas
echo -e "${GREEN}[3/6] Empaquetando y subiendo funciones Lambda...${NC}"

# App Server Lambda
echo "Empaquetando app-server..."
cd lambdas/app-server
zip -r ../../app-server.zip index.py > /dev/null 2>&1
cd ../..
aws s3 cp app-server.zip s3://$LAMBDA_BUCKET/app-server.zip --region $REGION
echo "✓ app-server.zip subido"

# Process Order Lambda
echo "Empaquetando process-order..."
cd lambdas/process-order
zip -r ../../process-order.zip index.py > /dev/null 2>&1
cd ../..
aws s3 cp process-order.zip s3://$LAMBDA_BUCKET/process-order.zip --region $REGION
echo "✓ process-order.zip subido"

echo -e "${GREEN}✓ Lambdas empaquetadas y subidas a S3${NC}"
echo ""

# Paso 4: Desplegar stack de recursos
echo -e "${GREEN}[4/6] Desplegando stack de recursos...${NC}"
aws cloudformation create-stack \
  --stack-name $RESOURCES_STACK_NAME \
  --template-body file://cloudformation/resources-stack.yaml \
  --parameters ParameterKey=IAMStackName,ParameterValue=$IAM_STACK_NAME \
  --region $REGION

echo "Esperando a que el stack de recursos se complete..."
aws cloudformation wait stack-create-complete \
  --stack-name $RESOURCES_STACK_NAME \
  --region $REGION

echo -e "${GREEN}✓ Stack de recursos desplegado${NC}"
echo ""

# Paso 5: Poblar DynamoDB
echo -e "${GREEN}[5/6] Poblando DynamoDB con datos de prueba...${NC}"
python3 scripts/populate-dynamodb.py

echo -e "${GREEN}✓ DynamoDB poblado${NC}"
echo ""

# Paso 6: Construir y desplegar frontend
echo -e "${GREEN}[6/6] Construyendo y desplegando frontend...${NC}"

# Obtener nombre del bucket
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name $RESOURCES_STACK_NAME \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
  --output text \
  --region $REGION)

# Obtener URL del API
API_URL=$(aws cloudformation describe-stacks \
  --stack-name $RESOURCES_STACK_NAME \
  --query "Stacks[0].Outputs[?OutputKey=='ApiGatewayUrl'].OutputValue" \
  --output text \
  --region $REGION)

echo "Bucket: $BUCKET_NAME"
echo "API URL: $API_URL"

# Construir frontend
cd frontend
echo "REACT_APP_API_URL=$API_URL" > .env
npm install
npm run build

# Desplegar a S3
aws s3 sync build/ s3://$BUCKET_NAME --delete --region $REGION

cd ..

echo -e "${GREEN}✓ Frontend desplegado${NC}"
echo ""

# Obtener CloudFront URL
CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
  --stack-name $RESOURCES_STACK_NAME \
  --query "Stacks[0].Outputs[?OutputKey=='CloudFrontUrl'].OutputValue" \
  --output text \
  --region $REGION)

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}¡Despliegue completado!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "API Gateway URL: ${YELLOW}$API_URL${NC}"
echo -e "CloudFront URL: ${YELLOW}https://$CLOUDFRONT_URL${NC}"
echo -e "S3 Bucket: ${YELLOW}$BUCKET_NAME${NC}"
echo ""
echo -e "Puedes probar el API con:"
echo -e "${YELLOW}./scripts/test-api.sh $API_URL${NC}"
