# Índice de Documentación - Célula 3

Guía completa de navegación por toda la documentación del proyecto.

## 📚 Documentación Principal

### 🚀 Para Empezar

| Documento | Descripción | Tiempo | Audiencia |
|-----------|-------------|--------|-----------|
| [README.md](README.md) | Documentación principal del proyecto | 15 min | Todos |
| [QUICKSTART.md](QUICKSTART.md) | Guía rápida para poner en marcha el sistema | 30 min | Developers |
| [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) | Resumen ejecutivo del proyecto | 10 min | Management |

### 🏗️ Arquitectura e Infraestructura

| Documento | Descripción | Tiempo | Audiencia |
|-----------|-------------|--------|-----------|
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | Estructura completa del proyecto | 10 min | Developers |
| [Arquitectura Celula 3.png](Arquitectura%20Celula%203.png) | Diagrama de arquitectura visual | 5 min | Todos |
| [iac/cloudformation-base.yaml](iac/cloudformation-base.yaml) | Template de infraestructura | 20 min | DevOps |
| [iac/pipeline.yaml](iac/pipeline.yaml) | Template del pipeline CI/CD | 15 min | DevOps |

### 🔧 Despliegue y Configuración

| Documento | Descripción | Tiempo | Audiencia |
|-----------|-------------|--------|-----------|
| [DEPLOYMENT.md](DEPLOYMENT.md) | Guía detallada de despliegue | 30 min | DevOps |
| [ACCOUNTS.md](ACCOUNTS.md) | Configuración de cuentas AWS | 20 min | DevOps |
| [buildspec.yml](buildspec.yml) | Configuración de CodeBuild | 10 min | DevOps |

### 💰 Costos y Planificación

| Documento | Descripción | Tiempo | Audiencia |
|-----------|-------------|--------|-----------|
| [COSTS.md](COSTS.md) | Estimación detallada de costos | 15 min | Management, DevOps |
| [BACKLOG.md](BACKLOG.md) | Product backlog e historias de usuario | 20 min | Product Owner, Developers |

### 📖 Referencias y Comandos

| Documento | Descripción | Tiempo | Audiencia |
|-----------|-------------|--------|-----------|
| [COMMANDS_CHEATSHEET.md](COMMANDS_CHEATSHEET.md) | Referencia rápida de comandos | 10 min | Developers, DevOps |

## 📁 Código Fuente

### Lambda Functions

| Archivo | Descripción | Lenguaje |
|---------|-------------|----------|
| [src/lambda/image-processor/lambda_function.py](src/lambda/image-processor/lambda_function.py) | Procesamiento de imágenes | Python |
| [src/lambda/api-handler/lambda_function.py](src/lambda/api-handler/lambda_function.py) | Handler del API REST | Python |

### Scripts de Despliegue

| Script | Descripción | Uso |
|--------|-------------|-----|
| [pipeline/deploy.sh](pipeline/deploy.sh) | Despliegue manual | `./pipeline/deploy.sh sandbox` |
| [setup/setup-accounts.sh](setup/setup-accounts.sh) | Configuración de cuentas | `./setup/setup-accounts.sh` |
| [setup/create-test-user.sh](setup/create-test-user.sh) | Crear usuario de prueba | `./setup/create-test-user.sh sandbox` |

### Scripts de Pruebas

| Script | Descripción | Uso |
|--------|-------------|-----|
| [tests/generate-test-data.py](tests/generate-test-data.py) | Generar imágenes sintéticas | `python3 tests/generate-test-data.py` |
| [tests/test-api.sh](tests/test-api.sh) | Suite de pruebas funcionales | `./tests/test-api.sh` |

## 🗂️ Configuración

### Parámetros por Ambiente

| Archivo | Ambiente | Descripción |
|---------|----------|-------------|
| [pipeline/parameters-sandbox.json](pipeline/parameters-sandbox.json) | Sandbox | Parámetros de desarrollo |
| [pipeline/parameters-pre-prod.json](pipeline/parameters-pre-prod.json) | Pre-Prod | Parámetros de pre-producción |
| [pipeline/parameters-prod.json](pipeline/parameters-prod.json) | Producción | Parámetros de producción |

### Otros

| Archivo | Descripción |
|---------|-------------|
| [.gitignore](.gitignore) | Archivos ignorados por Git |
| [src/config.py](src/config.py) | Configuración compartida |

## 📊 Datos de Prueba

| Recurso | Descripción |
|---------|-------------|
| [data/README.md](data/README.md) | Guía de datos de prueba |
| [data/test-metadata.json](data/test-metadata.json) | Metadatos de imágenes de prueba |
| `data/test-images/` | Imágenes generadas (50 archivos) |

## 📋 Flujos de Trabajo Comunes

### 1. Setup Inicial (Primera Vez)

```
1. Leer: QUICKSTART.md
2. Ejecutar: setup/setup-accounts.sh
3. Editar: pipeline/parameters-*.json
4. Ejecutar: pipeline/deploy.sh sandbox
5. Ejecutar: setup/create-test-user.sh sandbox
6. Ejecutar: tests/test-api.sh
```

**Documentos relevantes:**
- [QUICKSTART.md](QUICKSTART.md)
- [ACCOUNTS.md](ACCOUNTS.md)
- [DEPLOYMENT.md](DEPLOYMENT.md)

### 2. Desarrollo de Features

```
1. Leer: BACKLOG.md (seleccionar historia)
2. Modificar: src/lambda/*/lambda_function.py
3. Probar localmente (opcional)
4. Commit y push a GitHub
5. Pipeline despliega automáticamente
6. Verificar: tests/test-api.sh
```

**Documentos relevantes:**
- [BACKLOG.md](BACKLOG.md)
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
- [README.md](README.md)

### 3. Despliegue a Producción

```
1. Leer: DEPLOYMENT.md (sección producción)
2. Verificar: tests en sandbox y pre-prod
3. Ejecutar: pipeline/deploy.sh prod
   O aprobar en CodePipeline
4. Verificar: outputs del stack
5. Ejecutar: tests/test-api.sh (en prod)
6. Monitorear: CloudWatch Logs
```

**Documentos relevantes:**
- [DEPLOYMENT.md](DEPLOYMENT.md)
- [COMMANDS_CHEATSHEET.md](COMMANDS_CHEATSHEET.md)

### 4. Troubleshooting

```
1. Leer: README.md (sección Troubleshooting)
2. Consultar: COMMANDS_CHEATSHEET.md
3. Ver logs: CloudWatch
4. Verificar: CloudFormation events
5. Consultar: DEPLOYMENT.md (sección Troubleshooting)
```

**Documentos relevantes:**
- [README.md](README.md) - Sección Troubleshooting
- [DEPLOYMENT.md](DEPLOYMENT.md) - Sección Troubleshooting
- [COMMANDS_CHEATSHEET.md](COMMANDS_CHEATSHEET.md)

### 5. Estimación de Costos

```
1. Leer: COSTS.md
2. Identificar: ambiente y tráfico esperado
3. Calcular: costos por servicio
4. Configurar: alertas de costos
5. Revisar: mensualmente
```

**Documentos relevantes:**
- [COSTS.md](COSTS.md)
- [COMMANDS_CHEATSHEET.md](COMMANDS_CHEATSHEET.md) - Sección Costos

## 🎯 Por Rol

### Developer

**Lectura esencial:**
1. [README.md](README.md)
2. [QUICKSTART.md](QUICKSTART.md)
3. [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
4. [BACKLOG.md](BACKLOG.md)

**Referencia frecuente:**
- [COMMANDS_CHEATSHEET.md](COMMANDS_CHEATSHEET.md)
- [src/lambda/](src/lambda/)

### DevOps Engineer

**Lectura esencial:**
1. [DEPLOYMENT.md](DEPLOYMENT.md)
2. [ACCOUNTS.md](ACCOUNTS.md)
3. [iac/cloudformation-base.yaml](iac/cloudformation-base.yaml)
4. [iac/pipeline.yaml](iac/pipeline.yaml)

**Referencia frecuente:**
- [COMMANDS_CHEATSHEET.md](COMMANDS_CHEATSHEET.md)
- [pipeline/](pipeline/)

### QA Engineer

**Lectura esencial:**
1. [README.md](README.md)
2. [QUICKSTART.md](QUICKSTART.md)
3. [tests/test-api.sh](tests/test-api.sh)
4. [data/README.md](data/README.md)

**Referencia frecuente:**
- [tests/](tests/)
- [COMMANDS_CHEATSHEET.md](COMMANDS_CHEATSHEET.md)

### Product Owner

**Lectura esencial:**
1. [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md)
2. [BACKLOG.md](BACKLOG.md)
3. [COSTS.md](COSTS.md)
4. [README.md](README.md)

**Referencia frecuente:**
- [BACKLOG.md](BACKLOG.md)
- [COSTS.md](COSTS.md)

### Management

**Lectura esencial:**
1. [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md)
2. [COSTS.md](COSTS.md)
3. [README.md](README.md) - Sección Resumen

**Referencia frecuente:**
- [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md)

## 📈 Métricas del Proyecto

### Documentación

- **Total de documentos**: 15+
- **Líneas de código**: ~1,500
- **Líneas de IaC**: ~800
- **Líneas de documentación**: ~5,000
- **Scripts**: 5
- **Templates CloudFormation**: 2

### Cobertura

- ✅ Arquitectura: 100%
- ✅ Código: 100%
- ✅ Infraestructura: 100%
- ✅ Despliegue: 100%
- ✅ Pruebas: 100%
- ✅ Documentación: 100%

## 🔍 Búsqueda Rápida

### Por Tema

| Tema | Documentos |
|------|-----------|
| **Arquitectura** | README.md, PROJECT_STRUCTURE.md, Arquitectura.png |
| **Despliegue** | DEPLOYMENT.md, QUICKSTART.md, pipeline/deploy.sh |
| **Costos** | COSTS.md, EXECUTIVE_SUMMARY.md |
| **Seguridad** | README.md, DEPLOYMENT.md, iac/cloudformation-base.yaml |
| **Pruebas** | tests/, data/README.md |
| **CI/CD** | iac/pipeline.yaml, buildspec.yml |
| **APIs** | src/lambda/api-handler/, README.md |
| **Procesamiento** | src/lambda/image-processor/ |

### Por Servicio AWS

| Servicio | Documentos |
|----------|-----------|
| **Lambda** | src/lambda/, iac/cloudformation-base.yaml |
| **S3** | iac/cloudformation-base.yaml, COMMANDS_CHEATSHEET.md |
| **DynamoDB** | iac/cloudformation-base.yaml, COMMANDS_CHEATSHEET.md |
| **API Gateway** | iac/cloudformation-base.yaml, README.md |
| **Cognito** | iac/cloudformation-base.yaml, setup/create-test-user.sh |
| **CloudFormation** | iac/, DEPLOYMENT.md |
| **CodePipeline** | iac/pipeline.yaml, buildspec.yml |

## 📞 Soporte

Para preguntas o problemas:

1. **Consultar documentación**: Usar este índice para encontrar el documento relevante
2. **Revisar logs**: Ver COMMANDS_CHEATSHEET.md para comandos de logs
3. **Troubleshooting**: Ver secciones de troubleshooting en README.md y DEPLOYMENT.md
4. **Contactar equipo**: Alejandro Granados, Rodrigo Pulido

## 🔄 Actualizaciones

Este índice se actualiza con cada cambio significativo en la documentación.

**Última actualización**: Noviembre 2025  
**Versión**: 1.0  
**Mantenedores**: Célula 3 - Universidad La Salle

---

**Tip**: Usa Ctrl+F (Cmd+F en Mac) para buscar términos específicos en este índice.
