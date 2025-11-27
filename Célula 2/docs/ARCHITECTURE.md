# Arquitectura del Sistema de Scheduling Serverless

## Visión General

Este sistema implementa una arquitectura serverless completa en AWS para la generación automática de órdenes de compra basada en schedules programados.

## Componentes Principales

### 1. API Gateway (REST API)
- **Propósito**: Punto de entrada HTTP para todas las operaciones
- **Autenticación**: Amazon Cognito User Pools (JWT)
- **Endpoints**:
  - `POST /schedule` - Crear nuevo schedule
  - `GET /schedules` - Listar schedules
  - `GET /schedule/{id}` - Obtener schedule específico
  - `DELETE /schedule/{id}` - Cancelar schedule
  - `GET /orders` - Consultar órdenes generadas

### 2. AWS Lambda Functions

#### Scheduler Manager (`acme-scheduler-manager`)
- **Runtime**: Python 3.11
- **Responsabilidades**:
  - Crear schedules en EventBridge Scheduler
  - Consultar schedules existentes
  - Cancelar schedules
  - Gestionar definiciones en DynamoDB
- **Triggers**: API Gateway
- **Permisos**:
  - EventBridge Scheduler (CRUD)
  - DynamoDB (Read/Write en ScheduleDefinitionsTable)
  - CloudWatch Logs
  - KMS (Encrypt/Decrypt)

#### Order Executor (`acme-order-executor`)
- **Runtime**: Python 3.11
- **Responsabilidades**:
  - Generar órdenes de compra automáticamente
  - Aplicar lógica de negocio (precios, descuentos, prioridades)
  - Almacenar órdenes en DynamoDB
- **Triggers**: EventBridge Scheduler
- **Permisos**:
  - DynamoDB (Read/Write en PurchaseOrdersTable)
  - CloudWatch Logs
  - KMS (Encrypt/Decrypt)

### 3. Amazon EventBridge Scheduler
- **Propósito**: Orquestación de ejecuciones programadas
- **Características**:
  - Soporta expresiones rate y cron
  - Invoca Order Executor Lambda según schedule
  - Flexible time windows
- **Ejemplos de Frecuencias**:
  - `rate(1 hour)` - Cada hora
  - `rate(6 hours)` - Cada 6 horas
  - `rate(1 day)` - Diariamente
  - `cron(0 9 * * ? *)` - Todos los días a las 9 AM UTC

### 4. Amazon DynamoDB

#### PurchaseOrdersTable
- **Partition Key**: `orderId` (String)
- **Sort Key**: `createdAt` (String)
- **GSI**: StatusIndex
  - Partition Key: `status`
  - Sort Key: `createdAt`
- **Atributos**:
  - orderId, createdAt, scheduleId
  - gadgetType, quantity, unitPrice
  - subtotal, discountRate, discountAmount, total
  - priority, supplier, status
  - estimatedDeliveryDays, metadata

#### ScheduleDefinitionsTable
- **Partition Key**: `scheduleId` (String)
- **Sort Key**: `createdAt` (String)
- **Atributos**:
  - scheduleId, createdAt, scheduleName
  - frequency, gadgetType, quantity
  - enabled, status

### 5. Amazon Cognito
- **User Pool**: Gestión de usuarios y autenticación
- **App Client**: Configuración para autenticación de aplicaciones
- **Flujo de Autenticación**: USER_PASSWORD_AUTH
- **Tokens**: JWT (ID Token) para autorización en API Gateway

### 6. AWS KMS
- **Propósito**: Cifrado de datos en reposo
- **Uso**:
  - Cifrado de tablas DynamoDB (SSE-KMS)
  - Cifrado de variables de entorno de Lambda
- **Política**: Acceso controlado para servicios y roles específicos

### 7. VPC y Networking

#### VPC Configuration
- **CIDR Block**: 10.0.0.0/16
- **Subredes Privadas**:
  - PrivateSubnet1: 10.0.1.0/24 (AZ 1)
  - PrivateSubnet2: 10.0.2.0/24 (AZ 2)

#### VPC Endpoints
- **DynamoDB Endpoint** (Gateway): Acceso privado a DynamoDB
- **CloudWatch Logs Endpoint** (Interface): Logs sin internet

#### Security Groups
- **LambdaSecurityGroup**: Permite tráfico saliente para Lambdas

## Flujo de Datos

### Creación de Schedule
```
Usuario → API Gateway → Cognito (Auth) → Scheduler Manager Lambda
                                              ↓
                                    EventBridge Scheduler
                                              ↓
                                    ScheduleDefinitionsTable (DynamoDB)
```

### Ejecución Automática de Orden
```
EventBridge Scheduler (Trigger) → Order Executor Lambda
                                         ↓
                                   Lógica de Negocio
                                         ↓
                                   PurchaseOrdersTable (DynamoDB)
```

### Consulta de Órdenes
```
Usuario → API Gateway → Cognito (Auth) → Scheduler Manager Lambda
                                              ↓
                                    PurchaseOrdersTable (DynamoDB)
                                              ↓
                                         Respuesta JSON
```

## Seguridad

### Capas de Seguridad

1. **Autenticación y Autorización**
   - JWT tokens de Cognito
   - Validación en API Gateway Authorizer
   - Políticas IAM de mínimo privilegio

2. **Cifrado**
   - En tránsito: TLS 1.2+ (API Gateway)
   - En reposo: KMS para DynamoDB y Lambda

3. **Red**
   - Lambdas en subredes privadas
   - VPC Endpoints para servicios AWS
   - Sin acceso directo a internet

4. **Auditoría**
   - CloudWatch Logs para todas las funciones
   - CloudTrail para operaciones de API

## Escalabilidad

- **API Gateway**: Escala automáticamente
- **Lambda**: Concurrencia automática (hasta 1000 por defecto)
- **DynamoDB**: Modo On-Demand (escala automática)
- **EventBridge Scheduler**: Soporta millones de schedules

## Monitoreo y Observabilidad

### CloudWatch Metrics
- Invocaciones de Lambda
- Errores y throttling
- Duración de ejecución
- Consumo de DynamoDB

### CloudWatch Logs
- Logs estructurados de Lambda
- Trazabilidad de requests
- Debugging de errores

### Alarmas Recomendadas
- Tasa de errores de Lambda > 5%
- Throttling de DynamoDB
- Latencia de API Gateway > 1s
- Errores de autenticación Cognito

## Costos Estimados (Mensual)

Basado en 10,000 órdenes/mes:

- **Lambda**: ~$5
- **DynamoDB**: ~$10 (On-Demand)
- **API Gateway**: ~$35
- **EventBridge Scheduler**: ~$10
- **CloudWatch**: ~$5
- **KMS**: ~$1
- **Cognito**: Gratis (< 50,000 MAU)

**Total Estimado**: ~$66/mes

## Mejoras Futuras

1. **Notificaciones**: SNS/SES para alertas de órdenes
2. **Validación**: Step Functions para workflows complejos
3. **Cache**: ElastiCache para consultas frecuentes
4. **Analytics**: Kinesis + Athena para análisis
5. **Multi-región**: Replicación global de DynamoDB
6. **CI/CD**: CodePipeline para despliegues automatizados
