# Acme Image Handler - Serverless Architecture

Sistema serverless para gestión de imágenes de gadgets de Acme Corp, implementado con AWS Lambda, S3, DynamoDB, API Gateway y Cognito.

**Célula**: 3  
**Integrantes**: Alejandro Granados, Rodrigo Pulido  
**Versión**: 1.0  
**Organización**: Universidad La Salle - Ingeniería

## 📋 Descripción

Este proyecto implementa una arquitectura serverless completa para:
- Recibir y almacenar imágenes de productos (gadgets)
- Procesamiento automático (thumbnails, optimización, resize)
- Gestión de metadatos en DynamoDB
- APIs REST seguras con autenticación Cognito
- Pipeline CI/CD automatizado con CodePipeline
- Despliegue multi-ambiente (sandbox, pre-prod, prod)

## 🏗️ Arquitectura

### Componentes Principales

- **Amazon S3**: Almacenamiento de imágenes (raw y processed)
- **AWS Lambda**: Procesamiento de imágenes y API handlers
- **Amazon DynamoDB**: Base de datos de metadatos
- **API Gateway**: Endpoints REST
- **Amazon Cognito**: Autenticación y autorización
- **AWS KMS**: Cifrado de datos
- **VPC**: Aislamiento de red con subredes privadas
- **CodePipeline/CodeBuild**: CI/CD automatizado

### Flujo de Procesamiento

1. Cliente autenticado solicita URL de carga
2. Imagen se sube a S3 (bucket raw)
3. Evento S3 dispara Lambda de procesamiento
4. Lambda genera versiones: original, thumbnail (256px), preview (1024px)
5. Versiones se guardan en S3 (bucket processed)
6. Metadatos se registran en DynamoDB
7. Cliente consulta imágenes vía API Gateway

## 📁 Estructura del Proyecto

```
Célula 3/
├── iac/                          # Infrastructure as Code
│   ├── cloudformation-base.yaml  # Template principal
│   └── pipeline.yaml             # Pipeline CI/CD
├── src/                          # Código fuente
│   └── lambda/
│       ├── image-processor/      # Lambda procesamiento
│       │   ├── lambda_function.py
│       │   └── requirements.txt
│       └── api-handler/          # Lambda API
│           ├── lambda_function.py
│           └── requirements.txt
├── pipeline/                     # Scripts de despliegue
│   ├── deploy.sh
│   ├── parameters-sandbox.json
│   ├── parameters-pre-prod.json
│   └── parameters-prod.json
├── tests/                        # Pruebas y datos
│   ├── generate-test-data.py     # Generador de imágenes
│   └── test-api.sh               # Pruebas funcionales
├── data/                         # Datos de prueba
├── buildspec.yml                 # CodeBuild config
└── README.md
```

## 🚀 Despliegue

### Prerrequisitos

- AWS CLI configurado
- Cuenta AWS con permisos administrativos
- Python 3.11+
- Git

### Configuración Inicial

1. **Clonar el repositorio**
```bash
git clone <repo-url>
cd "Célula 3"
```

2. **Configurar parámetros de ambiente**

Editar los archivos en `pipeline/parameters-*.json` con tus valores:
- VPCId
- PrivateSubnet1
- PrivateSubnet2

### Despliegue Manual

```bash
# Desplegar a sandbox
./pipeline/deploy.sh sandbox

# Desplegar a pre-producción
./pipeline/deploy.sh pre-prod

# Desplegar a producción
./pipeline/deploy.sh prod
```

### Despliegue con CI/CD

1. **Crear el pipeline**
```bash
aws cloudformation create-stack \
  --stack-name acme-pipeline \
  --template-body file://iac/pipeline.yaml \
  --parameters \
    ParameterKey=GitHubOwner,ParameterValue=<your-github-user> \
    ParameterKey=GitHubRepo,ParameterValue=<your-repo> \
    ParameterKey=GitHubToken,ParameterValue=<your-token> \
  --capabilities CAPABILITY_NAMED_IAM
```

2. **Push a main para activar el pipeline**
```bash
git push origin main
```

El pipeline desplegará automáticamente a:
- Sandbox (automático)
- Pre-Prod (aprobación manual)
- Producción (aprobación manual)

## 🧪 Pruebas

### Generar Datos de Prueba

```bash
cd tests
python3 generate-test-data.py
```

Esto genera 50 imágenes sintéticas en `data/test-images/`

### Pruebas Funcionales

```bash
# Configurar variables
export API_URL="https://your-api-id.execute-api.us-east-1.amazonaws.com/sandbox"
export COGNITO_DOMAIN="your-cognito-domain"
export CLIENT_ID="your-client-id"
export USERNAME="test@example.com"
export PASSWORD="YourPassword123!"

# Ejecutar pruebas
./tests/test-api.sh
```

### Pruebas con curl

**1. Obtener token JWT**
```bash
curl -X POST https://<cognito-domain>.auth.us-east-1.amazoncognito.com/oauth2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=<client-id>" \
  -d "username=<email>" \
  -d "password=<password>"
```

**2. Listar imágenes**
```bash
curl -H "Authorization: Bearer <jwt-token>" \
  https://<api-id>.execute-api.us-east-1.amazonaws.com/sandbox/images
```

**3. Obtener URL de carga**
```bash
curl -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"gadgetId": "GADGET-001", "filename": "test.jpg"}' \
  https://<api-id>.execute-api.us-east-1.amazonaws.com/sandbox/upload-url
```

**4. Subir imagen**
```bash
curl -X PUT "<presigned-url>" \
  -H "Content-Type: image/jpeg" \
  --data-binary "@image.jpg"
```

**5. Obtener imagen específica**
```bash
curl -H "Authorization: Bearer <jwt-token>" \
  https://<api-id>.execute-api.us-east-1.amazonaws.com/sandbox/images/<image-id>
```

## 🔒 Seguridad

- **Cifrado**: Todos los datos cifrados con KMS (S3, DynamoDB, logs)
- **Red**: Lambdas en subredes privadas, sin acceso público
- **Autenticación**: Cognito User Pools con JWT
- **Autorización**: API Gateway con Cognito Authorizer
- **IAM**: Roles con permisos mínimos necesarios
- **URLs Firmadas**: Acceso temporal a imágenes (15 minutos)

## 📊 Monitoreo

### CloudWatch Logs

```bash
# Logs del procesador
aws logs tail /aws/lambda/acme-image-handler-processor-sandbox --follow

# Logs del API
aws logs tail /aws/lambda/acme-image-handler-api-sandbox --follow
```

### Métricas

- Lambda invocations, duration, errors
- API Gateway requests, latency, 4xx/5xx
- DynamoDB read/write capacity
- S3 bucket size, requests

## 💰 Estimación de Costos

**Ambiente Sandbox (estimado mensual)**
- Lambda: ~$5 (1M invocaciones)
- API Gateway: ~$3.50 (1M requests)
- S3: ~$2 (10GB storage)
- DynamoDB: ~$1 (on-demand)
- KMS: ~$1
- **Total**: ~$12.50/mes

**Producción** dependerá del volumen de tráfico.

## 📝 Outputs del Stack

Después del despliegue, obtener los outputs:

```bash
aws cloudformation describe-stacks \
  --stack-name acme-image-handler-sandbox \
  --query 'Stacks[0].Outputs' \
  --output table
```

Outputs incluyen:
- ApiUrl
- UserPoolId
- UserPoolClientId
- RawBucketName
- ProcessedBucketName
- DynamoDBTableName

## 🐛 Troubleshooting

**Lambda timeout en VPC**
- Verificar que las subredes tengan NAT Gateway
- Verificar VPC Endpoints para S3 y DynamoDB

**Error de autenticación**
- Verificar que el usuario existe en Cognito
- Verificar que el token no haya expirado (1 hora)

**Imagen no se procesa**
- Verificar logs de Lambda processor
- Verificar que el formato sea válido (JPEG, PNG)
- Verificar permisos de S3

## 📚 Referencias

- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [API Gateway with Cognito](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html)

## 👥 Equipo

- **Alejandro Granados** - Infraestructura y Pipeline
- **Rodrigo Pulido** - Desarrollo Lambda y APIs

## 📚 Documentación Completa

Este proyecto incluye documentación exhaustiva:

- **[INDEX.md](INDEX.md)** - Índice completo de toda la documentación
- **[QUICKSTART.md](QUICKSTART.md)** - Guía rápida de inicio (30 min)
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Guía detallada de despliegue
- **[ACCOUNTS.md](ACCOUNTS.md)** - Configuración de 3 cuentas AWS
- **[COSTS.md](COSTS.md)** - Estimación detallada de costos
- **[BACKLOG.md](BACKLOG.md)** - Product backlog e historias de usuario
- **[EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md)** - Resumen ejecutivo
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Estructura del proyecto
- **[COMMANDS_CHEATSHEET.md](COMMANDS_CHEATSHEET.md)** - Referencia de comandos

## 📄 Licencia

Universidad La Salle - Proyecto Académico 2025
