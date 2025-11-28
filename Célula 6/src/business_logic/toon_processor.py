"""
Lógica de negocio para procesamiento de toons
"""
import hashlib
import json
import time
from src.utils.logger import log_info


def process_toon(toon_data):
    """
    Procesa un toon: transformación, validación, enriquecimiento
    
    Args:
        toon_data: Diccionario con datos del toon
        
    Returns:
        dict: Resultado del procesamiento con hash, duration, etc.
    """
    start_time = time.time()
    
    toon_id = toon_data.get('toonId')
    toon_type = toon_data.get('type')
    payload = toon_data.get('payload', {})
    
    log_info("Iniciando procesamiento de toon", toonId=toon_id, type=toon_type)
    
    # 1. Transformación
    transformed_data = transform_toon(toon_data)
    
    # 2. Validación
    is_valid = validate_toon(transformed_data)
    
    # 3. Enriquecimiento
    enriched_data = enrich_toon(transformed_data)
    
    # 4. Calcular hash/fingerprint
    fingerprint = calculate_fingerprint(enriched_data)
    
    # 5. Calcular duración
    duration_ms = int((time.time() - start_time) * 1000)
    
    result = {
        'toonId': toon_id,
        'type': toon_type,
        'fingerprint': fingerprint,
        'durationMs': duration_ms,
        'isValid': is_valid,
        'processedData': enriched_data
    }
    
    log_info("Toon procesado exitosamente", 
             toonId=toon_id, 
             durationMs=duration_ms,
             fingerprint=fingerprint)
    
    return result


def transform_toon(toon_data):
    """
    Aplica transformaciones al toon
    
    Args:
        toon_data: Datos originales del toon
        
    Returns:
        dict: Datos transformados
    """
    # Ejemplo: normalizar campos, convertir tipos, etc.
    transformed = {
        'toonId': toon_data.get('toonId'),
        'type': toon_data.get('type', '').upper(),
        'payload': toon_data.get('payload', {}),
        'metadata': {
            'originalSize': len(json.dumps(toon_data)),
            'hasPayload': bool(toon_data.get('payload'))
        }
    }
    return transformed


def validate_toon(toon_data):
    """
    Valida que el toon cumpla con reglas de negocio
    
    Args:
        toon_data: Datos del toon
        
    Returns:
        bool: True si es válido
    """
    # Ejemplo: validar campos requeridos, rangos, formatos
    if not toon_data.get('toonId'):
        return False
    
    if not toon_data.get('type'):
        return False
    
    # Validaciones específicas por tipo
    toon_type = toon_data.get('type')
    if toon_type == 'IMAGE':
        return validate_image_toon(toon_data)
    elif toon_type == 'VIDEO':
        return validate_video_toon(toon_data)
    
    return True


def validate_image_toon(toon_data):
    """Validación específica para toons de tipo IMAGE"""
    payload = toon_data.get('payload', {})
    return 'url' in payload or 'data' in payload


def validate_video_toon(toon_data):
    """Validación específica para toons de tipo VIDEO"""
    payload = toon_data.get('payload', {})
    return 'url' in payload and 'duration' in payload


def enrich_toon(toon_data):
    """
    Enriquece el toon con información adicional
    
    Args:
        toon_data: Datos del toon
        
    Returns:
        dict: Datos enriquecidos
    """
    enriched = toon_data.copy()
    
    # Ejemplo: agregar metadatos calculados
    enriched['enrichment'] = {
        'processedBy': 'ToonProcessor-v1.0',
        'complexity': calculate_complexity(toon_data),
        'category': categorize_toon(toon_data)
    }
    
    return enriched


def calculate_complexity(toon_data):
    """Calcula un score de complejidad del toon"""
    payload_size = len(json.dumps(toon_data.get('payload', {})))
    if payload_size > 10000:
        return 'HIGH'
    elif payload_size > 1000:
        return 'MEDIUM'
    return 'LOW'


def categorize_toon(toon_data):
    """Categoriza el toon basado en su tipo y contenido"""
    toon_type = toon_data.get('type', '')
    if toon_type in ['IMAGE', 'VIDEO']:
        return 'MEDIA'
    elif toon_type in ['TEXT', 'DOCUMENT']:
        return 'CONTENT'
    return 'OTHER'


def calculate_fingerprint(toon_data):
    """
    Calcula un hash único del toon procesado
    
    Args:
        toon_data: Datos del toon
        
    Returns:
        str: Hash SHA256
    """
    # Serializar datos de forma determinística
    serialized = json.dumps(toon_data, sort_keys=True)
    hash_object = hashlib.sha256(serialized.encode())
    return hash_object.hexdigest()
