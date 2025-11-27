# Inicio Rápido - Sistema de Votación Gadget del Año

Guía rápida para desplegar y ejecutar el sistema en menos de 15 minutos.

## Requisitos Previos

```bash
# Verificar instalaciones
aws --version          # AWS CLI v2
python --version       # Python 3.11+
node --version         # Node.js 18+
```

## Despliegue en 5 Pasos

### 1. Clonar y Configurar (1 min)

```bash
cd gadget-voting-system
cp config.example.sh config.sh
# Editar config.sh con tu región AWS preferida
```

### 2. Desplegar Infraestructura (5-7 min)

**Linux/Mac:**
```bash
cd scripts
chmod +x *.sh
./deploy.sh
```

**Windows:**
```cmd
cd scripts
deploy.bat
```

El script automáticamente:
- ✅ Crea bucket S3
- ✅ Empaqueta Lambdas
- ✅ Despliega stacks CloudFormation
- ✅ Muestra los endpoints

### 3. Poblar Datos de Ejemplo (1 min)

**Linux/Mac:**
```bash
./populate-data.sh
```

**Windows:**
```cmd
populate-data.bat
```

Esto crea:
- 10 gadgets nominados
- 50 votos de ejemplo

### 4. Configurar Frontend (2 min)

```bash
cd ../frontend
cp .env.example .env
```

Editar `.env` con los valores del paso 2:
```env
REACT_APP_API_ENDPOINT=https://xxxxx.execute-api.us-east-1.amazonaws.com/prod
REACT_APP_USER_POOL_ID=us-east-1_xxxxxx
REACT_APP_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 5. Ejecutar Frontend (2 min)

```bash
npm install
npm start
```

Abre http://localhost:3000 🎉

## Crear Usuario de Prueba

**Linux/Mac:**
```bash
cd ../tests
./create-test-user.sh YOUR_USER_POOL_ID test@example.com TestPassword123!
```

**Windows:**
```cmd
cd ..\tests
create-test-user.bat YOUR_USER_POOL_ID test@example.com TestPassword123!
```

## Probar el Sistema

### Desde el Frontend
1. Abre http://localhost:3000
2. Haz clic en "Registrarse"
3. Crea una cuenta con tu email
4. Inicia sesión
5. Vota por tu gadget favorito
6. Observa los resultados actualizarse en tiempo real

### Desde la Terminal (curl)

**Linux/Mac:**
```bash
cd tests
./test-api.sh
```

**Windows:**
```cmd
cd tests
test-api.bat
```

## Verificar el Despliegue

### Ver Resultados
```bash
curl https://YOUR-API-ENDPOINT/results | python -m json.tool
```

### Ver Logs de Lambda
```bash
aws logs tail /aws/lambda/GadgetVoting-EmitVote --follow
```

### Ver Tablas DynamoDB
```bash
aws dynamodb scan --table-name VoteResults
```

## Arquitectura en 30 Segundos

```
Usuario → React → API Gateway → Lambda → DynamoDB
                      ↓
                   Cognito (Auth)
                      
DynamoDB Votes → Stream → Lambda → DynamoDB VoteResults
```

## Características Principales

✅ **Autenticación**: AWS Cognito con JWT tokens
✅ **Votación Única**: Idempotencia garantizada
✅ **Tiempo Real**: Actualización cada 3 segundos
✅ **Escalable**: Serverless, paga solo por uso
✅ **Seguro**: IAM roles con permisos mínimos

## Costos Estimados

- **Desarrollo/Testing**: < $1/mes
- **1,000 usuarios**: ~$5/mes
- **10,000 usuarios**: ~$40/mes

## Limpieza de Recursos

Cuando termines de probar:

**Linux/Mac:**
```bash
cd scripts
./cleanup.sh
```

**Windows:**
```cmd
cd scripts
cleanup.bat
```

Esto elimina:
- Stacks CloudFormation
- Tablas DynamoDB
- Funciones Lambda
- API Gateway
- User Pool Cognito
- Bucket S3

## Troubleshooting Rápido

### Error: "Stack already exists"
```bash
aws cloudformation delete-stack --stack-name gadget-voting-main
aws cloudformation wait stack-delete-complete --stack-name gadget-voting-main
```

### Error: "Bucket already exists"
Cambia el nombre del bucket en `config.sh` o `deploy.bat`

### Frontend no conecta
1. Verifica que `.env` tenga los valores correctos
2. Verifica CORS en API Gateway
3. Revisa la consola del navegador (F12)

### Lambda errors
```bash
aws logs tail /aws/lambda/FUNCTION-NAME --follow
```

## Próximos Pasos

- 📖 Lee [ARCHITECTURE.md](ARCHITECTURE.md) para entender el diseño
- 🚀 Lee [DEPLOYMENT.md](DEPLOYMENT.md) para despliegue en producción
- 🤝 Lee [CONTRIBUTING.md](CONTRIBUTING.md) para contribuir

## Soporte

- Issues: Abre un issue en GitHub
- Documentación: Ver archivos .md en el repositorio
- AWS Docs: https://docs.aws.amazon.com

## Recursos Útiles

- [AWS Lambda Python](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)
- [DynamoDB Streams](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html)
- [API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/)
- [Cognito User Pools](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-identity-pools.html)
- [React Docs](https://react.dev)

---

¿Listo para empezar? Ejecuta `./scripts/deploy.sh` y estarás votando en minutos! 🚀
