from PIL import Image
from io import BytesIO
import logging

logger = logging.getLogger()

def validate_image(image_bytes):
    """Valida que sea una imagen válida"""
    try:
        img = Image.open(BytesIO(image_bytes))
        img.verify()
        return True
    except Exception as e:
        logger.error(f"Validación fallida: {str(e)}")
        return False

def get_image_dimensions(image_bytes):
    """Obtiene dimensiones de imagen"""
    try:
        img = Image.open(BytesIO(image_bytes))
        return {'width': img.width, 'height': img.height}
    except Exception as e:
        logger.error(f"Error obteniendo dimensiones: {str(e)}")
        return None
