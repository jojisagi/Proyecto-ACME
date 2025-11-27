# Referencia Rápida de Comandos

Comandos útiles para gestionar el Sistema de Votación.

## 📦 Despliegue

### Despliegue Completo Automatizado

```bash
# Linux/Mac
cd scripts && ./deploy.sh

# Windows
cd scripts && deploy.bat
```

### Despliegue Manual Paso a Paso

```bash
# 1. Crear bucket S3
aws s3 mb s3://gadget-voting-lambda-code-UNIQUE-ID

# 2. Empaquetar Lambdas
cd scripts && ./package-lambdas.sh

# 3. Subir código a S3
aws s3 cp dist/lambda/ s3://YOUR-BUCKET/lambda/ --recursive

# 4. Desplegar stack IAM
aws cloudformation create-stack \
  --stack-name gadget-voting-iam \
  --template-body file://cloudformation/iam-stack.yaml \
  --capabilities CAPABILITY_NAMED_IAM

# 5. Esperar a que complete
aws cloudformation wait stack-create-complete \
  --stack-name gadget-voting-iam

# 6. Desplegar stack principal
aws cloudformation create-stack \
  --stack-name gadget-voting-main \
  --template-body file://cloudformation/main-stack.yaml \
  --parameters \
    ParameterKey=IamStackName,ParameterValue=gadget-voting-iam \
    ParameterKey=EmitVoteLambdaS3Bucket,ParameterValue=YOUR-BUCKET

# 7. Esperar a que complete
aws cloudformation wait stack-create-complete \
  --stack-name gadget-voting-main
```

## 🔍 Consultas y Verificación

### CloudFormation

```bash
# Listar todos los stacks
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE

# Ver detalles de un stack
aws cloudformation describe-stacks --stack-name gadget-voting-main

# Ver outputs del stack
aws cloudformation describe-stacks \
  --stack-name gadget-voting-main \
  --query 'Stacks[0].Outputs'

# Ver recursos del stack
aws cloudformation describe-stack-resources \
  --stack-name gadget-voting-main

# Ver eventos del stack (troubleshooting)
aws cloudformation describe-stack-events \
  --stack-name gadget-voting-main \
  --max-items 20
```

### Lambda

```bash
# Listar funciones Lambda
aws lambda list-functions --query 'Functions[?contains(FunctionName, `GadgetVoting`)].FunctionName'

# Ver configuración de una Lambda
aws lambda get-function --function-name GadgetVoting-EmitVote

# Ver variables de entorno
aws lambda get-function-configuration \
  --function-name GadgetVoting-EmitVote \
  --query 'Environment'

# Invocar Lambda directamente
aws lambda invoke \
  --function-name GadgetVoting-GetResults \
  --payload '{}' \
  response.json && cat response.json

# Ver métricas de Lambda
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=GadgetVoting-EmitVote \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

### DynamoDB

```bash
# Listar tablas
aws dynamodb list-tables

# Describir tabla
aws dynamodb describe-table --table-name Votes

# Contar items en tabla
aws dynamodb scan --table-name Votes --select COUNT

# Ver todos los votos
aws dynamodb scan --table-name Votes

# Ver resultados agregados
aws dynamodb scan --table-name VoteResults

# Ver voto de un usuario específico
aws dynamodb get-item \
  --table-name Votes \
  --key '{"userId": {"S": "user-001"}, "voteId": {"S": "VOTE"}}'

# Ver resultado de un gadget específico
aws dynamodb get-item \
  --table-name VoteResults \
  --key '{"gadgetId": {"S": "gadget-001"}}'

# Insertar voto manualmente (testing)
aws dynamodb put-item \
  --table-name Votes \
  --item '{
    "userId": {"S": "test-user-123"},
    "voteId": {"S": "VOTE"},
    "gadgetId": {"S": "gadget-001"},
    "timestamp": {"S": "2025-11-26T12:00:00Z"},
    "voteUuid": {"S": "test-uuid-123"}
  }'

# Actualizar contador manualmente (testing)
aws dynamodb update-item \
  --table-name VoteResults \
  --key '{"gadgetId": {"S": "gadget-001"}}' \
  --update-expression "ADD totalVotes :inc" \
  --expression-attribute-values '{":inc": {"N": "1"}}'
```

### API Gateway

```bash
# Listar APIs
aws apigateway get-rest-apis

# Ver detalles de API
aws apigateway get-rest-api --rest-api-id YOUR-API-ID

# Ver recursos (endpoints)
aws apigateway get-resources --rest-api-id YOUR-API-ID

# Ver métodos de un recurso
aws apigateway get-method \
  --rest-api-id YOUR-API-ID \
  --resource-id YOUR-RESOURCE-ID \
  --http-method POST

# Probar endpoint
curl -X GET https://YOUR-API-ID.execute-api.YOUR-REGION.amazonaws.com/prod/results
```

### Cognito

```bash
# Listar User Pools
aws cognito-idp list-user-pools --max-results 10

# Ver detalles del User Pool
aws cognito-idp describe-user-pool --user-pool-id YOUR-USER-POOL-ID

# Listar usuarios
aws cognito-idp list-users --user-pool-id YOUR-USER-POOL-ID

# Ver detalles de un usuario
aws cognito-idp admin-get-user \
  --user-pool-id YOUR-USER-POOL-ID \
  --username test@example.com

# Crear usuario
aws cognito-idp sign-up \
  --client-id YOUR-CLIENT-ID \
  --username test@example.com \
  --password TestPassword123! \
  --user-attributes Name=email,Value=test@example.com

# Confirmar usuario (bypass email verification)
aws cognito-idp admin-confirm-sign-up \
  --user-pool-id YOUR-USER-POOL-ID \
  --username test@example.com

# Autenticar y obtener token
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id YOUR-CLIENT-ID \
  --auth-parameters USERNAME=test@example.com,PASSWORD=TestPassword123!

# Eliminar usuario
aws cognito-idp admin-delete-user \
  --user-pool-id YOUR-USER-POOL-ID \
  --username test@example.com
```

## 📊 Logs y Monitoreo

### CloudWatch Logs

```bash
# Ver logs en tiempo real
aws logs tail /aws/lambda/GadgetVoting-EmitVote --follow

# Ver últimas 100 líneas
aws logs tail /aws/lambda/GadgetVoting-EmitVote --since 1h

# Buscar errores
aws logs filter-log-events \
  --log-group-name /aws/lambda/GadgetVoting-EmitVote \
  --filter-pattern "ERROR"

# Ver logs de todas las Lambdas
aws logs tail /aws/lambda/GadgetVoting-EmitVote --follow &
aws logs tail /aws/lambda/GadgetVoting-GetResults --follow &
aws logs tail /aws/lambda/GadgetVoting-StreamProcessor --follow &

# Listar log groups
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/GadgetVoting
```

### CloudWatch Metrics

```bash
# Métricas de Lambda - Invocaciones
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=GadgetVoting-EmitVote \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Métricas de Lambda - Errores
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=GadgetVoting-EmitVote \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Métricas de Lambda - Duración
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=GadgetVoting-EmitVote \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum

# Métricas de API Gateway
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Count \
  --dimensions Name=ApiName,Value=GadgetVotingAPI \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Métricas de DynamoDB
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=VoteResults \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

## 🧪 Testing

### Probar API con curl

```bash
# GET /results (público)
curl -X GET https://YOUR-API-ENDPOINT/results | python -m json.tool

# POST /vote (requiere token)
# Primero obtener token
ID_TOKEN=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id YOUR-CLIENT-ID \
  --auth-parameters USERNAME=test@example.com,PASSWORD=TestPassword123! \
  --query 'AuthenticationResult.IdToken' \
  --output text)

# Luego votar
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ID_TOKEN}" \
  -d '{"gadgetId": "gadget-001"}' \
  https://YOUR-API-ENDPOINT/vote

# Verificar CORS
curl -X OPTIONS \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -v \
  https://YOUR-API-ENDPOINT/vote
```

### Scripts de Prueba

```bash
# Test suite completo
cd tests && ./test-api.sh

# Crear usuario de prueba
cd tests && ./create-test-user.sh YOUR-USER-POOL-ID test@example.com TestPassword123!
```

## 🔄 Actualización

### Actualizar Código Lambda

```bash
# 1. Modificar código en lambda/*/lambda_function.py

# 2. Re-empaquetar
cd scripts && ./package-lambdas.sh

# 3. Subir a S3
aws s3 cp dist/lambda/ s3://YOUR-BUCKET/lambda/ --recursive

# 4. Actualizar función
aws lambda update-function-code \
  --function-name GadgetVoting-EmitVote \
  --s3-bucket YOUR-BUCKET \
  --s3-key lambda/emit-vote.zip
```

### Actualizar Stack CloudFormation

```bash
# Actualizar stack
aws cloudformation update-stack \
  --stack-name gadget-voting-main \
  --template-body file://cloudformation/main-stack.yaml \
  --parameters \
    ParameterKey=IamStackName,ParameterValue=gadget-voting-iam \
    ParameterKey=EmitVoteLambdaS3Bucket,ParameterValue=YOUR-BUCKET

# Esperar a que complete
aws cloudformation wait stack-update-complete \
  --stack-name gadget-voting-main
```

## 🗑️ Limpieza

### Limpieza Completa Automatizada

```bash
# Linux/Mac
cd scripts && ./cleanup.sh

# Windows
cd scripts && cleanup.bat
```

### Limpieza Manual

```bash
# 1. Eliminar stack principal
aws cloudformation delete-stack --stack-name gadget-voting-main
aws cloudformation wait stack-delete-complete --stack-name gadget-voting-main

# 2. Eliminar stack IAM
aws cloudformation delete-stack --stack-name gadget-voting-iam
aws cloudformation wait stack-delete-complete --stack-name gadget-voting-iam

# 3. Eliminar bucket S3
aws s3 rb s3://YOUR-BUCKET --force

# 4. Eliminar log groups (opcional)
aws logs delete-log-group --log-group-name /aws/lambda/GadgetVoting-EmitVote
aws logs delete-log-group --log-group-name /aws/lambda/GadgetVoting-GetResults
aws logs delete-log-group --log-group-name /aws/lambda/GadgetVoting-StreamProcessor
```

## 🔧 Troubleshooting

### Ver Errores de Stack

```bash
aws cloudformation describe-stack-events \
  --stack-name gadget-voting-main \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`]'
```

### Ver Errores de Lambda

```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/GadgetVoting-EmitVote \
  --filter-pattern "ERROR" \
  --start-time $(date -u -d '1 hour ago' +%s)000
```

### Verificar Event Source Mapping

```bash
aws lambda list-event-source-mappings \
  --function-name GadgetVoting-StreamProcessor
```

### Verificar DynamoDB Stream

```bash
aws dynamodb describe-table \
  --table-name Votes \
  --query 'Table.LatestStreamArn'
```

## 📱 Frontend

### Desarrollo Local

```bash
cd frontend
npm install
npm start
```

### Build para Producción

```bash
cd frontend
npm run build
```

### Desplegar a S3

```bash
# Crear bucket
aws s3 mb s3://gadget-voting-frontend

# Configurar como website
aws s3 website s3://gadget-voting-frontend \
  --index-document index.html

# Subir archivos
aws s3 sync build/ s3://gadget-voting-frontend --delete

# Hacer público
aws s3api put-bucket-policy \
  --bucket gadget-voting-frontend \
  --policy '{
    "Version": "2012-10-17",
    "Statement": [{
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::gadget-voting-frontend/*"
    }]
  }'
```

## 📊 Datos

### Poblar Datos de Ejemplo

```bash
cd scripts && ./populate-data.sh
```

### Limpiar Datos

```bash
# Vaciar tabla Votes
aws dynamodb scan --table-name Votes --attributes-to-get userId voteId \
  --query 'Items[*].[userId.S, voteId.S]' --output text | \
  while read userId voteId; do
    aws dynamodb delete-item --table-name Votes \
      --key "{\"userId\": {\"S\": \"$userId\"}, \"voteId\": {\"S\": \"$voteId\"}}"
  done

# Resetear contadores en VoteResults
aws dynamodb scan --table-name VoteResults --attributes-to-get gadgetId \
  --query 'Items[*].gadgetId.S' --output text | \
  while read gadgetId; do
    aws dynamodb update-item --table-name VoteResults \
      --key "{\"gadgetId\": {\"S\": \"$gadgetId\"}}" \
      --update-expression "SET totalVotes = :zero" \
      --expression-attribute-values '{":zero": {"N": "0"}}'
  done
```

## 🔐 Seguridad

### Rotar Credenciales

```bash
# Regenerar User Pool Client
aws cognito-idp create-user-pool-client \
  --user-pool-id YOUR-USER-POOL-ID \
  --client-name GadgetVotingClient-New \
  --generate-secret false \
  --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH
```

### Auditar Permisos IAM

```bash
# Ver política de un role
aws iam get-role-policy \
  --role-name GadgetVoting-EmitVote-Role \
  --policy-name EmitVotePolicy
```

## 💡 Tips Útiles

### Alias Útiles

```bash
# Agregar a ~/.bashrc o ~/.zshrc
alias gv-logs-emit='aws logs tail /aws/lambda/GadgetVoting-EmitVote --follow'
alias gv-logs-results='aws logs tail /aws/lambda/GadgetVoting-GetResults --follow'
alias gv-logs-stream='aws logs tail /aws/lambda/GadgetVoting-StreamProcessor --follow'
alias gv-results='curl https://YOUR-API-ENDPOINT/results | python -m json.tool'
alias gv-votes='aws dynamodb scan --table-name Votes --select COUNT'
```

### Watch Resultados en Tiempo Real

```bash
watch -n 3 'curl -s https://YOUR-API-ENDPOINT/results | python -m json.tool'
```

### Exportar Variables de Entorno

```bash
# Crear archivo .env
cat > .env << EOF
export AWS_REGION=us-east-1
export API_ENDPOINT=$(aws cloudformation describe-stacks --stack-name gadget-voting-main --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text)
export USER_POOL_ID=$(aws cloudformation describe-stacks --stack-name gadget-voting-main --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' --output text)
export CLIENT_ID=$(aws cloudformation describe-stacks --stack-name gadget-voting-main --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' --output text)
EOF

# Cargar variables
source .env
```

---

**Nota**: Reemplaza `YOUR-*` con tus valores reales obtenidos del despliegue.
