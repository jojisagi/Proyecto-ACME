#!/bin/bash

# Script de despliegue completo del Sistema de Votación

set -e

echo "========================================="
echo "Despliegue Sistema de Votación"
echo "========================================="
echo ""

# Variables
REGION=${AWS_REGION:-us-east-1}
IAM_STACK_NAME="gadget-voting-iam"
MAIN_STACK_NAME="gadget-voting-main"
S3_BUCKET_NAME="gadget-voting-lambda-code-${RANDOM}"

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Paso 1: Crear bucket S3 para código Lambda${NC}"
aws s3 mb s3://${S3_BUCKET_NAME} --region ${REGION}
echo -e "${GREEN}✓ Bucket creado: ${S3_BUCKET_NAME}${NC}"
echo ""

echo -e "${YELLOW}Paso 2: Empaquetar funciones Lambda${NC}"
cd scripts
./package-lambdas.sh
cd ..
echo ""

echo -e "${YELLOW}Paso 3: Subir código Lambda a S3${NC}"
aws s3 cp dist/lambda/ s3://${S3_BUCKET_NAME}/lambda/ --recursive
echo -e "${GREEN}✓ Código Lambda subido${NC}"
echo ""

echo -e "${YELLOW}Paso 4: Desplegar stack IAM${NC}"
aws cloudformation create-stack \
  --stack-name ${IAM_STACK_NAME} \
  --template-body file://cloudformation/iam-stack.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region ${REGION}

echo "Esperando a que el stack IAM se complete..."
aws cloudformation wait stack-create-complete \
  --stack-name ${IAM_STACK_NAME} \
  --region ${REGION}
echo -e "${GREEN}✓ Stack IAM desplegado${NC}"
echo ""

echo -e "${YELLOW}Paso 5: Desplegar stack principal${NC}"
aws cloudformation create-stack \
  --stack-name ${MAIN_STACK_NAME} \
  --template-body file://cloudformation/main-stack.yaml \
  --parameters \
    ParameterKey=IamStackName,ParameterValue=${IAM_STACK_NAME} \
    ParameterKey=EmitVoteLambdaS3Bucket,ParameterValue=${S3_BUCKET_NAME} \
  --region ${REGION}

echo "Esperando a que el stack principal se complete..."
aws cloudformation wait stack-create-complete \
  --stack-name ${MAIN_STACK_NAME} \
  --region ${REGION}
echo -e "${GREEN}✓ Stack principal desplegado${NC}"
echo ""

echo -e "${YELLOW}Paso 6: Obtener outputs del stack${NC}"
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name ${MAIN_STACK_NAME} \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text \
  --region ${REGION})

USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name ${MAIN_STACK_NAME} \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text \
  --region ${REGION})

CLIENT_ID=$(aws cloudformation describe-stacks \
  --stack-name ${MAIN_STACK_NAME} \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' \
  --output text \
  --region ${REGION})

echo ""
echo "========================================="
echo "Despliegue Completado"
echo "========================================="
echo ""
echo "API Endpoint: ${API_ENDPOINT}"
echo "User Pool ID: ${USER_POOL_ID}"
echo "Client ID: ${CLIENT_ID}"
echo ""
echo "Siguiente paso: Poblar datos de ejemplo"
echo "./scripts/populate-data.sh"
echo ""
echo "Configurar frontend:"
echo "cd frontend"
echo "cp .env.example .env"
echo "# Editar .env con los valores anteriores"
echo "npm install"
echo "npm start"
