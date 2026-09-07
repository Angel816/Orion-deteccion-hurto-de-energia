# src/priorizacion/puntuador.py
"""
Clase base para puntuadores de priorización
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from src.utilidades.registrador import registro

class PuntuadorBase:
    """
    Clase base para todos los puntuadores de priorización
    """
    
    def __init__(self, nombre: str = "puntuador_base"):
        self.nombre = nombre
        self.pesos = {}
        registro.info(f"📊 {nombre} inicializado")
    
    def calcular_puntajes(self, df: pd.DataFrame, 
                          probabilidades: np.ndarray) -> pd.DataFrame:
        raise NotImplementedError("Este método debe ser implementado por las subclases")
    
    def obtener_top_n(self, puntajes: pd.DataFrame, n: int = 100) -> pd.DataFrame:
        return puntajes.nlargest(n, 'puntaje_prioridad')