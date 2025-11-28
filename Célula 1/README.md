# AWS Cartoon Rekognition - Serverless Image Analysis System

## Descripción del Proyecto

Esta solución implementa una arquitectura serverless en AWS para el análisis automatizado de imágenes de caricaturas. El sistema permite a usuarios autenticados subir imágenes mediante URLs presignadas, procesa automáticamente las imágenes usando Amazon Rekognition para identificar personajes, almacena resultados en DynamoDB, y expone una API REST segura para consultar resultados.

### Características Principales

- **Autenticación Segura**: Integración con Amazon Cognito para autenticación JWT
- **Procesamiento Automático**: Análisis de imágenes mediante Amazon Rekognition
- **API REST**: Endpoints seguros para subida y consulta de resultados
- **Cifrado End-to-End**: KMS CMKs dedicadas para S3, DynamoDB, CloudWatch Logs
- **Infraestructura como Código**: 100% definida en CloudFormation
- **CI/CD Automatizado**: Pipeline completo con CodePipeline y CodeBuild
- **Multi-Ambiente**: Soporte para sandbox, preprod y producción
- **Red Privada**: Lambdas ejecutando en VPC con VPC Endpoints

## Arquitectura

La solución utiliza una arquitectura serverless multi-stack con los siguientes componentes:

```
Usuario → Cognito → API Gateway → Lambda Functions
                                      ↓
                    S3 ← → Rekognition → DynamoDB
                    
Todo dentro de VPC con VPC Endpoints
Cifrado KMS en todos los servicios
```

### Componentes Principales

1. **Amazon Cognito**: Autenticación y autorización de usuarios
2. **API Gateway**: Endpoints REST con autorización JWT
3. **AWS Lambda**: 3 funciones serverless
   - GeneratePresignedUrl: Genera URLs para subida
   - S3EventProcessor: Procesa imágenes con Rekognition
   - QueryResults: Consulta resultados de análisis
4. **Amazon S3**: Almacenamiento de imágenes con cifrado
5. **Amazon Rekognition**: Análisis de imágenes y detección de personajes
6. **Amazon DynamoDB**: Base de datos NoSQL para resultados
7. **AWS KMS**: Gestión de claves de cifrado
8. **VPC**: Red privada con subredes y VPC Endpoints

Para un diagrama detallado de la arquitectura, consulte `diagram.drawio` (cuando esté disponible).

## Prerrequisitos

Antes de desplegar esta solución, asegúrese de tener:

### Software Requerido

- **AWS CLI**: Versión 2.x o superior
  ```bash
  aws --version
  ```
- **Python**: Versión 3.11 o superior
  ```bash
  python --version
  ```
- **Git**: Para clonar el repositorio
  ```bash
  git --version
  ```
- **pip**: Gestor de paquetes de Python
  ```bash
  pip --version
  ```

### Cuenta AWS

- Cuenta AWS activa con permisos para crear:
  - CloudFormation stacks
  - IAM roles y políticas
  - VPC, subnets, security groups
  - Lambda functions
  - API Gateway
  - S3 buckets
  - DynamoDB tables
  - Cognito User Pools
  - KMS keys
  - CodePipeline y CodeBuild

### Configuración AWS CLI

Configure sus credenciales de AWS:

```bash
aws configure
```

Proporcione:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (ej: us-east-1)
- Default output format (json)

## Estructura del Repositorio

```
.
├── .kiro/
│   └── specs/
│       └── aws-cartoon-rekognition/    # Especificaciones del proyecto
│           ├── requirements.md
│           ├── design.md
│           └── tasks.md
├── data/
│   ├── dataset_metadata.json           # Datos sintéticos para testing
│   └── README.md
├── iac/                                # Plantillas CloudFormation
│   ├── kms.yml                        # CMKs para cifrado
│   ├── network.yml                    # VPC, subnets, endpoints
│   ├── s3.yml                         # Bucket de imágenes
│   ├── dynamodb.yml                   # Tabla de resultados
│   ├── cognito.yml                    # User Pool
│   ├── lambda.yml                     # Funciones Lambda
│   ├── api_gateway.yml                # REST API
│   ├── pipeline.yml                   # CI/CD Pipeline
│   ├── params-sandbox.json            # Parámetros sandbox
│   ├── params-preprod.json            # Parámetros preprod
│   ├── params-prod.json               # Parámetros producción
│   └── README.md
├── scripts/
│   ├── deploy.sh                      # Script de despliegue
│   └── README.md
├── src/
│   ├── lambdas/
│   │   ├── generate_presigned/        # Lambda: Generar URL presignada
│   │   │   └── handler.py
│   │   ├── s3_event_processor/        # Lambda: Procesar imágenes
│   │   │   └── handler.py
│   │   └── query_results/             # Lambda: Consultar resultados
│   │       └── handler.py
│   ├── generate_synthetic_data.py     # Generador de datos de prueba
│   └── README.md
├── tests/
│   ├── unit/                          # Tests unitarios
│   ├── property/                      # Property-based tests
│   ├── integration/                   # Tests de integración
│   └── README.md
├── buildspec.yml                      # Configuración CodeBuild
├── requirements.txt                   # Dependencias Python
├── pruebas_curl.md                    # Ejemplos de uso con curl
├── cost_estimate.md                   # Estimación de costos
├── validate_cfn.py                    # Validador de plantillas
├── validate_pipeline.py               # Validador de pipeline
└── README.md                          # Este archivo
```

## Instrucciones de Despliegue

### Paso 1: Clonar el Repositorio

```bash
git clone <repository-url>
cd aws-cartoon-rekognition
```

### Paso 2: Instalar Dependencias

```bash
pip install -r requirements.txt
```

### Paso 3: Configurar Parámetros

Edite los archivos de parámetros según su ambiente:

**Para Sandbox:**
```bash
nano iac/params-sandbox.json
```

**Para Preprod:**
```bash
nano iac/params-preprod.json
```

**Para Producción:**
```bash
nano iac/params-prod.json
```

Ajuste los valores según sus necesidades:
- `Environment`: sandbox, preprod, o prod
- `ProjectName`: Nombre del proyecto
- `VpcCidr`: CIDR de la VPC (default: 10.0.0.0/16)
- `LogRetentionDays`: Días de retención de logs

### Paso 4: Validar Plantillas CloudFormation

Antes de desplegar, valide las plantillas:

```bash
# Validar sintaxis
python validate_cfn.py

# Lint de plantillas
cfn-lint iac/*.yml
```

### Paso 5: Ejecutar Tests

```bash
# Tests unitarios
pytest tests/unit/ -v

# Property-based tests
pytest tests/property/ -v

# Tests de integración (requiere ambiente desplegado)
pytest tests/integration/ -v
```

### Paso 6: Desplegar Infraestructura

**Opción A: Despliegue Manual**

```bash
# Dar permisos de ejecución al script
chmod +x scripts/deploy.sh

# Desplegar a sandbox
./scripts/deploy.sh sandbox

# Desplegar a preprod
./scripts/deploy.sh preprod

# Desplegar a producción
./scripts/deploy.sh prod
```

**Opción B: Despliegue mediante CI/CD**

1. Configure GitHub connection en CodePipeline
2. Haga push a la rama principal
3. El pipeline se ejecutará automáticamente
4. Apruebe manualmente los despliegues a preprod y prod

### Paso 7: Verificar Stacks en CloudFormation

```bash
# Listar stacks
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE

# Ver detalles de un stack
aws cloudformation describe-stacks --stack-name cartoon-rekognition-network-sandbox

# Ver outputs de un stack
aws cloudformation describe-stacks --stack-name cartoon-rekognition-api-sandbox \
  --query 'Stacks[0].Outputs'
```

### Orden de Despliegue de Stacks

El script `deploy.sh` despliega los stacks en el siguiente orden:

1. `network.yml` - VPC, subnets, VPC endpoints
2. `kms.yml` - CMKs para cifrado
3. `s3.yml` - Bucket de imágenes
4. `dynamodb.yml` - Tabla de resultados
5. `cognito.yml` - User Pool
6. `lambda.yml` - Funciones Lambda
7. `api_gateway.yml` - REST API
8. `pipeline.yml` - CI/CD Pipeline (opcional)

## Configuración de Cognito

### Crear Usuario de Prueba

Una vez desplegado Cognito, cree un usuario de prueba:

```bash
# Obtener User Pool ID
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name cartoon-rekognition-cognito-sandbox \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

# Crear usuario
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username testuser \
  --user-attributes Name=email,Value=test@example.com \
  --temporary-password TempPass123! \
  --message-action SUPPRESS

# Confirmar usuario y establecer contraseña permanente
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username testuser \
  --password MySecurePass123! \
  --permanent
```

### Autenticar y Obtener JWT

```bash
# Obtener App Client ID
APP_CLIENT_ID=$(aws cloudformation describe-stacks \
  --stack-name cartoon-rekognition-cognito-sandbox \
  --query 'Stacks[0].Outputs[?OutputKey==`AppClientId`].OutputValue' \
  --output text)

# Autenticar
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id $APP_CLIENT_ID \
  --auth-parameters USERNAME=testuser,PASSWORD=MySecurePass123! \
  --query 'AuthenticationResult.IdToken' \
  --output text
```

Guarde el token JWT para usarlo en las llamadas a la API.

## Pruebas

### Pruebas con curl

Para ejemplos detallados de cómo usar la API con curl, consulte:

**[pruebas_curl.md](pruebas_curl.md)**

Este documento incluye:
- Autenticación con Cognito
- Obtener URL presignada para subida
- Subir imagen a S3
- Consultar resultados de análisis
- Manejo de errores (401, 404, 500)

### Flujo End-to-End

```bash
# 1. Obtener JWT (ver sección anterior)
JWT_TOKEN="<your-jwt-token>"

# 2. Obtener URL presignada
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name cartoon-rekognition-api-sandbox \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

curl -X GET "${API_ENDPOINT}/prod/get-upload-url?filename=mickey.jpg&contentType=image/jpeg" \
  -H "Authorization: Bearer ${JWT_TOKEN}"

# 3. Subir imagen (usar uploadUrl de la respuesta anterior)
curl -X PUT "<presigned-url>" \
  --upload-file mickey.jpg \
  -H "Content-Type: image/jpeg"

# 4. Esperar procesamiento (5-10 segundos)
sleep 10

# 5. Consultar resultados (usar imageId de paso 2)
curl -X GET "${API_ENDPOINT}/prod/result?imageId=<image-id>" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

## Monitoreo y Logs

### CloudWatch Logs

Todos los logs están centralizados en CloudWatch:

```bash
# Ver logs de Lambda GeneratePresignedUrl
aws logs tail /aws/lambda/cartoon-rekognition-generate-presigned-sandbox --follow

# Ver logs de Lambda S3EventProcessor
aws logs tail /aws/lambda/cartoon-rekognition-s3-processor-sandbox --follow

# Ver logs de Lambda QueryResults
aws logs tail /aws/lambda/cartoon-rekognition-query-results-sandbox --follow

# Ver logs de API Gateway
aws logs tail /aws/apigateway/cartoon-rekognition-api-sandbox --follow
```

### CloudWatch Metrics

Métricas clave a monitorear:

**Lambda:**
- Invocations: Número de invocaciones
- Errors: Número de errores
- Duration: Tiempo de ejecución
- Throttles: Invocaciones limitadas

**API Gateway:**
- Count: Número de requests
- 4XXError: Errores de cliente
- 5XXError: Errores de servidor
- Latency: Latencia de respuesta

**DynamoDB:**
- ConsumedReadCapacityUnits
- ConsumedWriteCapacityUnits
- UserErrors: Errores de throttling

### Alarmas CloudWatch

Configure alarmas para:

```bash
# Errores de Lambda > 5 en 5 minutos
aws cloudwatch put-metric-alarm \
  --alarm-name lambda-errors-high \
  --alarm-description "Lambda errors exceeded threshold" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold

# API Gateway 5xx > 1% de requests
aws cloudwatch put-metric-alarm \
  --alarm-name api-5xx-high \
  --alarm-description "API 5xx errors exceeded 1%" \
  --metric-name 5XXError \
  --namespace AWS/ApiGateway \
  --statistic Average \
  --period 300 \
  --threshold 0.01 \
  --comparison-operator GreaterThanThreshold
```

### X-Ray Tracing

X-Ray está habilitado en todas las Lambdas para tracing distribuido:

```bash
# Ver traces en consola
aws xray get-trace-summaries --start-time $(date -u -d '1 hour ago' +%s) --end-time $(date -u +%s)
```

## Troubleshooting

### Problemas Comunes

#### 1. Error: "Stack already exists"

**Causa**: Intento de crear un stack que ya existe

**Solución**:
```bash
# Actualizar stack existente
aws cloudformation update-stack --stack-name <stack-name> --template-body file://template.yml

# O eliminar y recrear
aws cloudformation delete-stack --stack-name <stack-name>
aws cloudformation wait stack-delete-complete --stack-name <stack-name>
```

#### 2. Lambda Timeout

**Causa**: Lambda excede el tiempo de ejecución configurado

**Solución**:
- Aumentar timeout en `lambda.yml`
- Optimizar código Lambda
- Verificar conectividad VPC Endpoints

```bash
# Ver duración promedio
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=<function-name> \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

#### 3. Error 401 Unauthorized

**Causa**: JWT inválido o expirado

**Solución**:
```bash
# Verificar expiración del token
echo $JWT_TOKEN | cut -d'.' -f2 | base64 -d | jq .exp

# Obtener nuevo token
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id $APP_CLIENT_ID \
  --auth-parameters USERNAME=testuser,PASSWORD=MySecurePass123!
```

#### 4. Rekognition No Detecta Personajes

**Causa**: Imagen de baja calidad o personaje no reconocido

**Solución**:
- Usar imágenes de alta resolución (>1024px)
- Verificar que la imagen contenga caricaturas claras
- Revisar logs de S3EventProcessor para ver labels detectados

```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/cartoon-rekognition-s3-processor-sandbox \
  --filter-pattern "Labels detected"
```

#### 5. VPC Endpoint Connection Issues

**Causa**: Security groups o NACLs bloqueando tráfico

**Solución**:
```bash
# Verificar security groups
aws ec2 describe-security-groups --group-ids <sg-id>

# Verificar VPC endpoints
aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=<vpc-id>"

# Test de conectividad desde Lambda
# Agregar código de prueba en Lambda para verificar acceso a servicios
```

#### 6. CloudFormation Rollback

**Causa**: Error durante creación/actualización de stack

**Solución**:
```bash
# Ver eventos del stack
aws cloudformation describe-stack-events --stack-name <stack-name> \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`]'

# Ver razón del fallo
aws cloudformation describe-stack-events --stack-name <stack-name> \
  --max-items 10 \
  --query 'StackEvents[*].[ResourceStatus,ResourceStatusReason]'
```

### Logs de Debugging

```bash
# Habilitar logging detallado en Lambda
# Agregar en handler.py:
import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Ver logs en tiempo real
aws logs tail /aws/lambda/<function-name> --follow --format short
```

### Validación de Configuración

```bash
# Verificar que todos los stacks estén desplegados
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  | grep cartoon-rekognition

# Verificar outputs de stacks
for stack in network kms s3 dynamodb cognito lambda api; do
  echo "=== Stack: $stack ==="
  aws cloudformation describe-stacks \
    --stack-name cartoon-rekognition-$stack-sandbox \
    --query 'Stacks[0].Outputs'
done
```

## Costos

### Estimación de Costos

Para una estimación detallada de costos mensuales, consulte:

**[cost_estimate.md](cost_estimate.md)**

### Resumen de Costos (Producción)

Basado en 10,000 imágenes/mes y 50,000 API calls/mes:

| Servicio | Costo Mensual Estimado |
|----------|------------------------|
| Lambda | $0.50 |
| API Gateway | $0.18 |
| S3 | $2.50 |
| DynamoDB | $1.50 |
| Rekognition | $10.00 |
| CloudWatch Logs | $5.00 |
| KMS | $4.40 |
| VPC Endpoints | $28.80 |
| NAT Gateway | $97.20 |
| Cognito | $0.00 (free tier) |
| **Total** | **~$150/mes** |

### Optimización de Costos

**Recomendaciones:**

1. **Eliminar NAT Gateway en sandbox**: Usar solo VPC Endpoints
2. **Reducir retención de logs**: 7 días en sandbox, 30 en prod
3. **Lifecycle policies en S3**: Mover a Glacier después de 90 días
4. **DynamoDB On-Demand**: Cambiar a provisioned si el tráfico es predecible
5. **Lambda ARM64**: Usar Graviton2 para 20% de ahorro

```bash
# Ver costos actuales con Cost Explorer
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '1 month ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=SERVICE
```

## Limpieza (Eliminar Recursos)

### Eliminar Todos los Recursos

**ADVERTENCIA**: Esto eliminará permanentemente todos los recursos y datos.

```bash
# Script de limpieza
./scripts/cleanup.sh sandbox

# O manualmente en orden inverso:
aws cloudformation delete-stack --stack-name cartoon-rekognition-pipeline-sandbox
aws cloudformation delete-stack --stack-name cartoon-rekognition-api-sandbox
aws cloudformation delete-stack --stack-name cartoon-rekognition-lambda-sandbox
aws cloudformation delete-stack --stack-name cartoon-rekognition-cognito-sandbox
aws cloudformation delete-stack --stack-name cartoon-rekognition-dynamodb-sandbox

# Vaciar bucket S3 antes de eliminar
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name cartoon-rekognition-s3-sandbox \
  --query 'Stacks[0].Outputs[?OutputKey==`BucketName`].OutputValue' \
  --output text)

aws s3 rm s3://$BUCKET_NAME --recursive
aws cloudformation delete-stack --stack-name cartoon-rekognition-s3-sandbox

aws cloudformation delete-stack --stack-name cartoon-rekognition-kms-sandbox
aws cloudformation delete-stack --stack-name cartoon-rekognition-network-sandbox

# Esperar a que se completen las eliminaciones
aws cloudformation wait stack-delete-complete --stack-name cartoon-rekognition-network-sandbox
```

### Verificar Eliminación

```bash
# Verificar que no queden stacks
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  | grep cartoon-rekognition

# Verificar que no queden recursos huérfanos
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Project,Values=cartoon-rekognition
```

## Soporte y Contribuciones

### Reportar Problemas

Si encuentra problemas o bugs:

1. Revise la sección de Troubleshooting
2. Verifique los logs en CloudWatch
3. Cree un issue en el repositorio con:
   - Descripción del problema
   - Pasos para reproducir
   - Logs relevantes
   - Ambiente (sandbox/preprod/prod)

### Contribuir

Para contribuir al proyecto:

1. Fork el repositorio
2. Cree una rama para su feature: `git checkout -b feature/nueva-funcionalidad`
3. Commit sus cambios: `git commit -am 'Agregar nueva funcionalidad'`
4. Push a la rama: `git push origin feature/nueva-funcionalidad`
5. Cree un Pull Request

### Documentación Adicional

- **Especificaciones**: `.kiro/specs/aws-cartoon-rekognition/`
- **Pruebas con curl**: `pruebas_curl.md`
- **Estimación de costos**: `cost_estimate.md`
- **Scripts de despliegue**: `scripts/README.md`
- **Tests**: `tests/README.md`
- **Infraestructura**: `iac/README.md`

## Licencia

[Especificar licencia del proyecto]

## Contacto

[Especificar información de contacto]

---

**Última actualización**: Noviembre 2025
