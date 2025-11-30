# Guía de Despliegue - Sistema de Scheduling Serverless

## Prerrequisitos

### Software Requerido
- AWS CLI v2.x o superior
- Python 3.9 o superior
- Git Bash (Windows) o Bash (Linux/Mac)
- PowerShell 7+ (opcional para Windows)
- jq (para procesamiento JSON en scripts bash)

### Configuración de AWS

1. **Instalar AWS CLI**:
```bash
# Windows (usando Chocolatey)
choco install awscli

# macOS (usando Homebrew)
brew install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

2. **Configurar Credenciales**:
```bash
aws configure
```

Proporciona:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (ej: us-east-1)
- Default output format (json)

3. **Verificar Permisos**:

Tu usuario IAM debe tener permisos para:
- CloudFormation (crear/actualizar stacks)
- IAM (crear roles y políticas)
- Lambda (crear/actualizar funciones)
- API Gateway (crear APIs)
- DynamoDB (crear tablas)
- EventBridge Scheduler (crear schedules)
- Cognito (crear user pools)
- KMS (crear claves)
- EC2 (crear VPC, subnets, endpoints)
- S3 (crear buckets, subir objetos)
- CloudWatch Logs (crear log groups)

## Proceso de Despliegue

### Opción 1: Despliegue Automatizado (Recomendado)

#### En Linux/Mac/Git Bash:

```bash
cd scheduling-system/scripts

# Hacer ejecutables los scripts
chmod +x *.sh

# Ejecutar despliegue completo
./deploy_stack.sh
```

#### En Windows PowerShell:

```powershell
cd scheduling-system\scripts

# Ejecutar despliegue completo
.\deploy_stack.ps1
```

### Opción 2: Despliegue Manual Paso a Paso

#### Paso 1: Desplegar Stack de IAM

```bash
aws cloudformation deploy \
  --template-file iac/iam_stack.yml \
  --stack-name acme-scheduling-iam \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

Esperar a que complete:
```bash
aws cloudformation wait stack-create-complete \
  --stack-name acme-scheduling-iam \
  --region us-east-1
```

#### Paso 2: Empaquetar Funciones Lambda

**Linux/Mac:**
```bash
cd scripts
./package_lambdas.sh
```

**Windows PowerShell:**
```powershell
cd scripts
.\package_lambdas.ps1
```

#### Paso 3: Crear Bucket S3 para Artefactos

```bash
# Obtener Account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Crear bucket
BUCKET_NAME="acme-scheduling-artifacts-$ACCOUNT_ID"
aws s3 mb "s3://$BUCKET_NAME" --region us-east-1
```

#### Paso 4: Subir Artefactos Lambda

```bash
aws s3 cp dist/scheduler_manager.zip "s3://$BUCKET_NAME/lambdas/scheduler_manager.zip"
aws s3 cp dist/order_executor.zip "s3://$BUCKET_NAME/lambdas/order_executor.zip"
```

#### Paso 5: Desplegar Stack Principal

```bash
aws cloudformation deploy \
  --template-file iac/main_stack.yml \
  --stack-name acme-scheduling-main \
  --parameter-overrides Environment=production \
  --region us-east-1
```

Esperar a que complete:
```bash
aws cloudformation wait stack-create-complete \
  --stack-name acme-scheduling-main \
  --region us-east-1
```

#### Paso 6: Actualizar Código de Lambdas

```bash
# Scheduler Manager
aws lambda update-function-code \
  --function-name acme-scheduler-manager \
  --s3-bucket $BUCKET_NAME \
  --s3-key lambdas/scheduler_manager.zip \
  --region us-east-1

# Order Executor
aws lambda update-function-code \
  --function-name acme-order-executor \
  --s3-bucket $BUCKET_NAME \
  --s3-key lambdas/order_executor.zip \
  --region us-east-1
```

#### Paso 7: Obtener Información del Despliegue

```bash
# API Endpoint
aws cloudformation describe-stacks \
  --stack-name acme-scheduling-main \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text

# User Pool ID
aws cloudformation describe-stacks \
  --stack-name acme-scheduling-main \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text

# Client ID
aws cloudformation describe-stacks \
  --stack-name acme-scheduling-main \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' \
  --output text
```

## Configuración Post-Despliegue

### Crear Usuario en Cognito

```bash
# Obtener User Pool ID
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name acme-scheduling-main \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

# Crear usuario
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username testuser \
  --temporary-password TempPass123! \
  --user-attributes Name=email,Value=test@acme.com

# Establecer contraseña permanente
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username testuser \
  --password TempPass123! \
  --permanent
```

### Poblar DynamoDB con Datos de Prueba (Opcional)

```bash
# Usar AWS CLI para cargar datos
aws dynamodb batch-write-item \
  --request-items file://data/sample_orders.json \
  --region us-east-1
```

## Verificación del Despliegue

### 1. Verificar Stacks de CloudFormation

```bash
aws cloudformation describe-stacks \
  --stack-name acme-scheduling-iam \
  --query 'Stacks[0].StackStatus'

aws cloudformation describe-stacks \
  --stack-name acme-scheduling-main \
  --query 'Stacks[0].StackStatus'
```

Ambos deben mostrar: `CREATE_COMPLETE` o `UPDATE_COMPLETE`

### 2. Verificar Funciones Lambda

```bash
aws lambda list-functions \
  --query 'Functions[?starts_with(FunctionName, `acme-`)].FunctionName'
```

Debe mostrar:
- acme-scheduler-manager
- acme-order-executor

### 3. Verificar API Gateway

```bash
aws apigateway get-rest-apis \
  --query 'items[?name==`AcmeSchedulingAPI`].id'
```

### 4. Verificar Tablas DynamoDB

```bash
aws dynamodb list-tables \
  --query 'TableNames[?contains(@, `Orders`) || contains(@, `Schedule`)]'
```

Debe mostrar:
- PurchaseOrdersTable
- ScheduleDefinitionsTable

## Pruebas Funcionales

### Ejecutar Suite de Pruebas

**Linux/Mac/Git Bash:**
```bash
cd scripts
./curl_tests.sh
```

**Windows PowerShell:**
```powershell
cd scripts
.\curl_tests.ps1
```

### Prueba Manual con curl

```bash
# Obtener configuración
API_ENDPOINT="https://xxxxx.execute-api.us-east-1.amazonaws.com/production"
CLIENT_ID="xxxxx"

# Autenticar
AUTH_RESPONSE=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id $CLIENT_ID \
  --auth-parameters USERNAME=testuser,PASSWORD=TempPass123!)

JWT_TOKEN=$(echo $AUTH_RESPONSE | jq -r '.AuthenticationResult.IdToken')

# Crear schedule
curl -X POST "$API_ENDPOINT/schedule" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scheduleName": "test-schedule",
    "frequency": "rate(1 hour)",
    "gadgetType": "Rocket Shoes",
    "quantity": 100,
    "enabled": true
  }'

# Listar schedules
curl -X GET "$API_ENDPOINT/schedules" \
  -H "Authorization: Bearer $JWT_TOKEN"

# Consultar órdenes
curl -X GET "$API_ENDPOINT/orders" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

## Troubleshooting

### Error: "User does not exist"
**Solución**: Crear usuario en Cognito (ver sección "Crear Usuario en Cognito")

### Error: "Access Denied" en Lambda
**Solución**: Verificar que el stack de IAM se desplegó correctamente y que los roles tienen los permisos necesarios

### Error: "VPC configuration is not valid"
**Solución**: Esperar a que los VPC Endpoints estén disponibles antes de invocar las Lambdas

### Error: "Table does not exist"
**Solución**: Verificar que el stack principal se desplegó completamente

### Logs de Lambda no aparecen
**Solución**: Verificar que el VPC Endpoint de CloudWatch Logs está configurado correctamente

## Limpieza de Recursos

Para eliminar todos los recursos creados:

```bash
# Eliminar stack principal
aws cloudformation delete-stack \
  --stack-name acme-scheduling-main \
  --region us-east-1

# Esperar a que se elimine
aws cloudformation wait stack-delete-complete \
  --stack-name acme-scheduling-main \
  --region us-east-1

# Eliminar stack de IAM
aws cloudformation delete-stack \
  --stack-name acme-scheduling-iam \
  --region us-east-1

# Esperar a que se elimine
aws cloudformation wait stack-delete-complete \
  --stack-name acme-scheduling-iam \
  --region us-east-1

# Eliminar bucket S3 (opcional)
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET_NAME="acme-scheduling-artifacts-$ACCOUNT_ID"
aws s3 rb "s3://$BUCKET_NAME" --force
```

## Actualizaciones

Para actualizar el código de las Lambdas:

```bash
# Empaquetar nuevamente
cd scripts
./package_lambdas.sh

# Subir a S3
aws s3 cp dist/scheduler_manager.zip "s3://$BUCKET_NAME/lambdas/scheduler_manager.zip"
aws s3 cp dist/order_executor.zip "s3://$BUCKET_NAME/lambdas/order_executor.zip"

# Actualizar funciones
aws lambda update-function-code \
  --function-name acme-scheduler-manager \
  --s3-bucket $BUCKET_NAME \
  --s3-key lambdas/scheduler_manager.zip

aws lambda update-function-code \
  --function-name acme-order-executor \
  --s3-bucket $BUCKET_NAME \
  --s3-key lambdas/order_executor.zip
```

## Soporte

Para problemas o preguntas:
1. Revisar logs de CloudWatch
2. Verificar eventos de CloudFormation
3. Consultar documentación de AWS
4. Contactar al equipo de arquitectura
