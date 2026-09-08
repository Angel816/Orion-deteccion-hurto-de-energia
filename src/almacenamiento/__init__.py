# src/almacenamiento/__init__.py
"""
Módulo de almacenamiento optimizado
"""

from src.almacenamiento.particionado import AlmacenamientoParticionado
from src.almacenamiento.compresion import CompresorDatos

__all__ = [
    'AlmacenamientoParticionado',
    'CompresorDatos'
]