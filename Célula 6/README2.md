# Sistema de Procesamiento Distribuido de Toons

Sistema serverless en AWS para procesamiento distribuido y escalable de trabajos (jobs) compuestos por múltiples "toons". Utiliza arquitectura event-driven con Lambda, SQS, DynamoDB y API Gateway.

## 📋 Tabla de Contenidos

- [Arquitectura](#arquitectura)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Funciones Lambda y Endpoints](#funciones-lambda-y-endpoints)
- [Pipeline de CI/CD](#pipeline-de-cicd)
- [Despliegue](#despliegue)
- [Pruebas con curl](#pruebas-con-curl)
- [Variables de Entorno](#variables-de-entorno)
- [Desarrollo Local](#desarrollo-local)
- [Monitoreo y Logs](#monitoreo-y-logs)

## 🏗️ Arquitectura

```
┌─────────────┐
│   Cliente   │
└──────┬──────┘
       │ POST /submit-job (JWT)
       ▼
┌─────────────────┐
│  API Gateway    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│ Lambda          │─────▶│  DynamoDB    │
│ SubmitJob       │      │  (Jobs)      │
└────────┬────────┘      └──────────────┘
         │
         │ Fan-out (1 msg/toon)
         ▼
┌─────────────────┐
│   SQS Queue     │
└────────┬────────┘
         │
         │ Trigger (batch=1)
         ▼
┌─────────────────┐      ┌──────────────┐
│ Lambda Worker   │─────▶│  DynamoDB    │
│ (Paralelo)      │      │  (Results)   │
└─────────────────┘      └──────────────┘

         │
         │ GET /jobs/{jobId}
         │ GET /results?jobId=X
         ▼
┌─────────────────┐
│ Lambda          │
│ GetJobStatus    │
│ GetResults      │
└─────────────────┘
```

**Componentes:**
- **API Gateway**: Endpoints REST autenticados con JWT
- **Lambda Functions**: 4 funciones serverless (SubmitJob, Worker, GetJobStatus, GetResults)
- **SQS**: Cola para procesamiento asíncrono con fan-out
- **DynamoDB**: 2 tablas (ToonJobs, ToonResults)
- **CloudWatch**: Logs estructurados y métricas

## 📁 Estructura del Proyecto

```
.
├── src/                          # CÓDIGO EJECUTABLE
│   ├── lambdas/                  # Funciones Lambda
│   │   ├── submit_job/           # POST /submit-job
│   │   │   └── handler.py
│   │   ├── worker/               # Procesador de toons
│   │   │   └── handler.py
│   │   ├── get_job_status/       # GET /jobs/{jobId}
│   │   │   └── handler.py
│   │   └── get_results/          # GET /results
│   │       └── handler.py
│   ├── business_logic/           # Lógica de negocio
│   │   ├── job_manager.py        # Gestión de jobs
│   │   └── toon_processor.py    # Procesamiento de toons
│   └── utils/                    # Utilidades compartidas
│       ├── auth.py               # Validación JWT
│       ├── dynamodb.py           # Helpers DynamoDB
│       └── logger.py             # Logging estructurado
├── iac/                          # INFRAESTRUCTURA
│   ├── cloudformation-template.yaml  # Template principal
│   ├── parameters.json           # Parámetros por ambiente
│   └── deploy.sh                 # Script de despliegue
├── data/                         # DATOS DE PRUEBA
│   ├── sample_jobs.json          # Jobs de ejemplo
│   ├── sample_toons.json         # Toons individuales
│   └── test_request.json         # Request completo
├── tests/                        # Tests unitarios
│   ├── test_job_manager.py
│   └── test_toon_processor.py
├── scripts/                      # Scripts de utilidad
│   ├── package-lambdas.sh        # Empaquetar localmente
│   └── validate-templates.sh     # Validar CloudFormation
├── buildspec.yml                 # AWS CodeBuild config
├── requirements.txt              # Dependencias Python
└── README.md                     # Este archivo
```


## 🔧 Funciones Lambda y Endpoints

### 1. Lambda SubmitJob

**Endpoint:** `POST /submit-job`  
**Autenticación:** JWT (Bearer token)

**Función:**
- Recibe un job con lista de toons (1...n)
- Valida el payload (jobId, toons con toonId y type)
- Registra el job en DynamoDB con estado `Pending`
- Divide el lote y envía cada toon como mensaje individual a SQS (fan-out)
- Actualiza el estado del job a `Processing`
- Retorna confirmación con jobId

**Request:**
```json
{
  "jobId": "JOB-001",
  "toons": [
    {
      "toonId": "TOON-001",
      "type": "IMAGE",
      "payload": {
        "url": "https://example.com/image.jpg",
        "width": 1920,
        "height": 1080
      }
    },
    {
      "toonId": "TOON-002",
      "type": "VIDEO",
      "payload": {
        "url": "https://example.com/video.mp4",
        "duration": 120
      }
    }
  ]
}
```

**Response:**
```json
{
  "message": "Job submitted successfully",
  "jobId": "JOB-001",
  "toonsCount": 2,
  "status": "Processing"
}
```

### 2. Lambda Worker

**Trigger:** SQS (1 toon por invocación)  
**Procesamiento:** Paralelo y asíncrono

**Función:**
- Recibe mensaje de SQS con un toon
- Extrae datos: toonId, type, payload
- **Procesa el toon:**
  - Transformación: Normaliza y estructura datos
  - Validación: Verifica reglas de negocio por tipo
  - Enriquecimiento: Agrega metadatos calculados
- Calcula hash/fingerprint (SHA256) del toon procesado
- Mide duración del procesamiento en ms
- Guarda resultado en DynamoDB (tabla ToonResults)
- Incrementa contador de toons procesados en el job
- Verifica si el job está completo y actualiza estado
- **Idempotente:** Usa cache en memoria para evitar reprocesar

**Características:**
- Timeout: 300 segundos
- Memory: 1024 MB
- Concurrencia: Hasta 1000 invocaciones simultáneas
- Dead Letter Queue (DLQ) después de 3 reintentos

### 3. Lambda GetJobStatus

**Endpoint:** `GET /jobs/{jobId}`  
**Autenticación:** JWT (Bearer token)

**Función:**
- Consulta información del job en DynamoDB
- Retorna estado actual, progreso y metadatos
- Calcula porcentaje de completitud

**Response:**
```json
{
  "jobId": "JOB-001",
  "status": "Processing",
  "totalToons": 10,
  "processedToons": 7,
  "userId": "user123",
  "metadata": {
    "createdAt": "2025-11-27T20:00:00Z",
    "updatedAt": "2025-11-27T20:05:30Z"
  },
  "progress": {
    "percentage": 70.0,
    "completed": false
  }
}
```

### 4. Lambda GetResults

**Endpoint:** `GET /results?jobId=JOB001`  
**Autenticación:** JWT (Bearer token)

**Función:**
- Consulta todos los resultados procesados de un job
- Retorna lista de toons con sus resultados
- Incluye fingerprint, duración, validación y datos procesados

**Response:**
```json
{
  "jobId": "JOB-001",
  "jobStatus": "Completed",
  "totalToons": 2,
  "resultsCount": 2,
  "results": [
    {
      "toonId": "TOON-001",
      "type": "IMAGE",
      "fingerprint": "a3f5b8c...",
      "durationMs": 150,
      "isValid": true,
      "processedAt": "2025-11-27T20:01:00Z",
      "processedData": {
        "toonId": "TOON-001",
        "type": "IMAGE",
        "enrichment": {
          "complexity": "MEDIUM",
          "category": "MEDIA"
        }
      }
    }
  ]
}
```


## 🚀 Pipeline de CI/CD

### Flujo Completo: GitHub → CodePipeline → CodeBuild → CloudFormation

```
┌──────────────┐
│   GitHub     │  Push a main/develop
│  Repository  │
└──────┬───────┘
       │
       │ Webhook
       ▼
┌──────────────────┐
│  CodePipeline    │  Orquesta el pipeline
└──────┬───────────┘
       │
       │ Source Stage
       ▼
┌──────────────────┐
│   CodeBuild      │  Ejecuta buildspec.yml
│                  │  - Instala deps
│                  │  - Ejecuta tests
│                  │  - Empaqueta Lambdas
│                  │  - Valida IaC
└──────┬───────────┘
       │
       │ Artifacts (dist/*.zip)
       ▼
┌──────────────────┐
│  CloudFormation  │  Deploy Stage
│                  │  - Crea/actualiza stack
│                  │  - Despliega Lambdas
│                  │  - Configura recursos
└──────┬───────────┘
       │
       ├─────────────────┐─────────────────┐
       ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Sandbox    │  │   PreProd    │  │     Prod     │
│   (dev)      │  │  (staging)   │  │ (production) │
└──────────────┘  └──────────────┘  └──────────────┘
```

### Ambientes

| Ambiente | Branch | Aprobación Manual | Características |
|----------|--------|-------------------|-----------------|
| **Sandbox (dev)** | `develop` | No | Testing rápido, datos sintéticos |
| **PreProd (staging)** | `main` | Sí | Validación pre-producción |
| **Prod (production)** | `main` | Sí | Ambiente productivo |

### Configuración del Pipeline

#### 1. Crear Pipeline en AWS CodePipeline

```bash
# Desde AWS Console o CLI
aws codepipeline create-pipeline --cli-input-json file://pipeline-config.json
```

**pipeline-config.json:**
```json
{
  "pipeline": {
    "name": "ToonProcessor-Pipeline",
    "roleArn": "arn:aws:iam::ACCOUNT_ID:role/CodePipelineServiceRole",
    "stages": [
      {
        "name": "Source",
        "actions": [{
          "name": "SourceAction",
          "actionTypeId": {
            "category": "Source",
            "owner": "ThirdParty",
            "provider": "GitHub",
            "version": "1"
          },
          "configuration": {
            "Owner": "YOUR_GITHUB_USER",
            "Repo": "toon-processor",
            "Branch": "main",
            "OAuthToken": "{{resolve:secretsmanager:github-token}}"
          },
          "outputArtifacts": [{"name": "SourceOutput"}]
        }]
      },
      {
        "name": "Build",
        "actions": [{
          "name": "BuildAction",
          "actionTypeId": {
            "category": "Build",
            "owner": "AWS",
            "provider": "CodeBuild",
            "version": "1"
          },
          "configuration": {
            "ProjectName": "ToonProcessor-Build"
          },
          "inputArtifacts": [{"name": "SourceOutput"}],
          "outputArtifacts": [{"name": "BuildOutput"}]
        }]
      },
      {
        "name": "Deploy-Sandbox",
        "actions": [{
          "name": "DeployToSandbox",
          "actionTypeId": {
            "category": "Deploy",
            "owner": "AWS",
            "provider": "CloudFormation",
            "version": "1"
          },
          "configuration": {
            "ActionMode": "CREATE_UPDATE",
            "StackName": "toon-processor-dev",
            "TemplatePath": "BuildOutput::iac/cloudformation-template.yaml",
            "ParameterOverrides": "{\"Environment\":\"dev\"}",
            "Capabilities": "CAPABILITY_NAMED_IAM"
          },
          "inputArtifacts": [{"name": "BuildOutput"}]
        }]
      },
      {
        "name": "Deploy-PreProd",
        "actions": [{
          "name": "ApprovalForPreProd",
          "actionTypeId": {
            "category": "Approval",
            "owner": "AWS",
            "provider": "Manual",
            "version": "1"
          }
        }, {
          "name": "DeployToPreProd",
          "actionTypeId": {
            "category": "Deploy",
            "owner": "AWS",
            "provider": "CloudFormation",
            "version": "1"
          },
          "configuration": {
            "ActionMode": "CREATE_UPDATE",
            "StackName": "toon-processor-staging",
            "TemplatePath": "BuildOutput::iac/cloudformation-template.yaml",
            "ParameterOverrides": "{\"Environment\":\"staging\"}",
            "Capabilities": "CAPABILITY_NAMED_IAM"
          },
          "inputArtifacts": [{"name": "BuildOutput"}],
          "runOrder": 2
        }]
      },
      {
        "name": "Deploy-Prod",
        "actions": [{
          "name": "ApprovalForProd",
          "actionTypeId": {
            "category": "Approval",
            "owner": "AWS",
            "provider": "Manual",
            "version": "1"
          }
        }, {
          "name": "DeployToProd",
          "actionTypeId": {
            "category": "Deploy",
            "owner": "AWS",
            "provider": "CloudFormation",
            "version": "1"
          },
          "configuration": {
            "ActionMode": "CREATE_UPDATE",
            "StackName": "toon-processor-prod",
            "TemplatePath": "BuildOutput::iac/cloudformation-template.yaml",
            "ParameterOverrides": "{\"Environment\":\"prod\"}",
            "Capabilities": "CAPABILITY_NAMED_IAM"
          },
          "inputArtifacts": [{"name": "BuildOutput"}],
          "runOrder": 2
        }]
      }
    ]
  }
}
```


#### 2. Crear Proyecto CodeBuild

```bash
aws codebuild create-project \
  --name ToonProcessor-Build \
  --source type=CODEPIPELINE \
  --artifacts type=CODEPIPELINE \
  --environment type=LINUX_CONTAINER,image=aws/codebuild/standard:7.0,computeType=BUILD_GENERAL1_SMALL \
  --service-role arn:aws:iam::ACCOUNT_ID:role/CodeBuildServiceRole
```

El proyecto usará automáticamente el `buildspec.yml` del repositorio.

#### 3. Configurar Webhook de GitHub

```bash
# Desde GitHub Repository Settings → Webhooks
# Payload URL: https://codepipeline.REGION.amazonaws.com/...
# Content type: application/json
# Events: Push events
```

### Proceso de Despliegue

1. **Developer hace push a GitHub**
   ```bash
   git add .
   git commit -m "feat: nueva funcionalidad"
   git push origin develop  # Para sandbox
   # o
   git push origin main     # Para preprod/prod
   ```

2. **CodePipeline detecta cambios** (webhook)

3. **CodeBuild ejecuta buildspec.yml:**
   - Install: Python 3.11, pytest, herramientas
   - Pre-Build: Instala deps, ejecuta tests, valida CloudFormation
   - Build: Empaqueta 4 Lambdas en .zip con dependencias
   - Post-Build: Genera manifiesto, verifica artefactos

4. **CloudFormation despliega a Sandbox** (automático)
   - Crea/actualiza DynamoDB, SQS, Lambdas, API Gateway
   - Actualiza código de Lambdas con nuevos .zip

5. **Aprobación manual para PreProd** (opcional)
   - Revisor aprueba en AWS Console

6. **CloudFormation despliega a PreProd**

7. **Aprobación manual para Prod** (requerido)
   - Revisor senior aprueba

8. **CloudFormation despliega a Prod**

### Rollback

Si algo falla:
```bash
# Rollback automático de CloudFormation
aws cloudformation cancel-update-stack --stack-name toon-processor-prod

# O rollback manual a versión anterior
aws cloudformation update-stack \
  --stack-name toon-processor-prod \
  --use-previous-template
```


## 📦 Despliegue

### Opción 1: Despliegue Manual (para desarrollo local)

#### Prerrequisitos
```bash
# Instalar AWS CLI
aws --version

# Configurar credenciales
aws configure

# Instalar dependencias Python
pip install -r requirements.txt
```

#### Paso 1: Validar Plantillas
```bash
chmod +x scripts/validate-templates.sh
./scripts/validate-templates.sh
```

#### Paso 2: Empaquetar Lambdas
```bash
chmod +x scripts/package-lambdas.sh
./scripts/package-lambdas.sh
```

#### Paso 3: Crear Stack de CloudFormation
```bash
# Crear stack inicial
aws cloudformation create-stack \
  --stack-name toon-processor-dev \
  --template-body file://iac/cloudformation-template.yaml \
  --parameters file://iac/parameters.json \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

# Esperar a que se complete
aws cloudformation wait stack-create-complete \
  --stack-name toon-processor-dev
```

#### Paso 4: Actualizar Código de Lambdas
```bash
# SubmitJob
aws lambda update-function-code \
  --function-name SubmitJob-dev \
  --zip-file fileb://dist/submit_job.zip

# Worker
aws lambda update-function-code \
  --function-name ToonWorker-dev \
  --zip-file fileb://dist/worker.zip

# GetJobStatus
aws lambda update-function-code \
  --function-name GetJobStatus-dev \
  --zip-file fileb://dist/get_job_status.zip

# GetResults
aws lambda update-function-code \
  --function-name GetResults-dev \
  --zip-file fileb://dist/get_results.zip
```

#### Paso 5: Obtener URL del API
```bash
aws cloudformation describe-stacks \
  --stack-name toon-processor-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text
```

### Opción 2: Despliegue con Script
```bash
chmod +x iac/deploy.sh
./iac/deploy.sh
```

### Opción 3: Despliegue Automático (CI/CD)

Una vez configurado CodePipeline:
```bash
# Push a develop → despliega a sandbox automáticamente
git push origin develop

# Push a main → requiere aprobaciones para preprod/prod
git push origin main
```

### Verificar Despliegue

```bash
# Ver estado del stack
aws cloudformation describe-stacks --stack-name toon-processor-dev

# Ver recursos creados
aws cloudformation list-stack-resources --stack-name toon-processor-dev

# Ver logs de Lambda
aws logs tail /aws/lambda/SubmitJob-dev --follow
```


## 🧪 Pruebas con curl

### Configuración Inicial

```bash
# 1. Obtener URL del API
export API_URL=$(aws cloudformation describe-stacks \
  --stack-name toon-processor-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

echo "API URL: $API_URL"

# 2. Generar token JWT (para desarrollo)
# En producción, usar Cognito o tu servicio de autenticación
export JWT_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
```

### Test 1: Enviar Job (POST /submit-job)

```bash
# Enviar job con 3 toons
curl -X POST "${API_URL}/submit-job" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "jobId": "JOB-TEST-001",
    "toons": [
      {
        "toonId": "TOON-001",
        "type": "IMAGE",
        "payload": {
          "url": "https://picsum.photos/1920/1080",
          "width": 1920,
          "height": 1080,
          "format": "jpeg"
        }
      },
      {
        "toonId": "TOON-002",
        "type": "VIDEO",
        "payload": {
          "url": "https://example.com/video.mp4",
          "duration": 120,
          "resolution": "1080p"
        }
      },
      {
        "toonId": "TOON-003",
        "type": "TEXT",
        "payload": {
          "content": "Este es un texto de prueba",
          "language": "es"
        }
      }
    ]
  }'
```

**Respuesta esperada:**
```json
{
  "message": "Job submitted successfully",
  "jobId": "JOB-TEST-001",
  "toonsCount": 3,
  "status": "Processing"
}
```

### Test 2: Consultar Estado del Job (GET /jobs/{jobId})

```bash
# Consultar inmediatamente (puede estar en Processing)
curl -X GET "${API_URL}/jobs/JOB-TEST-001" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

**Respuesta esperada (en progreso):**
```json
{
  "jobId": "JOB-TEST-001",
  "status": "Processing",
  "totalToons": 3,
  "processedToons": 1,
  "userId": "user123",
  "metadata": {
    "createdAt": "2025-11-27T20:00:00.000Z",
    "updatedAt": "2025-11-27T20:00:05.000Z"
  },
  "progress": {
    "percentage": 33.33,
    "completed": false
  }
}
```

```bash
# Esperar unos segundos y consultar de nuevo
sleep 5
curl -X GET "${API_URL}/jobs/JOB-TEST-001" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

**Respuesta esperada (completado):**
```json
{
  "jobId": "JOB-TEST-001",
  "status": "Completed",
  "totalToons": 3,
  "processedToons": 3,
  "userId": "user123",
  "metadata": {
    "createdAt": "2025-11-27T20:00:00.000Z",
    "updatedAt": "2025-11-27T20:00:10.000Z"
  },
  "progress": {
    "percentage": 100.0,
    "completed": true
  }
}
```

### Test 3: Obtener Resultados (GET /results?jobId=X)

```bash
curl -X GET "${API_URL}/results?jobId=JOB-TEST-001" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

**Respuesta esperada:**
```json
{
  "jobId": "JOB-TEST-001",
  "jobStatus": "Completed",
  "totalToons": 3,
  "resultsCount": 3,
  "results": [
    {
      "toonId": "TOON-001",
      "type": "IMAGE",
      "fingerprint": "a3f5b8c9d2e1f4a7b6c5d8e9f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0",
      "durationMs": 145,
      "isValid": true,
      "processedAt": "2025-11-27T20:00:02.000Z",
      "processedData": {
        "toonId": "TOON-001",
        "type": "IMAGE",
        "payload": {
          "url": "https://picsum.photos/1920/1080",
          "width": 1920,
          "height": 1080,
          "format": "jpeg"
        },
        "metadata": {
          "originalSize": 156,
          "hasPayload": true
        },
        "enrichment": {
          "processedBy": "ToonProcessor-v1.0",
          "complexity": "LOW",
          "category": "MEDIA"
        }
      }
    },
    {
      "toonId": "TOON-002",
      "type": "VIDEO",
      "fingerprint": "b4c6d8e0f2a4b6c8d0e2f4a6b8c0d2e4f6a8b0c2d4e6f8a0b2c4d6e8f0a2b4c6",
      "durationMs": 178,
      "isValid": true,
      "processedAt": "2025-11-27T20:00:05.000Z",
      "processedData": {
        "toonId": "TOON-002",
        "type": "VIDEO",
        "enrichment": {
          "complexity": "MEDIUM",
          "category": "MEDIA"
        }
      }
    },
    {
      "toonId": "TOON-003",
      "type": "TEXT",
      "fingerprint": "c5d7e9f1a3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d3e5f7a9b1c3d5e7f9a1b3c5d7",
      "durationMs": 92,
      "isValid": true,
      "processedAt": "2025-11-27T20:00:08.000Z",
      "processedData": {
        "toonId": "TOON-003",
        "type": "TEXT",
        "enrichment": {
          "complexity": "LOW",
          "category": "CONTENT"
        }
      }
    }
  ]
}
```

### Test 4: Casos de Error

#### Job no encontrado
```bash
curl -X GET "${API_URL}/jobs/JOB-NOEXISTE" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

**Respuesta:**
```json
{
  "error": "Job no encontrado"
}
```

#### Sin autenticación
```bash
curl -X POST "${API_URL}/submit-job" \
  -H "Content-Type: application/json" \
  -d '{"jobId": "TEST"}'
```

**Respuesta:**
```json
{
  "error": "Header Authorization no presente"
}
```

#### Payload inválido
```bash
curl -X POST "${API_URL}/submit-job" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "jobId": "JOB-002"
  }'
```

**Respuesta:**
```json
{
  "error": "Campo 'toons' requerido"
}
```

### Test 5: Job con Muchos Toons (Prueba de Escalabilidad)

```bash
# Usar archivo de datos de prueba
curl -X POST "${API_URL}/submit-job" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d @data/sample_jobs.json
```

### Script de Prueba Completo

```bash
#!/bin/bash
# test-api.sh - Script para probar todos los endpoints

set -e

API_URL="https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/dev"
JWT_TOKEN="YOUR_JWT_TOKEN"
JOB_ID="JOB-$(date +%s)"

echo "=== Test 1: Enviar Job ==="
SUBMIT_RESPONSE=$(curl -s -X POST "${API_URL}/submit-job" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"jobId\": \"${JOB_ID}\",
    \"toons\": [
      {\"toonId\": \"TOON-001\", \"type\": \"IMAGE\", \"payload\": {}},
      {\"toonId\": \"TOON-002\", \"type\": \"VIDEO\", \"payload\": {}}
    ]
  }")

echo "$SUBMIT_RESPONSE" | jq .

echo ""
echo "=== Test 2: Consultar Estado (inmediato) ==="
sleep 2
curl -s -X GET "${API_URL}/jobs/${JOB_ID}" \
  -H "Authorization: Bearer ${JWT_TOKEN}" | jq .

echo ""
echo "=== Esperando procesamiento... ==="
sleep 5

echo ""
echo "=== Test 3: Consultar Estado (después de espera) ==="
curl -s -X GET "${API_URL}/jobs/${JOB_ID}" \
  -H "Authorization: Bearer ${JWT_TOKEN}" | jq .

echo ""
echo "=== Test 4: Obtener Resultados ==="
curl -s -X GET "${API_URL}/results?jobId=${JOB_ID}" \
  -H "Authorization: Bearer ${JWT_TOKEN}" | jq .

echo ""
echo "=== Tests completados ==="
```

Ejecutar:
```bash
chmod +x test-api.sh
./test-api.sh
```


## 🔐 Variables de Entorno

Cada Lambda requiere las siguientes variables de entorno (configuradas automáticamente por CloudFormation):

### SubmitJob
```bash
JOBS_TABLE_NAME=ToonJobs-dev
TOON_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789/ToonProcessingQueue-dev
JWT_SECRET={{resolve:secretsmanager:ToonProcessor/JWT:SecretString:secret}}
```

### Worker
```bash
JOBS_TABLE_NAME=ToonJobs-dev
RESULTS_TABLE_NAME=ToonResults-dev
```

### GetJobStatus
```bash
JOBS_TABLE_NAME=ToonJobs-dev
```

### GetResults
```bash
JOBS_TABLE_NAME=ToonJobs-dev
RESULTS_TABLE_NAME=ToonResults-dev
```

### Configurar JWT Secret en Secrets Manager

```bash
# Crear secret para JWT
aws secretsmanager create-secret \
  --name ToonProcessor/JWT \
  --description "JWT secret para autenticación" \
  --secret-string '{"secret":"your-super-secret-key-change-in-production"}'

# Actualizar secret
aws secretsmanager update-secret \
  --secret-id ToonProcessor/JWT \
  --secret-string '{"secret":"new-secret-key"}'
```

## 💻 Desarrollo Local

### Instalar Dependencias
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Si existe
```

### Ejecutar Tests
```bash
# Todos los tests
pytest

# Con cobertura
pytest --cov=src --cov-report=html

# Solo tests unitarios
pytest tests/test_job_manager.py -v

# Ver reporte de cobertura
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```

### Linting
```bash
# Instalar flake8
pip install flake8

# Ejecutar linter
flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 src/ --count --max-line-length=100 --statistics
```

### Empaquetar Lambdas Localmente
```bash
./scripts/package-lambdas.sh
```

### Validar CloudFormation
```bash
./scripts/validate-templates.sh
```

### Simular Invocación de Lambda

```bash
# Crear evento de prueba
cat > event.json <<EOF
{
  "body": "{\"jobId\":\"JOB-LOCAL-001\",\"toons\":[{\"toonId\":\"TOON-001\",\"type\":\"IMAGE\",\"payload\":{}}]}",
  "headers": {
    "Authorization": "Bearer test-token"
  }
}
EOF

# Invocar Lambda localmente (requiere configurar AWS SAM)
sam local invoke SubmitJobFunction --event event.json
```

### Variables de Entorno para Testing Local

```bash
# .env (no commitear)
export JOBS_TABLE_NAME=ToonJobs-local
export RESULTS_TABLE_NAME=ToonResults-local
export TOON_QUEUE_URL=http://localhost:4566/000000000000/ToonQueue
export JWT_SECRET=local-dev-secret-key
export AWS_REGION=us-east-1
```

### Usar LocalStack para Testing Local

```bash
# Instalar LocalStack
pip install localstack

# Iniciar LocalStack
localstack start

# Crear recursos locales
aws --endpoint-url=http://localhost:4566 dynamodb create-table \
  --table-name ToonJobs-local \
  --attribute-definitions AttributeName=jobId,AttributeType=S \
  --key-schema AttributeName=jobId,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

aws --endpoint-url=http://localhost:4566 sqs create-queue \
  --queue-name ToonQueue
```


## 📊 Monitoreo y Logs

### CloudWatch Logs

Cada Lambda escribe logs estructurados en JSON:

```json
{
  "timestamp": "2025-11-27T20:00:00.000Z",
  "level": "INFO",
  "message": "Toon procesado exitosamente",
  "jobId": "JOB-001",
  "toonId": "TOON-001",
  "durationMs": 150,
  "fingerprint": "a3f5b8c..."
}
```

#### Ver Logs en Tiempo Real

```bash
# SubmitJob
aws logs tail /aws/lambda/SubmitJob-dev --follow

# Worker
aws logs tail /aws/lambda/ToonWorker-dev --follow

# GetJobStatus
aws logs tail /aws/lambda/GetJobStatus-dev --follow

# GetResults
aws logs tail /aws/lambda/GetResults-dev --follow
```

#### Buscar en Logs

```bash
# Buscar por jobId
aws logs filter-log-events \
  --log-group-name /aws/lambda/ToonWorker-dev \
  --filter-pattern "JOB-001"

# Buscar errores
aws logs filter-log-events \
  --log-group-name /aws/lambda/ToonWorker-dev \
  --filter-pattern "ERROR"
```

### CloudWatch Metrics

Métricas automáticas de Lambda:
- **Invocations**: Número de invocaciones
- **Duration**: Duración de ejecución
- **Errors**: Número de errores
- **Throttles**: Invocaciones limitadas
- **ConcurrentExecutions**: Ejecuciones concurrentes

#### Ver Métricas

```bash
# Invocaciones en las últimas 24 horas
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=ToonWorker-dev \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum
```

### Alarmas CloudWatch

```bash
# Crear alarma para errores en Worker
aws cloudwatch put-metric-alarm \
  --alarm-name ToonWorker-Errors \
  --alarm-description "Alerta cuando Worker tiene errores" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --dimensions Name=FunctionName,Value=ToonWorker-dev
```

### X-Ray Tracing

Habilitar tracing distribuido:

```bash
# Actualizar Lambda para usar X-Ray
aws lambda update-function-configuration \
  --function-name ToonWorker-dev \
  --tracing-config Mode=Active
```

### Dashboard CloudWatch

Crear dashboard personalizado:

```bash
aws cloudwatch put-dashboard \
  --dashboard-name ToonProcessor-Dashboard \
  --dashboard-body file://dashboard.json
```

**dashboard.json:**
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Invocations", {"stat": "Sum", "label": "SubmitJob"}],
          ["...", {"stat": "Sum", "label": "Worker"}]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "us-east-1",
        "title": "Lambda Invocations"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Duration", {"stat": "Average"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "Average Duration"
      }
    }
  ]
}
```

### SQS Monitoring

```bash
# Ver mensajes en cola
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789/ToonProcessingQueue-dev \
  --attribute-names All

# Ver mensajes en DLQ
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789/ToonDLQ-dev \
  --attribute-names ApproximateNumberOfMessages
```

### DynamoDB Monitoring

```bash
# Ver métricas de tabla
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=ToonJobs-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

## 🐛 Troubleshooting

### Problema: Lambda timeout

**Síntoma:** Worker Lambda alcanza timeout de 300s

**Solución:**
```bash
# Aumentar timeout
aws lambda update-function-configuration \
  --function-name ToonWorker-dev \
  --timeout 600
```

### Problema: Mensajes en DLQ

**Síntoma:** Mensajes acumulados en Dead Letter Queue

**Diagnóstico:**
```bash
# Ver mensajes en DLQ
aws sqs receive-message \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789/ToonDLQ-dev \
  --max-number-of-messages 10
```

**Solución:** Revisar logs del Worker para el toonId específico

### Problema: Job queda en Processing

**Síntoma:** Job nunca llega a Completed

**Diagnóstico:**
```bash
# Verificar job en DynamoDB
aws dynamodb get-item \
  --table-name ToonJobs-dev \
  --key '{"jobId": {"S": "JOB-001"}}'

# Verificar resultados procesados
aws dynamodb query \
  --table-name ToonResults-dev \
  --key-condition-expression "jobId = :jobId" \
  --expression-attribute-values '{":jobId": {"S": "JOB-001"}}'
```

### Problema: Error de autenticación

**Síntoma:** "Token inválido" o "Token expirado"

**Solución:**
```bash
# Verificar JWT secret en Secrets Manager
aws secretsmanager get-secret-value \
  --secret-id ToonProcessor/JWT

# Generar nuevo token con el secret correcto
```

## 📚 Recursos Adicionales

- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [SQS Best Practices](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-best-practices.html)
- [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)
- [CloudFormation User Guide](https://docs.aws.amazon.com/cloudformation/)

## 📝 Licencia

[Especificar licencia del proyecto]

## 👥 Contribuidores

[Lista de contribuidores]

## 📞 Soporte

Para preguntas o problemas:
- Crear issue en GitHub
- Contactar al equipo de desarrollo
- Revisar documentación en Wiki

---

**Última actualización:** 2025-11-27  
**Versión:** 1.0.0
