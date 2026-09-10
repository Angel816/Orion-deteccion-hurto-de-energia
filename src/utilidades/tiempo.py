# src/utilidades/tiempo.py
"""
Gestión centralizada de fechas y zonas horarias para Orion
"""

from datetime import datetime
from zoneinfo import ZoneInfo

# Zona horaria de Perú (UTC-5)
ZONA_PERU = ZoneInfo("America/Lima")

def ahora_peru() -> datetime:
    """
    Retorna la fecha y hora actual en zona horaria de Perú
    
    Retorna:
        datetime con zona horaria de Perú
    """
    return datetime.now(ZONA_PERU)

def fecha_hoy_peru() -> str:
    """
    Retorna la fecha actual en Perú en formato YYYY-MM-DD
    """
    return ahora_peru().strftime('%Y-%m-%d')

def timestamp_peru() -> str:
    """
    Retorna el timestamp actual en Perú en formato YYYYMMDD_HHMMSS
    """
    return ahora_peru().strftime('%Y%m%d_%H%M%S')

def iso_peru() -> str:
    """
    Retorna la fecha actual en Perú en formato ISO
    """
    return ahora_peru().isoformat()

def formatear_fecha(fecha: datetime, formato: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    Formatea una fecha en zona horaria de Perú
    
    Parámetros:
        fecha: datetime a formatear
        formato: formato de salida
    
    Retorna:
        String con la fecha formateada
    """
    if fecha.tzinfo is None:
        # Si no tiene zona horaria, asumir que es UTC y convertir
        from datetime import timezone
        fecha = fecha.replace(tzinfo=timezone.utc)
    
    return fecha.astimezone(ZONA_PERU).strftime(formato)