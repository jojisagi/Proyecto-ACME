# Estimación de Costos AWS - Proyecto Célula 9

Estimación mensual aproximada (Región us-east-1) basada en AWS Pricing Calculator.

## Detalle de Servicios

### 1. **AWS KMS:** $1.00 USD
- Costo por 1 llave maestra administrada por el cliente (CMK)
- $1.00/mes por cada CMK activa
- En este proyecto: 2 CMKs (S3 + DynamoDB) = **$2.00 USD**

### 2. **AWS Lambda:** $0.00 USD
- Cubierto por la Capa Gratuita (Free Tier) al ser < 400,000 GB-segundos
- Free Tier incluye:
  - 1 millón de solicitudes gratuitas por mes
  - 400,000 GB-segundos de tiempo de cómputo por mes
- Estimación de uso:
  - 4 funciones Lambda
  - ~10,000 invocaciones/mes
  - 128 MB de memoria por función
  - Duración promedio: 200ms
- **Costo adicional:** $0.00 (dentro del Free Tier)

### 3. **Amazon DynamoDB:** $0.00 USD
- Cubierto por la Capa Gratuita (hasta 25GB de almacenamiento)
- Free Tier incluye:
  - 25 GB de almacenamiento
  - 25 unidades de capacidad de lectura
  - 25 unidades de capacidad de escritura
- Modo: Pay-per-request (On-Demand)
- Estimación: ~1 GB de datos, ~50,000 operaciones/mes
- **Costo adicional:** $0.00 (dentro del Free Tier)

### 4. **Amazon API Gateway:** ~$0.05 USD
- Costo estimado por 50,000 peticiones HTTP API ($1.00 por millón)
- Pricing: $1.00 por millón de solicitudes
- Free Tier: 1 millón de llamadas API gratuitas durante 12 meses
- Estimación: 50,000 requests/mes
- **Costo:** $0.05 USD (o $0.00 si está en Free Tier)

### 5. **Amazon S3:** $0.00 USD
- Cubierto por la Capa Gratuita para almacenamiento y transferencia básica
- Free Tier incluye:
  - 5 GB de almacenamiento estándar
  - 20,000 solicitudes GET
  - 2,000 solicitudes PUT
- Estimación: ~50 MB para frontend (HTML/CSS/JS)
- **Costo adicional:** $0.00 (dentro del Free Tier)

### 6. **Amazon CloudFront:** $0.00 USD
- Free Tier incluye:
  - 1 TB de transferencia de datos salientes
  - 10,000,000 solicitudes HTTP/HTTPS
  - Válido por 12 meses
- Estimación: ~10 GB transferencia/mes, ~100,000 requests
- **Costo adicional:** $0.00 (dentro del Free Tier)

### 7. **Amazon Cognito:** $0.00 USD
- Free Tier permanente:
  - Primeros 50,000 MAU (Monthly Active Users) gratuitos
- Estimación: ~100 usuarios activos/mes
- **Costo:** $0.00 (dentro del Free Tier)

### 8. **Amazon VPC:** $0.00 USD
- VPC, Subnets, Security Groups: Sin costo
- VPC Endpoints (Gateway): Sin costo para DynamoDB y S3
- **Costo:** $0.00

### 9. **Amazon CloudWatch:** $0.00 USD
- Free Tier incluye:
  - 10 métricas personalizadas
  - 10 alarmas
  - 5 GB de ingesta de logs
  - 5 GB de almacenamiento de logs
- **Costo adicional:** $0.00 (dentro del Free Tier)

---

## Resumen de Costos

| Servicio | Costo Mensual (Free Tier) | Costo Mensual (Sin Free Tier) |
|----------|---------------------------|-------------------------------|
| KMS (2 CMKs) | $2.00 | $2.00 |
| Lambda | $0.00 | $0.20 |
| DynamoDB | $0.00 | $1.25 |
| API Gateway | $0.00 | $0.05 |
| S3 | $0.00 | $0.01 |
| CloudFront | $0.00 | $0.85 |
| Cognito | $0.00 | $0.00 |
| VPC | $0.00 | $0.00 |
| CloudWatch | $0.00 | $0.50 |
| **TOTAL** | **~$2.00 USD** | **~$4.86 USD** |

---

## Escenarios de Uso

### Escenario 1: Desarrollo/Pruebas (Free Tier Activo)
- **Costo mensual:** ~$2.00 USD
- Usuarios: < 100
- Requests: < 50,000/mes
- Almacenamiento: < 1 GB

### Escenario 2: Producción Baja (Sin Free Tier)
- **Costo mensual:** ~$5-10 USD
- Usuarios: 100-500
- Requests: 100,000-500,000/mes
- Almacenamiento: 1-5 GB

### Escenario 3: Producción Media
- **Costo mensual:** ~$20-50 USD
- Usuarios: 1,000-5,000
- Requests: 1-5 millones/mes
- Almacenamiento: 10-50 GB
- Desglose adicional:
  - Lambda: $5-15
  - DynamoDB: $5-20
  - API Gateway: $1-5
  - CloudFront: $5-10
  - KMS: $2

### Escenario 4: Producción Alta
- **Costo mensual:** ~$100-300 USD
- Usuarios: 10,000-50,000
- Requests: 10-50 millones/mes
- Almacenamiento: 100-500 GB
- Desglose adicional:
  - Lambda: $20-80
  - DynamoDB: $30-120
  - API Gateway: $10-50
  - CloudFront: $30-100
  - KMS: $2

---

## Optimización de Costos

### Recomendaciones para Reducir Costos

1. **Lambda**
   - ✅ Optimizar memoria asignada (usar solo lo necesario)
   - ✅ Reducir tiempo de ejecución
   - ✅ Usar arquitectura ARM (Graviton2) para 20% de ahorro
   - ✅ Implementar cache para reducir invocaciones

2. **DynamoDB**
   - ✅ Usar modo On-Demand solo si el tráfico es impredecible
   - ✅ Considerar modo Provisioned para tráfico constante
   - ✅ Implementar TTL para eliminar datos antiguos automáticamente
   - ✅ Usar índices secundarios solo cuando sea necesario

3. **API Gateway**
   - ✅ Implementar cache de API Gateway ($0.02/hora)
   - ✅ Usar HTTP API en lugar de REST API (más barato)
   - ✅ Implementar throttling para evitar abuso

4. **CloudFront**
   - ✅ Configurar TTL apropiado para maximizar cache
   - ✅ Comprimir contenido (gzip/brotli)
   - ✅ Usar Price Class 100 (solo NA y Europa) si es suficiente

5. **S3**
   - ✅ Usar S3 Intelligent-Tiering para datos poco accedidos
   - ✅ Habilitar compresión de archivos
   - ✅ Eliminar versiones antiguas de objetos

6. **CloudWatch**
   - ✅ Configurar retención de logs apropiada (7-30 días)
   - ✅ Filtrar logs innecesarios
   - ✅ Usar métricas estándar en lugar de personalizadas

7. **General**
   - ✅ Implementar tags para tracking de costos
   - ✅ Configurar AWS Budgets con alertas
   - ✅ Revisar AWS Cost Explorer mensualmente
   - ✅ Eliminar recursos no utilizados

---

## Monitoreo de Costos

### Configurar AWS Budgets

```bash
# Crear presupuesto mensual de $10
aws budgets create-budget \
  --account-id $(aws sts get-caller-identity --query Account --output text) \
  --budget file://budget.json \
  --notifications-with-subscribers file://notifications.json
```

**budget.json:**
```json
{
  "BudgetName": "Celula9-Monthly-Budget",
  "BudgetLimit": {
    "Amount": "10",
    "Unit": "USD"
  },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST"
}
```

### Ver Costos Actuales

```bash
# Costos del mes actual
aws ce get-cost-and-usage \
  --time-period Start=$(date -d "$(date +%Y-%m-01)" +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=SERVICE

# Costos por tag
aws ce get-cost-and-usage \
  --time-period Start=2025-01-01,End=2025-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=TAG,Key=Project
```

### Alertas Recomendadas

1. **Alerta de Presupuesto:** Notificar cuando se alcance el 80% del presupuesto
2. **Alerta de Anomalías:** Detectar picos inusuales de costo
3. **Alerta de Free Tier:** Notificar cuando se acerque al límite del Free Tier

---

## Calculadora de Costos

Para una estimación personalizada, usa:
- **AWS Pricing Calculator:** https://calculator.aws/
- **AWS Cost Explorer:** Para análisis de costos históricos
- **AWS Budgets:** Para establecer límites y alertas

---

## Notas Importantes

⚠️ **Free Tier:**
- Válido por 12 meses desde la creación de la cuenta AWS
- Algunos servicios tienen Free Tier permanente (Cognito, Lambda parcial)
- Monitorear uso para evitar cargos inesperados

💡 **Tips:**
- Los costos pueden variar según la región AWS
- us-east-1 suele ser la región más económica
- Revisar factura mensualmente para optimizar
- Usar tags para identificar costos por proyecto

📊 **Proyección Anual:**
- Con Free Tier: ~$24 USD/año
- Sin Free Tier (uso bajo): ~$60 USD/año
- Producción media: ~$300-600 USD/año
- Producción alta: ~$1,200-3,600 USD/año

---

**Última actualización:** Noviembre 2025  
**Célula 9 - Acme Inc.**
