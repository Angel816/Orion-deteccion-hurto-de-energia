# src/modelos/__init__.py
"""
Módulo de modelos de detección de hurto
"""

from src.modelos.detector import DetectorBase
from src.modelos.isolation_forest import BosqueAislamiento
from src.modelos.random_forest import BosqueAleatorio
from src.modelos.ensemble import Conjunto
from src.modelos.enrutador import EnrutadorModelos

__all__ = [
    'DetectorBase',
    'BosqueAislamiento',
    'BosqueAleatorio',
    'Conjunto',
    'EnrutadorModelos'
]