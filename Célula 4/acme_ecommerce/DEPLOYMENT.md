# Guía de Despliegue - E-commerce AWS Serverless

## Requisitos Previos

- AWS CLI configurado con credenciales válidas
- Python 3.11 o superior
- Node.js 18 o superior
- Permisos IAM para crear recursos en AWS

## Arquitectura

```
┌─────────────┐
│  CloudFront │ ← CDN para distribución global
└──────┬──────┘
       │
       ├─────────────┐
       │             │
   ┌───▼───┐    ┌───▼────────┐
   │  S3   │    │ API Gateway│
   │Bucket │    └─────┬──────┘
   └───────┘          │
                      │
              ┌───────▼────────┐
              │ Lambda         │
              │ (App Server)   │
              └───┬────────┬───┘
                  │        │
         ┌────────▼──┐  ┌──▼─────┐
         │ DynamoDB  │  │  SQS   │
         │  Orders   │  │ Queue  │
         └───────────┘  └───┬────┘
                            │
                    ┌───────▼──────────┐
                    │ Step Functions   │
                    │   Workflow       │
                    └───────┬──────────┘
                            │
                    ┌───────▼────────┐
                    │ Lambda         │
                    │(Process Order) │
                    └───┬────────────┘
                        │
                    ┌───▼───┐
                    │  SNS  │
                    │ Topic │
                    └───────┘
```

## Despliegue Automático

### Opción 1: Script Completo

```bash
./scripts/deploy.sh
```

Este script ejecuta todos los pasos automáticamente:
1. Despliega stack IAM
2. Crea bucket S3 para código Lambda
3. Empaqueta y sube funciones Lambda a S3
4. Despliega stack de recursos
5. Pobla DynamoDB
6. Construye y despliega frontend

### Opción 2: Despliegue Manual

#### Paso 1: Desplegar Stack IAM

```bash
aws cloudformation create-stack \
  --stack-name ecommerce-iam \
  --template-body file://cloudformation/iam-stack.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

# Esperar a que se complete
aws cloudformation wait stack-create-complete \
  --stack-name ecommerce-iam \
  --region us-east-1
```

#### Paso 2: Crear Bucket y Subir Código Lambda

```bash
# Obtener ID de cuenta
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
LAMBDA_BUCKET="ecommerce-lambda-code-$ACCOUNT_ID"

# Crear bucket
aws s3 mb s3://$LAMBDA_BUCKET --region us-east-1

# Empaquetar y subir app-server
cd lambdas/app-server
zip -r ../../app-server.zip index.py
cd ../..
aws s3 cp app-server.zip s3://$LAMBDA_BUCKET/app-server.zip

# Empaquetar y subir process-order
cd lambdas/process-order
zip -r ../../process-order.zip index.py
cd ../..
aws s3 cp process-order.zip s3://$LAMBDA_BUCKET/process-order.zip
```

#### Paso 3: Desplegar Stack de Recursos

```bash
aws cloudformation create-stack \
  --stack-name ecommerce-resources \
  --template-body file://cloudformation/resources-stack.yaml \
  --parameters ParameterKey=IAMStackName,ParameterValue=ecommerce-iam \
  --region us-east-1

# Esperar a que se complete
aws cloudformation wait stack-create-complete \
  --stack-name ecommerce-resources \
  --region us-east-1
```

#### Paso 4: Poblar DynamoDB

```bash
# Generar datos (ya generados)
python3 data/generate-orders.py

# Poblar tabla
python3 scripts/populate-dynamodb.py
```

#### Paso 5: Obtener Outputs

```bash
# URL del API Gateway
aws cloudformation describe-stacks \
  --stack-name ecommerce-resources \
  --query "Stacks[0].Outputs[?OutputKey=='ApiGatewayUrl'].OutputValue" \
  --output text

# Nombre del bucket S3
aws cloudformation describe-stacks \
  --stack-name ecommerce-resources \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
  --output text

# URL de CloudFront
aws cloudformation describe-stacks \
  --stack-name ecommerce-resources \
  --query "Stacks[0].Outputs[?OutputKey=='CloudFrontUrl'].OutputValue" \
  --output text
```

#### Paso 6: Desplegar Frontend

```bash
cd frontend

# Configurar URL del API
echo "REACT_APP_API_URL=<TU_API_GATEWAY_URL>" > .env

# Instalar dependencias
npm install

# Construir
npm run build

# Desplegar a S3
aws s3 sync build/ s3://<TU_BUCKET_NAME> --delete
```

## Pruebas

### Probar API Gateway

```bash
# Obtener URL del API
API_URL=$(aws cloudformation describe-stacks \
  --stack-name ecommerce-resources \
  --query "Stacks[0].Outputs[?OutputKey=='ApiGatewayUrl'].OutputValue" \
  --output text)

# Ejecutar pruebas
./scripts/test-api.sh $API_URL
```

### Pruebas Individuales

```bash
# Health check
curl $API_URL/health

# Listar órdenes
curl $API_URL/orders

# Crear orden
curl -X POST $API_URL/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customerId": "cust-test",
    "customerName": "Test User",
    "customerEmail": "test@example.com",
    "items": [{"productId": "prod-101", "name": "Test Product", "quantity": 1, "price": 99.99}],
    "totalAmount": 99.99,
    "paymentMethod": "credit_card",
    "shippingAddress": {
      "street": "Test St 123",
      "city": "Madrid",
      "state": "Madrid",
      "zipCode": "28001",
      "country": "España"
    }
  }'
```

## Configurar SNS para Emails

Para recibir notificaciones por email:

```bash
# Obtener ARN del topic
SNS_TOPIC_ARN=$(aws cloudformation describe-stacks \
  --stack-name ecommerce-resources \
  --query "Stacks[0].Outputs[?OutputKey=='SNSTopicArn'].OutputValue" \
  --output text)

# Suscribir email
aws sns subscribe \
  --topic-arn $SNS_TOPIC_ARN \
  --protocol email \
  --notification-endpoint tu-email@example.com

# Confirmar suscripción en tu email
```

## Ejecutar Step Functions

```bash
# Obtener ARN de la state machine
STATE_MACHINE_ARN=$(aws cloudformation describe-stacks \
  --stack-name ecommerce-resources \
  --query "Stacks[0].Outputs[?OutputKey=='StateMachineArn'].OutputValue" \
  --output text)

# Ejecutar workflow
aws stepfunctions start-execution \
  --state-machine-arn $STATE_MACHINE_ARN \
  --input '{"orderId": "order-001"}'
```

## Monitoreo

### CloudWatch Logs

```bash
# Logs de Lambda App Server
aws logs tail /aws/lambda/app-server --follow

# Logs de Lambda Process Order
aws logs tail /aws/lambda/process-order --follow
```

### Métricas

- API Gateway: Requests, Latency, 4XX/5XX errors
- Lambda: Invocations, Duration, Errors
- DynamoDB: Read/Write capacity, Throttles
- Step Functions: Executions, Success/Failed

## Actualizar Código

### Actualizar Lambda

```bash
# Opción 1: Script automatizado (recomendado)
./scripts/update-lambdas.sh

# Opción 2: Manual
# App Server
cd lambdas/app-server
zip -r ../../app-server.zip index.py
aws s3 cp ../../app-server.zip s3://ecommerce-lambda-code-<ACCOUNT_ID>/app-server.zip
aws lambda update-function-code \
  --function-name app-server \
  --s3-bucket ecommerce-lambda-code-<ACCOUNT_ID> \
  --s3-key app-server.zip

# Process Order
cd ../process-order
zip -r ../../process-order.zip index.py
aws s3 cp ../../process-order.zip s3://ecommerce-lambda-code-<ACCOUNT_ID>/process-order.zip
aws lambda update-function-code \
  --function-name process-order \
  --s3-bucket ecommerce-lambda-code-<ACCOUNT_ID> \
  --s3-key process-order.zip
```

### Actualizar Frontend

```bash
cd frontend
npm run build
aws s3 sync build/ s3://<BUCKET_NAME> --delete

# Invalidar caché de CloudFront
DISTRIBUTION_ID=$(aws cloudfront list-distributions \
  --query "DistributionList.Items[?Origins.Items[?DomainName=='<BUCKET_NAME>.s3.amazonaws.com']].Id" \
  --output text)

aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*"
```

## Limpieza

Para eliminar todos los recursos:

```bash
./scripts/cleanup.sh
```

O manualmente:

```bash
# Vaciar bucket S3
aws s3 rm s3://<BUCKET_NAME> --recursive

# Eliminar stacks
aws cloudformation delete-stack --stack-name ecommerce-resources
aws cloudformation delete-stack --stack-name ecommerce-iam
```

## Costos Estimados

Con el tier gratuito de AWS:
- Lambda: Primeros 1M requests/mes gratis
- DynamoDB: 25GB storage gratis
- API Gateway: Primeros 1M requests/mes gratis
- S3: 5GB storage gratis
- CloudFront: 50GB transfer gratis

Después del tier gratuito: ~$10-50/mes dependiendo del tráfico

## Troubleshooting

### Error: Stack already exists
```bash
aws cloudformation delete-stack --stack-name <STACK_NAME>
aws cloudformation wait stack-delete-complete --stack-name <STACK_NAME>
```

### Error: Lambda timeout
Aumentar timeout en CloudFormation template (máximo 900 segundos)

### Error: DynamoDB throttling
Aumentar capacidad de lectura/escritura o cambiar a modo on-demand

### Error: CORS en API Gateway
Verificar que los headers CORS estén configurados en las respuestas Lambda

## Seguridad

- ✅ Roles IAM con permisos mínimos
- ✅ Encriptación en tránsito (HTTPS)
- ✅ Validación de entrada en Lambdas
- ⚠️ Agregar autenticación (Cognito) para producción
- ⚠️ Agregar WAF para protección DDoS
- ⚠️ Habilitar CloudTrail para auditoría

## Próximos Pasos

1. Agregar autenticación con Cognito
2. Implementar caché con ElastiCache
3. Agregar búsqueda con OpenSearch
4. Implementar CI/CD con CodePipeline
5. Agregar monitoreo con X-Ray
6. Implementar backup automático de DynamoDB
