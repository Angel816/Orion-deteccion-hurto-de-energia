# src/priorizacion/aprendizaje_activo.py
"""
Aprendizaje Activo para selección de casos inciertos
"""

import pandas as pd
import numpy as np
from src.utilidades.registrador import registro

class AprendizajeActivo:
    """
    Selecciona casos inciertos (probabilidad ≈ 0.5) para maximizar el aprendizaje
    """
    
    def __init__(self, peso_incertidumbre: float = 0.3):
        self.peso_incertidumbre = peso_incertidumbre
        registro.info(f"🎯 Aprendizaje Activo inicializado (peso: {peso_incertidumbre})")
    
    def seleccionar_casos(self, puntajes: pd.DataFrame, 
                          probabilidades: np.ndarray,
                          n: int = 100) -> pd.DataFrame:
        incertidumbre = 1 - np.abs(probabilidades - 0.5) * 2
        
        seleccion = puntajes.copy()
        seleccion['incertidumbre'] = incertidumbre
        
        if 'puntaje_prioridad' in seleccion.columns:
            seleccion['puntaje_combinado'] = (
                seleccion['puntaje_prioridad'] * (1 - self.peso_incertidumbre) +
                seleccion['incertidumbre'] * self.peso_incertidumbre
            )
        else:
            seleccion['puntaje_combinado'] = seleccion['incertidumbre']
        
        seleccionados = seleccion.nlargest(n, 'puntaje_combinado')
        registro.info(f"🎯 Seleccionados {len(seleccionados)} casos")
        return seleccionados