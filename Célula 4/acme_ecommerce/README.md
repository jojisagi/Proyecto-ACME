# E-commerce AWS Serverless Architecture

Proyecto de e-commerce usando arquitectura serverless en AWS con Lambda, Step Functions, DynamoDB, SQS, SNS y API Gateway.

## Estructura del Proyecto

```
.
├── cloudformation/          # Plantillas CloudFormation
│   ├── iam-stack.yaml      # Roles y políticas IAM
│   └── resources-stack.yaml # Recursos AWS
├── lambdas/                 # Funciones Lambda en Python 3
│   ├── app-server/
│   └── process-order/
├── step-functions/          # Definiciones de Step Functions
├── frontend/                # Aplicación React
├── data/                    # Datos de prueba para DynamoDB
└── scripts/                 # Scripts de prueba con curl

## Despliegue

### Opción 1: Despliegue Automatizado (Recomendado)
```bash
./scripts/deploy.sh
```

### Opción 2: Despliegue Manual

1. Desplegar stack IAM:
```bash
aws cloudformation create-stack \
  --stack-name ecommerce-iam \
  --template-body file://cloudformation/iam-stack.yaml \
  --capabilities CAPABILITY_NAMED_IAM
```

2. Crear bucket y subir código Lambda:
```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws s3 mb s3://ecommerce-lambda-code-$ACCOUNT_ID

cd lambdas/app-server && zip -r ../../app-server.zip index.py && cd ../..
cd lambdas/process-order && zip -r ../../process-order.zip index.py && cd ../..

aws s3 cp app-server.zip s3://ecommerce-lambda-code-$ACCOUNT_ID/
aws s3 cp process-order.zip s3://ecommerce-lambda-code-$ACCOUNT_ID/
```

3. Desplegar stack de recursos:
```bash
aws cloudformation create-stack \
  --stack-name ecommerce-resources \
  --template-body file://cloudformation/resources-stack.yaml \
  --parameters ParameterKey=IAMStackName,ParameterValue=ecommerce-iam
```

4. Poblar DynamoDB:
```bash
python3 scripts/populate-dynamodb.py
```

5. Probar API:
```bash
./scripts/test-api.sh <API_GATEWAY_URL>
```

### Actualizar Solo las Lambdas
```bash
./scripts/update-lambdas.sh
```

## Componentes

- **CloudFront + S3**: Distribución de contenido estático
- **API Gateway**: Punto de entrada REST
- **Lambda**: Funciones serverless (Python 3)
- **DynamoDB**: Base de datos NoSQL para órdenes
- **SQS**: Cola de mensajes para procesamiento asíncrono
- **SNS**: Notificaciones por email
- **Step Functions**: Orquestación de flujos de trabajo
