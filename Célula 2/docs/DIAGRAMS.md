# Diagramas de Arquitectura - Sistema de Scheduling Serverless

## Diagrama de Arquitectura General

```mermaid
graph TB
    subgraph "Cliente"
        User[Usuario/Aplicación]
    end
    
    subgraph "AWS Cloud"
        subgraph "Autenticación"
            Cognito[Amazon Cognito<br/>User Pool]
        end
        
        subgraph "API Layer"
            APIGW[API Gateway<br/>REST API]
            Auth[Cognito<br/>Authorizer]
        end
        
        subgraph "VPC - 10.0.0.0/16"
            subgraph "Private Subnet 1"
                Lambda1[Scheduler Manager<br/>Lambda]
            end
            
            subgraph "Private Subnet 2"
                Lambda2[Order Executor<br/>Lambda]
            end
            
            subgraph "VPC Endpoints"
                VPCE1[DynamoDB<br/>Endpoint]
                VPCE2[CloudWatch<br/>Endpoint]
            end
        end
        
        subgraph "Scheduling"
            EBS[EventBridge<br/>Scheduler]
        end
        
        subgraph "Storage"
            DDB1[(PurchaseOrders<br/>Table)]
            DDB2[(ScheduleDefinitions<br/>Table)]
        end
        
        subgraph "Security"
            KMS[AWS KMS<br/>CMK]
        end
        
        subgraph "Monitoring"
            CW[CloudWatch<br/>Logs]
        end
    end
    
    User -->|HTTPS| APIGW
    APIGW -->|Validate JWT| Auth
    Auth -->|Check| Cognito
    APIGW -->|Invoke| Lambda1
    Lambda1 -->|Create/Delete| EBS
    Lambda1 -->|Read/Write| DDB2
    Lambda1 -->|Query| DDB1
    EBS -->|Trigger| Lambda2
    Lambda2 -->|Write Orders| DDB1
    Lambda1 -->|Logs| CW
    Lambda2 -->|Logs| CW
    DDB1 -.->|Encrypted by| KMS
    DDB2 -.->|Encrypted by| KMS
    Lambda1 -.->|Via| VPCE1
    Lambda2 -.->|Via| VPCE1
    Lambda1 -.->|Via| VPCE2
    Lambda2 -.->|Via| VPCE2
    
    style User fill:#e1f5ff
    style Cognito fill:#ff9900
    style APIGW fill:#ff9900
    style Lambda1 fill:#ff9900
    style Lambda2 fill:#ff9900
    style EBS fill:#ff9900
    style DDB1 fill:#3b48cc
    style DDB2 fill:#3b48cc
    style KMS fill:#dd344c
    style CW fill:#ff9900
```

## Flujo de Creación de Schedule

```mermaid
sequenceDiagram
    participant U as Usuario
    participant AG as API Gateway
    participant C as Cognito
    participant SM as Scheduler Manager
    participant EB as EventBridge Scheduler
    participant DB as DynamoDB

    U->>AG: POST /schedule<br/>{scheduleName, frequency, gadgetType}
    AG->>C: Validar JWT Token
    C-->>AG: Token válido
    AG->>SM: Invocar Lambda
    
    SM->>SM: Validar parámetros
    SM->>EB: CreateSchedule()
    EB-->>SM: Schedule creado
    
    SM->>DB: PutItem (ScheduleDefinitionsTable)
    DB-->>SM: Item guardado
    
    SM-->>AG: Response 201
    AG-->>U: {message, schedule}
```

## Flujo de Ejecución Automática de Orden

```mermaid
sequenceDiagram
    participant EB as EventBridge Scheduler
    participant OE as Order Executor
    participant DB1 as ScheduleDefinitionsTable
    participant DB2 as PurchaseOrdersTable
    participant CW as CloudWatch

    EB->>OE: Trigger (según schedule)
    Note over EB,OE: Payload: {scheduleId, gadgetType, quantity}
    
    OE->>DB1: GetItem (scheduleId)
    DB1-->>OE: Schedule info
    
    OE->>OE: Aplicar lógica de negocio<br/>- Calcular precio<br/>- Aplicar descuento<br/>- Determinar prioridad<br/>- Asignar proveedor
    
    OE->>DB2: PutItem (orden generada)
    DB2-->>OE: Orden guardada
    
    OE->>CW: Log success
    OE-->>EB: Response 200
```

## Flujo de Consulta de Órdenes

```mermaid
sequenceDiagram
    participant U as Usuario
    participant AG as API Gateway
    participant C as Cognito
    participant SM as Scheduler Manager
    participant DB as PurchaseOrdersTable

    U->>AG: GET /orders?status=pending
    AG->>C: Validar JWT Token
    C-->>AG: Token válido
    AG->>SM: Invocar Lambda
    
    SM->>DB: Query (StatusIndex)
    DB-->>SM: Lista de órdenes
    
    SM->>SM: Formatear respuesta
    SM-->>AG: Response 200
    AG-->>U: {count, orders[]}
```

## Arquitectura de Red (VPC)

```mermaid
graph TB
    subgraph "VPC - 10.0.0.0/16"
        subgraph "Availability Zone 1"
            PS1[Private Subnet 1<br/>10.0.1.0/24]
            L1[Lambda 1]
        end
        
        subgraph "Availability Zone 2"
            PS2[Private Subnet 2<br/>10.0.2.0/24]
            L2[Lambda 2]
        end
        
        subgraph "VPC Endpoints"
            VPCE1[DynamoDB<br/>Gateway Endpoint]
            VPCE2[CloudWatch Logs<br/>Interface Endpoint]
        end
        
        RT[Route Table<br/>Private]
        SG[Security Group<br/>Lambda SG]
    end
    
    subgraph "AWS Services"
        DDB[DynamoDB]
        CW[CloudWatch]
    end
    
    L1 -.->|In| PS1
    L2 -.->|In| PS2
    PS1 -->|Routes via| RT
    PS2 -->|Routes via| RT
    RT -->|Gateway| VPCE1
    RT -->|Interface| VPCE2
    VPCE1 -.->|Private| DDB
    VPCE2 -.->|Private| CW
    L1 -.->|Protected by| SG
    L2 -.->|Protected by| SG
    
    style PS1 fill:#e8f4f8
    style PS2 fill:#e8f4f8
    style VPCE1 fill:#ff9900
    style VPCE2 fill:#ff9900
    style SG fill:#dd344c
```

## Modelo de Datos - DynamoDB

```mermaid
erDiagram
    PURCHASE_ORDERS {
        string orderId PK
        string createdAt SK
        string scheduleId
        string gadgetType
        number quantity
        decimal unitPrice
        decimal subtotal
        decimal discountRate
        decimal discountAmount
        decimal total
        string priority
        string supplier
        string status
        number estimatedDeliveryDays
        object metadata
    }
    
    SCHEDULE_DEFINITIONS {
        string scheduleId PK
        string createdAt SK
        string scheduleName
        string frequency
        string gadgetType
        number quantity
        boolean enabled
        string status
        string deletedAt
    }
    
    PURCHASE_ORDERS ||--o{ SCHEDULE_DEFINITIONS : "generated_by"
```

## Flujo de Seguridad

```mermaid
graph LR
    subgraph "Capas de Seguridad"
        A[1. Autenticación<br/>Cognito JWT]
        B[2. Autorización<br/>API Gateway]
        C[3. IAM Roles<br/>Mínimo Privilegio]
        D[4. Cifrado en Tránsito<br/>TLS 1.2+]
        E[5. Cifrado en Reposo<br/>KMS]
        F[6. Aislamiento de Red<br/>VPC Privada]
    end
    
    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    
    style A fill:#4caf50
    style B fill:#4caf50
    style C fill:#4caf50
    style D fill:#4caf50
    style E fill:#4caf50
    style F fill:#4caf50
```

## Ciclo de Vida de un Schedule

```mermaid
stateDiagram-v2
    [*] --> Created: POST /schedule
    Created --> Active: enabled=true
    Created --> Disabled: enabled=false
    Active --> Executing: EventBridge trigger
    Executing --> Active: Success
    Executing --> Failed: Error
    Failed --> Active: Retry
    Active --> Disabled: Update
    Disabled --> Active: Update
    Active --> Deleted: DELETE /schedule
    Disabled --> Deleted: DELETE /schedule
    Deleted --> [*]
    
    note right of Active
        Genera órdenes
        automáticamente
    end note
    
    note right of Deleted
        Soft delete
        en DynamoDB
    end note
```

## Estados de una Orden

```mermaid
stateDiagram-v2
    [*] --> Pending: Orden creada
    Pending --> Processing: Validación
    Processing --> Completed: Aprobada
    Processing --> Failed: Error
    Completed --> Shipped: Enviada
    Shipped --> Delivered: Entregada
    Pending --> Cancelled: Cancelada
    Processing --> Cancelled: Cancelada
    Failed --> [*]
    Delivered --> [*]
    Cancelled --> [*]
    
    note right of Pending
        Estado inicial
        al crear orden
    end note
    
    note right of Completed
        Lista para envío
    end note
```

## Arquitectura de Despliegue

```mermaid
graph TB
    subgraph "Desarrollo Local"
        Code[Código Fuente]
        Scripts[Scripts de<br/>Despliegue]
    end
    
    subgraph "AWS CloudFormation"
        IAM[IAM Stack<br/>Roles y Políticas]
        Main[Main Stack<br/>Recursos]
    end
    
    subgraph "Artefactos"
        S3[S3 Bucket<br/>Lambda ZIPs]
    end
    
    subgraph "Recursos Desplegados"
        Lambda[Lambda Functions]
        API[API Gateway]
        DB[DynamoDB Tables]
        Sched[EventBridge<br/>Scheduler]
    end
    
    Code -->|1. Package| Scripts
    Scripts -->|2. Deploy| IAM
    IAM -->|3. Create Roles| Main
    Scripts -->|4. Upload| S3
    Main -->|5. Create| Lambda
    Main -->|6. Create| API
    Main -->|7. Create| DB
    Lambda -->|8. Integrate| Sched
    
    style Code fill:#e1f5ff
    style Scripts fill:#e1f5ff
    style IAM fill:#ff9900
    style Main fill:#ff9900
    style S3 fill:#3b48cc
    style Lambda fill:#ff9900
    style API fill:#ff9900
    style DB fill:#3b48cc
    style Sched fill:#ff9900
```

## Monitoreo y Observabilidad

```mermaid
graph TB
    subgraph "Fuentes de Datos"
        L1[Lambda Logs]
        L2[API Gateway Logs]
        M1[Lambda Metrics]
        M2[DynamoDB Metrics]
        M3[API Metrics]
    end
    
    subgraph "CloudWatch"
        Logs[CloudWatch Logs]
        Metrics[CloudWatch Metrics]
        Alarms[CloudWatch Alarms]
    end
    
    subgraph "Acciones"
        SNS[SNS Topics]
        Email[Email Notifications]
        Lambda[Lambda Actions]
    end
    
    L1 --> Logs
    L2 --> Logs
    M1 --> Metrics
    M2 --> Metrics
    M3 --> Metrics
    
    Logs --> Alarms
    Metrics --> Alarms
    
    Alarms --> SNS
    SNS --> Email
    SNS --> Lambda
    
    style Logs fill:#ff9900
    style Metrics fill:#ff9900
    style Alarms fill:#dd344c
    style SNS fill:#ff9900
```

## Escalabilidad

```mermaid
graph LR
    subgraph "Carga Baja"
        A1[API Gateway<br/>10 req/s]
        L1[Lambda<br/>2 instancias]
        D1[DynamoDB<br/>5 RCU/WCU]
    end
    
    subgraph "Carga Media"
        A2[API Gateway<br/>100 req/s]
        L2[Lambda<br/>20 instancias]
        D2[DynamoDB<br/>50 RCU/WCU]
    end
    
    subgraph "Carga Alta"
        A3[API Gateway<br/>1000 req/s]
        L3[Lambda<br/>200 instancias]
        D3[DynamoDB<br/>500 RCU/WCU]
    end
    
    A1 -.->|Auto-scale| A2
    A2 -.->|Auto-scale| A3
    L1 -.->|Auto-scale| L2
    L2 -.->|Auto-scale| L3
    D1 -.->|On-Demand| D2
    D2 -.->|On-Demand| D3
    
    style A1 fill:#90ee90
    style A2 fill:#ffd700
    style A3 fill:#ff6347
    style L1 fill:#90ee90
    style L2 fill:#ffd700
    style L3 fill:#ff6347
    style D1 fill:#90ee90
    style D2 fill:#ffd700
    style D3 fill:#ff6347
```

## Costos por Componente

```mermaid
pie title Distribución de Costos Mensuales (10K órdenes)
    "API Gateway" : 35
    "DynamoDB" : 10
    "EventBridge" : 10
    "Lambda" : 5
    "CloudWatch" : 5
    "KMS" : 1
```

---

## Notas sobre los Diagramas

Estos diagramas están en formato Mermaid y se pueden visualizar en:
- GitHub (renderizado automático)
- VS Code (con extensión Mermaid)
- Herramientas online: https://mermaid.live/

Para exportar a imágenes:
1. Visita https://mermaid.live/
2. Copia el código del diagrama
3. Exporta como PNG/SVG
