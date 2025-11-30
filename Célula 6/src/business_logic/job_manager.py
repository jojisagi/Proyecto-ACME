"""
Lógica de negocio para gestión de jobs
"""
import uuid
from src.utils.dynamodb import create_job, update_job_status, get_job


def generate_job_id():
    """Genera un ID único para un job"""
    return f"JOB-{uuid.uuid4().hex[:12].upper()}"


def validate_job_payload(payload):
    """
    Valida el payload de un job
    
    Args:
        payload: Diccionario con jobId y toons
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if 'jobId' not in payload:
        return False, "Campo 'jobId' requerido"
    
    if 'toons' not in payload:
        return False, "Campo 'toons' requerido"
    
    toons = payload['toons']
    if not isinstance(toons, list) or len(toons) == 0:
        return False, "'toons' debe ser una lista con al menos un elemento"
    
    # Validar cada toon
    for idx, toon in enumerate(toons):
        if 'toonId' not in toon:
            return False, f"Toon en posición {idx} no tiene 'toonId'"
        if 'type' not in toon:
            return False, f"Toon en posición {idx} no tiene 'type'"
    
    return True, None


def initialize_job(job_id, toons, user_id):
    """
    Inicializa un job en DynamoDB
    
    Args:
        job_id: ID del job
        toons: Lista de toons
        user_id: ID del usuario
    """
    create_job(job_id, len(toons), user_id)


def mark_job_processing(job_id):
    """Marca un job como en procesamiento"""
    update_job_status(job_id, 'Processing')


def check_job_completion(job_id):
    """
    Verifica si un job ha completado todos sus toons
    
    Args:
        job_id: ID del job
        
    Returns:
        bool: True si está completo
    """
    job = get_job(job_id)
    if not job:
        return False
    
    total = job.get('totalToons', 0)
    processed = job.get('processedToons', 0)
    
    if processed >= total:
        update_job_status(job_id, 'Completed')
        return True
    
    return False
