# Quick Start Guide - Sistema de Scheduling Serverless

## 🚀 Inicio Rápido (5 minutos)

Esta guía te llevará desde cero hasta tener el sistema funcionando en AWS.

## Prerrequisitos

- AWS CLI configurado con credenciales válidas
- Python 3.9+
- Permisos de IAM para crear recursos

## Paso 1: Desplegar la Infraestructura

### En Windows (PowerShell):

```powershell
cd scheduling-system\scripts
.\deploy_stack.ps1
```

### En Linux/Mac (Bash):

```bash
cd scheduling-system/scripts
chmod +x *.sh
./deploy_stack.sh
```

⏱️ **Tiempo estimado**: 10-15 minutos

El script automáticamente:
- ✅ Despliega el stack de IAM
- ✅ Empaqueta las funciones Lambda
- ✅ Crea bucket S3 para artefactos
- ✅ Despliega el stack principal
- ✅ Actualiza el código de las Lambdas
- ✅ Muestra la información de configuración

## Paso 2: Crear Usuario de Prueba

Copia y ejecuta estos comandos (reemplaza los valores según tu despliegue):

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
  --user-attributes Name=email,Value=test@acme.com

# Establecer contraseña permanente
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username testuser \
  --password TempPass123! \
  --permanent
```

## Paso 3: Ejecutar Pruebas

### En Windows (PowerShell):

```powershell
.\curl_tests.ps1
```

### En Linux/Mac (Bash):

```bash
./curl_tests.sh
```

Verás la ejecución de:
- ✅ Autenticación con Cognito
- ✅ Creación de 2 schedules
- ✅ Consulta de schedules
- ✅ Consulta de órdenes
- ✅ Cancelación de schedule

## 🎯 Ejemplos de Uso

### Ejemplo 1: Crear Schedule para Rocket Shoes (Cada Hora)

```bash
# Obtener token JWT
AUTH_RESPONSE=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id YOUR_CLIENT_ID \
  --auth-parameters USERNAME=testuser,PASSWORD=TempPass123!)

JWT_TOKEN=$(echo $AUTH_RESPONSE | jq -r '.AuthenticationResult.IdToken')

# Crear schedule
curl -X POST "https://YOUR_API_ENDPOINT/schedule" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scheduleName": "rocket-shoes-hourly",
    "frequency": "rate(1 hour)",
    "gadgetType": "Rocket Shoes",
    "quantity": 100,
    "enabled": true
  }'
```

**Resultado esperado:**
```json
{
  "message": "Schedule creado exitosamente",
  "schedule": {
    "scheduleId": "a1b2c3d4-...",
    "scheduleName": "rocket-shoes-hourly",
    "frequency": "rate(1 hour)",
    "gadgetType": "Rocket Shoes",
    "quantity": 100,
    "status": "active"
  }
}
```

### Ejemplo 2: Crear Schedule para Jetpack (Diario a las 9 AM)

```bash
curl -X POST "https://YOUR_API_ENDPOINT/schedule" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scheduleName": "jetpack-daily-9am",
    "frequency": "cron(0 9 * * ? *)",
    "gadgetType": "Jetpack",
    "quantity": 50,
    "enabled": true
  }'
```

### Ejemplo 3: Listar Todos los Schedules

```bash
curl -X GET "https://YOUR_API_ENDPOINT/schedules" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**Resultado esperado:**
```json
{
  "count": 2,
  "schedules": [
    {
      "scheduleId": "...",
      "scheduleName": "rocket-shoes-hourly",
      "frequency": "rate(1 hour)",
      "gadgetType": "Rocket Shoes",
      "quantity": 100,
      "status": "active"
    },
    {
      "scheduleId": "...",
      "scheduleName": "jetpack-daily-9am",
      "frequency": "cron(0 9 * * ? *)",
      "gadgetType": "Jetpack",
      "quantity": 50,
      "status": "active"
    }
  ]
}
```

### Ejemplo 4: Consultar Órdenes Generadas

```bash
# Todas las órdenes
curl -X GET "https://YOUR_API_ENDPOINT/orders" \
  -H "Authorization: Bearer $JWT_TOKEN"

# Solo órdenes pendientes
curl -X GET "https://YOUR_API_ENDPOINT/orders?status=pending" \
  -H "Authorization: Bearer $JWT_TOKEN"

# Primeras 10 órdenes
curl -X GET "https://YOUR_API_ENDPOINT/orders?limit=10" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### Ejemplo 5: Cancelar un Schedule

```bash
# Reemplaza SCHEDULE_ID con el ID real
curl -X DELETE "https://YOUR_API_ENDPOINT/schedule/SCHEDULE_ID" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**Resultado esperado:**
```json
{
  "message": "Schedule cancelado exitosamente",
  "scheduleId": "a1b2c3d4-..."
}
```

## 🐍 Ejemplo en Python

```python
import boto3
import requests
import json

# Configuración
REGION = 'us-east-1'
CLIENT_ID = 'your-client-id'
API_ENDPOINT = 'https://your-api-endpoint'
USERNAME = 'testuser'
PASSWORD = 'TempPass123!'

# 1. Autenticación
cognito = boto3.client('cognito-idp', region_name=REGION)
auth_response = cognito.initiate_auth(
    ClientId=CLIENT_ID,
    AuthFlow='USER_PASSWORD_AUTH',
    AuthParameters={
        'USERNAME': USERNAME,
        'PASSWORD': PASSWORD
    }
)

jwt_token = auth_response['AuthenticationResult']['IdToken']
headers = {
    'Authorization': f'Bearer {jwt_token}',
    'Content-Type': 'application/json'
}

# 2. Crear schedule
schedule_data = {
    'scheduleName': 'python-test-schedule',
    'frequency': 'rate(6 hours)',
    'gadgetType': 'Drone',
    'quantity': 75,
    'enabled': True
}

response = requests.post(
    f'{API_ENDPOINT}/schedule',
    headers=headers,
    json=schedule_data
)

print('Schedule creado:')
print(json.dumps(response.json(), indent=2))

# 3. Listar schedules
response = requests.get(
    f'{API_ENDPOINT}/schedules',
    headers=headers
)

schedules = response.json()
print(f'\nTotal de schedules: {schedules["count"]}')

# 4. Consultar órdenes
response = requests.get(
    f'{API_ENDPOINT}/orders?limit=5',
    headers=headers
)

orders = response.json()
print(f'\nÓrdenes recientes: {orders["count"]}')
for order in orders['orders'][:3]:
    print(f'  - {order["gadgetType"]}: {order["quantity"]} unidades (${order["total"]})')
```

## 📊 Verificar el Sistema

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

### 3. Verificar Tablas DynamoDB

```bash
aws dynamodb list-tables \
  --query 'TableNames[?contains(@, `Orders`) || contains(@, `Schedule`)]'
```

Debe mostrar:
- PurchaseOrdersTable
- ScheduleDefinitionsTable

### 4. Ver Logs de Lambda

```bash
# Logs de Scheduler Manager
aws logs tail /aws/lambda/acme-scheduler-manager --follow

# Logs de Order Executor
aws logs tail /aws/lambda/acme-order-executor --follow
```

## 🔍 Monitoreo en Tiempo Real

### Ver Schedules en EventBridge

```bash
aws scheduler list-schedules \
  --query 'Schedules[*].[Name,State]' \
  --output table
```

### Consultar Órdenes en DynamoDB

```bash
aws dynamodb scan \
  --table-name PurchaseOrdersTable \
  --max-items 5 \
  --query 'Items[*].[orderId.S,gadgetType.S,quantity.N,status.S]' \
  --output table
```

### Ver Métricas de Lambda

```bash
# Invocaciones en la última hora
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=acme-order-executor \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum
```

## 🧹 Limpieza (Eliminar Todo)

Cuando termines de probar:

```bash
# Eliminar stack principal
aws cloudformation delete-stack --stack-name acme-scheduling-main
aws cloudformation wait stack-delete-complete --stack-name acme-scheduling-main

# Eliminar stack de IAM
aws cloudformation delete-stack --stack-name acme-scheduling-iam
aws cloudformation wait stack-delete-complete --stack-name acme-scheduling-iam

# Eliminar bucket S3 (opcional)
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws s3 rb "s3://acme-scheduling-artifacts-$ACCOUNT_ID" --force
```

## 💡 Tips y Trucos

### Tip 1: Guardar Variables de Entorno

Crea un archivo `.env` (no lo subas a Git):

```bash
export AWS_REGION=us-east-1
export API_ENDPOINT=https://abc123.execute-api.us-east-1.amazonaws.com/production
export USER_POOL_ID=us-east-1_ABC123
export CLIENT_ID=abc123xyz
export COGNITO_USERNAME=testuser
export COGNITO_PASSWORD=TempPass123!
```

Luego carga las variables:
```bash
source .env
```

### Tip 2: Alias Útiles

Agrega a tu `.bashrc` o `.zshrc`:

```bash
alias acme-logs-scheduler='aws logs tail /aws/lambda/acme-scheduler-manager --follow'
alias acme-logs-executor='aws logs tail /aws/lambda/acme-order-executor --follow'
alias acme-list-schedules='aws scheduler list-schedules --output table'
alias acme-list-orders='aws dynamodb scan --table-name PurchaseOrdersTable --max-items 10'
```

### Tip 3: Script de Autenticación Rápida

Guarda esto como `get-token.sh`:

```bash
#!/bin/bash
CLIENT_ID="your-client-id"
USERNAME="testuser"
PASSWORD="TempPass123!"

AUTH_RESPONSE=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id $CLIENT_ID \
  --auth-parameters USERNAME=$USERNAME,PASSWORD=$PASSWORD)

export JWT_TOKEN=$(echo $AUTH_RESPONSE | jq -r '.AuthenticationResult.IdToken')
echo "Token guardado en \$JWT_TOKEN"
echo "Expira en: $(echo $AUTH_RESPONSE | jq -r '.AuthenticationResult.ExpiresIn') segundos"
```

Uso:
```bash
source get-token.sh
curl -H "Authorization: Bearer $JWT_TOKEN" $API_ENDPOINT/schedules
```

## 📚 Recursos Adicionales

- **Documentación completa**: Ver `/docs` folder
- **Arquitectura**: `docs/ARCHITECTURE.md`
- **Guía de despliegue**: `docs/DEPLOYMENT_GUIDE.md`
- **Referencia de API**: `docs/API_REFERENCE.md`

## ❓ Preguntas Frecuentes

**P: ¿Cuánto cuesta ejecutar esto?**
R: Aproximadamente $66/mes para 10,000 órdenes. Ver `docs/ARCHITECTURE.md` para detalles.

**P: ¿Puedo cambiar la región?**
R: Sí, establece `export AWS_REGION=tu-region` antes de desplegar.

**P: ¿Cómo agrego más tipos de gadgets?**
R: Edita `src/order_executor/app.py` y actualiza los diccionarios `base_prices` y `suppliers`.

**P: ¿Puedo usar esto en producción?**
R: Sí, pero considera agregar:
- Monitoreo con CloudWatch Alarms
- Backup de DynamoDB
- CI/CD con CodePipeline
- Multi-región para alta disponibilidad

## 🎉 ¡Listo!

Ahora tienes un sistema serverless completo funcionando en AWS. Experimenta creando diferentes schedules y observa cómo se generan las órdenes automáticamente.

**¡Feliz coding!** 🚀
