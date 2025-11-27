import json
import boto3
import logging
from io import BytesIO
from PIL import Image
import os
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Variables de entorno
PROCESSED_BUCKET = os.environ.get('PROCESSED_BUCKET', 'acme-gadgets-processed')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'GadgetImages')

def lambda_handler(event, context):
    """
    Procesa imágenes de gadgets:
    - Crea thumbnail (256px)
    - Crea preview (1024px)
    - Guarda versión original validada
    """
    try:
        logger.info(f"Event recibido: {json.dumps(event)}")
        
        # Obtener información del evento S3
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        logger.info(f"Procesando imagen: s3://{bucket}/{key}")
        
        # Descargar imagen original
        response = s3_client.get_object(Bucket=bucket, Key=key)
        image_data = response['Body'].read()
        
        # Abrir imagen con Pillow
        image = Image.open(BytesIO(image_data))
        
        # Validar que sea imagen válida
        if image.format not in ['JPEG', 'PNG', 'WEBP']:
            raise ValueError(f"Formato no soportado: {image.format}")
        
        # Extraer metadata
        image_id = key.split('/')[-1].split('.')[0]
        gadget_id = key.split('/')[0]
        
        # Crear versiones
        thumbnail = create_thumbnail(image)
        preview = create_preview(image)
        
        # Guardar en bucket procesado
        save_version(thumbnail, f"{gadget_id}/{image_id}_thumbnail.jpg", PROCESSED_BUCKET)
        save_version(preview, f"{gadget_id}/{image_id}_preview.jpg", PROCESSED_BUCKET)
        save_version(image, f"{gadget_id}/{image_id}_original.jpg", PROCESSED_BUCKET)
        
        # Registrar en DynamoDB
        register_metadata(gadget_id, image_id, image)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Imagen procesada exitosamente',
                'gadgetId': gadget_id,
                'imageId': image_id
            })
        }
        
    except Exception as e:
        logger.error(f"Error procesando imagen: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def create_thumbnail(image):
    """Crea thumbnail de 256x256"""
    img_copy = image.copy()
    img_copy.thumbnail((256, 256))
    return img_copy

def create_preview(image):
    """Crea preview de 1024x1024"""
    img_copy = image.copy()
    img_copy.thumbnail((1024, 1024))
    return img_copy

def save_version(image, s3_key, bucket):
    """Guarda versión de imagen en S3"""
    buffer = BytesIO()
    image.save(buffer, format='JPEG', quality=85)
    buffer.seek(0)
    
    s3_client.put_object(
        Bucket=bucket,
        Key=s3_key,
        Body=buffer.getvalue(),
        ContentType='image/jpeg',
        Metadata={
            'processed-date': datetime.utcnow().isoformat()
        }
    )
    logger.info(f"Guardado: s3://{bucket}/{s3_key}")

def register_metadata(gadget_id, image_id, image):
    """Registra metadatos en DynamoDB"""
    table = dynamodb.Table(DYNAMODB_TABLE)
    
    metadata = {
        'gadgetId': gadget_id,
        'imageId': image_id,
        'width': image.width,
        'height': image.height,
        'format': image.format,
        'processedAt': datetime.utcnow().isoformat(),
        'status': 'processed'
    }
    
    table.put_item(Item=metadata)
    logger.info(f"Metadata registrado para {gadget_id}/{image_id}")
