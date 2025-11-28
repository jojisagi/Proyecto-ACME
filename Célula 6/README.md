# Sistema de Procesamiento de Toons

Sistema serverless en AWS para procesamiento distribuido de trabajos (jobs) compuestos por múltiples "toons".

## Arquitectura

- **API Gateway**: Endpoints REST autenticados con JWT
- **Lambda Functions**: 4 funciones para submit, worker, status y results
- **DynamoDB**: Almacenamiento de jobs y resultados
- **SQS**: Cola para procesamiento asíncrono (fan-out)
- **CloudWatch**: Logs estructurados

## Estructura del Proyecto

```
.
├── src/                    # Código ejecutable
│   ├── lambdas/           # Funciones Lambda
│   ├── business_logic/    # Lógica de negocio
│   └── utils/             # Utilidades compartidas
├── iac/                   # Infraestructura como código
│   └── cloudformation-template.yaml
├── data/                  # Datos de prueba
└── requirements.txt       # Dependencias Python
```

## Funciones Lambda

### 1. SubmitJob
- **Endpoint**: `POST /submit-job`
- **Autenticación**: JWT (Bearer token)
- **Función**: Recibe job, valida, registra en DynamoDB, envía toons a SQS

### 2. Worker
- **Trigger**: SQS (1 toon por invocación)
- **Función**: Procesa toon, calcula hash, guarda resultado, actualiza progreso
- **Características**: Idempotente

### 3. GetJobStatus
- **Endpoint**: `GET /jobs/{jobId}`
- **Función**: Consulta estado y progreso del job

### 4. GetResults
- **Endpoint**: `GET /results?jobId=JOB001`
- **Función**: Devuelve resultados procesados por toon

## Despliegue

### Prerrequisitos
```bash
pip install -r requirements.txt
aws configure
```

### Crear Stack
```bash
aws cloudformation create-stack \
  --stack-name toon-processor-dev \
  --template-body file://iac/cloudformation-template.yaml \
  --parameters file://iac/parameters.json \
  --capabilities CAPABILITY_NAMED_IAM
```

### Empaquetar y Actualizar Lambdas
```bash
# SubmitJob
cd src/lambdas/submit_job
zip -r ../../../submit_job.zip . -x "*.pyc" -x "__pycache__/*"
cd ../../..
aws lambda update-function-code \
  --function-name SubmitJob-dev \
  --zip-file fileb://submit_job.zip

# Worker
cd src/lambdas/worker
zip -r ../../../worker.zip . -x "*.pyc" -x "__pycache__/*"
cd ../../..
aws lambda update-function-code \
  --function-name ToonWorker-dev \
  --zip-file fileb://worker.zip

# GetJobStatus
cd src/lambdas/get_job_status
zip -r ../../../get_job_status.zip . -x "*.pyc" -x "__pycache__/*"
cd ../../..
aws lambda update-function-code \
  --function-name GetJobStatus-dev \
  --zip-file fileb://get_job_status.zip

# GetResults
cd src/lambdas/get_results
zip -r ../../../get_results.zip . -x "*.pyc" -x "__pycache__/*"
cd ../../..
aws lambda update-function-code \
  --function-name GetResults-dev \
  --zip-file fileb://get_results.zip
```

## Uso

### Enviar Job
```bash
curl -X POST https://YOUR_API_ENDPOINT/dev/submit-job \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d @data/test_request.json
```

### Consultar Estado
```bash
curl https://YOUR_API_ENDPOINT/dev/jobs/JOB-001 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Obtener Resultados
```bash
curl "https://YOUR_API_ENDPOINT/dev/results?jobId=JOB-001" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Variables de Entorno

Cada Lambda requiere:
- `JOBS_TABLE_NAME`: Nombre de tabla DynamoDB de jobs
- `RESULTS_TABLE_NAME`: Nombre de tabla DynamoDB de resultados
- `TOON_QUEUE_URL`: URL de cola SQS (solo SubmitJob)
- `JWT_SECRET`: Secret para validar JWT

## Datos de Prueba

Ver carpeta `data/` para ejemplos de:
- `sample_jobs.json`: Jobs de ejemplo
- `sample_toons.json`: Toons individuales
- `test_request.json`: Request completo para testing

## Monitoreo

Los logs están en CloudWatch Logs con formato JSON estructurado:
```json
{
  "timestamp": "2025-11-27T...",
  "level": "INFO",
  "message": "Toon procesado exitosamente",
  "jobId": "JOB-001",
  "toonId": "TOON-001",
  "durationMs": 150
}
```
