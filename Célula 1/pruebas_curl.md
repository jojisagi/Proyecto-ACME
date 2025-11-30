# Guía de Pruebas con curl - Sistema de Análisis de Caricaturas

Esta guía proporciona ejemplos completos de cómo interactuar con la API del sistema de análisis de caricaturas usando curl. Incluye autenticación con Cognito, subida de imágenes y consulta de resultados.

## Tabla de Contenidos

1. [Prerrequisitos](#prerrequisitos)
2. [Autenticación con Cognito](#autenticación-con-cognito)
3. [Obtener URL Presignada](#obtener-url-presignada)
4. [Subir Imagen a S3](#subir-imagen-a-s3)
5. [Consultar Resultados](#consultar-resultados)
6. [Ejemplos de Errores](#ejemplos-de-errores)

---

## Prerrequisitos

Antes de comenzar, asegúrate de tener:

- AWS CLI instalado y configurado
- curl instalado
- jq instalado (opcional, para formatear JSON)
- Acceso a los siguientes valores (obtenidos de los outputs de CloudFormation):
  - `USER_POOL_ID`: ID del Cognito User Pool
  - `APP_CLIENT_ID`: ID del App Client de Cognito
  - `API_ENDPOINT`: URL base del API Gateway (ej: `https://abc123.execute-api.us-east-1.amazonaws.com`)

```bash
# Configurar variables de entorno
export USER_POOL_ID="us-east-1_XXXXXXXXX"
export APP_CLIENT_ID="abcdefghijklmnopqrstuvwxyz"
export API_ENDPOINT="https://abc123.execute-api.us-east-1.amazonaws.com"
export AWS_REGION="us-east-1"
```

---

## Autenticación con Cognito

### Paso 1: Crear un Usuario de Prueba

```bash
# Crear usuario en Cognito User Pool
aws cognito-idp sign-up \
  --client-id $APP_CLIENT_ID \
  --username testuser@example.com \
  --password "TestPassword123!" \
  --user-attributes Name=email,Value=testuser@example.com \
  --region $AWS_REGION
```

**Respuesta esperada:**
```json
{
    "UserConfirmed": false,
    "UserSub": "12345678-1234-1234-1234-123456789012"
}
```

### Paso 2: Confirmar el Usuario (Admin)

Si el User Pool requiere verificación de email, un administrador puede confirmar el usuario:

```bash
# Confirmar usuario (requiere permisos de administrador)
aws cognito-idp admin-confirm-sign-up \
  --user-pool-id $USER_POOL_ID \
  --username testuser@example.com \
  --region $AWS_REGION
```

### Paso 3: Establecer Contraseña Permanente (Opcional)

Si el usuario fue creado por un administrador:

```bash
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username testuser@example.com \
  --password "TestPassword123!" \
  --permanent \
  --region $AWS_REGION
```

### Paso 4: Autenticar y Obtener JWT Token

```bash
# Autenticar usuario y obtener tokens
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id $APP_CLIENT_ID \
  --auth-parameters USERNAME=testuser@example.com,PASSWORD="TestPassword123!" \
  --region $AWS_REGION
```

**Respuesta esperada:**
```json
{
    "ChallengeParameters": {},
    "AuthenticationResult": {
        "AccessToken": "eyJraWQiOiJxxx...very-long-token...xxx",
        "ExpiresIn": 3600,
        "TokenType": "Bearer",
        "RefreshToken": "eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ...",
        "IdToken": "eyJraWQiOiJxxx...another-long-token...xxx"
    }
}
```

### Paso 5: Extraer y Guardar el Access Token

```bash
# Extraer el Access Token y guardarlo en variable de entorno
export JWT_TOKEN=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id $APP_CLIENT_ID \
  --auth-parameters USERNAME=testuser@example.com,PASSWORD="TestPassword123!" \
  --region $AWS_REGION \
  --query 'AuthenticationResult.AccessToken' \
  --output text)

# Verificar que el token fue guardado
echo "Token guardado: ${JWT_TOKEN:0:50}..."
```

---

## Obtener URL Presignada

Una vez autenticado, puedes solicitar una URL presignada para subir una imagen.

### Solicitud

```bash
curl -X GET "${API_ENDPOINT}/prod/get-upload-url?filename=mickey_mouse.jpg&contentType=image/jpeg" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json"
```

### Respuesta Exitosa (200 OK)

```json
{
  "uploadUrl": "https://cartoon-rekognition-images-prod-123456789012.s3.amazonaws.com/a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAIOSFODNN7EXAMPLE%2F20251127%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20251127T103000Z&X-Amz-Expires=300&X-Amz-SignedHeaders=host&X-Amz-Signature=abcdef1234567890...",
  "imageId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "expiresIn": 300
}
```

### Guardar imageId para uso posterior

```bash
# Extraer y guardar el imageId
export IMAGE_ID=$(curl -s -X GET "${API_ENDPOINT}/prod/get-upload-url?filename=mickey_mouse.jpg&contentType=image/jpeg" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  | jq -r '.imageId')

# Extraer y guardar la URL presignada
export UPLOAD_URL=$(curl -s -X GET "${API_ENDPOINT}/prod/get-upload-url?filename=mickey_mouse.jpg&contentType=image/jpeg" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  | jq -r '.uploadUrl')

echo "Image ID: $IMAGE_ID"
echo "Upload URL obtenida (válida por 5 minutos)"
```

---

## Subir Imagen a S3

Usa la URL presignada para subir la imagen directamente a S3.

### Solicitud

```bash
# Subir imagen usando la URL presignada
curl -X PUT "$UPLOAD_URL" \
  -H "Content-Type: image/jpeg" \
  --data-binary "@/path/to/your/image.jpg"
```

**Nota:** Reemplaza `/path/to/your/image.jpg` con la ruta real a tu archivo de imagen.

### Respuesta Exitosa (200 OK)

S3 retorna una respuesta vacía con código 200 si la subida fue exitosa.

### Ejemplo con imagen de prueba

```bash
# Crear una imagen de prueba simple (requiere ImageMagick)
convert -size 800x600 xc:blue -pointsize 72 -fill white \
  -gravity center -annotate +0+0 "Mickey Mouse" \
  test_cartoon.jpg

# Subir la imagen
curl -X PUT "$UPLOAD_URL" \
  -H "Content-Type: image/jpeg" \
  --data-binary "@test_cartoon.jpg" \
  -w "\nHTTP Status: %{http_code}\n"
```

### Verificación

Después de subir la imagen, el sistema automáticamente:
1. Detecta el evento S3
2. Invoca la Lambda S3EventProcessor
3. Llama a Amazon Rekognition para analizar la imagen
4. Guarda los resultados en DynamoDB

Este proceso puede tomar entre 5-30 segundos dependiendo del tamaño de la imagen.

---

## Consultar Resultados

Una vez que la imagen ha sido procesada, puedes consultar los resultados del análisis.

### Solicitud

```bash
curl -X GET "${API_ENDPOINT}/prod/result?imageId=${IMAGE_ID}" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json"
```

### Respuesta Exitosa (200 OK)

```json
{
  "imageId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "characterName": "Mickey Mouse",
  "confidence": 98.5,
  "timestamp": "2025-11-27T10:35:42Z",
  "metadata": {
    "s3Bucket": "cartoon-rekognition-images-prod-123456789012",
    "s3Key": "a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg",
    "imageSize": 1024000,
    "labels": [
      {
        "name": "Mickey Mouse",
        "confidence": 98.5
      },
      {
        "name": "Cartoon",
        "confidence": 99.2
      },
      {
        "name": "Animation",
        "confidence": 97.8
      }
    ],
    "processingTime": 2345
  }
}
```

### Consulta con formato legible

```bash
# Usar jq para formatear la respuesta
curl -s -X GET "${API_ENDPOINT}/prod/result?imageId=${IMAGE_ID}" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  | jq '.'
```

### Script completo de flujo end-to-end

```bash
#!/bin/bash

# Configuración
export USER_POOL_ID="us-east-1_XXXXXXXXX"
export APP_CLIENT_ID="abcdefghijklmnopqrstuvwxyz"
export API_ENDPOINT="https://abc123.execute-api.us-east-1.amazonaws.com"
export AWS_REGION="us-east-1"

echo "=== 1. Autenticando usuario ==="
export JWT_TOKEN=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id $APP_CLIENT_ID \
  --auth-parameters USERNAME=testuser@example.com,PASSWORD="TestPassword123!" \
  --region $AWS_REGION \
  --query 'AuthenticationResult.AccessToken' \
  --output text)

echo "Token obtenido: ${JWT_TOKEN:0:50}..."

echo -e "\n=== 2. Solicitando URL presignada ==="
RESPONSE=$(curl -s -X GET "${API_ENDPOINT}/prod/get-upload-url?filename=test.jpg&contentType=image/jpeg" \
  -H "Authorization: Bearer ${JWT_TOKEN}")

export IMAGE_ID=$(echo $RESPONSE | jq -r '.imageId')
export UPLOAD_URL=$(echo $RESPONSE | jq -r '.uploadUrl')

echo "Image ID: $IMAGE_ID"
echo "URL presignada obtenida"

echo -e "\n=== 3. Subiendo imagen ==="
curl -X PUT "$UPLOAD_URL" \
  -H "Content-Type: image/jpeg" \
  --data-binary "@test_cartoon.jpg" \
  -w "\nHTTP Status: %{http_code}\n"

echo -e "\n=== 4. Esperando procesamiento (30 segundos) ==="
sleep 30

echo -e "\n=== 5. Consultando resultados ==="
curl -s -X GET "${API_ENDPOINT}/prod/result?imageId=${IMAGE_ID}" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  | jq '.'

echo -e "\n=== Flujo completado ==="
```

---

## Ejemplos de Errores

### Error 401: Unauthorized (Sin JWT o JWT Inválido)

**Solicitud sin token:**
```bash
curl -X GET "${API_ENDPOINT}/prod/get-upload-url?filename=test.jpg&contentType=image/jpeg" \
  -H "Content-Type: application/json"
```

**Respuesta:**
```json
{
  "message": "Unauthorized"
}
```

**HTTP Status:** 401

---

**Solicitud con token expirado o inválido:**
```bash
curl -X GET "${API_ENDPOINT}/prod/get-upload-url?filename=test.jpg&contentType=image/jpeg" \
  -H "Authorization: Bearer invalid-token-12345" \
  -H "Content-Type: application/json"
```

**Respuesta:**
```json
{
  "message": "Unauthorized"
}
```

**HTTP Status:** 401

---

### Error 400: Bad Request (Parámetros Faltantes o Inválidos)

**Solicitud sin parámetros requeridos:**
```bash
curl -X GET "${API_ENDPOINT}/prod/get-upload-url" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json"
```

**Respuesta:**
```json
{
  "error": "BadRequest",
  "message": "Missing required parameters: filename, contentType"
}
```

**HTTP Status:** 400

---

**Solicitud con contentType inválido:**
```bash
curl -X GET "${API_ENDPOINT}/prod/get-upload-url?filename=test.txt&contentType=text/plain" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json"
```

**Respuesta:**
```json
{
  "error": "BadRequest",
  "message": "Invalid content type. Only image/jpeg and image/png are supported"
}
```

**HTTP Status:** 400

---

### Error 404: Not Found (ImageId No Existe)

**Solicitud con imageId inexistente:**
```bash
curl -X GET "${API_ENDPOINT}/prod/result?imageId=00000000-0000-0000-0000-000000000000" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json"
```

**Respuesta:**
```json
{
  "error": "NotFound",
  "message": "Analysis result not found for imageId: 00000000-0000-0000-0000-000000000000"
}
```

**HTTP Status:** 404

---

**Solicitud con imageId en formato inválido:**
```bash
curl -X GET "${API_ENDPOINT}/prod/result?imageId=invalid-id-format" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json"
```

**Respuesta:**
```json
{
  "error": "BadRequest",
  "message": "Invalid imageId format. Must be a valid UUID"
}
```

**HTTP Status:** 400

---

### Error 429: Too Many Requests (Rate Limiting)

**Solicitud cuando se excede el límite de tasa:**
```bash
# Simular múltiples solicitudes rápidas
for i in {1..1500}; do
  curl -X GET "${API_ENDPOINT}/prod/get-upload-url?filename=test$i.jpg&contentType=image/jpeg" \
    -H "Authorization: Bearer ${JWT_TOKEN}" &
done
wait
```

**Respuesta:**
```json
{
  "message": "Too Many Requests"
}
```

**HTTP Status:** 429

---

### Error 500: Internal Server Error

**Escenario:** Error interno del servidor (ej: Lambda timeout, error de Rekognition)

```bash
curl -X GET "${API_ENDPOINT}/prod/result?imageId=${IMAGE_ID}" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json"
```

**Respuesta:**
```json
{
  "error": "InternalServerError",
  "message": "An internal error occurred while processing your request",
  "requestId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "timestamp": "2025-11-27T10:35:42Z"
}
```

**HTTP Status:** 500

**Acción recomendada:** Verificar logs en CloudWatch usando el requestId para troubleshooting.

---

### Error 503: Service Unavailable

**Escenario:** Servicio temporalmente no disponible (ej: DynamoDB throttling, mantenimiento)

```bash
curl -X GET "${API_ENDPOINT}/prod/result?imageId=${IMAGE_ID}" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json"
```

**Respuesta:**
```json
{
  "error": "ServiceUnavailable",
  "message": "Service temporarily unavailable. Please try again later"
}
```

**HTTP Status:** 503

**Acción recomendada:** Implementar retry con exponential backoff.

---

## Troubleshooting

### Verificar que el token JWT es válido

```bash
# Decodificar el JWT (solo la parte del payload)
echo $JWT_TOKEN | cut -d'.' -f2 | base64 -d 2>/dev/null | jq '.'
```

### Verificar conectividad con API Gateway

```bash
curl -I "${API_ENDPOINT}/prod/get-upload-url"
```

### Verificar logs de Lambda en CloudWatch

```bash
# Listar log streams recientes
aws logs describe-log-streams \
  --log-group-name /aws/lambda/GeneratePresignedUrl \
  --order-by LastEventTime \
  --descending \
  --max-items 5 \
  --region $AWS_REGION

# Ver logs de un stream específico
aws logs get-log-events \
  --log-group-name /aws/lambda/GeneratePresignedUrl \
  --log-stream-name '2025/11/27/[$LATEST]abc123...' \
  --region $AWS_REGION
```

### Verificar estado del procesamiento de imagen

```bash
# Consultar DynamoDB directamente (requiere permisos)
aws dynamodb get-item \
  --table-name CartoonAnalysisResults-prod \
  --key "{\"ImageId\": {\"S\": \"$IMAGE_ID\"}}" \
  --region $AWS_REGION
```

---

## Notas Adicionales

### Seguridad

- **Nunca compartas tu JWT token** en logs, repositorios o comunicaciones públicas
- Los tokens expiran después de 1 hora (3600 segundos)
- Las URLs presignadas expiran después de 5 minutos (300 segundos)
- Usa HTTPS para todas las comunicaciones

### Límites

- **Tamaño máximo de imagen:** 15 MB (límite de Rekognition)
- **Formatos soportados:** JPEG, PNG
- **Rate limit:** 1000 requests/segundo con burst de 2000
- **Timeout de Lambda:** 30 segundos (GeneratePresignedUrl, QueryResults), 300 segundos (S3EventProcessor)

### Mejores Prácticas

1. **Implementar retry logic** para errores 5xx y 429
2. **Validar respuestas** antes de procesar
3. **Manejar tokens expirados** refrescando con el refresh token
4. **Monitorear tiempos de respuesta** para detectar problemas de performance
5. **Usar variables de entorno** para configuración sensible

---

## Referencias

- [AWS CLI Cognito IDP Commands](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/)
- [Amazon Rekognition DetectLabels](https://docs.aws.amazon.com/rekognition/latest/dg/API_DetectLabels.html)
- [S3 Presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/PresignedUrlUploadObject.html)
- [API Gateway Error Responses](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-gatewayResponse-definition.html)

---

**Última actualización:** 27 de noviembre de 2025
