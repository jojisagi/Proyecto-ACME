#!/bin/bash

# Archivo de configuración para el despliegue
# Copiar a config.sh y ajustar los valores

# Región AWS
export AWS_REGION="us-east-1"

# Nombres de los stacks
export IAM_STACK_NAME="gadget-voting-iam"
export MAIN_STACK_NAME="gadget-voting-main"

# Bucket S3 para código Lambda (debe ser único globalmente)
export S3_BUCKET_NAME="gadget-voting-lambda-code-$(date +%s)"

# Configuración de Cognito (se obtienen después del despliegue)
export USER_POOL_ID=""
export CLIENT_ID=""

# API Gateway endpoint (se obtiene después del despliegue)
export API_ENDPOINT=""

# Usuario de prueba
export TEST_USER_EMAIL="test@example.com"
export TEST_USER_PASSWORD="TestPassword123!"
