"""
Helpers para operaciones con DynamoDB
"""
import boto3
import os
from datetime import datetime
from src.utils.logger import log_info, log_error

dynamodb = boto3.resource('dynamodb')


def get_jobs_table():
    """Obtiene referencia a tabla de Jobs"""
    table_name = os.environ.get('JOBS_TABLE_NAME', 'ToonJobs')
    return dynamodb.Table(table_name)


def get_results_table():
    """Obtiene referencia a tabla de Results"""
    table_name = os.environ.get('RESULTS_TABLE_NAME', 'ToonResults')
    return dynamodb.Table(table_name)


def create_job(job_id, toons_count, user_id):
    """
    Crea un nuevo job en DynamoDB
    
    Args:
        job_id: ID único del job
        toons_count: Número total de toons
        user_id: ID del usuario que creó el job
    """
    table = get_jobs_table()
    timestamp = datetime.utcnow().isoformat()
    
    item = {
        'jobId': job_id,
        'status': 'Pending',
        'totalToons': toons_count,
        'processedToons': 0,
        'userId': user_id,
        'createdAt': timestamp,
        'updatedAt': timestamp
    }
    
    table.put_item(Item=item)
    log_info("Job creado en DynamoDB", jobId=job_id, toonsCount=toons_count)


def update_job_status(job_id, status):
    """Actualiza el estado de un job"""
    table = get_jobs_table()
    timestamp = datetime.utcnow().isoformat()
    
    table.update_item(
        Key={'jobId': job_id},
        UpdateExpression='SET #status = :status, updatedAt = :timestamp',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':status': status,
            ':timestamp': timestamp
        }
    )
    log_info("Estado de job actualizado", jobId=job_id, status=status)


def increment_processed_toons(job_id):
    """Incrementa el contador de toons procesados"""
    table = get_jobs_table()
    timestamp = datetime.utcnow().isoformat()
    
    response = table.update_item(
        Key={'jobId': job_id},
        UpdateExpression='ADD processedToons :inc SET updatedAt = :timestamp',
        ExpressionAttributeValues={
            ':inc': 1,
            ':timestamp': timestamp
        },
        ReturnValues='ALL_NEW'
    )
    return response['Attributes']


def get_job(job_id):
    """Obtiene información de un job"""
    table = get_jobs_table()
    response = table.get_item(Key={'jobId': job_id})
    return response.get('Item')


def save_toon_result(job_id, toon_id, result_data):
    """
    Guarda el resultado del procesamiento de un toon
    
    Args:
        job_id: ID del job
        toon_id: ID del toon
        result_data: Datos del resultado (hash, duration, etc.)
    """
    table = get_results_table()
    timestamp = datetime.utcnow().isoformat()
    
    item = {
        'jobId': job_id,
        'toonId': toon_id,
        'processedAt': timestamp,
        **result_data
    }
    
    table.put_item(Item=item)
    log_info("Resultado guardado", jobId=job_id, toonId=toon_id)


def get_results_by_job(job_id):
    """Obtiene todos los resultados de un job"""
    table = get_results_table()
    response = table.query(
        KeyConditionExpression='jobId = :jobId',
        ExpressionAttributeValues={':jobId': job_id}
    )
    return response.get('Items', [])
