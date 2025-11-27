"""
Lambda Function: Image Processor
Procesa imágenes subidas a S3, genera thumbnails y versiones optimizadas
"""
import json
import os
import boto3
import uuid
from datetime import datetime
from PIL import Image
from io import BytesIO
import logging

# Configuración
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

PROCESSED_BUCKET = os.environ['PROCESSED_BUCKET']
DYNAMODB_TABLE = os.environ['DYNAMODB_TABLE']
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'sandbox')

# Dimensiones de procesamiento
THUMBNAIL_SIZE = (256, 256)
PREVIEW_SIZE = (1024, 1024)

table = dynamodb.Table(DYNAMODB_TABLE)


def lambda_handler(event, context):
    """
    Handler principal - procesa eventos de S3
    """
    logger.info(f"Event received: {json.dumps(event)}")
    
    try:
        for record in event['Records']:
            # Obtener información del objeto S3
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            logger.info(f"Processing image: s3://{bucket}/{key}")
            
            # Descargar imagen original
            response = s3_client.get_object(Bucket=bucket, Key=key)
            image_data = response['Body'].read()
            
            # Validar que es una imagen
            try:
                img = Image.open(BytesIO(image_data))
                original_format = img.format
                original_size = img.size
            except Exception as e:
                logger.error(f"Invalid image format: {e}")
                continue
            
            # Generar ID único para la imagen
            image_id = str(uuid.uuid4())
            
            # Extraer gadgetId del nombre del archivo o usar default
            # Formato esperado: gadgetId/filename.jpg
            parts = key.split('/')
            if len(parts) > 1:
                gadget_id = parts[0]
                filename = parts[1]
            else:
                gadget_id = 'unknown'
                filename = key
            
            # Procesar y guardar versiones
            versions = {}
            
            # 1. Original (validada y optimizada)
            original_key = f"{gadget_id}/{image_id}/original.jpg"
            save_image(img, original_key, quality=95)
            versions['original'] = original_key
            
            # 2. Thumbnail
            thumbnail_key = f"{gadget_id}/{image_id}/thumbnail.jpg"
            thumbnail = create_thumbnail(img, THUMBNAIL_SIZE)
            save_image(thumbnail, thumbnail_key, quality=85)
            versions['thumbnail'] = thumbnail_key
            
            # 3. Preview
            preview_key = f"{gadget_id}/{image_id}/preview.jpg"
            preview = create_thumbnail(img, PREVIEW_SIZE)
            save_image(preview, preview_key, quality=90)
            versions['preview'] = preview_key
            
            # Guardar metadatos en DynamoDB
            metadata = {
                'gadgetId': gadget_id,
                'imageId': image_id,
                'originalFilename': filename,
                'originalSize': {
                    'width': original_size[0],
                    'height': original_size[1]
                },
                'format': original_format or 'JPEG',
                'versions': versions,
                'uploadedAt': datetime.utcnow().isoformat(),
                'processedAt': datetime.utcnow().isoformat(),
                'environment': ENVIRONMENT,
                'status': 'processed'
            }
            
            table.put_item(Item=metadata)
            
            logger.info(f"Image processed successfully: {image_id}")
            logger.info(f"Metadata saved to DynamoDB: {gadget_id}/{image_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Images processed successfully',
                'count': len(event['Records'])
            })
        }
    
    except Exception as e:
        logger.error(f"Error processing images: {str(e)}", exc_info=True)
        raise


def create_thumbnail(img, size):
    """
    Crea un thumbnail manteniendo el aspect ratio
    """
    img_copy = img.copy()
    img_copy.thumbnail(size, Image.Resampling.LANCZOS)
    
    # Crear imagen con fondo blanco si es necesario
    if img_copy.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img_copy.size, (255, 255, 255))
        if img_copy.mode == 'P':
            img_copy = img_copy.convert('RGBA')
        background.paste(img_copy, mask=img_copy.split()[-1] if img_copy.mode == 'RGBA' else None)
        img_copy = background
    elif img_copy.mode != 'RGB':
        img_copy = img_copy.convert('RGB')
    
    return img_copy


def save_image(img, key, quality=90):
    """
    Guarda una imagen en S3
    """
    buffer = BytesIO()
    
    # Convertir a RGB si es necesario
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        if img.mode == 'RGBA':
            background.paste(img, mask=img.split()[-1])
        else:
            background.paste(img)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    img.save(buffer, format='JPEG', quality=quality, optimize=True)
    buffer.seek(0)
    
    s3_client.put_object(
        Bucket=PROCESSED_BUCKET,
        Key=key,
        Body=buffer,
        ContentType='image/jpeg',
        ServerSideEncryption='aws:kms'
    )
    
    logger.info(f"Saved image to s3://{PROCESSED_BUCKET}/{key}")
