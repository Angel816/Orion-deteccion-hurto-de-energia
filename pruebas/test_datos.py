# pruebas/test_datos.py
"""
Pruebas para el módulo de datos
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.datos.cargador import CargadorIncremental
from src.datos.validador import ValidadorDatos
from src.datos.limpiador import LimpiadorDatos

class TestCargador:
    def test_init(self):
        cargador = CargadorIncremental()
        assert cargador is not None
        assert hasattr(cargador, 'cargar_archivos_nuevos')

class TestValidador:
    def test_validar_consumo(self):
        validador = ValidadorDatos()
        df = pd.DataFrame({
            'id_cliente': ['CL001', 'CL002'],
            'fecha': ['2024-01-01', '2024-01-01'],
            'consumo_kwh': [100, 200]
        })
        resultado = validador.validar(df, 'consumo')
        assert resultado['estado'] == 'aceptado'

class TestLimpiador:
    def test_limpiar_consumo(self):
        limpiador = LimpiadorDatos()
        df = pd.DataFrame({
            'id_cliente': ['CL001', 'CL002'],
            'fecha': ['2024-01-01', '2024-01-01'],
            'consumo_kwh': [100, -5]
        })
        df_limpio = limpiador.limpiar_consumo(df)
        assert (df_limpio['consumo_kwh'] >= 0).all()