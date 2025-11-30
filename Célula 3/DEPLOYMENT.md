# Guía de Despliegue - Acme Image Handler

## Cuentas AWS Requeridas

Este proyecto requiere **3 cuentas AWS separadas** para los diferentes ambientes:

### 1. Cuenta de Construcción (Build Account)
- **Propósito**: Ejecutar el pipeline CI/CD
- **Servicios**: CodePipeline, CodeBuild, S3 (artifacts)
- **Account ID**: `111111111111` (ejemplo)

### 2. Cuenta de Dry-Run / Sandbox
- **Propósito**: Ambiente de desarrollo y pruebas
- **Servicios**: Lambda, API Gateway, S3, DynamoDB, Cognito
- **Account ID**: `222222222222` (ejemplo)

### 3. Cuenta de Producción
- **Propósito**: Ambiente productivo
- **Servicios**: Lambda, API Gateway, S3, DynamoDB, Cognito
- **Account ID**: `333333333333` (ejemplo)

## Configuración de Cuentas

### Paso 1: Configurar IAM Roles Cross-Account

#### En la Cuenta de Build

Crear rol para CodePipeline que pueda asumir roles en otras cuentas:

```bash
aws iam create-role \
  --role-name CodePipelineCrossAccountRole \
  --assume-role-policy-document file://trust-policy.json
```

**trust-policy.json**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "codepipeline.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

#### En las Cuentas de Sandbox y Producción

Crear rol que permita despliegues desde la cuenta de build:

```bash
aws iam create-role \
  --role-name CloudFormationDeploymentRole \
  --assume-role-policy-document file://cross-account-trust.json
```

**cross-account-trust.json**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::111111111111:root"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### Paso 2: Configurar VPC y Subnets

En cada cuenta (Sandbox y Producción):

```bash
# Crear VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16

# Crear subnets privadas
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.1.0/24 --availability-zone us-east-1a
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.2.0/24 --availability-zone us-east-1b

# Crear NAT Gateway (para que Lambdas accedan a internet)
aws ec2 create-nat-gateway --subnet-id subnet-xxx --allocation-id eipalloc-xxx

# Crear VPC Endpoints para S3 y DynamoDB
aws ec2 create-vpc-endpoint --vpc-id vpc-xxx --service-name com.amazonaws.us-east-1.s3
aws ec2 create-vpc-endpoint --vpc-id vpc-xxx --service-name com.amazonaws.us-east-1.dynamodb
```

### Paso 3: Actualizar Parámetros

Editar los archivos de parámetros con los valores reales:

**pipeline/parameters-sandbox.json**:
```json
[
  {
    "ParameterKey": "EnvironmentName",
    "ParameterValue": "sandbox"
  },
  {
    "ParameterKey": "VPCId",
    "ParameterValue": "vpc-0123456789abcdef0"
  },
  {
    "ParameterKey": "PrivateSubnet1",
    "ParameterValue": "subnet-0123456789abcdef0"
  },
  {
    "ParameterKey": "PrivateSubnet2",
    "ParameterValue": "subnet-0123456789abcdef1"
  },
  {
    "ParameterKey": "ProjectName",
    "ParameterValue": "acme-image-handler"
  }
]
```

Repetir para `parameters-pre-prod.json` y `parameters-prod.json`.

## Despliegue Inicial

### Opción 1: Despliegue Manual por Ambiente

#### Sandbox
```bash
# Configurar credenciales de la cuenta Sandbox
export AWS_PROFILE=sandbox

# Desplegar
cd "Célula 3"
./pipeline/deploy.sh sandbox

# Obtener outputs
aws cloudformation describe-stacks \
  --stack-name acme-image-handler-sandbox \
  --query 'Stacks[0].Outputs' \
  --output table
```

#### Pre-Producción
```bash
export AWS_PROFILE=pre-prod
./pipeline/deploy.sh pre-prod
```

#### Producción
```bash
export AWS_PROFILE=prod
./pipeline/deploy.sh prod
```

### Opción 2: Despliegue con Pipeline CI/CD

#### 1. Crear Pipeline en la Cuenta de Build

```bash
# Configurar credenciales de la cuenta Build
export AWS_PROFILE=build

# Crear el pipeline
aws cloudformation create-stack \
  --stack-name acme-image-handler-pipeline \
  --template-body file://iac/pipeline.yaml \
  --parameters \
    ParameterKey=GitHubOwner,ParameterValue=your-github-user \
    ParameterKey=GitHubRepo,ParameterValue=your-repo-name \
    ParameterKey=GitHubBranch,ParameterValue=main \
    ParameterKey=GitHubToken,ParameterValue=ghp_xxxxxxxxxxxx \
    ParameterKey=SandboxAccountId,ParameterValue=222222222222 \
    ParameterKey=PreProdAccountId,ParameterValue=222222222222 \
    ParameterKey=ProdAccountId,ParameterValue=333333333333 \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

#### 2. Activar el Pipeline

```bash
# Push a GitHub
git add .
git commit -m "Initial deployment"
git push origin main
```

El pipeline ejecutará automáticamente:
1. **Source**: Obtiene código de GitHub
2. **Build**: Empaqueta Lambdas y valida templates
3. **Deploy Sandbox**: Despliega automáticamente
4. **Deploy Pre-Prod**: Requiere aprobación manual
5. **Deploy Prod**: Requiere aprobación manual

## Post-Despliegue

### 1. Crear Usuario de Prueba en Cognito

```bash
# Obtener User Pool ID
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name acme-image-handler-sandbox \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

# Crear usuario
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username test@example.com \
  --user-attributes Name=email,Value=test@example.com Name=email_verified,Value=true \
  --temporary-password TempPassword123! \
  --message-action SUPPRESS

# Establecer password permanente
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username test@example.com \
  --password TestPassword123! \
  --permanent
```

### 2. Probar el API

```bash
# Obtener API URL
API_URL=$(aws cloudformation describe-stacks \
  --stack-name acme-image-handler-sandbox \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text)

# Obtener Client ID
CLIENT_ID=$(aws cloudformation describe-stacks \
  --stack-name acme-image-handler-sandbox \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' \
  --output text)

# Obtener Cognito Domain
COGNITO_DOMAIN=$(aws cloudformation describe-stacks \
  --stack-name acme-image-handler-sandbox \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolDomain`].OutputValue' \
  --output text)

# Configurar variables para pruebas
export API_URL=$API_URL
export CLIENT_ID=$CLIENT_ID
export COGNITO_DOMAIN=$COGNITO_DOMAIN
export USERNAME=test@example.com
export PASSWORD=TestPassword123!

# Ejecutar pruebas
./tests/test-api.sh
```

### 3. Subir Imágenes de Prueba

```bash
# Generar imágenes sintéticas
cd tests
python3 generate-test-data.py

# Las imágenes estarán en data/test-images/
# Puedes subirlas manualmente usando el API
```

## Actualización del Stack

### Actualización Manual

```bash
# Modificar código o templates
vim src/lambda/api-handler/lambda_function.py

# Desplegar cambios
./pipeline/deploy.sh sandbox
```

### Actualización vía Pipeline

```bash
# Commit y push
git add .
git commit -m "Update API handler"
git push origin main

# El pipeline se ejecutará automáticamente
```

## Rollback

### Rollback Manual

```bash
# Listar versiones del stack
aws cloudformation list-stack-resources \
  --stack-name acme-image-handler-sandbox

# Rollback a versión anterior
aws cloudformation cancel-update-stack \
  --stack-name acme-image-handler-sandbox
```

### Rollback en Pipeline

Desde la consola de CodePipeline:
1. Ir a la ejecución fallida
2. Click en "Retry" o "Stop and rollback"

## Eliminación de Recursos

### Eliminar Stack

```bash
# CUIDADO: Esto eliminará todos los recursos
aws cloudformation delete-stack \
  --stack-name acme-image-handler-sandbox

# Esperar a que se complete
aws cloudformation wait stack-delete-complete \
  --stack-name acme-image-handler-sandbox
```

### Eliminar Buckets S3 (si tienen contenido)

```bash
# Vaciar buckets antes de eliminar el stack
aws s3 rm s3://acme-gadgets-raw-222222222222-sandbox --recursive
aws s3 rm s3://acme-gadgets-processed-222222222222-sandbox --recursive
```

## Troubleshooting

### Error: Lambda no puede acceder a S3/DynamoDB

**Causa**: Lambdas en VPC sin NAT Gateway o VPC Endpoints

**Solución**:
```bash
# Crear VPC Endpoints
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-xxx \
  --service-name com.amazonaws.us-east-1.s3 \
  --route-table-ids rtb-xxx

aws ec2 create-vpc-endpoint \
  --vpc-id vpc-xxx \
  --service-name com.amazonaws.us-east-1.dynamodb \
  --route-table-ids rtb-xxx
```

### Error: Stack rollback por timeout

**Causa**: Lambda en VPC sin conectividad

**Solución**: Verificar que las subredes privadas tengan ruta a NAT Gateway

### Error: Cognito authentication failed

**Causa**: Usuario no existe o password incorrecto

**Solución**: Verificar usuario en Cognito User Pool

## Monitoreo Post-Despliegue

```bash
# Ver logs en tiempo real
aws logs tail /aws/lambda/acme-image-handler-processor-sandbox --follow

# Ver métricas
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=acme-image-handler-processor-sandbox \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

## Checklist de Despliegue

- [ ] 3 cuentas AWS configuradas
- [ ] VPCs y subnets creadas en cada cuenta
- [ ] NAT Gateways configurados
- [ ] VPC Endpoints para S3 y DynamoDB
- [ ] Parámetros actualizados en archivos JSON
- [ ] Pipeline creado (si se usa CI/CD)
- [ ] Stack desplegado exitosamente
- [ ] Usuario de prueba creado en Cognito
- [ ] Pruebas funcionales ejecutadas
- [ ] Imágenes de prueba subidas
- [ ] Monitoreo configurado
- [ ] Documentación actualizada
