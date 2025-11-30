#!/bin/bash

###############################################################################
# Script de Despliegue - Acme Image Handler
# Célula 3 - Arquitectura Serverless
###############################################################################

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
STACK_NAME="acme-image-handler"
TEMPLATE_FILE="iac/cloudformation-base.yaml"
REGION="${AWS_REGION:-us-east-1}"

# Función para imprimir mensajes
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Validar argumentos
if [ $# -lt 1 ]; then
    print_error "Uso: $0 <environment> [stack-name]"
    echo "Ambientes válidos: sandbox, pre-prod, prod"
    exit 1
fi

ENVIRONMENT=$1
STACK_NAME_FULL="${STACK_NAME}-${ENVIRONMENT}"

if [ $# -ge 2 ]; then
    STACK_NAME_FULL=$2
fi

# Validar ambiente
if [[ ! "$ENVIRONMENT" =~ ^(sandbox|pre-prod|prod)$ ]]; then
    print_error "Ambiente inválido: $ENVIRONMENT"
    echo "Ambientes válidos: sandbox, pre-prod, prod"
    exit 1
fi

PARAMS_FILE="pipeline/parameters-${ENVIRONMENT}.json"

# Verificar que existan los archivos necesarios
if [ ! -f "$TEMPLATE_FILE" ]; then
    print_error "Template no encontrado: $TEMPLATE_FILE"
    exit 1
fi

if [ ! -f "$PARAMS_FILE" ]; then
    print_error "Archivo de parámetros no encontrado: $PARAMS_FILE"
    exit 1
fi

print_message "========================================="
print_message "Desplegando Acme Image Handler"
print_message "Ambiente: $ENVIRONMENT"
print_message "Stack: $STACK_NAME_FULL"
print_message "Región: $REGION"
print_message "========================================="

# Validar template
print_message "Validando template de CloudFormation..."
aws cloudformation validate-template \
    --template-body file://$TEMPLATE_FILE \
    --region $REGION > /dev/null

print_message "✓ Template válido"

# Verificar si el stack existe
print_message "Verificando si el stack existe..."
if aws cloudformation describe-stacks \
    --stack-name $STACK_NAME_FULL \
    --region $REGION > /dev/null 2>&1; then
    
    STACK_EXISTS=true
    print_message "Stack existe - se actualizará"
else
    STACK_EXISTS=false
    print_message "Stack no existe - se creará"
fi

# Desplegar stack
print_message "Desplegando stack..."

if [ "$STACK_EXISTS" = true ]; then
    # Update stack
    aws cloudformation update-stack \
        --stack-name $STACK_NAME_FULL \
        --template-body file://$TEMPLATE_FILE \
        --parameters file://$PARAMS_FILE \
        --capabilities CAPABILITY_NAMED_IAM \
        --region $REGION || {
            if [ $? -eq 254 ]; then
                print_warning "No hay cambios para desplegar"
                exit 0
            else
                print_error "Error actualizando stack"
                exit 1
            fi
        }
    
    print_message "Esperando a que el stack se actualice..."
    aws cloudformation wait stack-update-complete \
        --stack-name $STACK_NAME_FULL \
        --region $REGION
else
    # Create stack
    aws cloudformation create-stack \
        --stack-name $STACK_NAME_FULL \
        --template-body file://$TEMPLATE_FILE \
        --parameters file://$PARAMS_FILE \
        --capabilities CAPABILITY_NAMED_IAM \
        --region $REGION
    
    print_message "Esperando a que el stack se cree..."
    aws cloudformation wait stack-create-complete \
        --stack-name $STACK_NAME_FULL \
        --region $REGION
fi

# Obtener outputs
print_message "========================================="
print_message "Stack desplegado exitosamente!"
print_message "========================================="
print_message "Outputs del stack:"

aws cloudformation describe-stacks \
    --stack-name $STACK_NAME_FULL \
    --region $REGION \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table

print_message "========================================="
print_message "Despliegue completado!"
print_message "========================================="
