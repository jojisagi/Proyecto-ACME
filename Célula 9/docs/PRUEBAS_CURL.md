# Documentación de Pruebas con cURL

Este documento describe los comandos necesarios para probar la API de la Célula 9.
Nota: Reemplaza `<api-id>`, `<region>` y `<JWT>` con los valores reales tras el despliegue.

### 1. Obtener Token JWT (Login)
Comando para autenticarse y recibir el token de acceso:
```bash
curl -X POST https://<cognito-domain>/oauth2/token \
 -H "Content-Type: application/x-www-form-urlencoded" \
 -d "grant_type=password&client_id=<client_id>&username=<user>&password=<password>"

#Crear gadget (POST)
 curl -X POST https://<api-id>.execute-api.<region>[.amazonaws.com/prod/vehicles](https://.amazonaws.com/prod/vehicles) \
 -H "Authorization: Bearer <JWT>" \
 -H "Content-Type: application/json" \
 -d 
 '{
    "name": "Hoverbike X1",
    "category": "vehicle",
    "maxSpeed": 280,
    "propulsionType": "antigravity",
    "seats": 1,
    "status": "prototype"
 }'

#Listar gadgets (GET)
 curl https://<api-id>.execute-api.<region>[.amazonaws.com/prod/vehicles](https://.amazonaws.com/prod/vehicles) \
 -H "Authorization: Bearer <JWT>"

#Actualizar gadget (PUT)
 curl -X PUT https://<api-id>.execute-api.<region>[.amazonaws.com/prod/vehicles/](https://.amazonaws.com/prod/vehicles/)<GadgetId> \
 -H "Authorization: Bearer <JWT>" \
 -H "Content-Type: application/json" \
 -d 
 '{
    "maxSpeed": 300,
    "status": "production"
 }'

#Borrar gadget (DELETE)
 curl -X DELETE https://<api-id>.execute-api.<region>[.amazonaws.com/prod/vehicles/](https://.amazonaws.com/prod/vehicles/)<GadgetId> \
 -H "Authorization: Bearer <JWT>"