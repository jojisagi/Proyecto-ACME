#!/bin/bash

# Script para desplegar la aplicación

set -e

ENVIRONMENT=${1:-sandbox}
REGION=${2:-us-east-1}
VPC_ID=${3}
SUBNET_1=${4}
SUBNET_2=${5}
KMS_KEY_ARN=${6}

echo "=========================================="
echo "Desplegando Acme Image Handler"
echo "Ambiente: $ENVIRONMENT"
echo "Región: $REGION"
echo "=========================================="

if [ -z "$VPC_ID" ] || [ -z "$SUBNET_1" ] || [ -z "$SUBNET_2" ] || [ -z "$KMS_KEY_ARN" ]; then
  echo "Error: Parámetros incompletos"
  echo "Uso: ./pipeline/deploy.sh <env> <region> <vpc-id> <subnet-1> <subnet-2> <kms-key-arn>"
  exit 1
fi

STACK_NAME="acme-image-handler-$ENVIRONMENT"
TEMPLATE_FILE="iac/cloudformation-base.yaml"

echo "Validando template..."
aws cloudformation validate-template \
  --template-body file://$TEMPLATE_FILE \
  --region $REGION

echo "Desplegando CloudFormation stack..."
aws cloudformation deploy \
  --template-file $TEMPLATE_FILE \
  --stack-name $STACK_NAME \
  --parameter-overrides \
    EnvironmentName=$ENVIRONMENT \
    VPCId=$VPC_ID \
    PrivateSubnet1=$SUBNET_1 \
    PrivateSubnet2=$SUBNET_2 \
    KMSKeyArn=$KMS_KEY_ARN \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $REGION \
  --no-fail-on-empty-changeset

echo "Stack desplegado exitosamente"
echo "Stack Name: $STACK_NAME"

# Obtener outputs
echo ""
echo "Outputs:"
aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs' \
  --output table