# API Reference - Sistema de Scheduling Serverless

## Base URL

```
https://{api-id}.execute-api.{region}.amazonaws.com/{stage}
```

Ejemplo:
```
https://abc123xyz.execute-api.us-east-1.amazonaws.com/production
```

## Autenticación

Todas las peticiones requieren un token JWT de Amazon Cognito en el header `Authorization`.

### Obtener Token JWT

```bash
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id {CLIENT_ID} \
  --auth-parameters USERNAME={username},PASSWORD={password} \
  --region {region}
```

**Respuesta:**
```json
{
  "AuthenticationResult": {
    "IdToken": "eyJraWQiOiJ...",
    "AccessToken": "eyJraWQiOiJ...",
    "RefreshToken": "eyJjdHkiOiJ...",
    "ExpiresIn": 3600,
    "TokenType": "Bearer"
  }
}
```

### Usar Token en Peticiones

```bash
curl -H "Authorization: Bearer {IdToken}" \
  https://api-endpoint/schedules
```

## Endpoints

### 1. Crear Schedule

Crea un nuevo schedule para generación automática de órdenes.

**Endpoint:** `POST /schedule`

**Headers:**
```
Authorization: Bearer {JWT_TOKEN}
Content-Type: application/json
```

**Request Body:**
```json
{
  "scheduleName": "rocket-shoes-hourly",
  "frequency": "rate(1 hour)",
  "gadgetType": "Rocket Shoes",
  "quantity": 100,
  "enabled": true
}
```

**Parámetros:**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| scheduleName | string | Sí | Nombre único del schedule |
| frequency | string | Sí | Expresión rate o cron |
| gadgetType | string | Sí | Tipo de gadget a ordenar |
| quantity | integer | Sí | Cantidad a ordenar |
| enabled | boolean | No | Estado inicial (default: true) |

**Expresiones de Frecuencia:**

- `rate(1 hour)` - Cada hora
- `rate(6 hours)` - Cada 6 horas
- `rate(1 day)` - Diariamente
- `cron(0 9 * * ? *)` - Todos los días a las 9 AM UTC
- `cron(0 0 * * MON *)` - Todos los lunes a medianoche

**Response:** `201 Created`
```json
{
  "message": "Schedule creado exitosamente",
  "schedule": {
    "scheduleId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "createdAt": "2025-11-27T10:30:00.000Z",
    "scheduleName": "rocket-shoes-hourly",
    "frequency": "rate(1 hour)",
    "gadgetType": "Rocket Shoes",
    "quantity": 100,
    "enabled": true,
    "status": "active"
  }
}
```

**Errores:**

- `400 Bad Request` - Parámetros inválidos
- `401 Unauthorized` - Token JWT inválido o expirado
- `409 Conflict` - Ya existe un schedule con ese nombre
- `500 Internal Server Error` - Error del servidor

---

### 2. Listar Schedules

Obtiene todos los schedules activos.

**Endpoint:** `GET /schedules`

**Headers:**
```
Authorization: Bearer {JWT_TOKEN}
```

**Response:** `200 OK`
```json
{
  "count": 2,
  "schedules": [
    {
      "scheduleId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "createdAt": "2025-11-27T10:30:00.000Z",
      "scheduleName": "rocket-shoes-hourly",
      "frequency": "rate(1 hour)",
      "gadgetType": "Rocket Shoes",
      "quantity": 100,
      "enabled": true,
      "status": "active"
    },
    {
      "scheduleId": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "createdAt": "2025-11-27T11:00:00.000Z",
      "scheduleName": "jetpack-daily",
      "frequency": "rate(1 day)",
      "gadgetType": "Jetpack",
      "quantity": 50,
      "enabled": true,
      "status": "active"
    }
  ],
  "eventBridgeSchedules": [
    {
      "Name": "rocket-shoes-hourly",
      "State": "ENABLED",
      "Arn": "arn:aws:scheduler:us-east-1:123456789012:schedule/default/rocket-shoes-hourly"
    }
  ]
}
```

**Errores:**

- `401 Unauthorized` - Token JWT inválido
- `500 Internal Server Error` - Error del servidor

---

### 3. Obtener Schedule Específico

Obtiene detalles de un schedule por su ID.

**Endpoint:** `GET /schedule/{scheduleId}`

**Headers:**
```
Authorization: Bearer {JWT_TOKEN}
```

**Path Parameters:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| scheduleId | string | UUID del schedule |

**Response:** `200 OK`
```json
{
  "schedule": {
    "scheduleId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "createdAt": "2025-11-27T10:30:00.000Z",
    "scheduleName": "rocket-shoes-hourly",
    "frequency": "rate(1 hour)",
    "gadgetType": "Rocket Shoes",
    "quantity": 100,
    "enabled": true,
    "status": "active",
    "eventBridgeDetails": {
      "state": "ENABLED",
      "arn": "arn:aws:scheduler:us-east-1:123456789012:schedule/default/rocket-shoes-hourly"
    }
  }
}
```

**Errores:**

- `401 Unauthorized` - Token JWT inválido
- `404 Not Found` - Schedule no encontrado
- `500 Internal Server Error` - Error del servidor

---

### 4. Cancelar Schedule

Cancela un schedule existente.

**Endpoint:** `DELETE /schedule/{scheduleId}`

**Headers:**
```
Authorization: Bearer {JWT_TOKEN}
```

**Path Parameters:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| scheduleId | string | UUID del schedule |

**Response:** `200 OK`
```json
{
  "message": "Schedule cancelado exitosamente",
  "scheduleId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Errores:**

- `401 Unauthorized` - Token JWT inválido
- `404 Not Found` - Schedule no encontrado
- `500 Internal Server Error` - Error del servidor

---

### 5. Consultar Órdenes

Obtiene las órdenes de compra generadas.

**Endpoint:** `GET /orders`

**Headers:**
```
Authorization: Bearer {JWT_TOKEN}
```

**Query Parameters:**

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| status | string | No | Filtrar por estado |
| limit | integer | No | Número máximo de resultados (default: 50) |

**Valores de Status:**
- `pending` - Pendiente
- `processing` - En proceso
- `completed` - Completada
- `shipped` - Enviada
- `delivered` - Entregada
- `cancelled` - Cancelada
- `failed` - Fallida

**Response:** `200 OK`
```json
{
  "count": 2,
  "orders": [
    {
      "orderId": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "createdAt": "2025-11-27T11:00:00.000Z",
      "scheduleId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "gadgetType": "Rocket Shoes",
      "quantity": 100,
      "unitPrice": 299.99,
      "subtotal": 29999.0,
      "discountRate": 0.15,
      "discountAmount": 4499.85,
      "total": 25499.15,
      "priority": "high",
      "supplier": "AcmeTech Footwear Inc.",
      "status": "pending",
      "estimatedDeliveryDays": 7,
      "metadata": {
        "generatedBy": "EventBridge Scheduler",
        "scheduleName": "rocket-shoes-hourly",
        "frequency": "rate(1 hour)"
      }
    }
  ]
}
```

**Ejemplos de Uso:**

```bash
# Todas las órdenes
GET /orders

# Órdenes pendientes
GET /orders?status=pending

# Primeras 10 órdenes
GET /orders?limit=10

# Órdenes completadas (máximo 20)
GET /orders?status=completed&limit=20
```

**Errores:**

- `401 Unauthorized` - Token JWT inválido
- `500 Internal Server Error` - Error del servidor

---

## Modelos de Datos

### Schedule Object

```json
{
  "scheduleId": "string (UUID)",
  "createdAt": "string (ISO 8601)",
  "scheduleName": "string",
  "frequency": "string (rate/cron expression)",
  "gadgetType": "string",
  "quantity": "integer",
  "enabled": "boolean",
  "status": "string (active|deleted)",
  "deletedAt": "string (ISO 8601, optional)"
}
```

### Order Object

```json
{
  "orderId": "string (UUID)",
  "createdAt": "string (ISO 8601)",
  "scheduleId": "string (UUID)",
  "gadgetType": "string",
  "quantity": "integer",
  "unitPrice": "number (Decimal)",
  "subtotal": "number (Decimal)",
  "discountRate": "number (Decimal)",
  "discountAmount": "number (Decimal)",
  "total": "number (Decimal)",
  "priority": "string (normal|medium|high)",
  "supplier": "string",
  "status": "string",
  "estimatedDeliveryDays": "integer",
  "metadata": {
    "generatedBy": "string",
    "scheduleName": "string",
    "frequency": "string"
  }
}
```

## Lógica de Negocio

### Cálculo de Descuentos

| Cantidad | Descuento |
|----------|-----------|
| 1-19 | 0% |
| 20-49 | 5% |
| 50-99 | 10% |
| 100+ | 15% |

### Prioridades

| Cantidad | Prioridad | Días de Entrega |
|----------|-----------|-----------------|
| 1-49 | normal | 21 |
| 50-99 | medium | 14 |
| 100+ | high | 7 |

### Precios Base por Gadget

| Gadget | Precio Unitario |
|--------|-----------------|
| Rocket Shoes | $299.99 |
| Jetpack | $4,999.99 |
| Laser Pointer | $49.99 |
| Invisible Cloak | $1,999.99 |
| Time Turner | $9,999.99 |
| Teleporter | $15,999.99 |
| Hoverboard | $899.99 |
| Smart Glasses | $399.99 |
| Drone | $599.99 |
| Robot Assistant | $2,499.99 |

## Códigos de Error

| Código | Descripción |
|--------|-------------|
| 200 | OK - Petición exitosa |
| 201 | Created - Recurso creado exitosamente |
| 400 | Bad Request - Parámetros inválidos |
| 401 | Unauthorized - Token JWT inválido o expirado |
| 403 | Forbidden - Sin permisos |
| 404 | Not Found - Recurso no encontrado |
| 409 | Conflict - Conflicto (ej: nombre duplicado) |
| 500 | Internal Server Error - Error del servidor |

## Rate Limits

- API Gateway: 10,000 requests/segundo (por defecto)
- Lambda: 1,000 invocaciones concurrentes (por defecto)
- DynamoDB: Sin límite (modo On-Demand)

## Ejemplos Completos

### Ejemplo 1: Crear y Consultar Schedule

```bash
# 1. Autenticar
AUTH_RESPONSE=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id abc123xyz \
  --auth-parameters USERNAME=testuser,PASSWORD=TempPass123!)

JWT_TOKEN=$(echo $AUTH_RESPONSE | jq -r '.AuthenticationResult.IdToken')

# 2. Crear schedule
curl -X POST "https://api-endpoint/schedule" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scheduleName": "daily-drone-order",
    "frequency": "cron(0 9 * * ? *)",
    "gadgetType": "Drone",
    "quantity": 75,
    "enabled": true
  }'

# 3. Listar schedules
curl -X GET "https://api-endpoint/schedules" \
  -H "Authorization: Bearer $JWT_TOKEN"

# 4. Consultar órdenes generadas
curl -X GET "https://api-endpoint/orders?status=pending" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### Ejemplo 2: Workflow Completo en Python

```python
import boto3
import requests
import json

# Autenticación
cognito = boto3.client('cognito-idp', region_name='us-east-1')
response = cognito.initiate_auth(
    ClientId='abc123xyz',
    AuthFlow='USER_PASSWORD_AUTH',
    AuthParameters={
        'USERNAME': 'testuser',
        'PASSWORD': 'TempPass123!'
    }
)

jwt_token = response['AuthenticationResult']['IdToken']
headers = {
    'Authorization': f'Bearer {jwt_token}',
    'Content-Type': 'application/json'
}

api_endpoint = 'https://api-endpoint'

# Crear schedule
schedule_data = {
    'scheduleName': 'hourly-jetpack',
    'frequency': 'rate(1 hour)',
    'gadgetType': 'Jetpack',
    'quantity': 50,
    'enabled': True
}

response = requests.post(
    f'{api_endpoint}/schedule',
    headers=headers,
    json=schedule_data
)

print(f'Schedule creado: {response.json()}')

# Listar schedules
response = requests.get(
    f'{api_endpoint}/schedules',
    headers=headers
)

schedules = response.json()
print(f'Total schedules: {schedules["count"]}')

# Consultar órdenes
response = requests.get(
    f'{api_endpoint}/orders?limit=10',
    headers=headers
)

orders = response.json()
print(f'Total órdenes: {orders["count"]}')
```

## Soporte

Para preguntas o problemas con la API:
- Revisar logs de CloudWatch
- Verificar formato de JWT token
- Consultar documentación de AWS EventBridge Scheduler
- Contactar al equipo de desarrollo
