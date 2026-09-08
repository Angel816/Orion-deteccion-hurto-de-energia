# pruebas/test_modelos.py
"""
Pruebas para el módulo de modelos
"""

import pytest
import numpy as np
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.modelos.isolation_forest import BosqueAislamiento
from src.modelos.enrutador import EnrutadorModelos

class TestBosqueAislamiento:
    def test_init(self):
        modelo = BosqueAislamiento()
        assert modelo is not None
        assert modelo.nombre == "bosque_aislamiento"
    
    def test_entrenar(self):
        modelo = BosqueAislamiento()
        X = np.random.randn(100, 5)
        modelo.entrenar(X)
        assert modelo.entrenado == True

class TestEnrutador:
    def test_seleccion(self):
        enrutador = EnrutadorModelos()
        resultado = enrutador.evaluar_suministro(
            {'consumo_promedio': 100, 'total_alarmas': 5},
            n_etiquetas=50
        )
        assert 'modelo_seleccionado' in resultado