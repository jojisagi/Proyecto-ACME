"""
Lambda Function: API Handler
Maneja las peticiones del API Gateway para gestión de imágenes
"""
import json
import os
import boto3
from datetime import datetime, timedelta
from decimal import Decimal
import logging

# Configuración
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

RAW_BUCKET = os.environ['RAW_BUCKET']
PROCESSED_BUCKET = os.environ['PROCESSED_BUCKET']
DYNAMODB_TABLE = os.environ['DYNAMODB_TABLE']
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'sandbox')

table = dynamodb.Table(DYNAMODB_TABLE)

# URL firmada válida por 15 minutos
PRESIGNED_URL_EXPIRATION = 900


def lambda_handler(event, context):
    """
    Handler principal - enruta las peticiones según el path y método
    """
    logger.info(f"Event received: {json.dumps(event)}")
    
    try:
        http_method = event.get('httpMethod')
        path = event.get('path', '')
        path_parameters = event.get('pathParameters') or {}
        
        # Obtener información del usuario desde Cognito
        claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        user_email = claims.get('email', 'unknown')
        
        logger.info(f"Request: {http_method} {path} by {user_email}")
        
        # Enrutamiento
        if path == '/upload-url' and http_method == 'POST':
            return handle_upload_url(event, user_email)
        
        elif path == '/images' and http_method == 'GET':
            return handle_list_images(event, user_email)
        
        elif path.startswith('/images/') and http_method == 'GET':
            image_id = path_parameters.get('imageId')
            return handle_get_image(image_id, user_email)
        
        else:
            return response(404, {'error': 'Not found'})
    
    except Exception as e:
        logger.error(f"Error handling request: {str(e)}", exc_info=True)
        return response(500, {'error': 'Internal server error', 'message': str(e)})


def handle_upload_url(event, user_email):
    """
    POST /upload-url
    Genera una URL firmada para subir una imagen
    """
    try:
        body = json.loads(event.get('body', '{}'))
        gadget_id = body.get('gadgetId')
        filename = body.get('filename', 'image.jpg')
        
        if not gadget_id:
            return response(400, {'error': 'gadgetId is required'})
        
        # Generar key para S3
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        key = f"{gadget_id}/{timestamp}-{filename}"
        
        # Generar URL firmada para PUT
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': RAW_BUCKET,
                'Key': key,
                'ContentType': 'image/jpeg'
            },
            ExpiresIn=PRESIGNED_URL_EXPIRATION
        )
        
        logger.info(f"Generated upload URL for {gadget_id}: {key}")
        
        return response(200, {
            'uploadUrl': presigned_url,
            'key': key,
            'gadgetId': gadget_id,
            'expiresIn': PRESIGNED_URL_EXPIRATION
        })
    
    except Exception as e:
        logger.error(f"Error generating upload URL: {str(e)}")
        return response(500, {'error': 'Failed to generate upload URL'})


def handle_list_images(event, user_email):
    """
    GET /images
    Lista todas las imágenes con paginación
    """
    try:
        query_params = event.get('queryStringParameters') or {}
        gadget_id = query_params.get('gadgetId')
        limit = int(query_params.get('limit', 50))
        
        if gadget_id:
            # Query por gadgetId específico
            response_data = table.query(
                KeyConditionExpression='gadgetId = :gid',
                ExpressionAttributeValues={':gid': gadget_id},
                Limit=limit
            )
        else:
            # Scan de toda la tabla
            response_data = table.scan(Limit=limit)
        
        items = response_data.get('Items', [])
        
        # Convertir Decimal a float para JSON
        items = json.loads(json.dumps(items, default=decimal_default))
        
        logger.info(f"Listed {len(items)} images")
        
        return response(200, {
            'images': items,
            'count': len(items),
            'scannedCount': response_data.get('ScannedCount', 0)
        })
    
    except Exception as e:
        logger.error(f"Error listing images: {str(e)}")
        return response(500, {'error': 'Failed to list images'})


def handle_get_image(image_id, user_email):
    """
    GET /images/{imageId}
    Obtiene metadatos y URLs firmadas de una imagen específica
    """
    try:
        if not image_id:
            return response(400, {'error': 'imageId is required'})
        
        # Buscar en DynamoDB - necesitamos hacer un scan porque solo tenemos imageId
        response_data = table.scan(
            FilterExpression='imageId = :iid',
            ExpressionAttributeValues={':iid': image_id}
        )
        
        items = response_data.get('Items', [])
        
        if not items:
            return response(404, {'error': 'Image not found'})
        
        item = items[0]
        
        # Generar URLs firmadas para cada versión
        versions = item.get('versions', {})
        signed_urls = {}
        
        for version_name, key in versions.items():
            signed_urls[version_name] = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': PROCESSED_BUCKET,
                    'Key': key
                },
                ExpiresIn=PRESIGNED_URL_EXPIRATION
            )
        
        # Convertir Decimal a float
        item = json.loads(json.dumps(item, default=decimal_default))
        item['signedUrls'] = signed_urls
        item['urlExpiresIn'] = PRESIGNED_URL_EXPIRATION
        
        logger.info(f"Retrieved image: {image_id}")
        
        return response(200, item)
    
    except Exception as e:
        logger.error(f"Error getting image: {str(e)}")
        return response(500, {'error': 'Failed to get image'})


def response(status_code, body):
    """
    Genera una respuesta HTTP estándar
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        'body': json.dumps(body)
    }


def decimal_default(obj):
    """
    Helper para convertir Decimal a float en JSON
    """
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError
