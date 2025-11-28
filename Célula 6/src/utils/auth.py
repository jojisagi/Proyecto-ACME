"""
Utilidades para validación de JWT
"""
import jwt
import os
from src.utils.logger import log_error


def validate_jwt(token):
    """
    Valida token JWT
    
    Args:
        token: Token JWT del header Authorization
        
    Returns:
        dict: Payload decodificado si es válido
        
    Raises:
        Exception: Si el token es inválido
    """
    try:
        # En producción, obtener secret de AWS Secrets Manager
        secret = os.environ.get('JWT_SECRET', 'your-secret-key')
        decoded = jwt.decode(token, secret, algorithms=['HS256'])
        return decoded
    except jwt.ExpiredSignatureError:
        log_error("Token JWT expirado")
        raise Exception("Token expirado")
    except jwt.InvalidTokenError as e:
        log_error("Token JWT inválido", error=e)
        raise Exception("Token inválido")


def extract_token_from_header(authorization_header):
    """
    Extrae token del header Authorization
    
    Args:
        authorization_header: Header "Bearer <token>"
        
    Returns:
        str: Token JWT
    """
    if not authorization_header:
        raise Exception("Header Authorization no presente")
    
    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise Exception("Formato de Authorization inválido")
    
    return parts[1]
