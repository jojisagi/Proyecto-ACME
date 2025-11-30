"""
Lambda GetJobStatus
Atiende GET /jobs/{jobId}
"""
import json
from src.utils.logger import log_info, log_error
from src.utils.dynamodb import get_job


def lambda_handler(event, context):
    """
    Handler principal de Lambda GetJobStatus
    
    Args:
        event: Evento de API Gateway
        context: Contexto de Lambda
        
    Returns:
        dict: Respuesta HTTP con información del job
    """
    try:
        log_info("GetJobStatus invocado", requestId=context.request_id)
        
        # 1. Extraer jobId de path parameters
        path_params = event.get('pathParameters', {})
        job_id = path_params.get('jobId')
        
        if not job_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'jobId requerido'})
            }
        
        log_info("Consultando job", jobId=job_id)
        
        # 2. Consultar DynamoDB
        job = get_job(job_id)
        
        if not job:
            log_info("Job no encontrado", jobId=job_id)
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Job no encontrado'})
            }
        
        # 3. Preparar respuesta
        response_data = {
            'jobId': job.get('jobId'),
            'status': job.get('status'),
            'totalToons': job.get('totalToons', 0),
            'processedToons': job.get('processedToons', 0),
            'userId': job.get('userId'),
            'metadata': {
                'createdAt': job.get('createdAt'),
                'updatedAt': job.get('updatedAt')
            },
            'progress': calculate_progress(job)
        }
        
        log_info("Job encontrado", jobId=job_id, status=job.get('status'))
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        log_error("Error en GetJobStatus", error=e)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def calculate_progress(job):
    """
    Calcula el porcentaje de progreso del job
    
    Args:
        job: Datos del job
        
    Returns:
        dict: Información de progreso
    """
    total = job.get('totalToons', 0)
    processed = job.get('processedToons', 0)
    
    if total == 0:
        percentage = 0
    else:
        percentage = round((processed / total) * 100, 2)
    
    return {
        'percentage': percentage,
        'completed': processed == total
    }
