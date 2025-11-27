# ✅ Checklist de Validación Post-Despliegue

Lista de verificación completa para validar que el sistema está funcionando correctamente.

## 📋 Pre-Despliegue

### Requisitos del Sistema
- [ ] AWS CLI instalado y configurado
- [ ] Python 3.11+ instalado
- [ ] Node.js 18+ instalado
- [ ] Credenciales AWS con permisos apropiados
- [ ] Región AWS seleccionada

### Archivos y Configuración
- [ ] Plantillas CloudFormation validadas
- [ ] Código Lambda sin errores de sintaxis
- [ ] Frontend compila sin errores (`npm run build`)
- [ ] Scripts tienen permisos de ejecución (Linux/Mac)

## 🚀 Durante el Despliegue

### Stack IAM
- [ ] Stack creado exitosamente
- [ ] 4 roles IAM creados
- [ ] Outputs exportados correctamente
- [ ] Sin errores en eventos del stack

### Stack Principal
- [ ] Stack creado exitosamente
- [ ] User Pool de Cognito creado
- [ ] User Pool Client creado
- [ ] Tabla Votes creada
- [ ] Tabla VoteResults creada
- [ ] Stream habilitado en Votes
- [ ] 3 funciones Lambda creadas
- [ ] Event Source Mapping configurado
- [ ] API Gateway creado
- [ ] Authorizer de Cognito configurado
- [ ] Endpoints /vote y /results creados
- [ ] CORS configurado
- [ ] Deployment y Stage creados
- [ ] Permisos de Lambda configurados
- [ ] Sin errores en eventos del stack

### Outputs del Stack
- [ ] ApiEndpoint disponible
- [ ] UserPoolId disponible
- [ ] UserPoolClientId disponible
- [ ] VotesTableName disponible
- [ ] VoteResultsTableName disponible

## 🔍 Post-Despliegue - Infraestructura

### CloudFormation
```bash
# Verificar estado de los stacks
aws cloudformation describe-stacks --stack-name gadget-voting-iam --query 'Stacks[0].StackStatus'
# Esperado: CREATE_COMPLETE

aws cloudformation describe-stacks --stack-name gadget-voting-main --query 'Stacks[0].StackStatus'
# Esperado: CREATE_COMPLETE
```
- [ ] Stack IAM en estado CREATE_COMPLETE
- [ ] Stack principal en estado CREATE_COMPLETE
- [ ] Todos los outputs disponibles

### Lambda Functions
```bash
# Listar funciones
aws lambda list-functions --query 'Functions[?contains(FunctionName, `GadgetVoting`)].FunctionName'
```
- [ ] GadgetVoting-EmitVote existe
- [ ] GadgetVoting-GetResults existe
- [ ] GadgetVoting-StreamProcessor existe
- [ ] Todas las funciones en estado Active
- [ ] Variables de entorno configuradas
- [ ] Roles IAM asignados correctamente

### DynamoDB
```bash
# Verificar tablas
aws dynamodb list-tables
```
- [ ] Tabla Votes existe
- [ ] Tabla VoteResults existe
- [ ] Stream habilitado en Votes
- [ ] Billing mode: PAY_PER_REQUEST

### API Gateway
```bash
# Obtener endpoint
aws cloudformation describe-stacks --stack-name gadget-voting-main --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text
```
- [ ] API Gateway creado
- [ ] Endpoint accesible
- [ ] Stage 'prod' desplegado
- [ ] Authorizer configurado

### Cognito
```bash
# Verificar User Pool
aws cognito-idp describe-user-pool --user-pool-id YOUR-USER-POOL-ID
```
- [ ] User Pool creado
- [ ] Client creado
- [ ] Email como username configurado
- [ ] Auto-verified attributes: email

## 🧪 Post-Despliegue - Funcionalidad

### Poblar Datos
```bash
cd scripts && ./populate-data.sh
```
- [ ] Script ejecutado sin errores
- [ ] 10 gadgets insertados en VoteResults
- [ ] 50 votos insertados en Votes
- [ ] Contadores actualizados en VoteResults (esperar 5-10 segundos)

### Verificar Datos
```bash
# Contar votos
aws dynamodb scan --table-name Votes --select COUNT

# Ver resultados
aws dynamodb scan --table-name VoteResults
```
- [ ] Tabla Votes tiene 50 items
- [ ] Tabla VoteResults tiene 10 items
- [ ] totalVotes > 0 en VoteResults

### API - GET /results (Público)
```bash
curl -X GET https://YOUR-API-ENDPOINT/results
```
- [ ] Respuesta HTTP 200
- [ ] JSON válido retornado
- [ ] Campo 'results' presente
- [ ] Campo 'totalVotes' presente
- [ ] Suma de votos coincide con datos

### API - POST /vote (Sin Auth - Debe Fallar)
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"gadgetId": "gadget-001"}' \
  https://YOUR-API-ENDPOINT/vote
```
- [ ] Respuesta HTTP 401 o 403
- [ ] Mensaje de error apropiado

### API - OPTIONS (CORS)
```bash
curl -X OPTIONS \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -v \
  https://YOUR-API-ENDPOINT/vote
```
- [ ] Respuesta HTTP 200
- [ ] Header Access-Control-Allow-Origin presente
- [ ] Header Access-Control-Allow-Methods presente
- [ ] Header Access-Control-Allow-Headers presente

### Cognito - Crear Usuario
```bash
cd tests && ./create-test-user.sh YOUR-USER-POOL-ID test@example.com TestPassword123!
```
- [ ] Usuario creado exitosamente
- [ ] Usuario confirmado
- [ ] Token JWT obtenido

### API - POST /vote (Con Auth)
```bash
# Usar token del paso anterior
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ID_TOKEN" \
  -d '{"gadgetId": "gadget-001"}' \
  https://YOUR-API-ENDPOINT/vote
```
- [ ] Respuesta HTTP 201
- [ ] Mensaje de éxito retornado
- [ ] Voto registrado en DynamoDB

### Verificar Voto en DynamoDB
```bash
aws dynamodb get-item \
  --table-name Votes \
  --key '{"userId": {"S": "YOUR-USER-SUB"}, "voteId": {"S": "VOTE"}}'
```
- [ ] Voto encontrado en tabla Votes
- [ ] gadgetId correcto
- [ ] timestamp presente

### Verificar Procesamiento de Stream
```bash
# Esperar 5-10 segundos, luego verificar
aws dynamodb get-item \
  --table-name VoteResults \
  --key '{"gadgetId": {"S": "gadget-001"}}'
```
- [ ] totalVotes incrementado en 1
- [ ] Procesamiento automático funcionando

### Idempotencia - Votar Dos Veces
```bash
# Intentar votar de nuevo con el mismo usuario
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ID_TOKEN" \
  -d '{"gadgetId": "gadget-002"}' \
  https://YOUR-API-ENDPOINT/vote
```
- [ ] Respuesta HTTP 409 (Conflict)
- [ ] Mensaje "Usuario ya ha votado"
- [ ] Voto original no modificado

### Lambda Logs
```bash
# Ver logs de EmitVote
aws logs tail /aws/lambda/GadgetVoting-EmitVote --since 10m

# Ver logs de StreamProcessor
aws logs tail /aws/lambda/GadgetVoting-StreamProcessor --since 10m
```
- [ ] Logs de EmitVote muestran voto registrado
- [ ] Logs de StreamProcessor muestran procesamiento
- [ ] Sin errores en logs

## 🖥️ Frontend

### Configuración
```bash
cd frontend
cp .env.example .env
# Editar .env con valores correctos
```
- [ ] Archivo .env creado
- [ ] REACT_APP_API_ENDPOINT configurado
- [ ] REACT_APP_USER_POOL_ID configurado
- [ ] REACT_APP_CLIENT_ID configurado

### Instalación y Build
```bash
npm install
npm run build
```
- [ ] Dependencias instaladas sin errores
- [ ] Build exitoso
- [ ] Carpeta build/ creada

### Ejecución Local
```bash
npm start
```
- [ ] Aplicación inicia en http://localhost:3000
- [ ] Sin errores en consola del navegador
- [ ] Página de login visible

### Registro de Usuario
- [ ] Formulario de registro funciona
- [ ] Validación de email funciona
- [ ] Validación de contraseña funciona
- [ ] Usuario creado en Cognito
- [ ] Mensaje de éxito mostrado

### Inicio de Sesión
- [ ] Formulario de login funciona
- [ ] Autenticación exitosa
- [ ] Redirección al dashboard
- [ ] Nombre de usuario mostrado en header

### Dashboard
- [ ] 10 gadgets mostrados
- [ ] Votos actuales visibles
- [ ] Porcentajes calculados correctamente
- [ ] Gráfico de barras renderizado
- [ ] Top 3 mostrado correctamente

### Votación
- [ ] Click en gadget funciona
- [ ] Mensaje de confirmación mostrado
- [ ] Voto registrado en backend
- [ ] Gadgets deshabilitados después de votar
- [ ] No se puede votar de nuevo

### Actualización en Tiempo Real
- [ ] Resultados se actualizan cada 3 segundos
- [ ] Contador de votos incrementa
- [ ] Porcentajes se recalculan
- [ ] Gráfico se actualiza
- [ ] Top 3 se reordena si es necesario

### Cerrar Sesión
- [ ] Botón de logout funciona
- [ ] Sesión cerrada en Cognito
- [ ] Redirección a login
- [ ] No se puede acceder al dashboard sin login

## 📊 Rendimiento

### Latencia
```bash
# Medir latencia de GET /results
time curl -X GET https://YOUR-API-ENDPOINT/results
```
- [ ] Latencia < 1 segundo para votar
- [ ] Latencia < 500ms para resultados
- [ ] Procesamiento de stream < 10 segundos

### Carga
```bash
# Ejecutar 10 requests concurrentes
for i in {1..10}; do
  curl -X GET https://YOUR-API-ENDPOINT/results &
done
wait
```
- [ ] Todas las requests exitosas
- [ ] Sin throttling
- [ ] Sin errores 5XX

## 🔒 Seguridad

### Autenticación
- [ ] Endpoint /vote requiere autenticación
- [ ] Token inválido es rechazado
- [ ] Token expirado es rechazado
- [ ] Endpoint /results es público

### Autorización
- [ ] Roles IAM con permisos mínimos
- [ ] Lambda no puede acceder a recursos no autorizados
- [ ] No hay credenciales hardcodeadas en código

### CORS
- [ ] CORS configurado correctamente
- [ ] Frontend puede hacer requests
- [ ] Preflight requests funcionan

### HTTPS
- [ ] Todos los endpoints usan HTTPS
- [ ] Certificados válidos

## 📈 Monitoreo

### CloudWatch Logs
```bash
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/GadgetVoting
```
- [ ] Log groups creados para cada Lambda
- [ ] Logs siendo escritos
- [ ] Retención configurada

### CloudWatch Metrics
```bash
aws cloudwatch list-metrics --namespace AWS/Lambda
```
- [ ] Métricas de Lambda disponibles
- [ ] Métricas de API Gateway disponibles
- [ ] Métricas de DynamoDB disponibles

## 💰 Costos

### Verificar Billing
- [ ] Revisar AWS Cost Explorer
- [ ] Verificar que recursos están en free tier (si aplica)
- [ ] Configurar alarmas de billing (recomendado)

## 📝 Documentación

### Archivos de Documentación
- [ ] README.md completo
- [ ] QUICKSTART.md disponible
- [ ] DEPLOYMENT.md disponible
- [ ] ARCHITECTURE.md disponible
- [ ] TESTING.md disponible
- [ ] Todos los scripts documentados

### Outputs Guardados
- [ ] API Endpoint guardado
- [ ] User Pool ID guardado
- [ ] Client ID guardado
- [ ] Región guardada

## 🎯 Casos de Uso

### Flujo Completo de Usuario
1. [ ] Usuario se registra
2. [ ] Usuario inicia sesión
3. [ ] Usuario ve dashboard con resultados
4. [ ] Usuario vota por un gadget
5. [ ] Usuario ve confirmación
6. [ ] Usuario ve resultados actualizados
7. [ ] Usuario intenta votar de nuevo (rechazado)
8. [ ] Usuario cierra sesión

### Flujo de Administrador
1. [ ] Poblar datos de ejemplo
2. [ ] Verificar datos en DynamoDB
3. [ ] Monitorear logs
4. [ ] Verificar métricas
5. [ ] Probar API con curl
6. [ ] Crear usuarios de prueba

## ✅ Checklist Final

### Funcionalidad Core
- [ ] ✅ Autenticación funciona
- [ ] ✅ Votación funciona
- [ ] ✅ Idempotencia funciona
- [ ] ✅ Agregación funciona
- [ ] ✅ Consulta de resultados funciona
- [ ] ✅ Dashboard actualiza en tiempo real

### Infraestructura
- [ ] ✅ Todos los recursos creados
- [ ] ✅ Sin errores en CloudFormation
- [ ] ✅ Lambdas funcionando
- [ ] ✅ DynamoDB operacional
- [ ] ✅ API Gateway accesible
- [ ] ✅ Cognito configurado

### Seguridad
- [ ] ✅ Autenticación requerida
- [ ] ✅ Roles IAM correctos
- [ ] ✅ CORS configurado
- [ ] ✅ HTTPS habilitado

### Rendimiento
- [ ] ✅ Latencia aceptable
- [ ] ✅ Sin throttling
- [ ] ✅ Escalabilidad verificada

### Documentación
- [ ] ✅ Documentación completa
- [ ] ✅ Scripts funcionando
- [ ] ✅ Ejemplos incluidos

## 🚨 Problemas Comunes

### Stack Creation Failed
- Verificar permisos IAM
- Verificar límites de servicio
- Revisar eventos del stack

### Lambda Timeout
- Aumentar timeout en configuración
- Verificar conectividad a DynamoDB
- Revisar logs para errores

### DynamoDB Throttling
- Cambiar a provisioned capacity
- Aumentar capacidad
- Implementar retry logic

### API Gateway 5XX
- Verificar configuración de Lambda
- Verificar permisos de invocación
- Revisar logs de API Gateway

### Frontend No Conecta
- Verificar variables de entorno
- Verificar CORS
- Verificar endpoint en .env

## 📞 Soporte

Si algún check falla:
1. Revisar logs de CloudWatch
2. Verificar eventos de CloudFormation
3. Consultar TROUBLESHOOTING.md
4. Abrir issue en GitHub

---

**Nota**: Marca cada checkbox ✅ a medida que completas la validación.

**Estado del Sistema**: 
- [ ] ✅ Totalmente Operacional
- [ ] ⚠️ Operacional con Advertencias
- [ ] ❌ No Operacional

**Fecha de Validación**: _______________
**Validado por**: _______________
