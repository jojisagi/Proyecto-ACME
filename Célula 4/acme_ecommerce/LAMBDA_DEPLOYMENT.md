# Despliegue de Funciones Lambda

## 📦 Estructura de Código Lambda

Las funciones Lambda están organizadas en directorios separados con su código fuente:

```
lambdas/
├── app-server/
│   ├── index.py           # Código de la función
│   └── requirements.txt   # Dependencias (si las hay)
└── process-order/
    ├── index.py           # Código de la función
    └── requirements.txt   # Dependencias (si las hay)
```

## 🏗️ Arquitectura de Despliegue

### Flujo de Despliegue

```
1. Código Local (lambdas/*/index.py)
        ↓
2. Empaquetamiento (ZIP)
        ↓
3. S3 Bucket (ecommerce-lambda-code-<ACCOUNT_ID>)
        ↓
4. CloudFormation referencia el ZIP en S3
        ↓
5. Lambda Function desplegada
```

### Bucket S3 para Código Lambda

El código Lambda se almacena en un bucket S3 dedicado:
- **Nombre**: `ecommerce-lambda-code-<ACCOUNT_ID>`
- **Región**: us-east-1 (o la región configurada)
- **Versionamiento**: Habilitado
- **Archivos**:
  - `app-server.zip`
  - `process-order.zip`

### Referencia en CloudFormation

Las funciones Lambda en CloudFormation referencian el código desde S3:

```yaml
AppServerFunction:
  Type: AWS::Lambda::Function
  Properties:
    FunctionName: app-server
    Runtime: python3.11
    Handler: index.lambda_handler
    Code:
      S3Bucket: !Ref LambdaCodeBucket
      S3Key: app-server.zip
```

## 🚀 Despliegue Inicial

### Opción 1: Script Automatizado (Recomendado)

```bash
./scripts/deploy.sh
```

Este script:
1. Crea el bucket S3 para código Lambda
2. Empaqueta las funciones en archivos ZIP
3. Sube los ZIP a S3
4. Despliega el stack de CloudFormation
5. CloudFormation crea las funciones Lambda desde S3

### Opción 2: Manual

```bash
# 1. Obtener ID de cuenta
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
LAMBDA_BUCKET="ecommerce-lambda-code-$ACCOUNT_ID"

# 2. Crear bucket
aws s3 mb s3://$LAMBDA_BUCKET --region us-east-1

# 3. Habilitar versionamiento
aws s3api put-bucket-versioning \
  --bucket $LAMBDA_BUCKET \
  --versioning-configuration Status=Enabled

# 4. Empaquetar app-server
cd lambdas/app-server
zip -r ../../app-server.zip index.py
cd ../..

# 5. Empaquetar process-order
cd lambdas/process-order
zip -r ../../process-order.zip index.py
cd ../..

# 6. Subir a S3
aws s3 cp app-server.zip s3://$LAMBDA_BUCKET/app-server.zip
aws s3 cp process-order.zip s3://$LAMBDA_BUCKET/process-order.zip

# 7. Desplegar CloudFormation
aws cloudformation create-stack \
  --stack-name ecommerce-resources \
  --template-body file://cloudformation/resources-stack.yaml \
  --parameters ParameterKey=IAMStackName,ParameterValue=ecommerce-iam
```

## 🔄 Actualizar Código Lambda

Cuando modificas el código de una función Lambda, no necesitas redesplegar toda la infraestructura.

### Opción 1: Script Automatizado (Recomendado)

```bash
# Edita el código
vim lambdas/app-server/index.py

# Actualiza la función
./scripts/update-lambdas.sh
```

### Opción 2: Actualizar una Función Específica

```bash
# App Server
cd lambdas/app-server
zip -r ../../app-server.zip index.py
cd ../..

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws s3 cp app-server.zip s3://ecommerce-lambda-code-$ACCOUNT_ID/app-server.zip

aws lambda update-function-code \
  --function-name app-server \
  --s3-bucket ecommerce-lambda-code-$ACCOUNT_ID \
  --s3-key app-server.zip
```

### Opción 3: Desde la Consola AWS

1. Ir a AWS Lambda Console
2. Seleccionar la función (app-server o process-order)
3. En "Code source", hacer clic en "Upload from" → "Amazon S3 location"
4. Ingresar: `s3://ecommerce-lambda-code-<ACCOUNT_ID>/app-server.zip`
5. Hacer clic en "Save"

## 📝 Agregar Dependencias

Si necesitas agregar dependencias de Python:

### 1. Actualizar requirements.txt

```bash
# lambdas/app-server/requirements.txt
boto3>=1.26.0
requests>=2.28.0
```

### 2. Instalar Dependencias Localmente

```bash
cd lambdas/app-server
pip install -r requirements.txt -t .
```

### 3. Empaquetar con Dependencias

```bash
# Desde el directorio lambdas/app-server
zip -r ../../app-server.zip . -x "*.pyc" -x "__pycache__/*"
```

### 4. Subir y Actualizar

```bash
cd ../..
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws s3 cp app-server.zip s3://ecommerce-lambda-code-$ACCOUNT_ID/app-server.zip

aws lambda update-function-code \
  --function-name app-server \
  --s3-bucket ecommerce-lambda-code-$ACCOUNT_ID \
  --s3-key app-server.zip
```

## 🔍 Verificar Despliegue

### Ver Versión Actual

```bash
aws lambda get-function --function-name app-server \
  --query 'Configuration.[FunctionName,LastModified,CodeSize]' \
  --output table
```

### Ver Código Fuente en S3

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws s3 ls s3://ecommerce-lambda-code-$ACCOUNT_ID/
```

### Ver Versiones en S3

```bash
aws s3api list-object-versions \
  --bucket ecommerce-lambda-code-$ACCOUNT_ID \
  --prefix app-server.zip
```

### Probar Función

```bash
# Invocar directamente
aws lambda invoke \
  --function-name app-server \
  --payload '{"httpMethod":"GET","path":"/health"}' \
  response.json

cat response.json
```

## 🐛 Troubleshooting

### Error: "No such file or directory"

**Problema**: El archivo ZIP no se encuentra en S3.

**Solución**:
```bash
# Verificar que el archivo existe
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws s3 ls s3://ecommerce-lambda-code-$ACCOUNT_ID/

# Si no existe, subirlo
./scripts/update-lambdas.sh
```

### Error: "InvalidParameterValueException: Unzipped size must be smaller than..."

**Problema**: El paquete Lambda es demasiado grande (>250MB descomprimido).

**Solución**:
1. Usar Lambda Layers para dependencias grandes
2. Optimizar dependencias (usar solo lo necesario)
3. Usar contenedores Docker para Lambdas grandes

### Error: "AccessDenied" al subir a S3

**Problema**: No tienes permisos para subir al bucket.

**Solución**:
```bash
# Verificar permisos
aws s3api get-bucket-policy --bucket ecommerce-lambda-code-$ACCOUNT_ID

# Verificar tu identidad
aws sts get-caller-identity
```

### Lambda no se actualiza

**Problema**: El código no cambia después de actualizar.

**Solución**:
```bash
# Forzar actualización con nueva versión
aws lambda update-function-code \
  --function-name app-server \
  --s3-bucket ecommerce-lambda-code-$ACCOUNT_ID \
  --s3-key app-server.zip \
  --publish
```

## 📊 Versionamiento

### Publicar Nueva Versión

```bash
aws lambda publish-version \
  --function-name app-server \
  --description "Version con nueva funcionalidad"
```

### Listar Versiones

```bash
aws lambda list-versions-by-function \
  --function-name app-server
```

### Crear Alias

```bash
# Crear alias "prod" apuntando a versión 1
aws lambda create-alias \
  --function-name app-server \
  --name prod \
  --function-version 1

# Actualizar alias a nueva versión
aws lambda update-alias \
  --function-name app-server \
  --name prod \
  --function-version 2
```

## 🔐 Seguridad

### Permisos del Bucket

El bucket S3 debe tener:
- Acceso privado (no público)
- Permisos para Lambda leer los archivos
- Permisos para tu usuario/rol subir archivos

### Encriptación

```bash
# Habilitar encriptación en el bucket
aws s3api put-bucket-encryption \
  --bucket ecommerce-lambda-code-$ACCOUNT_ID \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

## 📈 Mejores Prácticas

### 1. Versionamiento
- ✅ Habilitar versionamiento en S3
- ✅ Usar versiones de Lambda para rollback
- ✅ Crear aliases para ambientes (dev, staging, prod)

### 2. CI/CD
- ✅ Automatizar empaquetamiento en pipeline
- ✅ Ejecutar tests antes de desplegar
- ✅ Usar CodePipeline o GitHub Actions

### 3. Organización
- ✅ Un directorio por función Lambda
- ✅ requirements.txt para dependencias
- ✅ README.md en cada directorio

### 4. Tamaño del Paquete
- ✅ Minimizar dependencias
- ✅ Usar Lambda Layers para código compartido
- ✅ Excluir archivos innecesarios del ZIP

### 5. Testing
- ✅ Probar localmente antes de desplegar
- ✅ Usar SAM CLI para testing local
- ✅ Implementar tests unitarios

## 🔗 Referencias

- [AWS Lambda Deployment Package](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html)
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [CloudFormation Lambda](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-lambda-function.html)
