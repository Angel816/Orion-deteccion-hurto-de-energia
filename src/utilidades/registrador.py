# src/utilidades/registrador.py
"""
Sistema de registro centralizado para Orion
"""

import sys
from pathlib import Path
from loguru import logger
from src.utilidades.configuracion import configuracion

def configurar_registrador():
    """
    Configura el sistema de registro
    """
    logger.remove()
    
    nivel_log = configuracion.obtener('registro.nivel', 'INFO')
    
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=nivel_log,
        colorize=True
    )
    
    archivo_log = configuracion.obtener('registro.archivo', 'registros/orion.log')
    ruta_log = Path(archivo_log)
    ruta_log.parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        archivo_log,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=nivel_log,
        rotation="1 day",
        retention="30 days",
        compression="zip"
    )
    
    logger.info("📋 Sistema de registro inicializado")
    return logger

registro = configurar_registrador()