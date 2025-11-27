# Estructura del Proyecto - Célula 3

## Árbol de Directorios

```
Célula 3/
│
├── README.md                          # Documentación principal
├── QUICKSTART.md                      # Guía rápida de inicio
├── DEPLOYMENT.md                      # Guía detallada de despliegue
├── ACCOUNTS.md                        # Configuración de cuentas AWS
├── COSTS.md                           # Estimación de costos
├── BACKLOG.md                         # Product backlog e historias de usuario
├── PROJECT_STRUCTURE.md               # Este archivo
├── .gitignore                         # Archivos ignorados por Git
├── buildspec.yml                      # Configuración de CodeBuild
│
├── iac/                               # Infrastructure as Code
│   ├── cloudformation-base.yaml       # Template principal de CloudFormation
│   └── pipeline.yaml                  # Template del pipeline CI/CD
│
├── src/                               # Código fuente
│   ├── config.py                      # Configuración compartida
│   └── lambda/                        # Funciones Lambda
│       ├── image-processor/           # Lambda de procesamiento de imágenes
│       │   ├── lambda_function.py     # Handler principal
│       │   └── requirements.txt       # Dependencias Python
│       └── api-handler/               # Lambda del API
│           ├── lambda_function.py     # Handler principal
│           └── requirements.txt       # Dependencias Python
│
├── pipeline/                          # Scripts y configuración de despliegue
│   ├── deploy.sh                      # Script de despliegue manual
│   ├── parameters-sandbox.json        # Parámetros para sandbox
│   ├── parameters-pre-prod.json       # Parámetros para pre-producción
│   └── parameters-prod.json           # Parámetros para producción
│
├── setup/                             # Scripts de configuración inicial
│   ├── setup-accounts.sh              # Configurar cuentas AWS
│   └── create-test-user.sh            # Crear usuario de prueba en Cognito
│
├── tests/                             # Pruebas y datos de prueba
│   ├── generate-test-data.py          # Generador de imágenes sintéticas
│   └── test-api.sh                    # Suite de pruebas funcionales
│
├── data/                              # Datos de prueba
│   ├── test-images/                   # Imágenes generadas (gitignored)
│   └── test-metadata.json             # Metadatos de imágenes de prueba
│
└── docs/                              # Documentación adicional (opcional)
    ├── architecture/                  # Diagramas de arquitectura
    ├── api/                           # Documentación del API
    └── runbooks/                      # Guías operacionales
```

## Descripción de Componentes

### Raíz del Proyecto

#### README.md
Documentación principal del proyecto con:
- Descripción general
- Arquitectura
- Instrucciones de despliegue
- Guía de uso
- Troubleshooting

#### QUICKSTART.md
Guía rápida para poner en marcha el sistema en 30 minutos.

#### DEPLOYMENT.md
Guía detallada de despliegue con:
- Configuración de 3 cuentas AWS
- Setup de VPC y networking
- Despliegue manual y automatizado
- Post-despliegue

#### ACCOUNTS.md
Documentación de las 3 cuentas AWS:
- Build Account (CI/CD)
- Sandbox Account (Desarrollo)
- Production Account (Producción)

#### COSTS.md
Estimación detallada de costos por:
- Servicio AWS
- Ambiente
- Escala de tráfico

#### BACKLOG.md
Product backlog con:
- Historias de usuario
- Estimaciones
- Sprints planificados

#### buildspec.yml
Configuración de CodeBuild para:
- Validar templates
- Instalar dependencias
- Empaquetar Lambdas
- Subir artefactos

### iac/ - Infrastructure as Code

#### cloudformation-base.yaml
Template principal que crea:
- **KMS**: Key para cifrado
- **S3**: Buckets raw y processed
- **DynamoDB**: Tabla GadgetImages
- **Cognito**: User Pool y Client
- **Lambda**: Funciones processor y api-handler
- **API Gateway**: REST API con endpoints
- **VPC**: Security Groups
- **IAM**: Roles y políticas

**Parámetros:**
- EnvironmentName (sandbox/pre-prod/prod)
- VPCId
- PrivateSubnet1
- PrivateSubnet2
- ProjectName

**Outputs:**
- KMSKeyId, KMSKeyArn
- RawBucketName, ProcessedBucketName
- DynamoDBTableName
- UserPoolId, UserPoolClientId, UserPoolDomain
- ApiUrl, ApiId
- Lambda ARNs

#### pipeline.yaml
Template del pipeline CI/CD que crea:
- **CodePipeline**: Pipeline multi-stage
- **CodeBuild**: Proyecto de build
- **S3**: Bucket de artefactos
- **IAM**: Roles para pipeline

**Stages:**
1. Source (GitHub)
2. Build (CodeBuild)
3. Deploy Sandbox (automático)
4. Deploy Pre-Prod (aprobación manual)
5. Deploy Prod (aprobación manual)

### src/ - Código Fuente

#### src/lambda/image-processor/
Lambda que procesa imágenes cuando se suben a S3.

**Funcionalidad:**
- Escucha eventos S3 ObjectCreated
- Valida formato de imagen
- Genera 3 versiones:
  - Original optimizada (quality 95%)
  - Thumbnail 256x256 (quality 85%)
  - Preview 1024x1024 (quality 90%)
- Guarda en bucket processed
- Registra metadatos en DynamoDB

**Dependencias:**
- Pillow (procesamiento de imágenes)
- boto3 (AWS SDK)

**Variables de entorno:**
- PROCESSED_BUCKET
- DYNAMODB_TABLE
- ENVIRONMENT
- KMS_KEY_ID

#### src/lambda/api-handler/
Lambda que maneja requests del API Gateway.

**Endpoints:**
- `POST /upload-url`: Genera presigned URL para subir imagen
- `GET /images`: Lista todas las imágenes (con paginación)
- `GET /images?gadgetId={id}`: Lista imágenes de un gadget
- `GET /images/{imageId}`: Obtiene detalles y URLs firmadas

**Funcionalidad:**
- Autenticación con Cognito JWT
- Generación de presigned URLs (15 min)
- Consultas a DynamoDB
- Manejo de errores

**Dependencias:**
- boto3 (AWS SDK)

**Variables de entorno:**
- RAW_BUCKET
- PROCESSED_BUCKET
- DYNAMODB_TABLE
- ENVIRONMENT
- KMS_KEY_ID

### pipeline/ - Despliegue

#### deploy.sh
Script bash para despliegue manual.

**Uso:**
```bash
./pipeline/deploy.sh <environment> [stack-name]
```

**Funcionalidad:**
- Valida template CloudFormation
- Verifica si stack existe
- Crea o actualiza stack
- Espera a que complete
- Muestra outputs

#### parameters-*.json
Archivos de parámetros por ambiente.

**Estructura:**
```json
[
  {"ParameterKey": "EnvironmentName", "ParameterValue": "sandbox"},
  {"ParameterKey": "VPCId", "ParameterValue": "vpc-xxx"},
  {"ParameterKey": "PrivateSubnet1", "ParameterValue": "subnet-xxx"},
  {"ParameterKey": "PrivateSubnet2", "ParameterValue": "subnet-yyy"},
  {"ParameterKey": "ProjectName", "ParameterValue": "acme-image-handler"}
]
```

### setup/ - Configuración Inicial

#### setup-accounts.sh
Script para configurar las cuentas AWS automáticamente.

**Funcionalidad:**
- Verifica perfiles AWS CLI
- Crea VPCs en sandbox y prod
- Crea subnets privadas
- Actualiza archivos de parámetros

#### create-test-user.sh
Script para crear usuarios de prueba en Cognito.

**Funcionalidad:**
- Obtiene User Pool ID del stack
- Crea usuario con email
- Establece password permanente
- Muestra información para pruebas

### tests/ - Pruebas

#### generate-test-data.py
Script Python para generar imágenes sintéticas.

**Funcionalidad:**
- Genera 50 imágenes únicas
- Diferentes dimensiones y colores
- Metadatos en JSON
- Categorías variadas de gadgets

**Output:**
- `data/test-images/GADGET-XXXX.jpg`
- `data/test-metadata.json`

#### test-api.sh
Suite de pruebas funcionales con curl.

**Tests:**
1. Autenticación con Cognito
2. Listar imágenes
3. Obtener URL de carga
4. Subir imagen (opcional)
5. Listar por gadgetId
6. Obtener imagen específica

**Variables requeridas:**
- API_URL
- COGNITO_DOMAIN
- CLIENT_ID
- USERNAME
- PASSWORD

### data/ - Datos de Prueba

#### test-images/
Directorio con imágenes generadas (gitignored).

#### test-metadata.json
Metadatos de las imágenes de prueba en formato JSON.

## Flujo de Trabajo

### Desarrollo Local

1. Modificar código en `src/lambda/`
2. Probar localmente (opcional)
3. Commit y push a GitHub
4. Pipeline despliega automáticamente

### Despliegue Manual

1. Editar parámetros en `pipeline/parameters-*.json`
2. Ejecutar `./pipeline/deploy.sh sandbox`
3. Verificar outputs
4. Crear usuario de prueba
5. Ejecutar pruebas

### Despliegue con CI/CD

1. Push a branch main
2. Pipeline se activa automáticamente
3. Build empaqueta Lambdas
4. Deploy a sandbox (automático)
5. Aprobar deploy a pre-prod
6. Aprobar deploy a prod

## Comandos Frecuentes

```bash
# Desplegar
./pipeline/deploy.sh sandbox

# Crear usuario
./setup/create-test-user.sh sandbox

# Generar datos
python3 tests/generate-test-data.py

# Probar API
./tests/test-api.sh

# Ver logs
aws logs tail /aws/lambda/acme-image-handler-processor-sandbox --follow

# Ver stack
aws cloudformation describe-stacks --stack-name acme-image-handler-sandbox

# Eliminar stack
aws cloudformation delete-stack --stack-name acme-image-handler-sandbox
```

## Convenciones

### Nombres de Recursos
- Stack: `acme-image-handler-{environment}`
- Lambda: `acme-image-handler-{function}-{environment}`
- Bucket: `acme-gadgets-{type}-{account-id}-{environment}`
- Tabla: `GadgetImages-{environment}`

### Tags
Todos los recursos tienen:
- `Environment`: sandbox/pre-prod/prod
- `Project`: acme-image-handler

### Regiones
- Por defecto: `us-east-1`
- Configurable vía AWS_REGION

## Seguridad

### Secretos
NUNCA commitear:
- Credenciales AWS
- Passwords
- Tokens de GitHub
- Keys privadas

### Cifrado
Todo cifrado con KMS:
- S3 buckets
- DynamoDB
- CloudWatch Logs
- Variables de entorno Lambda

### Red
- Lambdas en subnets privadas
- Sin acceso público directo
- VPC Endpoints para servicios AWS

## Mantenimiento

### Logs
- Retención: 30 días
- Ubicación: `/aws/lambda/{function-name}`

### Backups
- S3: Versionado habilitado
- DynamoDB: Point-in-time recovery

### Actualizaciones
- Dependencias Python: Revisar mensualmente
- Runtime Lambda: Actualizar cuando AWS deprece versión

## Contacto

**Equipo:**
- Alejandro Granados
- Rodrigo Pulido

**Universidad:** La Salle - Ingeniería  
**Proyecto:** Arquitecturas Serverless en AWS  
**Célula:** 3 - Image Handler
