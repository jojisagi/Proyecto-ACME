"""
Lambda Worker
Disparada desde SQS (un toon por invocación)
Procesa el toon de forma idempotente
"""
import json
from src.utils.logger import log_info, log_error
from src.utils.dynamodb import save_toon_result, increment_processed_toons
from src.business_logic.toon_processor import process_toon
from src.business_logic.job_manager import check_job_completion


# Cache para idempotencia (en memoria, válido durante la vida de la instancia)
processed_cache = set()


def lambda_handler(event, context):
    """
    Handler principal de Lambda Worker
    
    Args:
        event: Evento de SQS
        context: Contexto de Lambda
        
    Returns:
        dict: Resultado del procesamiento
    """
    try:
        log_info("Worker invocado", requestId=context.request_id)
        
        # Procesar cada mensaje de SQS
        for record in event['Records']:
            process_sqs_message(record)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Processed successfully'})
        }
        
    except Exception as e:
        log_error("Error en Worker", error=e)
        # No relanzar excepción para evitar reintentos innecesarios
        # El mensaje volverá a la cola según la configuración de DLQ
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def process_sqs_message(record):
    """
    Procesa un mensaje individual de SQS
    
    Args:
        record: Registro de SQS
    """
    try:
        # 1. Parsear mensaje
        message_body = json.loads(record['body'])
        job_id = message_body['jobId']
        toon = message_body['toon']
        toon_id = toon.get('toonId')
        
        log_info("Procesando mensaje SQS", jobId=job_id, toonId=toon_id)
        
        # 2. Verificar idempotencia
        idempotency_key = f"{job_id}:{toon_id}"
        if idempotency_key in processed_cache:
            log_info("Toon ya procesado (cache)", jobId=job_id, toonId=toon_id)
            return
        
        # 3. Procesar toon
        result = process_toon(toon)
        
        # 4. Guardar resultado en DynamoDB
        save_toon_result(job_id, toon_id, result)
        
        # 5. Incrementar contador de toons procesados
        updated_job = increment_processed_toons(job_id)
        
        log_info("Toon procesado y guardado", 
                 jobId=job_id, 
                 toonId=toon_id,
                 processedToons=updated_job.get('processedToons'))
        
        # 6. Marcar como procesado en cache
        processed_cache.add(idempotency_key)
        
        # 7. Verificar si el job está completo
        check_job_completion(job_id)
        
    except Exception as e:
        log_error("Error procesando mensaje SQS", 
                  error=e,
                  messageId=record.get('messageId'))
        raise
