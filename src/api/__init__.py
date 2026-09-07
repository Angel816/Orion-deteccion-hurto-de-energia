# src/api/__init__.py
"""
Módulo de API REST
"""

from src.api.principal import app
from src.api.rutas import router
from src.api.adaptador import AdaptadorAPI

__all__ = [
    'app',
    'router',
    'AdaptadorAPI'
]