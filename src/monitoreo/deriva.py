# src/monitoreo/deriva.py
"""
Detección de deriva (drift) en los datos
"""

import pandas as pd
import numpy as np
from scipy import stats
from src.utilidades.registrador import registro

class DetectorDeriva:
    """
    Detecta cambios en la distribución de los datos
    """
    
    def __init__(self, umbral: float = 0.05):
        self.umbral = umbral
        self.historial = []
    
    def detectar(self, datos_antiguos: pd.DataFrame, 
                 datos_nuevos: pd.DataFrame) -> dict:
        """
        Detecta deriva usando KS test
        """
        resultados = {}
        columnas_numericas = datos_antiguos.select_dtypes(include=[np.number]).columns
        
        for col in columnas_numericas:
            if col in datos_nuevos.columns:
                ref = datos_antiguos[col].dropna()
                nueva = datos_nuevos[col].dropna()
                
                if len(ref) > 10 and len(nueva) > 10:
                    stat, p_value = stats.ks_2samp(ref, nueva)
                    resultados[col] = {
                        'p_value': p_value,
                        'tiene_deriva': p_value < self.umbral
                    }
        
        self.historial.append({
            'timestamp': pd.Timestamp.now().isoformat(),
            'resultados': resultados
        })
        
        return resultados