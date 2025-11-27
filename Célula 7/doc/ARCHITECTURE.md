# Arquitectura del Sistema de Votación - Gadget del Año

## Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USUARIOS (Navegador)                         │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   React Frontend        │
                    │   (Dashboard Tiempo     │
                    │    Real)                │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Amazon Cognito        │
                    │   (Autenticación)       │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   API Gateway           │
                    │   REST API              │
                    │   - POST /vote          │
                    │   - GET /results        │
                    └──────┬──────────┬───────┘
                           │          │
              ┌────────────▼──┐   ┌──▼────────────┐
              │ Lambda        │   │ Lambda        │
              │ EmitVote      │   │ GetResults    │
              │ (Escritura)   │   │ (Lectura)     │
              └───────┬───────┘   └───────┬───────┘
                      │                   │
         ┌────────────▼────────┐   ┌──────▼──────────┐
         │ DynamoDB            │   │ DynamoDB        │
         │ Tabla: Votes        │   │ Tabla:          │
         │ - userId (PK)       │   │ VoteResults     │
         │ - voteId (SK)       │   │ - gadgetId (PK) │
         │ - gadgetId          │   │ - totalVotes    │
         │ - timestamp         │   │ - gadgetName    │
         └──────────┬──────────┘   └─────────────────┘
                    │                      ▲
         ┌──────────▼──────────┐          │
         │ DynamoDB Streams    │          │
         │ (NEW_IMAGE)         │          │
         └──────────┬──────────┘          │
                    │                      │
         ┌──────────▼──────────┐          │
         │ Lambda              │          │
         │ StreamProcessor     │──────────┘
         │ (Agregación)        │
         └─────────────────────┘
```

## Flujos de Datos

### 1. Flujo de Votación (Write Path)

```
Usuario → Frontend → API Gateway → Lambda EmitVote → DynamoDB Votes
                                         ↓
                                   Validaciones:
                                   - Token Cognito
                                   - Voto único
                                   - Gadget válido
```

**Pasos detallados:**
1. Usuario autenticado hace clic en un gadget
2. Frontend envía POST /vote con token JWT
3. API Gateway valida token con Cognito Authorizer
4. Lambda EmitVote:
   - Extrae userId del token
   - Verifica si ya votó (consulta DynamoDB)
   - Si no ha votado, inserta registro en tabla Votes
5. Retorna confirmación al usuario

### 2. Flujo de Agregación (Async Processing)

```
DynamoDB Votes → DynamoDB Stream → Lambda StreamProcessor → DynamoDB VoteResults
                                          ↓
                                    Actualización
                                    Atómica (ADD)
```

**Pasos detallados:**
1. Nuevo voto insertado en tabla Votes
2. DynamoDB Stream captura el evento (NEW_IMAGE)
3. Lambda StreamProcessor se dispara automáticamente
4. Extrae gadgetId del evento
5. Ejecuta UPDATE con ADD para incrementar contador atómicamente
6. VoteResults se actualiza en tiempo real

### 3. Flujo de Consulta (Read Path)

```
Usuario → Frontend → API Gateway → Lambda GetResults → DynamoDB VoteResults
                                                              ↓
                                                        Scan completo
                                                        Ordenar por votos
                                                        Calcular %
```

**Pasos detallados:**
1. Frontend consulta GET /results cada 3 segundos
2. API Gateway (sin autenticación requerida)
3. Lambda GetResults:
   - Escanea tabla VoteResults
   - Ordena por totalVotes descendente
   - Calcula porcentajes
4. Retorna JSON con resultados
5. Frontend actualiza dashboard en tiempo real

## Componentes AWS

### 1. Amazon Cognito
- **Propósito**: Autenticación y autorización de usuarios
- **Configuración**:
  - User Pool para gestión de usuarios
  - Email como username
  - Verificación de email
  - Client sin secret (para aplicaciones públicas)

### 2. API Gateway
- **Tipo**: REST API
- **Endpoints**:
  - `POST /vote` - Requiere autenticación Cognito
  - `GET /results` - Público
  - `OPTIONS /*` - CORS habilitado
- **Integración**: AWS_PROXY con Lambda

### 3. AWS Lambda

#### EmitVote
- **Runtime**: Python 3.11
- **Memoria**: 128 MB
- **Timeout**: 30 segundos
- **Permisos**: PutItem, GetItem en tabla Votes
- **Variables de entorno**:
  - `VOTES_TABLE`: Nombre de tabla Votes

#### GetResults
- **Runtime**: Python 3.11
- **Memoria**: 128 MB
- **Timeout**: 30 segundos
- **Permisos**: Scan, Query en tabla VoteResults
- **Variables de entorno**:
  - `RESULTS_TABLE`: Nombre de tabla VoteResults

#### StreamProcessor
- **Runtime**: Python 3.11
- **Memoria**: 256 MB
- **Timeout**: 60 segundos
- **Permisos**: 
  - Leer DynamoDB Streams de tabla Votes
  - UpdateItem en tabla VoteResults
- **Event Source**: DynamoDB Stream (batch size: 100)
- **Variables de entorno**:
  - `RESULTS_TABLE`: Nombre de tabla VoteResults

### 4. DynamoDB

#### Tabla Votes
- **Propósito**: Registro de auditoría de cada voto
- **Billing Mode**: PAY_PER_REQUEST
- **Clave Primaria**:
  - Partition Key: `userId` (String)
  - Sort Key: `voteId` (String) - Siempre "VOTE"
- **Atributos**:
  - `gadgetId`: ID del gadget votado
  - `timestamp`: Fecha/hora del voto
  - `voteUuid`: UUID único del voto
- **Stream**: Habilitado (NEW_IMAGE)
- **Patrón de acceso**: 
  - Escritura: 1 voto por usuario
  - Lectura: Verificación de voto existente

#### Tabla VoteResults
- **Propósito**: Contadores agregados para lectura rápida
- **Billing Mode**: PAY_PER_REQUEST
- **Clave Primaria**:
  - Partition Key: `gadgetId` (String)
- **Atributos**:
  - `gadgetName`: Nombre del gadget
  - `totalVotes`: Contador de votos (Number)
- **Patrón de acceso**:
  - Escritura: Actualizaciones atómicas (ADD)
  - Lectura: Scan completo (10 items)

### 5. IAM Roles

#### EmitVote Role
```json
{
  "Effect": "Allow",
  "Action": [
    "dynamodb:PutItem",
    "dynamodb:GetItem"
  ],
  "Resource": "arn:aws:dynamodb:*:*:table/Votes"
}
```

#### GetResults Role
```json
{
  "Effect": "Allow",
  "Action": [
    "dynamodb:Scan",
    "dynamodb:Query"
  ],
  "Resource": "arn:aws:dynamodb:*:*:table/VoteResults"
}
```

#### StreamProcessor Role
```json
{
  "Effect": "Allow",
  "Action": [
    "dynamodb:GetRecords",
    "dynamodb:GetShardIterator",
    "dynamodb:DescribeStream",
    "dynamodb:ListStreams"
  ],
  "Resource": "arn:aws:dynamodb:*:*:table/Votes/stream/*"
},
{
  "Effect": "Allow",
  "Action": ["dynamodb:UpdateItem"],
  "Resource": "arn:aws:dynamodb:*:*:table/VoteResults"
}
```

## Características de Seguridad

### 1. Autenticación
- JWT tokens de Cognito
- Validación en API Gateway Authorizer
- Tokens con expiración

### 2. Autorización
- Roles IAM con permisos mínimos (Least Privilege)
- Separación de roles por función (lectura/escritura)
- No hay credenciales hardcodeadas

### 3. Idempotencia
- Verificación de voto único por usuario
- Clave compuesta (userId + voteId) previene duplicados
- Respuesta 409 Conflict si ya votó

### 4. CORS
- Configurado en API Gateway
- Permite requests desde frontend
- Headers apropiados en respuestas Lambda

## Escalabilidad

### Capacidad
- **DynamoDB**: PAY_PER_REQUEST escala automáticamente
- **Lambda**: Concurrencia hasta 1000 por defecto
- **API Gateway**: 10,000 requests/segundo por defecto
- **Cognito**: 50,000 MAU gratis

### Optimizaciones
- Tabla VoteResults optimizada para lectura
- Agregación asíncrona vía Streams
- Sin joins ni transacciones complejas
- Frontend con polling cada 3 segundos (no WebSockets)

## Monitoreo y Observabilidad

### CloudWatch Logs
- Logs de cada Lambda
- Retención: 7 días por defecto
- Búsqueda y filtrado de errores

### CloudWatch Metrics
- Invocaciones de Lambda
- Errores y throttling
- Latencia de API Gateway
- Capacidad consumida de DynamoDB

### Alarmas Recomendadas
- Lambda errors > 5% en 5 minutos
- API Gateway 5XX > 10 en 5 minutos
- DynamoDB throttled requests > 0

## Costos Estimados

### Escenario: 1000 usuarios activos/mes

| Servicio | Uso | Costo Mensual |
|----------|-----|---------------|
| DynamoDB | 1000 writes + 100K reads | $0.50 |
| Lambda | 101K invocaciones | $0.20 |
| API Gateway | 101K requests | $3.50 |
| Cognito | 1000 MAU | Gratis |
| CloudWatch | Logs básicos | $0.50 |
| **Total** | | **~$4.70** |

### Escenario: 10,000 usuarios activos/mes

| Servicio | Uso | Costo Mensual |
|----------|-----|---------------|
| DynamoDB | 10K writes + 1M reads | $2.50 |
| Lambda | 1.01M invocaciones | $0.40 |
| API Gateway | 1.01M requests | $35.00 |
| Cognito | 10K MAU | Gratis |
| CloudWatch | Logs | $2.00 |
| **Total** | | **~$39.90** |

## Mejoras Futuras

### Corto Plazo
1. WebSockets para actualizaciones en tiempo real
2. Caché con ElastiCache/DAX
3. CloudFront para frontend
4. Backup automático de DynamoDB

### Mediano Plazo
1. Analytics con Kinesis Data Streams
2. Machine Learning para detección de fraude
3. Multi-región para alta disponibilidad
4. GraphQL API con AppSync

### Largo Plazo
1. Microservicios con ECS/EKS
2. Event-driven con EventBridge
3. Data Lake con S3 + Athena
4. CI/CD con CodePipeline
