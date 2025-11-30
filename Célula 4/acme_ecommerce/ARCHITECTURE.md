# Arquitectura E-commerce AWS Serverless

## Diagrama de Arquitectura

```
                                    ┌─────────────────┐
                                    │   CloudFront    │
                                    │      CDN        │
                                    └────────┬────────┘
                                             │
                        ┌────────────────────┼────────────────────┐
                        │                    │                    │
                   ┌────▼─────┐       ┌─────▼──────┐      ┌─────▼─────┐
                   │    S3    │       │    API     │      │  Static   │
                   │  Bucket  │       │  Gateway   │      │  Assets   │
                   │(Frontend)│       │   (REST)   │      └───────────┘
                   └──────────┘       └─────┬──────┘
                                             │
                                      ┌──────▼───────┐
                                      │   Lambda     │
                                      │ App Server   │
                                      │  (Python 3)  │
                                      └──┬────────┬──┘
                                         │        │
                              ┌──────────▼──┐  ┌─▼──────────┐
                              │  DynamoDB   │  │    SQS     │
                              │   Orders    │  │   Queue    │
                              │   Table     │  │            │
                              └─────────────┘  └─────┬──────┘
                                                     │
                                              ┌──────▼────────┐
                                              │     Step      │
                                              │  Functions    │
                                              │  Workflow     │
                                              └──────┬────────┘
                                                     │
                                    ┌────────────────┼────────────────┐
                                    │                │                │
                             ┌──────▼──────┐  ┌─────▼─────┐  ┌──────▼──────┐
                             │   Lambda    │  │  Payment  │  │  Shipment   │
                             │   Process   │  │  System   │  │   System    │
                             │   Order     │  │ (External)│  │  (External) │
                             └──────┬──────┘  └───────────┘  └─────────────┘
                                    │
                             ┌──────▼──────┐
                             │     SNS     │
                             │    Topic    │
                             │(Notifications)│
                             └──────┬──────┘
                                    │
                             ┌──────▼──────┐
                             │    Email    │
                             │   Cliente   │
                             └─────────────┘
```

## Componentes Principales

### 1. Frontend (React + S3 + CloudFront)

**Tecnología**: React 18, JavaScript ES6+

**Responsabilidades**:
- Interfaz de usuario para gestión de órdenes
- Comunicación con API Gateway
- Visualización de estados de órdenes

**Archivos**:
- `frontend/src/App.js` - Componente principal
- `frontend/src/components/OrderList.js` - Lista de órdenes
- `frontend/src/components/OrderForm.js` - Formulario de creación
- `frontend/src/components/OrderDetail.js` - Detalles de orden
- `frontend/src/services/api.js` - Cliente HTTP

**Despliegue**:
- Build estático en S3
- Distribución global vía CloudFront
- HTTPS obligatorio

### 2. API Gateway

**Tipo**: REST API

**Endpoints**:
```
GET  /health              - Health check
GET  /orders              - Listar órdenes
GET  /orders/{orderId}    - Obtener orden específica
POST /orders              - Crear nueva orden
```

**Características**:
- Validación de requests
- Throttling (10,000 requests/segundo)
- CORS habilitado
- Integración Lambda Proxy

### 3. Lambda: App Server

**Runtime**: Python 3.11

**Archivo**: `lambdas/app-server/index.py`

**Funciones**:
- `create_order()` - Crear orden en DynamoDB y enviar a SQS
- `get_orders()` - Listar órdenes (con filtro por cliente)
- `get_order()` - Obtener orden específica
- `health_check()` - Verificar estado del servicio

**Variables de Entorno**:
- `QUEUE_URL` - URL de la cola SQS

**Permisos IAM**:
- DynamoDB: GetItem, PutItem, Query, Scan
- SQS: SendMessage
- CloudWatch Logs: CreateLogGroup, CreateLogStream, PutLogEvents

**Timeout**: 30 segundos
**Memoria**: 128 MB

### 4. DynamoDB: Orders Table

**Tipo**: NoSQL (Document Store)

**Schema**:
```json
{
  "orderId": "string (HASH KEY)",
  "customerId": "string (GSI HASH KEY)",
  "customerName": "string",
  "customerEmail": "string",
  "orderDate": "string (ISO 8601) (GSI RANGE KEY)",
  "status": "string (PENDING|PAYMENT_PROCESSED|SHIPPED|DELIVERED)",
  "totalAmount": "number",
  "paymentMethod": "string",
  "items": [
    {
      "productId": "string",
      "name": "string",
      "quantity": "number",
      "price": "number"
    }
  ],
  "shippingAddress": {
    "street": "string",
    "city": "string",
    "state": "string",
    "zipCode": "string",
    "country": "string"
  },
  "paymentDate": "string (opcional)",
  "transactionId": "string (opcional)",
  "shipmentDate": "string (opcional)",
  "trackingNumber": "string (opcional)",
  "estimatedDeliveryDays": "number (opcional)",
  "deliveryDate": "string (opcional)"
}
```

**Índices**:
- Primary Key: `orderId` (HASH)
- GSI: `CustomerIndex`
  - HASH: `customerId`
  - RANGE: `orderDate`

**Capacidad**:
- Read: 5 RCU
- Write: 5 WCU
- Modo: Provisioned (cambiar a On-Demand para producción)

### 5. SQS: Order Processing Queue

**Tipo**: Standard Queue

**Configuración**:
- Visibility Timeout: 300 segundos
- Message Retention: 14 días
- Receive Wait Time: 20 segundos (Long Polling)

**Formato de Mensaje**:
```json
{
  "orderId": "order-001"
}
```

**Propósito**:
- Desacoplar creación de orden del procesamiento
- Buffer para picos de tráfico
- Garantizar procesamiento asíncrono

### 6. Step Functions: Order Workflow

**Archivo**: `step-functions/order-workflow.json`

**Estados**:

1. **ProcessPayment**
   - Invoca Lambda process-order con action=process_payment
   - Retry: 3 intentos con backoff exponencial
   - Timeout: 30 segundos
   - En error → PaymentFailed

2. **ArrangeShipment**
   - Invoca Lambda process-order con action=arrange_shipment
   - Retry: 2 intentos
   - Timeout: 30 segundos
   - En error → ShipmentFailed

3. **SendNotification**
   - Invoca Lambda process-order con action=send_notification
   - Retry: 2 intentos
   - En error → NotificationFailed (continúa)

4. **OrderCompleted** (Success)
5. **PaymentFailed** (Fail)
6. **ShipmentFailed** (Fail)

**Características**:
- Reintentos automáticos
- Manejo de errores
- Logging completo
- Visualización de ejecución

### 7. Lambda: Process Order

**Runtime**: Python 3.11

**Archivo**: `lambdas/process-order/index.py`

**Acciones**:

1. **process_payment**
   - Simula procesamiento de pago (90% éxito)
   - Actualiza estado a PAYMENT_PROCESSED
   - Genera transactionId
   - Registra paymentDate

2. **arrange_shipment**
   - Genera tracking number
   - Calcula fecha estimada de entrega
   - Actualiza estado a SHIPPED
   - Registra shipmentDate

3. **send_notification**
   - Obtiene detalles de orden
   - Genera mensaje de confirmación
   - Publica a SNS Topic
   - Registra notificationSentDate

**Variables de Entorno**:
- `SNS_TOPIC_ARN` - ARN del topic SNS

**Permisos IAM**:
- DynamoDB: GetItem, UpdateItem
- SNS: Publish
- CloudWatch Logs: CreateLogGroup, CreateLogStream, PutLogEvents

**Timeout**: 30 segundos
**Memoria**: 128 MB

### 8. SNS: Order Notifications

**Tipo**: Standard Topic

**Protocolo**: Email, SMS (configurable)

**Formato de Mensaje**:
```
Subject: Order Confirmation - {orderId}

Body:
Order Confirmation - E-commerce Store

Dear {customerName},

Thank you for your order!

Order Details:
--------------
Order ID: {orderId}
Order Date: {orderDate}
Status: {status}

Items:
- {item.name} x{item.quantity} - ${item.price}

Total Amount: ${totalAmount}

Shipping Address:
{address}

Tracking Number: {trackingNumber}
Estimated Delivery: {estimatedDeliveryDays} business days

Thank you for shopping with us!
```

**Suscripciones**:
- Email (requiere confirmación)
- SMS (opcional)
- Lambda (para procesamiento adicional)

## Flujo de Datos

### Flujo 1: Crear Orden

```
1. Usuario → Frontend (React)
2. Frontend → API Gateway (POST /orders)
3. API Gateway → Lambda App Server
4. Lambda App Server → DynamoDB (PutItem)
5. Lambda App Server → SQS (SendMessage)
6. Lambda App Server → API Gateway (Response 201)
7. API Gateway → Frontend (Order Created)
```

### Flujo 2: Procesar Orden

```
1. SQS Queue → Step Functions (Trigger)
2. Step Functions → Lambda Process Order (process_payment)
3. Lambda → DynamoDB (UpdateItem: PAYMENT_PROCESSED)
4. Step Functions → Lambda Process Order (arrange_shipment)
5. Lambda → DynamoDB (UpdateItem: SHIPPED)
6. Step Functions → Lambda Process Order (send_notification)
7. Lambda → DynamoDB (GetItem)
8. Lambda → SNS (Publish)
9. SNS → Email Cliente
```

### Flujo 3: Consultar Órdenes

```
1. Usuario → Frontend (React)
2. Frontend → API Gateway (GET /orders)
3. API Gateway → Lambda App Server
4. Lambda App Server → DynamoDB (Scan/Query)
5. Lambda App Server → API Gateway (Response 200)
6. API Gateway → Frontend (Orders List)
```

## Seguridad

### IAM Roles

**AppServerLambdaRole**:
- Acceso a DynamoDB Orders table
- Envío de mensajes a SQS
- Escritura de logs a CloudWatch

**ProcessOrderLambdaRole**:
- Lectura/escritura en DynamoDB Orders table
- Publicación en SNS topic
- Escritura de logs a CloudWatch

**StepFunctionsRole**:
- Invocación de Lambda functions
- Lectura/eliminación de mensajes SQS
- Publicación en SNS topic

### Encriptación

- **En tránsito**: HTTPS/TLS 1.2+
- **En reposo**: 
  - DynamoDB: Encriptación por defecto
  - S3: Encriptación AES-256
  - SQS: Encriptación opcional

### Validación

- API Gateway: Validación de esquema JSON
- Lambda: Validación de campos requeridos
- DynamoDB: Validación de tipos

## Escalabilidad

### Límites Actuales

- API Gateway: 10,000 requests/segundo
- Lambda: 1,000 ejecuciones concurrentes
- DynamoDB: 5 RCU / 5 WCU (ajustable)
- SQS: Ilimitado

### Estrategias de Escalado

1. **DynamoDB**: Cambiar a modo On-Demand
2. **Lambda**: Aumentar concurrencia reservada
3. **API Gateway**: Implementar caché
4. **CloudFront**: Caché de contenido estático

## Monitoreo

### Métricas Clave

**API Gateway**:
- Count (requests)
- Latency (p50, p95, p99)
- 4XXError, 5XXError

**Lambda**:
- Invocations
- Duration
- Errors
- Throttles
- ConcurrentExecutions

**DynamoDB**:
- ConsumedReadCapacityUnits
- ConsumedWriteCapacityUnits
- UserErrors
- SystemErrors

**Step Functions**:
- ExecutionsStarted
- ExecutionsSucceeded
- ExecutionsFailed
- ExecutionTime

### Alarmas Recomendadas

1. Lambda Errors > 10 en 5 minutos
2. API Gateway 5XX > 5% en 5 minutos
3. DynamoDB Throttles > 0
4. Step Functions Failed > 3 en 10 minutos

## Costos

### Estimación Mensual (después del tier gratuito)

**Escenario**: 100,000 órdenes/mes

- **Lambda**: $0.20 (1M invocations)
- **API Gateway**: $3.50 (1M requests)
- **DynamoDB**: $1.25 (5 RCU/WCU)
- **S3**: $0.50 (10GB storage)
- **CloudFront**: $8.50 (100GB transfer)
- **SQS**: $0.40 (1M requests)
- **SNS**: $0.50 (100K emails)
- **Step Functions**: $2.50 (100K transitions)

**Total**: ~$17.35/mes

### Optimizaciones de Costo

1. Usar Lambda con arquitectura ARM (Graviton2) - 20% más barato
2. DynamoDB On-Demand solo si tráfico variable
3. CloudFront con caché agresivo
4. S3 Intelligent-Tiering para archivos antiguos
5. Reserved Capacity para cargas predecibles

## Mejoras Futuras

### Corto Plazo
- [ ] Agregar autenticación con Cognito
- [ ] Implementar paginación en lista de órdenes
- [ ] Agregar filtros avanzados
- [ ] Implementar caché con ElastiCache

### Mediano Plazo
- [ ] Búsqueda full-text con OpenSearch
- [ ] Notificaciones en tiempo real con WebSockets
- [ ] Dashboard de analytics
- [ ] Sistema de recomendaciones

### Largo Plazo
- [ ] Multi-región con DynamoDB Global Tables
- [ ] Machine Learning para detección de fraude
- [ ] Integración con sistemas de inventario
- [ ] Programa de lealtad y puntos
