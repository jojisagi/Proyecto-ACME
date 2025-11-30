<<<<<<< HEAD
# Proyecto-ACME
=======
# Sistema de Scheduling Serverless para Órdenes de Compra - Acme Inc.

## Descripción
Sistema serverless completo para la generación automática de órdenes de compra utilizando AWS EventBridge Scheduler, Lambda, DynamoDB, API Gateway y Cognito.

## Arquitectura

### Componentes Principales:
- **API Gateway**: REST API con autenticación Cognito
- **AWS Lambda**: 2 funciones (scheduler_manager, order_executor)
- **EventBridge Scheduler**: Programación de ejecuciones automáticas
- **DynamoDB**: Almacenamiento de órdenes y definiciones de schedules
- **Cognito**: Autenticación y autorización de usuarios
- **KMS**: Cifrado de datos en reposo
- **VPC**: Red privada con endpoints para servicios AWS

## Estructura del Proyecto

```
/scheduling-system
├── iac/
│   ├── iam_stack.yml          # Roles y políticas IAM
│   └── main_stack.yml         # Recursos principales AWS
├── src/
│   ├── scheduler_manager/
│   │   └── app.py            # Lambda: CRUD de schedules
│   ├── order_executor/
│   │   └── app.py            # Lambda: Generación de órdenes
│   └── data_generator/
│       └── app.py            # Generador de datos sintéticos
├── data/
│   └── sample_orders.json    # 50+ registros de prueba
├── scripts/
│   ├── package_lambdas.sh    # Empaquetado de Lambdas
│   ├── deploy_stack.sh       # Despliegue de CloudFormation
│   └── curl_tests.sh         # Pruebas funcionales con JWT
└── README.md
```

## Despliegue

### Prerrequisitos:
- AWS CLI configurado
- Python 3.9+
- Permisos de IAM para crear recursos

### Pasos:

1. **Empaquetar Lambdas:**
```bash
cd scripts
./package_lambdas.sh
```

2. **Desplegar Stack de IAM:**
```bash
aws cloudformation deploy \
  --template-file iac/iam_stack.yml \
  --stack-name acme-scheduling-iam \
  --capabilities CAPABILITY_NAMED_IAM
```

3. **Desplegar Stack Principal:**
```bash
./deploy_stack.sh
```

4. **Crear Usuario en Cognito:**
```bash
# Obtener User Pool ID del output del stack
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name acme-scheduling-main \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

# Crear usuario
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username testuser \
  --temporary-password TempPass123! \
  --user-attributes Name=email,Value=test@acme.com
```

5. **Ejecutar Pruebas:**
```bash
./curl_tests.sh
```

## API Endpoints

### POST /schedule
Crear un nuevo schedule para generación automática de órdenes.

**Request:**
```json
{
  "scheduleName": "rocket-shoes-hourly",
  "frequency": "rate(1 hour)",
  "gadgetType": "Rocket Shoes",
  "quantity": 100,
  "enabled": true
}
```

### GET /schedules
Listar todos los schedules activos.

### GET /schedules/{scheduleId}
Obtener detalles de un schedule específico.

### DELETE /schedule/{scheduleId}
Cancelar un schedule existente.

### GET /orders
Consultar órdenes generadas.

**Query Parameters:**
- `status`: filtrar por estado (pending, completed, failed)
- `limit`: número de resultados (default: 50)

## Seguridad

- **Cifrado en reposo**: KMS para DynamoDB y variables de entorno
- **Cifrado en tránsito**: TLS 1.2+ en API Gateway
- **Autenticación**: JWT tokens de Cognito
- **Red privada**: Lambdas en VPC con subredes privadas
- **VPC Endpoints**: Acceso privado a servicios AWS sin internet

## Monitoreo

- CloudWatch Logs para todas las funciones Lambda
- CloudWatch Metrics para API Gateway y DynamoDB
- EventBridge Scheduler logs

## Costos Estimados

- Lambda: ~$0.20/millón de invocaciones
- DynamoDB: On-demand pricing
- API Gateway: ~$3.50/millón de requests
- EventBridge Scheduler: $1.00/millón de invocaciones

## Soporte

Para problemas o preguntas, contactar al equipo de arquitectura de Acme Inc.
>>>>>>> 42783e4 (Initial commit: Célula 2 - Scheduling Serverless System)
