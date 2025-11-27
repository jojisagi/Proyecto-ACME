# Guía de Pruebas - Sistema de Votación

Documentación completa de pruebas para validar el sistema.

## Tipos de Pruebas

### 1. Pruebas de Infraestructura

#### Validar Plantillas CloudFormation

```bash
# Validar stack IAM
aws cloudformation validate-template \
  --template-body file://cloudformation/iam-stack.yaml

# Validar stack principal
aws cloudformation validate-template \
  --template-body file://cloudformation/main-stack.yaml
```

#### Verificar Recursos Desplegados

```bash
# Listar recursos del stack
aws cloudformation describe-stack-resources \
  --stack-name gadget-voting-main

# Verificar estado del stack
aws cloudformation describe-stacks \
  --stack-name gadget-voting-main \
  --query 'Stacks[0].StackStatus'
```

### 2. Pruebas de Lambda

#### Probar EmitVote Localmente

```python
# test_emit_vote.py
import json
import os
os.environ['VOTES_TABLE'] = 'Votes'

from lambda.emit_vote.lambda_function import lambda_handler

event = {
    'requestContext': {
        'authorizer': {
            'claims': {
                'sub': 'test-user-123'
            }
        }
    },
    'body': json.dumps({'gadgetId': 'gadget-001'})
}

result = lambda_handler(event, None)
print(json.dumps(result, indent=2))
```

#### Probar GetResults

```bash
# Invocar Lambda directamente
aws lambda invoke \
  --function-name GadgetVoting-GetResults \
  --payload '{}' \
  response.json

cat response.json | python -m json.tool
```

#### Probar StreamProcessor

```bash
# Ver logs en tiempo real
aws logs tail /aws/lambda/GadgetVoting-StreamProcessor --follow

# Insertar voto de prueba y observar procesamiento
aws dynamodb put-item \
  --table-name Votes \
  --item '{
    "userId": {"S": "test-user-999"},
    "voteId": {"S": "VOTE"},
    "gadgetId": {"S": "gadget-001"},
    "timestamp": {"S": "2025-11-26T12:00:00Z"},
    "voteUuid": {"S": "test-uuid-123"}
  }'
```

### 3. Pruebas de API Gateway

#### Test Suite Completo

**Linux/Mac:**
```bash
cd tests
./test-api.sh
```

**Windows:**
```cmd
cd tests
test-api.bat
```

#### Pruebas Individuales

**GET /results (Sin autenticación)**
```bash
curl -X GET \
  https://YOUR-API-ENDPOINT/results \
  -H "Content-Type: application/json"
```

Respuesta esperada:
```json
{
  "results": [
    {
      "gadgetId": "gadget-001",
      "gadgetName": "SmartWatch Pro X",
      "totalVotes": 15,
      "percentage": 30.0
    }
  ],
  "totalVotes": 50
}
```

**POST /vote (Con autenticación)**
```bash
# Primero obtener token
ID_TOKEN=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id YOUR_CLIENT_ID \
  --auth-parameters USERNAME=test@example.com,PASSWORD=TestPassword123! \
  --query 'AuthenticationResult.IdToken' \
  --output text)

# Votar
curl -X POST \
  https://YOUR-API-ENDPOINT/vote \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ID_TOKEN}" \
  -d '{"gadgetId": "gadget-001"}'
```

Respuesta esperada (primera vez):
```json
{
  "message": "Voto registrado exitosamente",
  "gadgetId": "gadget-001",
  "timestamp": "2025-11-26T12:00:00.000000"
}
```

Respuesta esperada (segunda vez):
```json
{
  "error": "Usuario ya ha votado",
  "existingVote": "gadget-001"
}
```

**OPTIONS /vote (CORS)**
```bash
curl -X OPTIONS \
  https://YOUR-API-ENDPOINT/vote \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -v
```

Verificar headers:
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: POST,OPTIONS`
- `Access-Control-Allow-Headers: Content-Type,X-Amz-Date,Authorization...`

### 4. Pruebas de DynamoDB

#### Verificar Tabla Votes

```bash
# Contar votos
aws dynamodb scan \
  --table-name Votes \
  --select COUNT

# Ver votos de un usuario
aws dynamodb get-item \
  --table-name Votes \
  --key '{"userId": {"S": "user-001"}, "voteId": {"S": "VOTE"}}'
```

#### Verificar Tabla VoteResults

```bash
# Ver todos los resultados
aws dynamodb scan \
  --table-name VoteResults

# Ver resultado de un gadget específico
aws dynamodb get-item \
  --table-name VoteResults \
  --key '{"gadgetId": {"S": "gadget-001"}}'
```

#### Verificar DynamoDB Stream

```bash
# Listar streams
aws dynamodb describe-table \
  --table-name Votes \
  --query 'Table.LatestStreamArn'

# Ver event source mapping
aws lambda list-event-source-mappings \
  --function-name GadgetVoting-StreamProcessor
```

### 5. Pruebas de Cognito

#### Crear Usuario de Prueba

```bash
cd tests
./create-test-user.sh YOUR_USER_POOL_ID test@example.com TestPassword123!
```

#### Verificar Usuario

```bash
aws cognito-idp admin-get-user \
  --user-pool-id YOUR_USER_POOL_ID \
  --username test@example.com
```

#### Probar Autenticación

```bash
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id YOUR_CLIENT_ID \
  --auth-parameters USERNAME=test@example.com,PASSWORD=TestPassword123!
```

### 6. Pruebas de Frontend

#### Pruebas Manuales

1. **Registro de Usuario**
   - Abrir http://localhost:3000
   - Clic en "Registrarse"
   - Ingresar email y contraseña
   - Verificar mensaje de éxito

2. **Inicio de Sesión**
   - Ingresar credenciales
   - Verificar redirección al dashboard
   - Verificar nombre de usuario en header

3. **Votación**
   - Seleccionar un gadget
   - Verificar mensaje de confirmación
   - Verificar que no se puede votar de nuevo
   - Verificar actualización de resultados

4. **Resultados en Tiempo Real**
   - Observar actualización cada 3 segundos
   - Verificar gráfico de barras
   - Verificar top 3
   - Verificar porcentajes

5. **Cerrar Sesión**
   - Clic en "Cerrar Sesión"
   - Verificar redirección a login

#### Pruebas Automatizadas (Opcional)

```bash
cd frontend
npm test
```

### 7. Pruebas de Carga

#### Simular Múltiples Votos

```bash
# Script para crear 100 usuarios y votar
for i in {1..100}; do
  EMAIL="user${i}@test.com"
  PASSWORD="TestPass${i}!"
  
  # Crear usuario
  aws cognito-idp sign-up \
    --client-id $CLIENT_ID \
    --username $EMAIL \
    --password $PASSWORD \
    --user-attributes Name=email,Value=$EMAIL
  
  # Confirmar usuario
  aws cognito-idp admin-confirm-sign-up \
    --user-pool-id $USER_POOL_ID \
    --username $EMAIL
  
  # Obtener token
  TOKEN=$(aws cognito-idp initiate-auth \
    --auth-flow USER_PASSWORD_AUTH \
    --client-id $CLIENT_ID \
    --auth-parameters USERNAME=$EMAIL,PASSWORD=$PASSWORD \
    --query 'AuthenticationResult.IdToken' \
    --output text)
  
  # Votar (distribuir entre gadgets)
  GADGET_ID="gadget-00$((RANDOM % 10 + 1))"
  curl -X POST \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"gadgetId\": \"$GADGET_ID\"}" \
    $API_ENDPOINT/vote
  
  echo "Usuario $i votó por $GADGET_ID"
done
```

#### Monitorear Rendimiento

```bash
# Métricas de Lambda
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=GadgetVoting-EmitVote \
  --start-time 2025-11-26T00:00:00Z \
  --end-time 2025-11-26T23:59:59Z \
  --period 300 \
  --statistics Average,Maximum

# Métricas de API Gateway
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Latency \
  --dimensions Name=ApiName,Value=GadgetVotingAPI \
  --start-time 2025-11-26T00:00:00Z \
  --end-time 2025-11-26T23:59:59Z \
  --period 300 \
  --statistics Average,Maximum
```

### 8. Pruebas de Seguridad

#### Intentar Votar sin Token

```bash
curl -X POST \
  https://YOUR-API-ENDPOINT/vote \
  -H "Content-Type: application/json" \
  -d '{"gadgetId": "gadget-001"}'
```

Esperado: HTTP 401 Unauthorized

#### Intentar Votar con Token Inválido

```bash
curl -X POST \
  https://YOUR-API-ENDPOINT/vote \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer INVALID_TOKEN" \
  -d '{"gadgetId": "gadget-001"}'
```

Esperado: HTTP 401 Unauthorized

#### Intentar Votar por Gadget Inexistente

```bash
curl -X POST \
  https://YOUR-API-ENDPOINT/vote \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $VALID_TOKEN" \
  -d '{"gadgetId": "gadget-999"}'
```

Esperado: HTTP 201 (se permite, pero no afecta resultados)

### 9. Pruebas de Idempotencia

```bash
# Votar dos veces con el mismo usuario
TOKEN="YOUR_VALID_TOKEN"

# Primera vez
curl -X POST \
  https://YOUR-API-ENDPOINT/vote \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"gadgetId": "gadget-001"}'

# Segunda vez (debe fallar)
curl -X POST \
  https://YOUR-API-ENDPOINT/vote \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"gadgetId": "gadget-002"}'
```

Esperado:
- Primera vez: HTTP 201
- Segunda vez: HTTP 409 Conflict

### 10. Pruebas de Recuperación

#### Simular Fallo de Lambda

```bash
# Deshabilitar función
aws lambda update-function-configuration \
  --function-name GadgetVoting-EmitVote \
  --environment Variables={VOTES_TABLE=INVALID_TABLE}

# Intentar votar (debe fallar)
curl -X POST https://YOUR-API-ENDPOINT/vote ...

# Restaurar
aws lambda update-function-configuration \
  --function-name GadgetVoting-EmitVote \
  --environment Variables={VOTES_TABLE=Votes}
```

#### Verificar Dead Letter Queue (si está configurado)

```bash
aws sqs receive-message \
  --queue-url YOUR_DLQ_URL \
  --max-number-of-messages 10
```

## Checklist de Validación

### Pre-Despliegue
- [ ] Plantillas CloudFormation validadas
- [ ] Código Lambda sin errores de sintaxis
- [ ] Frontend compila sin errores
- [ ] Variables de entorno configuradas

### Post-Despliegue
- [ ] Stacks creados exitosamente
- [ ] Tablas DynamoDB creadas
- [ ] Lambdas desplegadas
- [ ] API Gateway accesible
- [ ] Cognito User Pool creado
- [ ] Datos de ejemplo poblados

### Funcionalidad
- [ ] Usuario puede registrarse
- [ ] Usuario puede iniciar sesión
- [ ] Usuario puede votar
- [ ] Voto se registra en DynamoDB
- [ ] Stream procesa voto
- [ ] Resultados se actualizan
- [ ] Dashboard muestra resultados
- [ ] Idempotencia funciona
- [ ] No se puede votar dos veces

### Seguridad
- [ ] Autenticación requerida para votar
- [ ] Tokens JWT validados
- [ ] CORS configurado correctamente
- [ ] Roles IAM con permisos mínimos
- [ ] No hay credenciales hardcodeadas

### Rendimiento
- [ ] Latencia < 1 segundo para votar
- [ ] Latencia < 500ms para resultados
- [ ] Stream procesa en < 5 segundos
- [ ] Frontend actualiza cada 3 segundos

## Troubleshooting

### Lambda Timeout
```bash
aws lambda update-function-configuration \
  --function-name FUNCTION_NAME \
  --timeout 60
```

### DynamoDB Throttling
```bash
# Cambiar a provisioned capacity
aws dynamodb update-table \
  --table-name Votes \
  --billing-mode PROVISIONED \
  --provisioned-throughput ReadCapacityUnits=10,WriteCapacityUnits=10
```

### API Gateway 5XX Errors
```bash
# Ver logs de API Gateway
aws logs tail /aws/apigateway/GadgetVotingAPI --follow
```

## Métricas de Éxito

- ✅ 100% de votos procesados
- ✅ 0 errores en Lambda
- ✅ < 1% de requests con error en API Gateway
- ✅ Latencia p99 < 2 segundos
- ✅ Disponibilidad > 99.9%

## Reportar Problemas

Si encuentras un problema durante las pruebas:
1. Captura logs relevantes
2. Documenta pasos para reproducir
3. Incluye versiones de software
4. Abre un issue en GitHub
