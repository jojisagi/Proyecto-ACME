"""
Utilidad para logging estructurado con contexto
"""
import json
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def log_info(message, **context):
    """Log mensaje INFO con contexto estructurado"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": "INFO",
        "message": message,
        **context
    }
    logger.info(json.dumps(log_entry))


def log_error(message, error=None, **context):
    """Log mensaje ERROR con contexto estructurado"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": "ERROR",
        "message": message,
        **context
    }
    if error:
        log_entry["error"] = str(error)
    logger.error(json.dumps(log_entry))
