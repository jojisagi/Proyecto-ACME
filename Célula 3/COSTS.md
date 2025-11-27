# Estimación de Costos - Acme Image Handler

## Resumen Ejecutivo

| Ambiente | Costo Mensual Estimado | Costo Anual |
|----------|------------------------|-------------|
| **Sandbox** | $45 - $60 | $540 - $720 |
| **Pre-Producción** | $60 - $80 | $720 - $960 |
| **Producción** | $115 - $500+ | $1,380 - $6,000+ |
| **Build (CI/CD)** | $7 - $15 | $84 - $180 |
| **TOTAL** | **$227 - $655+** | **$2,724 - $7,860+** |

*Nota: Los costos de producción varían significativamente según el tráfico*

## Desglose Detallado por Servicio

### 1. AWS Lambda

#### Pricing
- **Requests**: $0.20 por 1M requests
- **Duration**: $0.0000166667 por GB-segundo
- **Free Tier**: 1M requests/mes, 400,000 GB-segundos/mes

#### Estimación Sandbox
```
Invocaciones mensuales: 100,000
Memoria promedio: 512 MB
Duración promedio: 2 segundos

Costo requests: (100,000 / 1,000,000) × $0.20 = $0.02
Costo duration: (100,000 × 0.5 GB × 2s) × $0.0000166667 = $1.67
Total Lambda Sandbox: ~$1.69/mes (dentro del free tier)
```

#### Estimación Producción
```
Invocaciones mensuales: 5,000,000
Memoria promedio: 1024 MB
Duración promedio: 3 segundos

Costo requests: (5,000,000 / 1,000,000) × $0.20 = $1.00
Costo duration: (5,000,000 × 1 GB × 3s) × $0.0000166667 = $250
Total Lambda Producción: ~$251/mes
```

### 2. Amazon API Gateway

#### Pricing
- **REST API**: $3.50 por millón de requests
- **Data Transfer**: $0.09/GB (primeros 10TB)

#### Estimación Sandbox
```
Requests mensuales: 100,000
Data transfer: 10 GB

Costo requests: (100,000 / 1,000,000) × $3.50 = $0.35
Costo data: 10 × $0.09 = $0.90
Total API Gateway Sandbox: ~$1.25/mes
```

#### Estimación Producción
```
Requests mensuales: 5,000,000
Data transfer: 500 GB

Costo requests: (5,000,000 / 1,000,000) × $3.50 = $17.50
Costo data: 500 × $0.09 = $45
Total API Gateway Producción: ~$62.50/mes
```

### 3. Amazon S3

#### Pricing
- **Storage**: $0.023/GB (Standard)
- **PUT requests**: $0.005 per 1,000
- **GET requests**: $0.0004 per 1,000
- **Data Transfer Out**: $0.09/GB

#### Estimación Sandbox
```
Storage: 10 GB (imágenes)
PUT requests: 10,000/mes
GET requests: 50,000/mes
Data transfer: 20 GB/mes

Costo storage: 10 × $0.023 = $0.23
Costo PUT: (10,000 / 1,000) × $0.005 = $0.05
Costo GET: (50,000 / 1,000) × $0.0004 = $0.02
Costo transfer: 20 × $0.09 = $1.80
Total S3 Sandbox: ~$2.10/mes
```

#### Estimación Producción
```
Storage: 500 GB
PUT requests: 500,000/mes
GET requests: 2,500,000/mes
Data transfer: 1,000 GB/mes

Costo storage: 500 × $0.023 = $11.50
Costo PUT: (500,000 / 1,000) × $0.005 = $2.50
Costo GET: (2,500,000 / 1,000) × $0.0004 = $1.00
Costo transfer: 1,000 × $0.09 = $90
Total S3 Producción: ~$105/mes
```

### 4. Amazon DynamoDB

#### Pricing (On-Demand)
- **Write Request Units**: $1.25 per million
- **Read Request Units**: $0.25 per million
- **Storage**: $0.25/GB

#### Estimación Sandbox
```
Write requests: 10,000/mes
Read requests: 50,000/mes
Storage: 1 GB

Costo writes: (10,000 / 1,000,000) × $1.25 = $0.01
Costo reads: (50,000 / 1,000,000) × $0.25 = $0.01
Costo storage: 1 × $0.25 = $0.25
Total DynamoDB Sandbox: ~$0.27/mes
```

#### Estimación Producción
```
Write requests: 500,000/mes
Read requests: 2,500,000/mes
Storage: 50 GB

Costo writes: (500,000 / 1,000,000) × $1.25 = $0.63
Costo reads: (2,500,000 / 1,000,000) × $0.25 = $0.63
Costo storage: 50 × $0.25 = $12.50
Total DynamoDB Producción: ~$13.76/mes
```

### 5. Amazon Cognito

#### Pricing
- **MAU (Monthly Active Users)**: Primeros 50,000 gratis
- **Después**: $0.0055 por MAU

#### Estimación Sandbox
```
MAU: 10 usuarios
Total Cognito Sandbox: $0/mes (free tier)
```

#### Estimación Producción
```
MAU: 1,000 usuarios
Total Cognito Producción: $0/mes (dentro del free tier)
```

### 6. AWS KMS

#### Pricing
- **Customer Master Key**: $1/mes por key
- **Requests**: $0.03 per 10,000 requests

#### Estimación por Ambiente
```
Keys: 1
Requests: 100,000/mes

Costo key: $1.00
Costo requests: (100,000 / 10,000) × $0.03 = $0.30
Total KMS: ~$1.30/mes por ambiente
```

### 7. VPC y Networking

#### NAT Gateway
- **Hourly charge**: $0.045/hora = $32.40/mes
- **Data processing**: $0.045/GB

#### Estimación Sandbox
```
NAT Gateway: 1 × $32.40 = $32.40
Data processing: 50 GB × $0.045 = $2.25
Total NAT Sandbox: ~$34.65/mes
```

#### Estimación Producción (Multi-AZ)
```
NAT Gateway: 2 × $32.40 = $64.80
Data processing: 200 GB × $0.045 = $9.00
Total NAT Producción: ~$73.80/mes
```

#### VPC Endpoints (Alternativa sin costo de NAT)
- **S3 Gateway Endpoint**: $0 (gratis)
- **DynamoDB Gateway Endpoint**: $0 (gratis)
- **Interface Endpoints**: $0.01/hora = $7.20/mes cada uno

### 8. CloudWatch

#### Pricing
- **Logs Ingestion**: $0.50/GB
- **Logs Storage**: $0.03/GB
- **Metrics**: Primeros 10 custom metrics gratis

#### Estimación Sandbox
```
Logs ingestion: 5 GB/mes
Logs storage: 10 GB
Custom metrics: 5

Costo ingestion: 5 × $0.50 = $2.50
Costo storage: 10 × $0.03 = $0.30
Total CloudWatch Sandbox: ~$2.80/mes
```

#### Estimación Producción
```
Logs ingestion: 50 GB/mes
Logs storage: 100 GB
Custom metrics: 20

Costo ingestion: 50 × $0.50 = $25.00
Costo storage: 100 × $0.03 = $3.00
Costo metrics: 10 × $0.30 = $3.00
Total CloudWatch Producción: ~$31.00/mes
```

### 9. CI/CD (CodePipeline + CodeBuild)

#### Pricing
- **CodePipeline**: $1/mes por pipeline activo
- **CodeBuild**: $0.005/minuto (general1.small)

#### Estimación
```
Pipeline: 1 × $1 = $1.00
Builds: 100 builds/mes × 5 min × $0.005 = $2.50
Artifact Storage (S3): 10 GB × $0.023 = $0.23
Total CI/CD: ~$3.73/mes
```

## Resumen por Ambiente

### Sandbox (Desarrollo)
```
Lambda:           $1.69
API Gateway:      $1.25
S3:               $2.10
DynamoDB:         $0.27
Cognito:          $0.00
KMS:              $1.30
NAT Gateway:     $34.65
CloudWatch:       $2.80
─────────────────────
TOTAL:          ~$44.06/mes
```

### Producción (Tráfico Medio)
```
Lambda:         $251.00
API Gateway:     $62.50
S3:             $105.00
DynamoDB:        $13.76
Cognito:          $0.00
KMS:              $1.30
NAT Gateway:     $73.80
CloudWatch:      $31.00
─────────────────────
TOTAL:         ~$538.36/mes
```

### Build Account
```
CodePipeline:     $1.00
CodeBuild:        $2.50
S3 Artifacts:     $0.23
─────────────────────
TOTAL:           ~$3.73/mes
```

## Optimizaciones de Costos

### 1. Eliminar NAT Gateway (Ahorro: $32-73/mes)
- Usar VPC Endpoints para S3 y DynamoDB (gratis)
- Lambdas solo acceden a servicios AWS
- **Ahorro anual**: $384 - $876

### 2. Reserved Capacity para DynamoDB
- Si el tráfico es predecible
- Ahorro de hasta 75% vs On-Demand
- **Ahorro potencial**: $10/mes en producción

### 3. S3 Intelligent-Tiering
- Mueve automáticamente objetos a clases más baratas
- Ahorro de hasta 68% en storage
- **Ahorro potencial**: $7/mes en producción

### 4. Lambda Provisioned Concurrency (solo si necesario)
- Reduce cold starts pero aumenta costos
- Solo para producción con SLA estrictos

### 5. CloudWatch Logs Retention
- Reducir retención de 30 a 7 días
- **Ahorro**: 50% en storage de logs

## Proyección de Costos por Escala

| Tráfico Mensual | Lambda | API GW | S3 | DynamoDB | Total/mes |
|-----------------|--------|--------|----|-----------|-----------| 
| 100K requests | $2 | $1 | $2 | $0.30 | ~$45 |
| 1M requests | $20 | $10 | $20 | $3 | ~$120 |
| 5M requests | $100 | $50 | $100 | $15 | ~$400 |
| 10M requests | $200 | $100 | $200 | $30 | ~$750 |
| 50M requests | $1,000 | $500 | $1,000 | $150 | ~$3,500 |

*Nota: Incluye costos base de infraestructura (NAT, KMS, etc.)*

## Alertas de Costos Recomendadas

### CloudWatch Billing Alarms

```bash
# Alerta para Sandbox
aws cloudwatch put-metric-alarm \
  --alarm-name acme-sandbox-cost-alert \
  --alarm-description "Alerta si costos superan $60/mes" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 21600 \
  --evaluation-periods 1 \
  --threshold 60 \
  --comparison-operator GreaterThanThreshold

# Alerta para Producción
aws cloudwatch put-metric-alarm \
  --alarm-name acme-prod-cost-alert \
  --alarm-description "Alerta si costos superan $600/mes" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 21600 \
  --evaluation-periods 1 \
  --threshold 600 \
  --comparison-operator GreaterThanThreshold
```

### AWS Budgets

```bash
# Crear presupuesto mensual
aws budgets create-budget \
  --account-id 123456789012 \
  --budget file://budget.json \
  --notifications-with-subscribers file://notifications.json
```

## Conclusiones

1. **Costo inicial bajo**: El free tier de AWS cubre gran parte del desarrollo
2. **Escalabilidad**: Los costos crecen linealmente con el tráfico
3. **Optimización**: Eliminar NAT Gateway puede reducir costos en 40-60%
4. **Monitoreo**: Configurar alertas para evitar sorpresas
5. **Producción**: El costo real dependerá del volumen de tráfico

## Recomendaciones

- **Fase 1 (Desarrollo)**: Usar VPC Endpoints en lugar de NAT Gateway
- **Fase 2 (Piloto)**: Monitorear costos reales vs estimados
- **Fase 3 (Producción)**: Evaluar Reserved Capacity si el tráfico es predecible
- **Siempre**: Configurar alertas de costos y revisar mensualmente
