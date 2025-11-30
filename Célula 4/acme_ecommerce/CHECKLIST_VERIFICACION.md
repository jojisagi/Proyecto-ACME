# ✅ Checklist de Verificación - Cambios Lambda

## 📋 Verificación de Archivos Modificados

### CloudFormation
- [x] `cloudformation/resources-stack.yaml` - Código embebido eliminado
- [x] `cloudformation/resources-stack.yaml` - Recurso LambdaCodeBucket agregado
- [x] `cloudformation/resources-stack.yaml` - Funciones Lambda referencian S3
- [x] `cloudformation/resources-stack.yaml` - Output LambdaCodeBucketName agregado

### Scripts
- [x] `scripts/deploy.sh` - Paso 2: Crear bucket Lambda agregado
- [x] `scripts/deploy.sh` - Paso 3: Empaquetar y subir Lambdas agregado
- [x] `scripts/deploy.sh` - Pasos renumerados (1-6)
- [x] `scripts/update-lambdas.sh` - Script nuevo creado
- [x] `scripts/update-lambdas.sh` - Permisos de ejecución configurados
- [x] `scripts/cleanup.sh` - Limpieza de bucket Lambda agregada
- [x] `scripts/cleanup.sh` - Pasos renumerados (1-4)

### Código Lambda
- [x] `lambdas/app-server/index.py` - Código permanece separado
- [x] `lambdas/process-order/index.py` - Código permanece separado
- [x] `lambdas/app-server/requirements.txt` - Archivo existe
- [x] `lambdas/process-order/requirements.txt` - Archivo existe

### Documentación
- [x] `README.md` - Sección de despliegue actualizada
- [x] `DEPLOYMENT.md` - Pasos manuales actualizados
- [x] `QUICK_START.md` - Sección de actualización Lambda agregada
- [x] `PROJECT_SUMMARY.md` - Estadísticas actualizadas
- [x] `INDEX.md` - Nuevo script agregado
- [x] `LAMBDA_DEPLOYMENT.md` - Guía completa creada (NUEVO)
- [x] `CHANGES.md` - Documentación de cambios creada (NUEVO)
- [x] `CHECKLIST_VERIFICACION.md` - Este archivo (NUEVO)

### Configuración
- [x] `.gitignore` - Reglas para archivos ZIP agregadas

## 🧪 Verificación Funcional

### Pre-Despliegue
- [ ] AWS CLI configurado (`aws configure`)
- [ ] Credenciales AWS válidas
- [ ] Región configurada (us-east-1 o preferida)
- [ ] Python 3.11+ instalado
- [ ] Node.js 18+ instalado (para frontend)

### Despliegue Inicial
```bash
# Ejecutar
./scripts/deploy.sh
```

- [ ] Stack IAM creado exitosamente
- [ ] Bucket Lambda creado: `ecommerce-lambda-code-<ACCOUNT_ID>`
- [ ] Archivo `app-server.zip` subido a S3
- [ ] Archivo `process-order.zip` subido a S3
- [ ] Stack de recursos creado exitosamente
- [ ] Función Lambda `app-server` creada
- [ ] Función Lambda `process-order` creada
- [ ] DynamoDB poblado con 50 órdenes
- [ ] Frontend desplegado en S3
- [ ] URLs mostradas al final del script

### Verificación de Lambdas
```bash
# Listar funciones
aws lambda list-functions --query 'Functions[?contains(FunctionName,`app-server`) || contains(FunctionName,`process-order`)].FunctionName'
```

- [ ] Función `app-server` existe
- [ ] Función `process-order` existe

```bash
# Verificar configuración
aws lambda get-function-configuration --function-name app-server
```

- [ ] Runtime: python3.11
- [ ] Handler: index.lambda_handler
- [ ] Timeout: 30
- [ ] MemorySize: 128

### Verificación de S3
```bash
# Listar archivos en bucket Lambda
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws s3 ls s3://ecommerce-lambda-code-$ACCOUNT_ID/
```

- [ ] Archivo `app-server.zip` existe
- [ ] Archivo `process-order.zip` existe

```bash
# Verificar versionamiento
aws s3api get-bucket-versioning --bucket ecommerce-lambda-code-$ACCOUNT_ID
```

- [ ] Versionamiento habilitado

### Verificación de API
```bash
# Obtener URL del API
API_URL=$(aws cloudformation describe-stacks \
  --stack-name ecommerce-resources \
  --query "Stacks[0].Outputs[?OutputKey=='ApiGatewayUrl'].OutputValue" \
  --output text)

# Probar API
./scripts/test-api.sh $API_URL
```

- [ ] Test 1: Health check - 200 OK
- [ ] Test 2: Crear orden - 201 Created
- [ ] Test 3: Listar órdenes - 200 OK
- [ ] Test 4: Obtener orden - 200 OK
- [ ] Test 5: Crear orden múltiple - 201 Created
- [ ] Test 6: Buscar por cliente - 200 OK
- [ ] Test 7: Error datos incompletos - 400 Bad Request
- [ ] Test 8: Orden inexistente - 404 Not Found

### Actualización de Lambda
```bash
# Modificar código
echo "# Test comment" >> lambdas/app-server/index.py

# Actualizar
./scripts/update-lambdas.sh
```

- [ ] Script ejecuta sin errores
- [ ] Archivos ZIP creados
- [ ] Archivos subidos a S3
- [ ] Funciones Lambda actualizadas
- [ ] Archivos temporales limpiados

```bash
# Verificar actualización
aws lambda get-function --function-name app-server \
  --query 'Configuration.LastModified'
```

- [ ] Fecha de modificación actualizada

### Verificación de Logs
```bash
# Ver logs recientes
aws logs tail /aws/lambda/app-server --since 5m
```

- [ ] Logs visibles
- [ ] Sin errores críticos

### Limpieza
```bash
./scripts/cleanup.sh
```

- [ ] Confirmación solicitada
- [ ] Bucket frontend vaciado
- [ ] Bucket Lambda vaciado
- [ ] Stack de recursos eliminado
- [ ] Stack IAM eliminado
- [ ] Archivos locales limpiados

## 📊 Verificación de Documentación

### README.md
- [x] Sección "Despliegue" actualizada
- [x] Opción 1: Despliegue automatizado
- [x] Opción 2: Despliegue manual con pasos S3
- [x] Sección "Actualizar Solo las Lambdas" agregada

### DEPLOYMENT.md
- [x] Paso 2: Crear bucket y subir código Lambda
- [x] Paso 3: Desplegar stack de recursos
- [x] Pasos renumerados correctamente
- [x] Sección "Actualizar Lambda" con script update-lambdas.sh

### QUICK_START.md
- [x] Sección "Actualizar Código Lambda" agregada
- [x] Comando `./scripts/update-lambdas.sh` documentado
- [x] Pasos del script explicados

### LAMBDA_DEPLOYMENT.md (NUEVO)
- [x] Estructura de código Lambda
- [x] Arquitectura de despliegue
- [x] Flujo de despliegue
- [x] Despliegue inicial (automatizado y manual)
- [x] Actualizar código Lambda
- [x] Agregar dependencias
- [x] Verificar despliegue
- [x] Troubleshooting
- [x] Versionamiento
- [x] Seguridad
- [x] Mejores prácticas

### CHANGES.md (NUEVO)
- [x] Resumen de cambios
- [x] Cambios implementados detallados
- [x] Beneficios explicados
- [x] Comparación antes/después
- [x] Flujo de trabajo
- [x] Estructura de archivos
- [x] Guía de migración
- [x] Testing
- [x] Notas adicionales

## 🎯 Verificación de Mejores Prácticas

### Código
- [x] Código Lambda en archivos Python separados
- [x] Syntax highlighting disponible
- [x] Estructura de directorios clara
- [x] requirements.txt para dependencias

### Infraestructura
- [x] Código separado de infraestructura
- [x] Versionamiento en S3
- [x] Bucket dedicado para código Lambda
- [x] Referencias correctas en CloudFormation

### Scripts
- [x] Scripts con permisos de ejecución
- [x] Manejo de errores (set -e)
- [x] Output con colores
- [x] Mensajes informativos
- [x] Limpieza de archivos temporales

### Documentación
- [x] Guías actualizadas
- [x] Ejemplos de comandos
- [x] Troubleshooting incluido
- [x] Mejores prácticas documentadas

## 🔍 Verificación de Integración

### CloudFormation → S3
- [ ] Template referencia bucket correcto
- [ ] S3Key correcto (app-server.zip, process-order.zip)
- [ ] Bucket existe antes de crear stack

### S3 → Lambda
- [ ] Archivos ZIP en S3
- [ ] Lambda puede leer desde S3
- [ ] Permisos IAM correctos

### Script → S3 → Lambda
- [ ] Script empaqueta correctamente
- [ ] Script sube a S3
- [ ] Lambda se actualiza desde S3

## ✅ Checklist Final

### Archivos Críticos
- [x] cloudformation/resources-stack.yaml - Modificado correctamente
- [x] scripts/deploy.sh - Actualizado con nuevos pasos
- [x] scripts/update-lambdas.sh - Creado y funcional
- [x] scripts/cleanup.sh - Actualizado para limpiar bucket Lambda
- [x] lambdas/app-server/index.py - Código separado intacto
- [x] lambdas/process-order/index.py - Código separado intacto

### Funcionalidad
- [ ] Despliegue inicial funciona
- [ ] Actualización de Lambda funciona
- [ ] API responde correctamente
- [ ] Limpieza funciona

### Documentación
- [x] Todas las guías actualizadas
- [x] Nuevas guías creadas
- [x] Ejemplos de comandos correctos
- [x] Referencias actualizadas

## 📝 Notas de Verificación

### Problemas Conocidos
- Ninguno identificado

### Mejoras Futuras
- [ ] Agregar tests unitarios para Lambdas
- [ ] Implementar CI/CD pipeline
- [ ] Agregar Lambda Layers para dependencias
- [ ] Implementar blue/green deployment

### Feedback
- Documentar aquí cualquier problema encontrado durante la verificación
- Sugerencias de mejora

---

**Fecha de Verificación**: _______________
**Verificado por**: _______________
**Estado**: ⬜ Pendiente | ⬜ En Progreso | ⬜ Completado
**Notas adicionales**: 

---
