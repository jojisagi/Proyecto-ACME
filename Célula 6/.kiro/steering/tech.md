# Technology Stack

## Build System & Tools

- **Runtime**: Python 3.11+
- **IaC**: AWS CloudFormation
- **Cloud Provider**: AWS (Lambda, API Gateway, DynamoDB, SQS/SNS, Cognito)

## Common Commands

### Deployment
```bash
# Desplegar infraestructura
aws cloudformation deploy --template-file iac/cloudformation-template.yaml --stack-name toon-processor --capabilities CAPABILITY_IAM

# Empaquetar Lambdas
cd src/lambdas && zip -r submit_job.zip submit_job/ && cd ../..
```

### Testing
```bash
# Ejecutar tests locales
python -m pytest src/tests/

# Invocar Lambda localmente
python src/lambdas/submit_job/handler.py
```

### Development
```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
export JOBS_TABLE_NAME=ToonJobs
export RESULTS_TABLE_NAME=ToonResults
export TOON_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/...
```

## Dependencies

- boto3 (AWS SDK)
- PyJWT (autenticación JWT)
- python-dotenv (variables de entorno)

## Code Style

- Usar 4 espacios para indentación
- Seguir PEP 8 para Python
- Nombres de variables en snake_case
- Nombres de clases en PascalCase
- Docstrings para todas las funciones públicas
- Logging estructurado con contexto de jobId/toonId
- Manejo explícito de excepciones
