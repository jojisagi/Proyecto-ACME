# Índice de Documentación - Sistema de Scheduling Serverless

## 📖 Guías de Inicio

| Documento | Descripción | Tiempo de Lectura |
|-----------|-------------|-------------------|
| [README.md](README.md) | Descripción general del proyecto | 5 min |
| [QUICK_START.md](QUICK_START.md) | Guía de inicio rápido con ejemplos | 10 min |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Resumen ejecutivo del proyecto | 5 min |

## 🏗️ Documentación Técnica

| Documento | Descripción | Audiencia |
|-----------|-------------|-----------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Arquitectura detallada del sistema | Arquitectos, DevOps |
| [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) | Guía paso a paso de despliegue | DevOps, Desarrolladores |
| [docs/API_REFERENCE.md](docs/API_REFERENCE.md) | Documentación completa de la API | Desarrolladores |
| [docs/DIAGRAMS.md](docs/DIAGRAMS.md) | Diagramas visuales (Mermaid) | Todos |

## 💻 Código Fuente

### Infraestructura como Código (IaC)

| Archivo | Descripción | Recursos |
|---------|-------------|----------|
| [iac/iam_stack.yml](iac/iam_stack.yml) | Roles y políticas IAM | 3 roles, políticas |
| [iac/main_stack.yml](iac/main_stack.yml) | Stack principal de AWS | VPC, Lambda, API Gateway, DynamoDB, Cognito, KMS |

### Funciones Lambda

| Archivo | Descripción | Runtime | Trigger |
|---------|-------------|---------|---------|
| [src/scheduler_manager/app.py](src/scheduler_manager/app.py) | Gestión de schedules (CRUD) | Python 3.11 | API Gateway |
| [src/order_executor/app.py](src/order_executor/app.py) | Generación de órdenes | Python 3.11 | EventBridge Scheduler |
| [src/data_generator/app.py](src/data_generator/app.py) | Generador de datos sintéticos | Python 3.11 | Manual |

## 🔧 Scripts de Automatización

### Scripts Bash (Linux/Mac/Git Bash)

| Script | Descripción | Uso |
|--------|-------------|-----|
| [scripts/package_lambdas.sh](scripts/package_lambdas.sh) | Empaqueta Lambdas en ZIP | `./package_lambdas.sh` |
| [scripts/deploy_stack.sh](scripts/deploy_stack.sh) | Despliega infraestructura completa | `./deploy_stack.sh` |
| [scripts/curl_tests.sh](scripts/curl_tests.sh) | Suite de pruebas funcionales | `./curl_tests.sh` |

### Scripts PowerShell (Windows)

| Script | Descripción | Uso |
|--------|-------------|-----|
| [scripts/package_lambdas.ps1](scripts/package_lambdas.ps1) | Empaqueta Lambdas en ZIP | `.\package_lambdas.ps1` |
| [scripts/deploy_stack.ps1](scripts/deploy_stack.ps1) | Despliega infraestructura completa | `.\deploy_stack.ps1` |
| [scripts/curl_tests.ps1](scripts/curl_tests.ps1) | Suite de pruebas funcionales | `.\curl_tests.ps1` |

## 📊 Datos de Prueba

| Archivo | Descripción | Registros |
|---------|-------------|-----------|
| [data/sample_orders.json](data/sample_orders.json) | Órdenes sintéticas para pruebas | 50+ |

## 🗺️ Mapa de Navegación por Rol

### Para Arquitectos de Soluciones

1. Leer [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) para visión general
2. Revisar [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) para detalles técnicos
3. Estudiar [docs/DIAGRAMS.md](docs/DIAGRAMS.md) para visualización
4. Analizar [iac/main_stack.yml](iac/main_stack.yml) para recursos AWS

### Para Desarrolladores

1. Comenzar con [QUICK_START.md](QUICK_START.md)
2. Consultar [docs/API_REFERENCE.md](docs/API_REFERENCE.md) para endpoints
3. Revisar código en [src/](src/)
4. Ejecutar [scripts/curl_tests.sh](scripts/curl_tests.sh) para probar

### Para DevOps/SRE

1. Leer [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)
2. Ejecutar [scripts/deploy_stack.sh](scripts/deploy_stack.sh)
3. Revisar [iac/](iac/) para infraestructura
4. Configurar monitoreo según [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

### Para Product Managers

1. Leer [README.md](README.md) para descripción general
2. Revisar [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) para métricas
3. Ver [docs/DIAGRAMS.md](docs/DIAGRAMS.md) para flujos de negocio
4. Consultar costos en [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## 📋 Checklist de Implementación

### Fase 1: Preparación
- [ ] Instalar AWS CLI
- [ ] Configurar credenciales AWS
- [ ] Verificar permisos IAM
- [ ] Clonar repositorio

### Fase 2: Despliegue
- [ ] Ejecutar `deploy_stack.sh` o `deploy_stack.ps1`
- [ ] Verificar stacks en CloudFormation
- [ ] Crear usuario en Cognito
- [ ] Anotar API Endpoint y credenciales

### Fase 3: Validación
- [ ] Ejecutar `curl_tests.sh` o `curl_tests.ps1`
- [ ] Verificar logs en CloudWatch
- [ ] Consultar tablas DynamoDB
- [ ] Verificar schedules en EventBridge

### Fase 4: Monitoreo
- [ ] Configurar alarmas CloudWatch
- [ ] Revisar métricas de Lambda
- [ ] Monitorear costos en Cost Explorer
- [ ] Documentar configuración específica

## 🔍 Búsqueda Rápida

### Buscar por Tema

**Autenticación:**
- [docs/API_REFERENCE.md#autenticación](docs/API_REFERENCE.md)
- [QUICK_START.md#paso-2-crear-usuario-de-prueba](QUICK_START.md)

**Seguridad:**
- [docs/ARCHITECTURE.md#seguridad](docs/ARCHITECTURE.md)
- [iac/iam_stack.yml](iac/iam_stack.yml)

**API Endpoints:**
- [docs/API_REFERENCE.md#endpoints](docs/API_REFERENCE.md)
- [QUICK_START.md#ejemplos-de-uso](QUICK_START.md)

**Costos:**
- [docs/ARCHITECTURE.md#costos-estimados](docs/ARCHITECTURE.md)
- [docs/DIAGRAMS.md#costos-por-componente](docs/DIAGRAMS.md)

**Troubleshooting:**
- [docs/DEPLOYMENT_GUIDE.md#troubleshooting](docs/DEPLOYMENT_GUIDE.md)
- [QUICK_START.md#verificar-el-sistema](QUICK_START.md)

**Lógica de Negocio:**
- [src/order_executor/app.py](src/order_executor/app.py)
- [docs/API_REFERENCE.md#lógica-de-negocio](docs/API_REFERENCE.md)

## 📞 Soporte y Recursos

### Documentación AWS
- [EventBridge Scheduler](https://docs.aws.amazon.com/scheduler/latest/UserGuide/what-is-scheduler.html)
- [Lambda](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html)
- [DynamoDB](https://docs.aws.amazon.com/dynamodb/latest/developerguide/Introduction.html)
- [API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html)
- [Cognito](https://docs.aws.amazon.com/cognito/latest/developerguide/what-is-amazon-cognito.html)

### Herramientas Útiles
- [AWS CLI](https://aws.amazon.com/cli/)
- [Mermaid Live Editor](https://mermaid.live/)
- [Postman](https://www.postman.com/) - Para pruebas de API
- [AWS Console](https://console.aws.amazon.com/)

### Contacto
Para preguntas o problemas:
- Revisar documentación en `/docs`
- Consultar logs de CloudWatch
- Contactar al equipo de arquitectura de Acme Inc.

## 📝 Notas de Versión

### v1.0.0 (Actual)
- ✅ Implementación completa de arquitectura serverless
- ✅ 2 funciones Lambda (Scheduler Manager, Order Executor)
- ✅ API Gateway con 5 endpoints
- ✅ Autenticación con Cognito
- ✅ Cifrado KMS
- ✅ VPC con subredes privadas
- ✅ Scripts de despliegue (Bash + PowerShell)
- ✅ Documentación completa
- ✅ 50+ datos de prueba

### Próximas Versiones (Roadmap)
- [ ] v1.1.0: Notificaciones SNS/SES
- [ ] v1.2.0: Step Functions para workflows
- [ ] v1.3.0: Multi-región
- [ ] v2.0.0: CI/CD con CodePipeline

## 🎯 Objetivos del Proyecto

1. **Automatización**: Generación automática de órdenes sin intervención manual
2. **Escalabilidad**: Arquitectura serverless que escala automáticamente
3. **Seguridad**: Múltiples capas de seguridad (autenticación, cifrado, red)
4. **Observabilidad**: Logs y métricas completas en CloudWatch
5. **Mantenibilidad**: Código limpio, documentado y con IaC

## ✅ Estado del Proyecto

**Estado**: ✅ Completado y Listo para Producción

**Última Actualización**: Noviembre 2025

**Mantenedor**: Equipo de Arquitectura - Acme Inc.

---

**Nota**: Este índice se actualiza automáticamente con cada cambio en la documentación.
