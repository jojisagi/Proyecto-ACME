"""
Lambda SubmitJob
Recibe petición POST /submit-job autenticada (JWT)
"""
import json
import os
import boto3
from src.utils.auth import validate_jwt, extract_token_from_header
from src.utils.logger import log_info, log_error
from src.business_logic.job_manager import (
    validate_job_payload,
    initialize_job,
    mark_job_processing
)

sqs = boto3.client('sqs')


def lambda_handler(event, context):
    """
    Handler principal de Lambda SubmitJob
    
    Args:
        event: Evento de API Gateway
        context: Contexto de Lambda
        
    Returns:
        dict: Respuesta HTTP
    """
    try:
        log_info("SubmitJob invocado", requestId=context.request_id)
        
        # 1. Validar JWT
        auth_header = event.get('headers', {}).get('Authorization')
        token = extract_token_from_header(auth_header)
        user_data = validate_jwt(token)
        user_id = user_data.get('sub', 'unknown')
        
        log_info("Usuario autenticado", userId=user_id)
        
        # 2. Parsear body
        body = json.loads(event.get('body', '{}'))
        
        # 3. Validar payload
        is_valid, error_msg = validate_job_payload(body)
        if not is_valid:
            log_error("Payload inválido", error=error_msg)
            return {
                'statusCode': 400,
                'body': json.dumps({'error': error_msg})
            }
        
        job_id = body['jobId']
        toons = body['toons']
        
        log_info("Job recibido", jobId=job_id, toonsCount=len(toons))
        
        # 4. Registrar job en DynamoDB (estado: Pending)
        initialize_job(job_id, toons, user_id)
        
        # 5. Enviar cada toon a SQS (fan-out)
        queue_url = os.environ.get('TOON_QUEUE_URL')
        if not queue_url:
            raise Exception("TOON_QUEUE_URL no configurada")
        
        for toon in toons:
            message_body = {
                'jobId': job_id,
                'toon': toon
            }
            
            sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(message_body),
                MessageAttributes={
                    'jobId': {
                        'StringValue': job_id,
                        'DataType': 'String'
                    },
                    'toonId': {
                        'StringValue': toon.get('toonId', ''),
                        'DataType': 'String'
                    }
                }
            )
        
        log_info("Toons enviados a SQS", jobId=job_id, count=len(toons))
        
        # 6. Actualizar estado a Processing
        mark_job_processing(job_id)
        
        # 7. Responder
        return {
            'statusCode': 202,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'message': 'Job submitted successfully',
                'jobId': job_id,
                'toonsCount': len(toons),
                'status': 'Processing'
            })
        }
        
    except Exception as e:
        log_error("Error en SubmitJob", error=e)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
