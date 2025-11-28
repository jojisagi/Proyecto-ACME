"""
Lambda GetResults
Atiende GET /results?jobId=JOB001
"""
import json
from src.utils.logger import log_info, log_error
from src.utils.dynamodb import get_results_by_job, get_job


def lambda_handler(event, context):
    """
    Handler principal de Lambda GetResults
    
    Args:
        event: Evento de API Gateway
        context: Contexto de Lambda
        
    Returns:
        dict: Respuesta HTTP con resultados del job
    """
    try:
        log_info("GetResults invocado", requestId=context.request_id)
        
        # 1. Extraer jobId de query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        job_id = query_params.get('jobId')
        
        if not job_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'jobId requerido en query string'})
            }
        
        log_info("Consultando resultados", jobId=job_id)
        
        # 2. Verificar que el job existe
        job = get_job(job_id)
        if not job:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Job no encontrado'})
            }
        
        # 3. Obtener resultados de DynamoDB
        results = get_results_by_job(job_id)
        
        log_info("Resultados obtenidos", jobId=job_id, count=len(results))
        
        # 4. Preparar respuesta
        response_data = {
            'jobId': job_id,
            'jobStatus': job.get('status'),
            'totalToons': job.get('totalToons', 0),
            'resultsCount': len(results),
            'results': format_results(results)
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        log_error("Error en GetResults", error=e)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def format_results(results):
    """
    Formatea los resultados para la respuesta
    
    Args:
        results: Lista de resultados de DynamoDB
        
    Returns:
        list: Resultados formateados
    """
    formatted = []
    
    for result in results:
        formatted.append({
            'toonId': result.get('toonId'),
            'type': result.get('type'),
            'fingerprint': result.get('fingerprint'),
            'durationMs': result.get('durationMs'),
            'isValid': result.get('isValid'),
            'processedAt': result.get('processedAt'),
            'processedData': result.get('processedData', {})
        })
    
    # Ordenar por toonId
    formatted.sort(key=lambda x: x.get('toonId', ''))
    
    return formatted
