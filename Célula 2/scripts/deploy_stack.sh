#!/bin/bash

# Script para desplegar los stacks de CloudFormation
# Compatible con Windows (Git Bash) y Linux

set -e

echo "=== Desplegando Sistema de Scheduling de Órdenes de Compra ==="
echo ""

# Variables
IAM_STACK_NAME="acme-scheduling-iam"
MAIN_STACK_NAME="acme-scheduling-main"
REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="${ENVIRONMENT:-production}"

echo "Configuración:"
echo "  Región: $REGION"
echo "  Ambiente: $ENVIRONMENT"
echo ""

# Paso 1: Desplegar Stack de IAM
echo "=== Paso 1: Desplegando Stack de IAM ==="
aws cloudformation deploy \
  --template-file ../iac/iam_stack.yml \
  --stack-name $IAM_STACK_NAME \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $REGION \
  --no-fail-on-empty-changeset

echo "✓ Stack de IAM desplegado"
echo ""

# Esperar a que el stack esté completo
echo "Esperando a que el stack de IAM esté completo..."
aws cloudformation wait stack-create-complete \
  --stack-name $IAM_STACK_NAME \
  --region $REGION 2>/dev/null || \
aws cloudformation wait stack-update-complete \
  --stack-name $IAM_STACK_NAME \
  --region $REGION 2>/dev/null || true

echo "✓ Stack de IAM completado"
echo ""

# Paso 2: Empaquetar Lambdas
echo "=== Paso 2: Empaquetando Lambdas ==="
./package_lambdas.sh
echo ""

# Paso 3: Crear bucket S3 para artefactos (si no existe)
BUCKET_NAME="acme-scheduling-artifacts-$(aws sts get-caller-identity --query Account --output text)"
echo "=== Paso 3: Verificando bucket S3 para artefactos ==="
echo "Bucket: $BUCKET_NAME"

if aws s3 ls "s3://$BUCKET_NAME" 2>&1 | grep -q 'NoSuchBucket'; then
    echo "Creando bucket S3..."
    aws s3 mb "s3://$BUCKET_NAME" --region $REGION
    echo "✓ Bucket creado"
else
    echo "✓ Bucket ya existe"
fi
echo ""

# Paso 4: Subir artefactos Lambda a S3
echo "=== Paso 4: Subiendo artefactos Lambda a S3 ==="
aws s3 cp ../dist/scheduler_manager.zip "s3://$BUCKET_NAME/lambdas/scheduler_manager.zip"
aws s3 cp ../dist/order_executor.zip "s3://$BUCKET_NAME/lambdas/order_executor.zip"
echo "✓ Artefactos subidos"
echo ""

# Paso 5: Desplegar Stack Principal
echo "=== Paso 5: Desplegando Stack Principal ==="
aws cloudformation deploy \
  --template-file ../iac/main_stack.yml \
  --stack-name $MAIN_STACK_NAME \
  --parameter-overrides Environment=$ENVIRONMENT \
  --region $REGION \
  --no-fail-on-empty-changeset

echo "✓ Stack principal desplegado"
echo ""

# Esperar a que el stack esté completo
echo "Esperando a que el stack principal esté completo..."
aws cloudformation wait stack-create-complete \
  --stack-name $MAIN_STACK_NAME \
  --region $REGION 2>/dev/null || \
aws cloudformation wait stack-update-complete \
  --stack-name $MAIN_STACK_NAME \
  --region $REGION 2>/dev/null || true

echo "✓ Stack principal completado"
echo ""

# Paso 6: Actualizar código de Lambdas
echo "=== Paso 6: Actualizando código de funciones Lambda ==="

echo "Actualizando scheduler_manager..."
aws lambda update-function-code \
  --function-name acme-scheduler-manager \
  --s3-bucket $BUCKET_NAME \
  --s3-key lambdas/scheduler_manager.zip \
  --region $REGION > /dev/null

echo "Actualizando order_executor..."
aws lambda update-function-code \
  --function-name acme-order-executor \
  --s3-bucket $BUCKET_NAME \
  --s3-key lambdas/order_executor.zip \
  --region $REGION > /dev/null

echo "✓ Funciones Lambda actualizadas"
echo ""

# Paso 7: Obtener outputs del stack
echo "=== Paso 7: Información del Despliegue ==="
echo ""
echo "API Endpoint:"
aws cloudformation describe-stacks \
  --stack-name $MAIN_STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text \
  --region $REGION

echo ""
echo "User Pool ID:"
aws cloudformation describe-stacks \
  --stack-name $MAIN_STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text \
  --region $REGION

echo ""
echo "User Pool Client ID:"
aws cloudformation describe-stacks \
  --stack-name $MAIN_STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' \
  --output text \
  --region $REGION

echo ""
echo "=== Despliegue Completado Exitosamente ==="
echo ""
echo "Siguiente paso: Crear un usuario en Cognito y ejecutar las pruebas"
echo "Comando: ./curl_tests.sh"
