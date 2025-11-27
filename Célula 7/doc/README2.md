# 🏆 Sistema de Votación en Tiempo Real - Gadget del Año

Sistema de votación serverless de alto rendimiento construido con AWS. Permite a usuarios autenticados votar una sola vez por su gadget favorito y ver resultados agregados en tiempo real.

## ✨ Características

- 🔐 **Autenticación segura** con AWS Cognito
- ⚡ **Tiempo real** - Resultados actualizados cada 3 segundos
- 🎯 **Idempotencia** - Un voto por usuario garantizado
- 📊 **Dashboard interactivo** con gráficos en vivo
- 🚀 **Serverless** - Escalable y económico
- 🔒 **Seguro** - IAM roles con permisos mínimos

## 🏗️ Arquitectura

```
Usuario → React → API Gateway → Lambda → DynamoDB
              ↓
           Cognito (Auth)
              
DynamoDB Votes → Stream → Lambda → DynamoDB VoteResults
```

### Componentes AWS

- **Amazon Cognito**: Autenticación de usuarios
- **API Gateway**: REST API con endpoints /vote y /results
- **AWS Lambda**: 3 funciones (EmitVote, GetResults, StreamProcessor)
- **DynamoDB**: 2 tablas (Votes, VoteResults)
- **DynamoDB Streams**: Procesamiento asíncrono
- **CloudWatch**: Logs y métricas

## 📁 Estructura del Proyecto

```
├── cloudformation/          # Infraestructura como Código
│   ├── iam-stack.yaml      # Roles y políticas IAM
│   └── main-stack.yaml     # Recursos principales AWS
├── lambda/                  # Funciones Lambda (Python 3.11)
│   ├── emit-vote/          # Registrar votos
│   ├── get-results/        # Consultar resultados
│   └── stream-processor/   # Agregar votos
├── frontend/               # Aplicación React
│   ├── src/components/     # Componentes UI
│   └── src/services/       # API y Auth
├── scripts/                # Scripts de automatización
│   ├── deploy.sh/.bat      # Despliegue completo
│   ├── package-lambdas.*   # Empaquetar Lambdas
│   ├── populate-data.*     # Poblar datos
│   └── cleanup.*           # Limpiar recursos
├── tests/                  # Scripts de prueba
│   ├── test-api.*          # Probar API con curl
│   └── create-test-user.*  # Crear usuario Cognito
└── data/                   # Datos de ejemplo
    ├── gadgets.json        # 10 gadgets nominados
    └── sample-votes.json   # 50 votos de ejemplo
```

## 🚀 Inicio Rápido

### Requisitos Previos

- AWS CLI configurado
- Python 3.11+
- Node.js 18+
- Cuenta AWS con permisos apropiados

### Despliegue en 5 Minutos

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
1. ✅ Crea bucket S3 para código Lambda
2. ✅ Empaqueta las 3 funciones Lambda
3. ✅ Despliega stack IAM con roles
4. ✅ Despliega stack principal con recursos
5. ✅ Muestra los endpoints y configuración

### Poblar Datos de Ejemplo

```bash
# Linux/Mac
./scripts/populate-data.sh

# Windows
scripts\populate-data.bat
```

Esto crea:
- 10 gadgets nominados
- 50 votos de ejemplo distribuidos

### Configurar y Ejecutar Frontend

```bash
cd frontend
cp .env.example .env
# Editar .env con los valores del despliegue
npm install
npm start
```

Abre http://localhost:3000 🎉

## 📖 Documentación

- **[QUICKSTART.md](QUICKSTART.md)** - Inicio rápido en 15 minutos
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Guía completa de despliegue
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Diseño técnico detallado
- **[TESTING.md](TESTING.md)** - Guía de pruebas exhaustiva
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Guía para contribuidores
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Resumen ejecutivo

## 🧪 Pruebas

### Probar API con curl

```bash
cd tests
./test-api.sh  # Linux/Mac
test-api.bat   # Windows
```

### Crear Usuario de Prueba

```bash
cd tests
./create-test-user.sh YOUR_USER_POOL_ID test@example.com TestPassword123!
```

### Verificar Resultados

```bash
curl https://YOUR-API-ENDPOINT/results | python -m json.tool
```

## 💰 Costos Estimados

| Usuarios/mes | Costo Mensual |
|--------------|---------------|
| Desarrollo   | < $1          |
| 1,000        | ~$5           |
| 10,000       | ~$40          |
| 100,000      | ~$300         |

## 🔒 Seguridad

- ✅ Autenticación JWT con Cognito
- ✅ Roles IAM con permisos mínimos
- ✅ CORS configurado correctamente
- ✅ Validación de entrada en Lambdas
- ✅ Logs de auditoría en CloudWatch
- ✅ HTTPS en todos los endpoints

## 📊 Datos de Ejemplo

### 10 Gadgets Nominados

1. SmartWatch Pro X - Wearables
2. AirPods Ultra - Audio
3. Drone Phantom 5 - Fotografía
4. VR Headset Elite - Realidad Virtual
5. Robot Aspiradora AI - Hogar Inteligente
6. Tablet Creator Pro - Tablets
7. Smart Speaker Max - Audio
8. Gaming Console Next - Gaming
9. E-Reader Premium - Lectura
10. Smart Thermostat - Hogar Inteligente

## 🛠️ Tecnologías

**Backend:**
- AWS Lambda (Python 3.11)
- DynamoDB (PAY_PER_REQUEST)
- API Gateway (REST)
- Cognito User Pools
- DynamoDB Streams

**Frontend:**
- React 18
- Recharts (gráficos)
- Axios (HTTP client)
- amazon-cognito-identity-js

**Infrastructure:**
- CloudFormation (YAML)
- IAM Roles y Políticas
- CloudWatch Logs

## 🔄 Flujo de Votación

1. **Usuario vota** → Frontend envía POST /vote con JWT token
2. **Lambda EmitVote** → Valida token, verifica idempotencia, guarda en DynamoDB Votes
3. **DynamoDB Stream** → Captura nuevo voto automáticamente
4. **Lambda StreamProcessor** → Incrementa contador en DynamoDB VoteResults
5. **Frontend consulta** → GET /results cada 3 segundos
6. **Lambda GetResults** → Lee VoteResults y retorna JSON
7. **Dashboard actualiza** → Muestra resultados en tiempo real

## 🧹 Limpieza de Recursos

Para eliminar todos los recursos AWS creados:

```bash
# Linux/Mac
./scripts/cleanup.sh

# Windows
scripts\cleanup.bat
```

## 🤝 Contribuir

Ver [CONTRIBUTING.md](CONTRIBUTING.md) para guía de contribución.

## 📄 Licencia

MIT License - Ver [LICENSE](LICENSE)

## 🎯 Casos de Uso

Este sistema puede adaptarse para:
- Encuestas y polls
- Sistemas de rating
- Votaciones corporativas
- Concursos y competencias
- Feedback de productos
- Elecciones internas

## 📞 Soporte

- **Documentación**: Ver archivos .md en el repositorio
- **Issues**: Abre un issue en GitHub
- **AWS Docs**: https://docs.aws.amazon.com

## 🎉 Demo

1. Registra una cuenta
2. Inicia sesión
3. Vota por tu gadget favorito
4. Observa los resultados actualizarse en tiempo real
5. Intenta votar de nuevo (verás que no puedes)

---

**Desarrollado para**: Acme Inc.  
**Proyecto**: Sistema de Votación "Gadget del Año"  
**Versión**: 1.0.0  
**Fecha**: Noviembre 2025
