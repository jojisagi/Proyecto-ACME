# Cheatsheet de Comandos - Célula 3

Referencia rápida de comandos útiles para el proyecto.

## AWS CLI - Configuración

```bash
# Configurar perfiles
aws configure --profile build
aws configure --profile sandbox
aws configure --profile prod

# Verificar identidad
aws sts get-caller-identity --profile sandbox

# Listar perfiles configurados
cat ~/.aws/credentials

# Establecer perfil por defecto para sesión
export AWS_PROFILE=sandbox
```

## CloudFormation

```bash
# Validar template
aws cloudformation validate-template \
  --template-body file://iac/cloudformation-base.yaml

# Crear stack
aws cloudformation create-stack \
  --stack-name acme-image-handler-sandbox \
  --template-body file://iac/cloudformation-base.yaml \
  --parameters file://pipeline/parameters-sandbox.json \
  --capabilities CAPABILITY_NAMED_IAM

# Actualizar stack
aws cloudformation update-stack \
  --stack-name acme-image-handler-sandbox \
  --template-body file://iac/cloudformation-base.yaml \
  --parameters file://pipeline/parameters-sandbox.json \
  --capabilities CAPABILITY_NAMED_IAM

# Eliminar stack
aws cloudformation delete-stack \
  --stack-name acme-image-handler-sandbox

# Describir stack
aws cloudformation describe-stacks \
  --stack-name acme-image-handler-sandbox

# Ver outputs
aws cloudformation describe-stacks \
  --stack-name acme-image-handler-sandbox \
  --query 'Stacks[0].Outputs' \
  --output table

# Ver eventos
aws cloudformation describe-stack-events \
  --stack-name acme-image-handler-sandbox \
  --max-items 20

# Esperar a que complete
aws cloudformation wait stack-create-complete \
  --stack-name acme-image-handler-sandbox

# Listar todos los stacks
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE
```

## Lambda

```bash
# Listar funciones
aws lambda list-functions --query 'Functions[*].[FunctionName,Runtime,LastModified]' --output table

# Invocar función
aws lambda invoke \
  --function-name acme-image-handler-processor-sandbox \
  --payload '{"test": true}' \
  response.json

# Ver configuración
aws lambda get-function \
  --function-name acme-image-handler-processor-sandbox

# Actualizar código
aws lambda update-function-code \
  --function-name acme-image-handler-processor-sandbox \
  --zip-file fileb://function.zip

# Ver variables de entorno
aws lambda get-function-configuration \
  --function-name acme-image-handler-processor-sandbox \
  --query 'Environment'

# Ver métricas
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=acme-image-handler-processor-sandbox \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

## CloudWatch Logs

```bash
# Ver logs en tiempo real
aws logs tail /aws/lambda/acme-image-handler-processor-sandbox --follow

# Ver logs con filtro
aws logs tail /aws/lambda/acme-image-handler-processor-sandbox \
  --filter-pattern "ERROR" \
  --follow

# Listar log groups
aws logs describe-log-groups --query 'logGroups[*].logGroupName'

# Buscar en logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/acme-image-handler-processor-sandbox \
  --filter-pattern "ERROR" \
  --start-time $(date -u -d '1 hour ago' +%s)000

# Crear log group
aws logs create-log-group \
  --log-group-name /aws/lambda/my-function

# Establecer retención
aws logs put-retention-policy \
  --log-group-name /aws/lambda/acme-image-handler-processor-sandbox \
  --retention-in-days 30
```

## S3

```bash
# Listar buckets
aws s3 ls

# Listar contenido de bucket
aws s3 ls s3://acme-gadgets-raw-123456789-sandbox/

# Subir archivo
aws s3 cp image.jpg s3://acme-gadgets-raw-123456789-sandbox/TEST-001/

# Descargar archivo
aws s3 cp s3://acme-gadgets-processed-123456789-sandbox/TEST-001/image-id/original.jpg ./

# Sincronizar directorio
aws s3 sync ./data/test-images/ s3://acme-gadgets-raw-123456789-sandbox/TEST-BATCH/

# Eliminar archivo
aws s3 rm s3://acme-gadgets-raw-123456789-sandbox/TEST-001/image.jpg

# Vaciar bucket
aws s3 rm s3://acme-gadgets-raw-123456789-sandbox/ --recursive

# Ver propiedades
aws s3api head-object \
  --bucket acme-gadgets-processed-123456789-sandbox \
  --key TEST-001/image-id/original.jpg

# Generar presigned URL
aws s3 presign s3://acme-gadgets-processed-123456789-sandbox/image.jpg \
  --expires-in 900
```

## DynamoDB

```bash
# Listar tablas
aws dynamodb list-tables

# Describir tabla
aws dynamodb describe-table --table-name GadgetImages-sandbox

# Scan (listar todos los items)
aws dynamodb scan --table-name GadgetImages-sandbox --max-items 10

# Query por gadgetId
aws dynamodb query \
  --table-name GadgetImages-sandbox \
  --key-condition-expression "gadgetId = :gid" \
  --expression-attribute-values '{":gid":{"S":"TEST-001"}}'

# Get item
aws dynamodb get-item \
  --table-name GadgetImages-sandbox \
  --key '{"gadgetId":{"S":"TEST-001"},"imageId":{"S":"abc-123"}}'

# Put item
aws dynamodb put-item \
  --table-name GadgetImages-sandbox \
  --item file://item.json

# Delete item
aws dynamodb delete-item \
  --table-name GadgetImages-sandbox \
  --key '{"gadgetId":{"S":"TEST-001"},"imageId":{"S":"abc-123"}}'

# Contar items
aws dynamodb scan \
  --table-name GadgetImages-sandbox \
  --select COUNT
```

## Cognito

```bash
# Listar user pools
aws cognito-idp list-user-pools --max-results 10

# Describir user pool
aws cognito-idp describe-user-pool \
  --user-pool-id us-east-1_xxxxxxxxx

# Listar usuarios
aws cognito-idp list-users \
  --user-pool-id us-east-1_xxxxxxxxx

# Crear usuario
aws cognito-idp admin-create-user \
  --user-pool-id us-east-1_xxxxxxxxx \
  --username test@example.com \
  --user-attributes Name=email,Value=test@example.com Name=email_verified,Value=true \
  --temporary-password TempPass123!

# Establecer password permanente
aws cognito-idp admin-set-user-password \
  --user-pool-id us-east-1_xxxxxxxxx \
  --username test@example.com \
  --password Password123! \
  --permanent

# Eliminar usuario
aws cognito-idp admin-delete-user \
  --user-pool-id us-east-1_xxxxxxxxx \
  --username test@example.com

# Obtener usuario
aws cognito-idp admin-get-user \
  --user-pool-id us-east-1_xxxxxxxxx \
  --username test@example.com
```

## API Gateway

```bash
# Listar APIs
aws apigateway get-rest-apis

# Describir API
aws apigateway get-rest-api --rest-api-id xxxxx

# Listar recursos
aws apigateway get-resources --rest-api-id xxxxx

# Listar deployments
aws apigateway get-deployments --rest-api-id xxxxx

# Crear deployment
aws apigateway create-deployment \
  --rest-api-id xxxxx \
  --stage-name sandbox

# Ver logs
aws logs tail /aws/apigateway/xxxxx --follow
```

## VPC

```bash
# Listar VPCs
aws ec2 describe-vpcs

# Crear VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16

# Listar subnets
aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-xxxxx"

# Crear subnet
aws ec2 create-subnet \
  --vpc-id vpc-xxxxx \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a

# Listar VPC endpoints
aws ec2 describe-vpc-endpoints

# Crear VPC endpoint para S3
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-xxxxx \
  --service-name com.amazonaws.us-east-1.s3 \
  --route-table-ids rtb-xxxxx

# Listar security groups
aws ec2 describe-security-groups --filters "Name=vpc-id,Values=vpc-xxxxx"

# Listar NAT gateways
aws ec2 describe-nat-gateways
```

## IAM

```bash
# Listar roles
aws iam list-roles --query 'Roles[*].[RoleName,CreateDate]' --output table

# Describir role
aws iam get-role --role-name acme-image-handler-lambda-role-sandbox

# Listar políticas de un role
aws iam list-attached-role-policies \
  --role-name acme-image-handler-lambda-role-sandbox

# Ver política
aws iam get-policy --policy-arn arn:aws:iam::aws:policy/AWSLambdaBasicExecutionRole

# Listar usuarios
aws iam list-users

# Obtener caller identity
aws sts get-caller-identity
```

## CodePipeline

```bash
# Listar pipelines
aws codepipeline list-pipelines

# Ver estado del pipeline
aws codepipeline get-pipeline-state \
  --name acme-image-handler-pipeline

# Iniciar ejecución
aws codepipeline start-pipeline-execution \
  --name acme-image-handler-pipeline

# Ver ejecuciones
aws codepipeline list-pipeline-executions \
  --pipeline-name acme-image-handler-pipeline

# Ver detalles de ejecución
aws codepipeline get-pipeline-execution \
  --pipeline-name acme-image-handler-pipeline \
  --pipeline-execution-id xxxxx
```

## CodeBuild

```bash
# Listar proyectos
aws codebuild list-projects

# Iniciar build
aws codebuild start-build --project-name acme-image-handler-build

# Ver builds
aws codebuild list-builds-for-project \
  --project-name acme-image-handler-build

# Ver logs de build
aws codebuild batch-get-builds --ids xxxxx
```

## KMS

```bash
# Listar keys
aws kms list-keys

# Describir key
aws kms describe-key --key-id xxxxx

# Listar aliases
aws kms list-aliases

# Cifrar
aws kms encrypt \
  --key-id xxxxx \
  --plaintext "Hello World" \
  --output text \
  --query CiphertextBlob

# Descifrar
aws kms decrypt \
  --ciphertext-blob fileb://encrypted.txt \
  --output text \
  --query Plaintext | base64 --decode
```

## CloudWatch Alarms

```bash
# Listar alarmas
aws cloudwatch describe-alarms

# Crear alarma
aws cloudwatch put-metric-alarm \
  --alarm-name high-lambda-errors \
  --alarm-description "Lambda errors > 5%" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Average \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2

# Eliminar alarma
aws cloudwatch delete-alarms --alarm-names high-lambda-errors

# Ver historial de alarma
aws cloudwatch describe-alarm-history \
  --alarm-name high-lambda-errors \
  --max-records 10
```

## Costos

```bash
# Ver costos del mes actual
aws ce get-cost-and-usage \
  --time-period Start=$(date -u +%Y-%m-01),End=$(date -u +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE

# Ver forecast
aws ce get-cost-forecast \
  --time-period Start=$(date -u +%Y-%m-%d),End=$(date -u -d '+30 days' +%Y-%m-%d) \
  --metric BLENDED_COST \
  --granularity MONTHLY

# Listar budgets
aws budgets describe-budgets --account-id 123456789012
```

## Scripts del Proyecto

```bash
# Configurar cuentas
./setup/setup-accounts.sh

# Desplegar
./pipeline/deploy.sh sandbox
./pipeline/deploy.sh pre-prod
./pipeline/deploy.sh prod

# Crear usuario de prueba
./setup/create-test-user.sh sandbox

# Generar datos de prueba
cd tests
python3 generate-test-data.py

# Ejecutar pruebas
./tests/test-api.sh

# Ver estructura
tree -L 3 -I 'node_modules|venv|__pycache__'
```

## Pruebas con curl

```bash
# Variables
export API_URL="https://xxxxx.execute-api.us-east-1.amazonaws.com/sandbox"
export COGNITO_DOMAIN="acme-image-handler-sandbox-123456789"
export CLIENT_ID="xxxxxxxxxxxxxxxxxxxxx"
export USERNAME="test@example.com"
export PASSWORD="Password123!"

# Obtener token
TOKEN_RESPONSE=$(curl -s -X POST \
  "https://${COGNITO_DOMAIN}.auth.us-east-1.amazoncognito.com/oauth2/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&client_id=${CLIENT_ID}&username=${USERNAME}&password=${PASSWORD}")

JWT_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')

# Listar imágenes
curl -H "Authorization: Bearer ${JWT_TOKEN}" ${API_URL}/images | jq '.'

# Obtener URL de carga
curl -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"gadgetId": "TEST-001", "filename": "test.jpg"}' \
  ${API_URL}/upload-url | jq '.'

# Subir imagen
UPLOAD_URL="<presigned-url-from-previous-command>"
curl -X PUT "${UPLOAD_URL}" \
  -H "Content-Type: image/jpeg" \
  --data-binary "@image.jpg"

# Obtener imagen específica
curl -H "Authorization: Bearer ${JWT_TOKEN}" \
  ${API_URL}/images/<image-id> | jq '.'
```

## Troubleshooting

```bash
# Ver últimos errores en Lambda
aws logs filter-log-events \
  --log-group-name /aws/lambda/acme-image-handler-processor-sandbox \
  --filter-pattern "ERROR" \
  --start-time $(date -u -d '1 hour ago' +%s)000 \
  --query 'events[*].message' \
  --output text

# Ver stack events con errores
aws cloudformation describe-stack-events \
  --stack-name acme-image-handler-sandbox \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED` || ResourceStatus==`UPDATE_FAILED`]' \
  --output table

# Verificar conectividad de Lambda
aws lambda invoke \
  --function-name acme-image-handler-processor-sandbox \
  --payload '{"test": true}' \
  --log-type Tail \
  response.json \
  --query 'LogResult' \
  --output text | base64 --decode

# Ver métricas de API Gateway
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name 4XXError \
  --dimensions Name=ApiName,Value=acme-image-handler-api-sandbox \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

## Limpieza

```bash
# Vaciar buckets S3
aws s3 rm s3://acme-gadgets-raw-123456789-sandbox/ --recursive
aws s3 rm s3://acme-gadgets-processed-123456789-sandbox/ --recursive

# Eliminar stack
aws cloudformation delete-stack --stack-name acme-image-handler-sandbox

# Esperar a que se elimine
aws cloudformation wait stack-delete-complete \
  --stack-name acme-image-handler-sandbox

# Eliminar log groups
aws logs delete-log-group \
  --log-group-name /aws/lambda/acme-image-handler-processor-sandbox

# Eliminar VPC (si fue creada manualmente)
aws ec2 delete-vpc --vpc-id vpc-xxxxx
```

## Tips

```bash
# Usar jq para formatear JSON
aws cloudformation describe-stacks --stack-name acme-image-handler-sandbox | jq '.'

# Usar --query para filtrar
aws s3api list-buckets --query 'Buckets[?contains(Name, `acme`)].Name'

# Usar --output table para mejor visualización
aws dynamodb scan --table-name GadgetImages-sandbox --output table

# Guardar outputs en variables
API_URL=$(aws cloudformation describe-stacks \
  --stack-name acme-image-handler-sandbox \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text)

# Usar watch para monitorear
watch -n 5 'aws cloudformation describe-stacks --stack-name acme-image-handler-sandbox --query "Stacks[0].StackStatus"'
```
