# Quick Start Guide - Acme Image Handler

Guía rápida para poner en marcha el sistema en 30 minutos.

## Prerrequisitos

```bash
# Verificar instalaciones
aws --version          # AWS CLI 2.x
python3 --version      # Python 3.11+
git --version          # Git 2.x
```

## Paso 1: Configurar AWS CLI (5 min)

```bash
# Configurar perfiles para cada cuenta
aws configure --profile build
aws configure --profile sandbox
aws configure --profile prod

# Verificar
aws sts get-caller-identity --profile sandbox
```

## Paso 2: Configurar Infraestructura Base (10 min)

```bash
cd "Célula 3"

# Opción A: Script automático
./setup/setup-accounts.sh

# Opción B: Manual
# Editar pipeline/parameters-sandbox.json con tus VPC IDs
vim pipeline/parameters-sandbox.json
```

## Paso 3: Desplegar a Sandbox (10 min)

```bash
# Desplegar stack
./pipeline/deploy.sh sandbox

# Esperar a que complete (5-10 min)
# Verificar outputs
aws cloudformation describe-stacks \
  --stack-name acme-image-handler-sandbox \
  --profile sandbox \
  --query 'Stacks[0].Outputs' \
  --output table
```

## Paso 4: Crear Usuario de Prueba (2 min)

```bash
# Crear usuario en Cognito
./setup/create-test-user.sh sandbox

# Seguir las instrucciones en pantalla
```

## Paso 5: Probar el API (3 min)

```bash
# Configurar variables (usar outputs del paso 3)
export API_URL="https://xxxxx.execute-api.us-east-1.amazonaws.com/sandbox"
export COGNITO_DOMAIN="acme-image-handler-sandbox-123456789"
export CLIENT_ID="xxxxxxxxxxxxxxxxxxxxx"
export USERNAME="test@example.com"
export PASSWORD="YourPassword123!"

# Ejecutar pruebas
./tests/test-api.sh
```

## Paso 6: Generar y Subir Imágenes de Prueba (5 min)

```bash
# Generar 50 imágenes sintéticas
cd tests
python3 generate-test-data.py

# Las imágenes estarán en data/test-images/
ls -lh ../data/test-images/

# Subir una imagen de prueba
cd ..
# Obtener URL de carga
curl -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"gadgetId": "TEST-001", "filename": "test.jpg"}' \
  $API_URL/upload-url

# Usar la URL retornada para subir
curl -X PUT "<presigned-url>" \
  -H "Content-Type: image/jpeg" \
  --data-binary "@data/test-images/GADGET-0001.jpg"
```

## Verificación Rápida

```bash
# Ver logs de procesamiento
aws logs tail /aws/lambda/acme-image-handler-processor-sandbox --follow --profile sandbox

# Listar imágenes procesadas
curl -H "Authorization: Bearer $JWT_TOKEN" $API_URL/images | jq '.'

# Ver en DynamoDB
aws dynamodb scan \
  --table-name GadgetImages-sandbox \
  --profile sandbox \
  --max-items 5
```

## Troubleshooting Rápido

### Error: "Template validation error"
```bash
# Validar template
aws cloudformation validate-template \
  --template-body file://iac/cloudformation-base.yaml \
  --profile sandbox
```

### Error: "Lambda timeout"
```bash
# Verificar VPC Endpoints
aws ec2 describe-vpc-endpoints --profile sandbox

# Si no existen, crear:
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-xxxxx \
  --service-name com.amazonaws.us-east-1.s3 \
  --profile sandbox
```

### Error: "Access Denied"
```bash
# Verificar IAM role
aws iam get-role \
  --role-name acme-image-handler-lambda-role-sandbox \
  --profile sandbox
```

### Error: "User not found" en Cognito
```bash
# Listar usuarios
aws cognito-idp list-users \
  --user-pool-id us-east-1_xxxxxxxxx \
  --profile sandbox

# Crear usuario
./setup/create-test-user.sh sandbox
```

## Comandos Útiles

```bash
# Ver estado del stack
aws cloudformation describe-stacks \
  --stack-name acme-image-handler-sandbox \
  --profile sandbox

# Ver eventos del stack
aws cloudformation describe-stack-events \
  --stack-name acme-image-handler-sandbox \
  --profile sandbox \
  --max-items 10

# Ver logs Lambda
aws logs tail /aws/lambda/acme-image-handler-processor-sandbox --follow

# Ver métricas
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=acme-image-handler-processor-sandbox \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Eliminar stack (CUIDADO)
aws cloudformation delete-stack \
  --stack-name acme-image-handler-sandbox \
  --profile sandbox
```

## Próximos Pasos

1. **Configurar Pipeline CI/CD**
   ```bash
   aws cloudformation create-stack \
     --stack-name acme-pipeline \
     --template-body file://iac/pipeline.yaml \
     --parameters file://pipeline/pipeline-params.json \
     --capabilities CAPABILITY_NAMED_IAM \
     --profile build
   ```

2. **Desplegar a Pre-Producción**
   ```bash
   ./pipeline/deploy.sh pre-prod
   ```

3. **Configurar Monitoreo**
   - CloudWatch Dashboards
   - Alarmas
   - Budgets

4. **Optimizar Costos**
   - Eliminar NAT Gateway si no es necesario
   - Configurar S3 Lifecycle policies
   - Ajustar retención de logs

## Recursos Adicionales

- **Documentación completa**: [README.md](README.md)
- **Guía de despliegue**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Configuración de cuentas**: [ACCOUNTS.md](ACCOUNTS.md)
- **Estimación de costos**: [COSTS.md](COSTS.md)
- **Backlog**: [BACKLOG.md](BACKLOG.md)

## Soporte

Para problemas o preguntas:
- Revisar logs en CloudWatch
- Verificar eventos de CloudFormation
- Consultar documentación de AWS
- Contactar al equipo: Alejandro Granados, Rodrigo Pulido

---

**Tiempo total estimado**: 30-40 minutos  
**Costo estimado**: ~$0.50 para pruebas iniciales (dentro del free tier)
