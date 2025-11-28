#!/bin/bash
# Script de despliegue para el stack de CloudFormation

set -e

STACK_NAME="toon-processor-dev"
TEMPLATE_FILE="iac/cloudformation-template.yaml"
PARAMETERS_FILE="iac/parameters.json"

echo "Desplegando stack: $STACK_NAME"

# Validar template
echo "Validando template..."
aws cloudformation validate-template --template-body file://$TEMPLATE_FILE

# Desplegar o actualizar stack
if aws cloudformation describe-stacks --stack-name $STACK_NAME 2>/dev/null; then
    echo "Stack existe, actualizando..."
    aws cloudformation update-stack \
        --stack-name $STACK_NAME \
        --template-body file://$TEMPLATE_FILE \
        --parameters file://$PARAMETERS_FILE \
        --capabilities CAPABILITY_NAMED_IAM
    
    echo "Esperando actualización..."
    aws cloudformation wait stack-update-complete --stack-name $STACK_NAME
else
    echo "Creando nuevo stack..."
    aws cloudformation create-stack \
        --stack-name $STACK_NAME \
        --template-body file://$TEMPLATE_FILE \
        --parameters file://$PARAMETERS_FILE \
        --capabilities CAPABILITY_NAMED_IAM
    
    echo "Esperando creación..."
    aws cloudformation wait stack-create-complete --stack-name $STACK_NAME
fi

echo "Stack desplegado exitosamente"

# Mostrar outputs
echo ""
echo "Outputs del stack:"
aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs' \
    --output table
