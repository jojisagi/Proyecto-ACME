import json
import boto3
import logging
from datetime import datetime, timedelta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

import os
PROCESSED_BUCKET = os.environ.get('PROCESSED_BUCKET', 'acme-gadgets-processed')
RAW_BUCKET = os.environ.get('RAW_BUCKET', 'acme-gadgets-raw')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'GadgetImages')

def lambda_handler(event, context):
    """
    Maneja requests del API:
    - GET /images -> lista imágenes
    - POST /upload-url -> genera URL de carga
    - GET /image/{gadgetId}/{imageId} -> obtiene metadatos
    """
    try:
        http_method = event.get('httpMethod')
        path = event.get('path', '')
        
        logger.info(f"Método: {http_method}, Path: {path}")
        
        if http_method == 'GET' and path == '/images':
            return list_images()
        
        elif http_method == 'POST' and path == '/upload-url':
            body = json.loads(event.get('body', '{}'))
            gadget_id = body.get('gadgetId')
            return get_upload_url(gadget_id)
        
        elif http_method == 'GET' and '/image/' in path:
            parts = path.split('/')
            gadget_id = parts[-2]
            image_id = parts[-1]
            return get_image_metadata(gadget_id, image_id)
        
        else:
            return error_response(404, 'Endpoint no encontrado')
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return error_response(500, str(e))

def list_images():
    """Lista todas las imágenes"""
    try:
        table = dynamodb.Table(DYNAMODB_TABLE)
        response = table.scan()
        
        return success_response({
            'images': response.get('Items', []),
            'count': response.get('Count', 0)
        })
    except Exception as e:
        return error_response(500, str(e))

def get_upload_url(gadget_id):
    """Genera URL firmada para subir imagen"""
    try:
        if not gadget_id:
            return error_response(400, 'gadgetId es requerido')
        
        # Generar nombre único
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        key = f"{gadget_id}/{timestamp}_upload.jpg"
        
        # Generar URL firmada (válida 1 hora)
        url = s3_client.generate_presigned_url(
            'put_object',
            Params={'Bucket': RAW_BUCKET, 'Key': key},
            ExpiresIn=3600
        )
        
        return success_response({
            'uploadUrl': url,
            'gadgetId': gadget_id,
            'expiresIn': 3600
        })
    except Exception as e:
        return error_response(500, str(e))

def get_image_metadata(gadget_id, image_id):
    """Obtiene metadatos de una imagen"""
    try:
        table = dynamodb.Table(DYNAMODB_TABLE)
        response = table.get_item(
            Key={'gadgetId': gadget_id, 'imageId': image_id}
        )
        
        if 'Item' not in response:
            return error_response(404, 'Imagen no encontrada')
        
        return success_response(response['Item'])
    except Exception as e:
        return error_response(500, str(e))

def success_response(data):
    return {
        'statusCode': 200,
        'body': json.dumps(data),
        'headers': {'Content-Type': 'application/json'}
    }

def error_response(status_code, message):
    return {
        'statusCode': status_code,
        'body': json.dumps({'error': message}),
        'headers': {'Content-Type': 'application/json'}
    }
