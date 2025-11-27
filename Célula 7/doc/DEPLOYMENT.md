# Guía de Despliegue - Sistema de Votación Gadget del Año

## Requisitos Previos

- AWS CLI configurado con credenciales válidas
- Python 3.11 o superior
- Node.js 18 o superior
- Permisos IAM para crear recursos en AWS

## Despliegue Automático

### Linux/Mac

```bash
cd scripts
chmod +x *.sh
./deploy.sh
```

### Windows

```cmd
cd scripts
deploy.bat
```

## Despliegue Manual

### 1. Crear Bucket S3 para Código Lambda

```bash
aws s3 mb s3://gadget-voting-lambda-code-UNIQUE-ID
```

### 2. Empaquetar Funciones Lambda

Linux/Mac:
```bash
cd scripts
./package-lambdas.sh
```

Windows:
```cmd
cd scripts
package-lambdas.bat
```

### 3. Subir Código a S3

```bash
aws s3 cp dist/lambda/ s3://YOUR-BUCKET/lambda/ --recursive
```

### 4. Desplegar Stack IAM

```bash
aws cloudformation create-stack \
  --stack-name gadget-voting-iam \
  --template-body file://cloudformation/iam-stack.yaml \
  --capabilities CAPABILITY_NAMED_IAM

aws cloudformation wait stack-create-complete \
  --stack-name gadget-voting-iam
```

### 5. Desplegar Stack Principal

```bash
aws cloudformation create-stack \
  --stack-name gadget-voting-main \
  --template-body file://cloudformation/main-stack.yaml \
  --parameters \
    ParameterKey=IamStackName,ParameterValue=gadget-voting-iam \
    ParameterKey=EmitVoteLambdaS3Bucket,ParameterValue=YOUR-BUCKET

aws cloudformation wait stack-create-complete \
  --stack-name gadget-voting-main
```

### 6. Obtener Outputs

```bash
aws cloudformation describe-stacks \
  --stack-name gadget-voting-main \
  --query 'Stacks[0].Outputs'
```

Guarda estos valores:
- `ApiEndpoint`: URL del API Gateway
- `UserPoolId`: ID del User Pool de Cognito
- `UserPoolClientId`: ID del Client de Cognito

### 7. Poblar Datos de Ejemplo

Linux/Mac:
```bash
cd scripts
./populate-data.sh
```

Windows:
```cmd
cd scripts
populate-data.bat
```

### 8. Configurar Frontend

```bash
cd frontend
cp .env.example .env
```

Editar `.env` con los valores obtenidos en el paso 6:

```env
REACT_APP_API_ENDPOINT=https://YOUR-API-ID.execute-api.YOUR-REGION.amazonaws.com/prod
REACT_APP_USER_POOL_ID=YOUR_USER_POOL_ID
REACT_APP_CLIENT_ID=YOUR_CLIENT_ID
```

### 9. Instalar y Ejecutar Frontend

```bash
npm install
npm start
```

La aplicación estará disponible en `http://localhost:3000`

## Pruebas

### Probar API con curl

Linux/Mac:
```bash
cd tests
chmod +x test-api.sh
./test-api.sh
```

Windows:
```cmd
cd tests
test-api.bat
```

### Crear Usuario de Prueba

```bash
aws cognito-idp sign-up \
  --client-id YOUR_CLIENT_ID \
  --username test@example.com \
  --password TestPassword123!

# Confirmar usuario (solo para desarrollo)
aws cognito-idp admin-confirm-sign-up \
  --user-pool-id YOUR_USER_POOL_ID \
  --username test@example.com
```

## Despliegue de Frontend en Producción

### Opción 1: S3 + CloudFront

1. Construir aplicación:
```bash
cd frontend
npm run build
```

2. Crear bucket S3:
```bash
aws s3 mb s3://gadget-voting-frontend
aws s3 website s3://gadget-voting-frontend --index-document index.html
```

3. Subir archivos:
```bash
aws s3 sync build/ s3://gadget-voting-frontend --delete
```

4. Configurar CloudFront (opcional para HTTPS y CDN)

### Opción 2: Amplify Hosting

```bash
npm install -g @aws-amplify/cli
amplify init
amplify add hosting
amplify publish
```

## Limpieza de Recursos

Para eliminar todos los recursos creados:

```bash
# Eliminar stacks de CloudFormation
aws cloudformation delete-stack --stack-name gadget-voting-main
aws cloudformation wait stack-delete-complete --stack-name gadget-voting-main

aws cloudformation delete-stack --stack-name gadget-voting-iam
aws cloudformation wait stack-delete-complete --stack-name gadget-voting-iam

# Eliminar bucket S3
aws s3 rb s3://YOUR-BUCKET --force
```

## Troubleshooting

### Error: Stack creation failed

Verificar logs de CloudFormation:
```bash
aws cloudformation describe-stack-events \
  --stack-name gadget-voting-main \
  --max-items 10
```

### Error: Lambda no tiene permisos

Verificar que el stack IAM se desplegó correctamente y que los roles existen.

### Error: DynamoDB Stream no procesa votos

Verificar logs de Lambda StreamProcessor:
```bash
aws logs tail /aws/lambda/GadgetVoting-StreamProcessor --follow
```

### Frontend no se conecta al API

1. Verificar que las variables de entorno en `.env` son correctas
2. Verificar CORS en API Gateway
3. Verificar que el usuario está autenticado correctamente

## Monitoreo

### CloudWatch Logs

```bash
# Logs de EmitVote
aws logs tail /aws/lambda/GadgetVoting-EmitVote --follow

# Logs de GetResults
aws logs tail /aws/lambda/GadgetVoting-GetResults --follow

# Logs de StreamProcessor
aws logs tail /aws/lambda/GadgetVoting-StreamProcessor --follow
```

### Métricas de DynamoDB

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=VoteResults \
  --start-time 2025-11-26T00:00:00Z \
  --end-time 2025-11-26T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

## Costos Estimados

Con 1000 usuarios votando:
- DynamoDB: ~$0.50/mes (PAY_PER_REQUEST)
- Lambda: ~$0.20/mes (1M invocaciones gratis)
- API Gateway: ~$3.50/mes
- Cognito: Gratis (primeros 50,000 MAU)

**Total estimado: ~$4-5/mes**
