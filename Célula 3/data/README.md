# Datos de Prueba - Acme Image Handler

Este directorio contiene datos de prueba para el sistema de gestión de imágenes.

## Estructura

```
data/
├── README.md                  # Este archivo
├── test-images/               # Imágenes generadas (gitignored)
│   ├── GADGET-0001.jpg
│   ├── GADGET-0002.jpg
│   └── ...
└── test-metadata.json         # Metadatos de las imágenes
```

## Generar Datos de Prueba

Para generar 50 imágenes sintéticas de gadgets:

```bash
cd tests
python3 generate-test-data.py
```

Esto creará:
- 50 imágenes JPG en `data/test-images/`
- Archivo `data/test-metadata.json` con metadatos

## Características de las Imágenes

- **Cantidad**: 50 imágenes únicas
- **Formato**: JPEG
- **Dimensiones**: Variables (800x600, 1024x768, 1200x900, 1600x1200)
- **Categorías**: 10 categorías de gadgets
  - Smartphones
  - Tablets
  - Laptops
  - Smartwatches
  - Headphones
  - Cameras
  - Drones
  - Gaming Consoles
  - Smart Home
  - Wearables

## Metadatos

Cada imagen tiene metadatos asociados:

```json
{
  "gadgetId": "GADGET-0001",
  "name": "Smartphones Pro Max",
  "category": "Smartphones",
  "filename": "GADGET-0001.jpg",
  "resolution": {
    "width": 1024,
    "height": 768
  },
  "format": "JPEG",
  "fileSize": 123456,
  "generatedAt": "2025-11-27T10:30:00.000Z",
  "description": "Imagen sintética de Smartphones Pro Max para pruebas",
  "tags": ["smartphones", "test", "synthetic", "acme"]
}
```

## Subir Imágenes al Sistema

### Opción 1: Usando el API

```bash
# 1. Obtener token JWT
export JWT_TOKEN="<your-jwt-token>"
export API_URL="<your-api-url>"

# 2. Para cada imagen, obtener URL de carga
curl -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"gadgetId": "GADGET-0001", "filename": "GADGET-0001.jpg"}' \
  ${API_URL}/upload-url

# 3. Subir imagen usando la URL firmada
curl -X PUT "<presigned-url>" \
  -H "Content-Type: image/jpeg" \
  --data-binary "@data/test-images/GADGET-0001.jpg"
```

### Opción 2: Directamente a S3 (para pruebas)

```bash
# Subir todas las imágenes
aws s3 sync data/test-images/ \
  s3://acme-gadgets-raw-123456789-sandbox/TEST-BATCH/ \
  --profile sandbox
```

## Script de Carga Masiva

Crear un script para subir todas las imágenes:

```bash
#!/bin/bash

API_URL="<your-api-url>"
JWT_TOKEN="<your-jwt-token>"

for image in data/test-images/*.jpg; do
  filename=$(basename "$image")
  gadgetId="${filename%.jpg}"
  
  echo "Subiendo $filename..."
  
  # Obtener URL de carga
  response=$(curl -s -H "Authorization: Bearer ${JWT_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{\"gadgetId\": \"${gadgetId}\", \"filename\": \"${filename}\"}" \
    ${API_URL}/upload-url)
  
  upload_url=$(echo $response | jq -r '.uploadUrl')
  
  # Subir imagen
  curl -s -X PUT "${upload_url}" \
    -H "Content-Type: image/jpeg" \
    --data-binary "@${image}"
  
  echo "✓ $filename subido"
  sleep 1
done

echo "Todas las imágenes subidas"
```

## Verificar Procesamiento

Después de subir las imágenes, verificar que se procesaron:

```bash
# Ver logs de procesamiento
aws logs tail /aws/lambda/acme-image-handler-processor-sandbox --follow

# Listar imágenes procesadas
curl -H "Authorization: Bearer ${JWT_TOKEN}" ${API_URL}/images | jq '.count'

# Ver en DynamoDB
aws dynamodb scan \
  --table-name GadgetImages-sandbox \
  --select COUNT
```

## Limpiar Datos de Prueba

Para eliminar las imágenes de prueba:

```bash
# Eliminar del bucket raw
aws s3 rm s3://acme-gadgets-raw-123456789-sandbox/TEST-BATCH/ --recursive

# Eliminar del bucket processed
aws s3 rm s3://acme-gadgets-processed-123456789-sandbox/TEST-BATCH/ --recursive

# Eliminar de DynamoDB (requiere script)
# Ver COMMANDS_CHEATSHEET.md para comandos de DynamoDB
```

## Notas

- Las imágenes generadas son sintéticas y no representan productos reales
- Los archivos de imagen están en `.gitignore` y no se suben al repositorio
- El archivo `test-metadata.json` sí se incluye en el repositorio
- Cada ejecución del generador crea imágenes nuevas con IDs únicos

## Troubleshooting

### Error: "Pillow not installed"
```bash
pip install Pillow
```

### Error: "Permission denied"
```bash
chmod +x tests/generate-test-data.py
```

### Error: "Directory not found"
```bash
mkdir -p data/test-images
```

## Recursos Adicionales

- [Documentación de Pillow](https://pillow.readthedocs.io/)
- [AWS S3 CLI Reference](https://docs.aws.amazon.com/cli/latest/reference/s3/)
- [Guía de pruebas](../tests/test-api.sh)
