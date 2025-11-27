# Quick Start - E-commerce AWS Serverless

## 🚀 Inicio Rápido (5 minutos)

### Prerrequisitos
```bash
# Verificar instalaciones
aws --version          # AWS CLI
python3 --version      # Python 3.11+
node --version         # Node.js 18+
```

### Despliegue en 3 Pasos

#### 1. Configurar AWS CLI
```bash
aws configure
# AWS Access Key ID: [tu-access-key]
# AWS Secret Access Key: [tu-secret-key]
# Default region: us-east-1
# Default output format: json
```

#### 2. Desplegar Infraestructura
```bash
./scripts/deploy.sh
```

Este comando ejecuta automáticamente:
- ✅ Crea roles y políticas IAM
- ✅ Crea bucket S3 para código Lambda
- ✅ Empaqueta y sube Lambda functions a S3
- ✅ Despliega Lambda functions
- ✅ Configura API Gateway
- ✅ Crea tabla DynamoDB
- ✅ Configura SQS y SNS
- ✅ Despliega Step Functions
- ✅ Construye y despliega frontend React
- ✅ Configura CloudFront CDN
- ✅ Pobla base de datos con 50 órdenes

**Tiempo estimado**: 10-15 minutos

#### 3. Probar la Aplicación
```bash
# El script mostrará las URLs al finalizar
# API Gateway URL: https://xxxxx.execute-api.us-east-1.amazonaws.com/prod
# CloudFront URL: https://xxxxx.cloudfront.net

# Probar API
./scripts/test-api.sh <API_GATEWAY_URL>
```

## 📋 Ejemplos de Uso

### Crear una Orden

```bash
curl -X POST https://your-api-url.com/prod/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customerId": "cust-123",
    "customerName": "Juan Pérez",
    "customerEmail": "juan@example.com",
    "items": [
      {
        "productId": "prod-101",
        "name": "Laptop HP 15",
        "quantity": 1,
        "price": 299.99
      }
    ],
    "totalAmount": 299.99,
    "paymentMethod": "credit_card",
    "shippingAddress": {
      "street": "Calle Principal 123",
      "city": "Madrid",
      "state": "Madrid",
      "zipCode": "28001",
      "country": "España"
    }
  }'
```

**Respuesta**:
```json
{
  "orderId": "550e8400-e29b-41d4-a716-446655440000",
  "customerId": "cust-123",
  "customerName": "Juan Pérez",
  "status": "PENDING",
  "totalAmount": 299.99,
  "orderDate": "2024-11-26T10:30:00Z"
}
```

### Listar Órdenes

```bash
# Todas las órdenes
curl https://your-api-url.com/prod/orders

# Órdenes de un cliente específico
curl "https://your-api-url.com/prod/orders?customerId=cust-123"
```

### Obtener Orden Específica

```bash
curl https://your-api-url.com/prod/orders/550e8400-e29b-41d4-a716-446655440000
```

### Ejecutar Workflow de Procesamiento

```bash
# Obtener ARN de Step Functions
STATE_MACHINE_ARN=$(aws cloudformation describe-stacks \
  --stack-name ecommerce-resources \
  --query "Stacks[0].Outputs[?OutputKey=='StateMachineArn'].OutputValue" \
  --output text)

# Ejecutar workflow
aws stepfunctions start-execution \
  --state-machine-arn $STATE_MACHINE_ARN \
  --input '{"orderId": "550e8400-e29b-41d4-a716-446655440000"}'
```

## 🎯 Casos de Uso

### 1. E-commerce Básico
- Crear órdenes desde frontend
- Procesar pagos automáticamente
- Enviar notificaciones por email
- Tracking de envíos

### 2. Marketplace
- Múltiples vendedores
- Comisiones automáticas
- Gestión de inventario
- Reviews y ratings

### 3. Suscripciones
- Pagos recurrentes
- Renovaciones automáticas
- Gestión de planes
- Facturación mensual

### 4. B2B
- Órdenes de compra
- Aprobaciones multi-nivel
- Integración con ERP
- Facturación personalizada

## 📊 Monitoreo

### Ver Logs en Tiempo Real

```bash
# Lambda App Server
aws logs tail /aws/lambda/app-server --follow

# Lambda Process Order
aws logs tail /aws/lambda/process-order --follow

# Step Functions
aws logs tail /aws/states/order-processing-workflow --follow
```

### Métricas en CloudWatch

```bash
# Abrir consola de CloudWatch
aws cloudwatch get-dashboard --dashboard-name ecommerce-dashboard
```

### Ver Ejecuciones de Step Functions

```bash
# Listar ejecuciones
aws stepfunctions list-executions \
  --state-machine-arn $STATE_MACHINE_ARN \
  --max-results 10

# Ver detalles de ejecución
aws stepfunctions describe-execution \
  --execution-arn <EXECUTION_ARN>
```

## 🔄 Actualizar Código Lambda

Si solo necesitas actualizar el código de las funciones Lambda sin redesplegar toda la infraestructura:

```bash
# Edita el código en lambdas/app-server/index.py o lambdas/process-order/index.py
# Luego ejecuta:
./scripts/update-lambdas.sh
```

Este script:
1. Empaqueta las funciones Lambda
2. Sube los archivos ZIP a S3
3. Actualiza las funciones Lambda en AWS
4. Limpia archivos temporales

Los cambios están disponibles inmediatamente.

## 🔧 Configuración Avanzada

### Habilitar Notificaciones por Email

```bash
# Obtener ARN del topic SNS
SNS_TOPIC_ARN=$(aws cloudformation describe-stacks \
  --stack-name ecommerce-resources \
  --query "Stacks[0].Outputs[?OutputKey=='SNSTopicArn'].OutputValue" \
  --output text)

# Suscribir tu email
aws sns subscribe \
  --topic-arn $SNS_TOPIC_ARN \
  --protocol email \
  --notification-endpoint tu-email@example.com

# Confirmar suscripción en tu bandeja de entrada
```

### Configurar Dominio Personalizado

```bash
# 1. Crear certificado SSL en ACM
aws acm request-certificate \
  --domain-name api.tudominio.com \
  --validation-method DNS

# 2. Configurar dominio personalizado en API Gateway
aws apigateway create-domain-name \
  --domain-name api.tudominio.com \
  --certificate-arn <CERTIFICATE_ARN>

# 3. Crear registro DNS en Route 53
```

### Aumentar Capacidad de DynamoDB

```bash
# Cambiar a modo On-Demand
aws dynamodb update-table \
  --table-name Orders \
  --billing-mode PAY_PER_REQUEST

# O aumentar capacidad provisionada
aws dynamodb update-table \
  --table-name Orders \
  --provisioned-throughput ReadCapacityUnits=10,WriteCapacityUnits=10
```

## 🧪 Testing

### Tests Unitarios (Lambda)

```bash
cd lambdas/app-server
python3 -m pytest tests/

cd ../process-order
python3 -m pytest tests/
```

### Tests de Integración

```bash
# Ejecutar suite completa
./scripts/test-api.sh $API_URL

# Test individual
curl -X GET $API_URL/health
```

### Load Testing

```bash
# Instalar Apache Bench
brew install httpd  # macOS

# Test de carga
ab -n 1000 -c 10 $API_URL/orders
```

## 🐛 Troubleshooting

### Error: "Stack already exists"
```bash
# Eliminar stack existente
aws cloudformation delete-stack --stack-name ecommerce-resources
aws cloudformation wait stack-delete-complete --stack-name ecommerce-resources
```

### Error: "Lambda timeout"
```bash
# Aumentar timeout
aws lambda update-function-configuration \
  --function-name app-server \
  --timeout 60
```

### Error: "DynamoDB throttling"
```bash
# Cambiar a On-Demand
aws dynamodb update-table \
  --table-name Orders \
  --billing-mode PAY_PER_REQUEST
```

### Error: "CORS en frontend"
Verificar que las respuestas Lambda incluyan:
```python
'headers': {
    'Access-Control-Allow-Origin': '*',
    'Content-Type': 'application/json'
}
```

## 🧹 Limpieza

### Eliminar Todos los Recursos

```bash
./scripts/cleanup.sh
```

### Eliminar Solo el Frontend

```bash
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name ecommerce-resources \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
  --output text)

aws s3 rm s3://$BUCKET_NAME --recursive
```

## 📚 Recursos Adicionales

### Documentación
- [README.md](README.md) - Visión general del proyecto
- [ARCHITECTURE.md](ARCHITECTURE.md) - Arquitectura detallada
- [DEPLOYMENT.md](DEPLOYMENT.md) - Guía de despliegue completa

### AWS Documentation
- [Lambda Developer Guide](https://docs.aws.amazon.com/lambda/)
- [API Gateway Developer Guide](https://docs.aws.amazon.com/apigateway/)
- [DynamoDB Developer Guide](https://docs.aws.amazon.com/dynamodb/)
- [Step Functions Developer Guide](https://docs.aws.amazon.com/step-functions/)

### Tutoriales
- [AWS Serverless Workshop](https://aws.amazon.com/serverless/workshops/)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

## 💡 Tips y Mejores Prácticas

### Performance
- ✅ Usar Lambda con ARM (Graviton2) para mejor precio/performance
- ✅ Implementar caché en API Gateway para endpoints de lectura
- ✅ Usar DynamoDB Streams para procesamiento en tiempo real
- ✅ Optimizar tamaño de paquetes Lambda

### Seguridad
- ✅ Implementar autenticación con Cognito
- ✅ Usar AWS WAF para protección DDoS
- ✅ Habilitar CloudTrail para auditoría
- ✅ Rotar credenciales regularmente
- ✅ Usar Secrets Manager para datos sensibles

### Costos
- ✅ Usar Lambda con arquitectura ARM (20% más barato)
- ✅ Implementar caché agresivo en CloudFront
- ✅ DynamoDB On-Demand solo si tráfico variable
- ✅ Configurar alarmas de presupuesto
- ✅ Revisar AWS Cost Explorer mensualmente

### Monitoreo
- ✅ Configurar alarmas de CloudWatch
- ✅ Usar AWS X-Ray para tracing
- ✅ Implementar logging estructurado
- ✅ Dashboard personalizado en CloudWatch
- ✅ Alertas en Slack/Email para errores críticos

## 🎓 Próximos Pasos

1. **Semana 1**: Familiarízate con la arquitectura
2. **Semana 2**: Personaliza el frontend
3. **Semana 3**: Agrega autenticación con Cognito
4. **Semana 4**: Implementa búsqueda con OpenSearch
5. **Mes 2**: Agrega analytics y reportes
6. **Mes 3**: Implementa CI/CD con CodePipeline

## 🤝 Soporte

¿Necesitas ayuda?
- 📖 Revisa la documentación en `/docs`
- 🐛 Reporta issues en GitHub
- 💬 Únete a la comunidad en Discord
- 📧 Contacto: support@example.com

---

**¡Feliz desarrollo! 🚀**
