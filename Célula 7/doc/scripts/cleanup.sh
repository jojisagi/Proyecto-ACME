#!/bin/bash

# Script para limpiar todos los recursos AWS

set -e

MAIN_STACK_NAME=${1:-"gadget-voting-main"}
IAM_STACK_NAME=${2:-"gadget-voting-iam"}

echo "========================================="
echo "Limpieza de Recursos AWS"
echo "========================================="
echo ""
echo "ADVERTENCIA: Esto eliminará todos los recursos creados"
echo "Stack Principal: ${MAIN_STACK_NAME}"
echo "Stack IAM: ${IAM_STACK_NAME}"
echo ""
read -p "¿Continuar? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Operación cancelada"
    exit 1
fi

# Obtener bucket S3 de los parámetros del stack
echo "Obteniendo información del bucket S3..."
S3_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name ${MAIN_STACK_NAME} \
  --query 'Stacks[0].Parameters[?ParameterKey==`EmitVoteLambdaS3Bucket`].ParameterValue' \
  --output text 2>/dev/null || echo "")

# Eliminar stack principal
echo "Eliminando stack principal..."
aws cloudformation delete-stack --stack-name ${MAIN_STACK_NAME}
echo "Esperando a que se complete la eliminación..."
aws cloudformation wait stack-delete-complete --stack-name ${MAIN_STACK_NAME}
echo "✓ Stack principal eliminado"
echo ""

# Eliminar stack IAM
echo "Eliminando stack IAM..."
aws cloudformation delete-stack --stack-name ${IAM_STACK_NAME}
echo "Esperando a que se complete la eliminación..."
aws cloudformation wait stack-delete-complete --stack-name ${IAM_STACK_NAME}
echo "✓ Stack IAM eliminado"
echo ""

# Eliminar bucket S3 si existe
if [ -n "$S3_BUCKET" ]; then
    echo "Eliminando bucket S3: ${S3_BUCKET}..."
    aws s3 rb s3://${S3_BUCKET} --force 2>/dev/null || echo "Bucket no encontrado o ya eliminado"
    echo "✓ Bucket S3 eliminado"
fi

echo ""
echo "========================================="
echo "Limpieza completada"
echo "========================================="
echo ""
echo "Todos los recursos han sido eliminados."
echo ""
echo "Nota: Los logs de CloudWatch se mantienen por defecto."
echo "Para eliminarlos manualmente:"
echo "  aws logs delete-log-group --log-group-name /aws/lambda/GadgetVoting-EmitVote"
echo "  aws logs delete-log-group --log-group-name /aws/lambda/GadgetVoting-GetResults"
echo "  aws logs delete-log-group --log-group-name /aws/lambda/GadgetVoting-StreamProcessor"
