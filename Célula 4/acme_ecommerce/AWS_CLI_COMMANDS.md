# Comandos AWS CLI Útiles

## 📋 Tabla de Contenidos
- [CloudFormation](#cloudformation)
- [Lambda](#lambda)
- [DynamoDB](#dynamodb)
- [API Gateway](#api-gateway)
- [S3](#s3)
- [SQS](#sqs)
- [SNS](#sns)
- [Step Functions](#step-functions)
- [CloudWatch](#cloudwatch)
- [IAM](#iam)

---

## CloudFormation

### Crear Stack
```bash
# Stack IAM
aws cloudformation create-stack \
  --stack-name ecommerce-iam \
  --template-body file://cloudformation/iam-stack.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

# Stack Resources
aws cloudformation create-stack \
  --stack-name ecommerce-resources \
  --template-body file://cloudformation/resources-stack.yaml \
  --parameters ParameterKey=IAMStackName,ParameterValue=ecommerce-iam \
  --region us-east-1
```

### Verificar Estado
```bash
# Listar stacks
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE

# Describir stack específico
aws cloudformation describe-stacks \
  --stack-name ecommerce-resources

# Ver eventos
aws cloudformation describe-stack-events \
  --stack-name ecommerce-resources \
  --max-items 20
```

### Esperar Completitud
```bash
# Esperar creación
aws cloudformation wait stack-create-complete \
  --stack-name ecommerce-resources

# Esperar actualización
aws cloudformation wait stack-update-complete \
  --stack-name ecommerce-resources

# Esperar eliminación
aws cloudformation wait stack-delete-complete \
  --stack-name ecommerce-resources
```

### Obtener Outputs
```bash
# Todos los outputs
aws cloudformation describe-stacks \
  --stack-name ecommerce-resources \
  --query 'Stacks[0].Outputs'

# Output específico
aws cloudformation describe-stacks \
  --stack-name ecommerce-resources \
  --query "Stacks[0].Outputs[?OutputKey=='ApiGatewayUrl'].OutputValue" \
  --output text
```

### Actualizar Stack
```bash
aws cloudformation update-stack \
  --stack-name ecommerce-resources \
  --template-body file://cloudformation/resources-stack.yaml \
  --parameters ParameterKey=IAMStackName,ParameterValue=ecommerce-iam
```

### Eliminar Stack
```bash
aws cloudformation delete-stack \
  --stack-name ecommerce-resources

aws cloudformation delete-stack \
  --stack-name ecommerce-iam
```

---

## Lambda

### Listar Funciones
```bash
aws lambda list-functions \
  --query 'Functions[*].[FunctionName,Runtime,LastModified]' \
  --output table
```

### Describir Función
```bash
aws lambda get-function \
  --function-name app-server

aws lambda get-function-configuration \
  --function-name app-server
```

### Invocar Función
```bash
# Invocación síncrona
aws lambda invoke \
  --function-name app-server \
  --payload '{"httpMethod":"GET","path":"/health"}' \
  response.json

cat response.json

# Invocación asíncrona
aws lambda invoke \
  --function-name process-order \
  --invocation-type Event \
  --payload '{"orderId":"order-001","action":"process_payment"}' \
  response.json
```

### Actualizar Código
```bash
# Desde archivo ZIP
cd lambdas/app-server
zip -r function.zip index.py

aws lambda update-function-code \
  --function-name app-server \
  --zip-file fileb://function.zip

# Desde S3
aws lambda update-function-code \
  --function-name app-server \
  --s3-bucket my-bucket \
  --s3-key lambda/app-server.zip
```

### Actualizar Configuración
```bash
# Timeout
aws lambda update-function-configuration \
  --function-name app-server \
  --timeout 60

# Memoria
aws lambda update-function-configuration \
  --function-name app-server \
  --memory-size 256

# Variables de entorno
aws lambda update-function-configuration \
  --function-name app-server \
  --environment Variables={QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789/queue}
```

### Ver Logs
```bash
# Últimos logs
aws logs tail /aws/lambda/app-server --follow

# Logs con filtro
aws logs filter-log-events \
  --log-group-name /aws/lambda/app-server \
  --filter-pattern "ERROR"

# Logs en rango de tiempo
aws logs filter-log-events \
  --log-group-name /aws/lambda/app-server \
  --start-time $(date -u -d '1 hour ago' +%s)000
```

### Métricas
```bash
# Invocaciones
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=app-server \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Errores
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=app-server \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

---

## DynamoDB

### Describir Tabla
```bash
aws dynamodb describe-table \
  --table-name Orders
```

### Listar Tablas
```bash
aws dynamodb list-tables
```

### Scan (Leer todos los items)
```bash
aws dynamodb scan \
  --table-name Orders \
  --max-items 10
```

### Query (Buscar por clave)
```bash
# Por primary key
aws dynamodb query \
  --table-name Orders \
  --key-condition-expression "orderId = :oid" \
  --expression-attribute-values '{":oid":{"S":"order-001"}}'

# Por GSI
aws dynamodb query \
  --table-name Orders \
  --index-name CustomerIndex \
  --key-condition-expression "customerId = :cid" \
  --expression-attribute-values '{":cid":{"S":"cust-001"}}'
```

### Get Item
```bash
aws dynamodb get-item \
  --table-name Orders \
  --key '{"orderId":{"S":"order-001"}}'
```

### Put Item
```bash
aws dynamodb put-item \
  --table-name Orders \
  --item '{
    "orderId": {"S": "order-test"},
    "customerId": {"S": "cust-test"},
    "customerName": {"S": "Test User"},
    "totalAmount": {"N": "99.99"},
    "status": {"S": "PENDING"},
    "orderDate": {"S": "2024-11-26T10:00:00Z"}
  }'
```

### Update Item
```bash
aws dynamodb update-item \
  --table-name Orders \
  --key '{"orderId":{"S":"order-001"}}' \
  --update-expression "SET #status = :status" \
  --expression-attribute-names '{"#status":"status"}' \
  --expression-attribute-values '{":status":{"S":"SHIPPED"}}'
```

### Delete Item
```bash
aws dynamodb delete-item \
  --table-name Orders \
  --key '{"orderId":{"S":"order-test"}}'
```

### Batch Write
```bash
aws dynamodb batch-write-item \
  --request-items file://batch-items.json
```

### Actualizar Capacidad
```bash
# Provisioned
aws dynamodb update-table \
  --table-name Orders \
  --provisioned-throughput ReadCapacityUnits=10,WriteCapacityUnits=10

# On-Demand
aws dynamodb update-table \
  --table-name Orders \
  --billing-mode PAY_PER_REQUEST
```

### Backup
```bash
# Crear backup
aws dynamodb create-backup \
  --table-name Orders \
  --backup-name orders-backup-$(date +%Y%m%d)

# Listar backups
aws dynamodb list-backups \
  --table-name Orders

# Restaurar backup
aws dynamodb restore-table-from-backup \
  --target-table-name Orders-Restored \
  --backup-arn arn:aws:dynamodb:us-east-1:123456789:table/Orders/backup/01234567890
```

---

## API Gateway

### Listar APIs
```bash
aws apigateway get-rest-apis
```

### Describir API
```bash
API_ID=$(aws apigateway get-rest-apis \
  --query 'items[?name==`ecommerce-api`].id' \
  --output text)

aws apigateway get-rest-api \
  --rest-api-id $API_ID
```

### Listar Resources
```bash
aws apigateway get-resources \
  --rest-api-id $API_ID
```

### Listar Stages
```bash
aws apigateway get-stages \
  --rest-api-id $API_ID
```

### Crear Deployment
```bash
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod \
  --description "Deployment $(date)"
```

### Ver Logs
```bash
aws logs tail /aws/apigateway/$API_ID/prod --follow
```

### Métricas
```bash
# Requests
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Count \
  --dimensions Name=ApiName,Value=ecommerce-api \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Latency
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Latency \
  --dimensions Name=ApiName,Value=ecommerce-api \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

---

## S3

### Listar Buckets
```bash
aws s3 ls
```

### Listar Contenido
```bash
aws s3 ls s3://ecommerce-frontend-123456789/
```

### Subir Archivo
```bash
aws s3 cp index.html s3://ecommerce-frontend-123456789/
```

### Subir Directorio
```bash
aws s3 sync frontend/build/ s3://ecommerce-frontend-123456789/ --delete
```

### Descargar Archivo
```bash
aws s3 cp s3://ecommerce-frontend-123456789/index.html ./
```

### Eliminar Archivo
```bash
aws s3 rm s3://ecommerce-frontend-123456789/old-file.js
```

### Vaciar Bucket
```bash
aws s3 rm s3://ecommerce-frontend-123456789/ --recursive
```

### Configurar Website
```bash
aws s3 website s3://ecommerce-frontend-123456789/ \
  --index-document index.html \
  --error-document error.html
```

### Ver Política
```bash
aws s3api get-bucket-policy \
  --bucket ecommerce-frontend-123456789
```

---

## SQS

### Listar Colas
```bash
aws sqs list-queues
```

### Obtener URL de Cola
```bash
QUEUE_URL=$(aws sqs get-queue-url \
  --queue-name order-processing-queue \
  --query 'QueueUrl' \
  --output text)
```

### Enviar Mensaje
```bash
aws sqs send-message \
  --queue-url $QUEUE_URL \
  --message-body '{"orderId":"order-001"}'
```

### Recibir Mensajes
```bash
aws sqs receive-message \
  --queue-url $QUEUE_URL \
  --max-number-of-messages 10 \
  --wait-time-seconds 20
```

### Eliminar Mensaje
```bash
aws sqs delete-message \
  --queue-url $QUEUE_URL \
  --receipt-handle <RECEIPT_HANDLE>
```

### Purgar Cola
```bash
aws sqs purge-queue \
  --queue-url $QUEUE_URL
```

### Ver Atributos
```bash
aws sqs get-queue-attributes \
  --queue-url $QUEUE_URL \
  --attribute-names All
```

---

## SNS

### Listar Topics
```bash
aws sns list-topics
```

### Crear Suscripción Email
```bash
TOPIC_ARN=$(aws sns list-topics \
  --query 'Topics[?contains(TopicArn,`order-notifications`)].TopicArn' \
  --output text)

aws sns subscribe \
  --topic-arn $TOPIC_ARN \
  --protocol email \
  --notification-endpoint tu-email@example.com
```

### Listar Suscripciones
```bash
aws sns list-subscriptions-by-topic \
  --topic-arn $TOPIC_ARN
```

### Publicar Mensaje
```bash
aws sns publish \
  --topic-arn $TOPIC_ARN \
  --subject "Test Message" \
  --message "This is a test notification"
```

### Eliminar Suscripción
```bash
aws sns unsubscribe \
  --subscription-arn <SUBSCRIPTION_ARN>
```

---

## Step Functions

### Listar State Machines
```bash
aws stepfunctions list-state-machines
```

### Describir State Machine
```bash
STATE_MACHINE_ARN=$(aws stepfunctions list-state-machines \
  --query 'stateMachines[?name==`order-processing-workflow`].stateMachineArn' \
  --output text)

aws stepfunctions describe-state-machine \
  --state-machine-arn $STATE_MACHINE_ARN
```

### Iniciar Ejecución
```bash
aws stepfunctions start-execution \
  --state-machine-arn $STATE_MACHINE_ARN \
  --input '{"orderId":"order-001"}'
```

### Listar Ejecuciones
```bash
aws stepfunctions list-executions \
  --state-machine-arn $STATE_MACHINE_ARN \
  --max-results 10
```

### Describir Ejecución
```bash
aws stepfunctions describe-execution \
  --execution-arn <EXECUTION_ARN>
```

### Ver Historial de Ejecución
```bash
aws stepfunctions get-execution-history \
  --execution-arn <EXECUTION_ARN>
```

### Detener Ejecución
```bash
aws stepfunctions stop-execution \
  --execution-arn <EXECUTION_ARN>
```

---

## CloudWatch

### Listar Log Groups
```bash
aws logs describe-log-groups
```

### Ver Logs en Tiempo Real
```bash
aws logs tail /aws/lambda/app-server --follow
```

### Filtrar Logs
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/app-server \
  --filter-pattern "ERROR" \
  --start-time $(date -u -d '1 hour ago' +%s)000
```

### Crear Alarma
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name lambda-errors \
  --alarm-description "Lambda errors > 10" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --dimensions Name=FunctionName,Value=app-server
```

### Listar Alarmas
```bash
aws cloudwatch describe-alarms
```

### Ver Métricas
```bash
aws cloudwatch list-metrics \
  --namespace AWS/Lambda
```

---

## IAM

### Listar Roles
```bash
aws iam list-roles \
  --query 'Roles[?contains(RoleName,`ecommerce`)].RoleName'
```

### Describir Role
```bash
aws iam get-role \
  --role-name ecommerce-app-server-role
```

### Ver Políticas Adjuntas
```bash
aws iam list-attached-role-policies \
  --role-name ecommerce-app-server-role
```

### Ver Política Inline
```bash
aws iam get-role-policy \
  --role-name ecommerce-app-server-role \
  --policy-name AppServerPolicy
```

---

## Comandos Útiles Combinados

### Obtener Todas las URLs del Proyecto
```bash
echo "=== URLs del Proyecto ==="
echo ""
echo "API Gateway:"
aws cloudformation describe-stacks \
  --stack-name ecommerce-resources \
  --query "Stacks[0].Outputs[?OutputKey=='ApiGatewayUrl'].OutputValue" \
  --output text
echo ""
echo "CloudFront:"
aws cloudformation describe-stacks \
  --stack-name ecommerce-resources \
  --query "Stacks[0].Outputs[?OutputKey=='CloudFrontUrl'].OutputValue" \
  --output text
echo ""
echo "S3 Bucket:"
aws cloudformation describe-stacks \
  --stack-name ecommerce-resources \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
  --output text
```

### Ver Estado de Todos los Recursos
```bash
echo "=== Estado de Recursos ==="
echo ""
echo "CloudFormation Stacks:"
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query 'StackSummaries[?contains(StackName,`ecommerce`)].{Name:StackName,Status:StackStatus}' \
  --output table
echo ""
echo "Lambda Functions:"
aws lambda list-functions \
  --query 'Functions[?contains(FunctionName,`app-server`) || contains(FunctionName,`process-order`)].{Name:FunctionName,Runtime:Runtime,Status:State}' \
  --output table
echo ""
echo "DynamoDB Tables:"
aws dynamodb list-tables \
  --query 'TableNames[?contains(@,`Orders`)]' \
  --output table
```

### Monitoreo Completo
```bash
# Script de monitoreo
watch -n 5 '
echo "=== Lambda Invocations (Last 5 min) ==="
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=app-server \
  --start-time $(date -u -d "5 minutes ago" +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Sum \
  --query "Datapoints[*].Sum" \
  --output text

echo ""
echo "=== Lambda Errors (Last 5 min) ==="
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=app-server \
  --start-time $(date -u -d "5 minutes ago" +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Sum \
  --query "Datapoints[*].Sum" \
  --output text
'
```

---

## Variables de Entorno Útiles

```bash
# Configurar región por defecto
export AWS_DEFAULT_REGION=us-east-1

# Configurar perfil
export AWS_PROFILE=default

# Configurar output format
export AWS_DEFAULT_OUTPUT=json

# Guardar ARNs comunes
export STATE_MACHINE_ARN=$(aws stepfunctions list-state-machines \
  --query 'stateMachines[?name==`order-processing-workflow`].stateMachineArn' \
  --output text)

export QUEUE_URL=$(aws sqs get-queue-url \
  --queue-name order-processing-queue \
  --query 'QueueUrl' \
  --output text)

export TOPIC_ARN=$(aws sns list-topics \
  --query 'Topics[?contains(TopicArn,`order-notifications`)].TopicArn' \
  --output text)
```

---

## Tips y Trucos

### Formato de Output
```bash
# JSON (default)
aws lambda list-functions --output json

# Tabla
aws lambda list-functions --output table

# Texto
aws lambda list-functions --output text

# YAML
aws lambda list-functions --output yaml
```

### Query con JMESPath
```bash
# Filtrar por nombre
aws lambda list-functions \
  --query 'Functions[?contains(FunctionName,`app`)].FunctionName'

# Múltiples campos
aws lambda list-functions \
  --query 'Functions[*].[FunctionName,Runtime,LastModified]'

# Primer elemento
aws lambda list-functions \
  --query 'Functions[0].FunctionName'
```

### Paginación
```bash
# Limitar resultados
aws dynamodb scan \
  --table-name Orders \
  --max-items 10

# Siguiente página
aws dynamodb scan \
  --table-name Orders \
  --max-items 10 \
  --starting-token <TOKEN>
```

### Dry Run
```bash
# Validar sin ejecutar
aws cloudformation create-stack \
  --stack-name test \
  --template-body file://template.yaml \
  --dry-run
```
