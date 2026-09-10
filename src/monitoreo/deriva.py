# src/monitoreo/deriva.py
"""
Detección de deriva (drift) en los datos
Zona horaria: Perú (UTC-5)
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Any
from src.utilidades.registrador import registro
from src.utilidades.tiempo import ahora_peru, iso_peru


class DetectorDeriva:
    """
    Detecta cambios en la distribución de los datos
    """
    
    def __init__(self, umbral: float = 0.05):
        self.umbral = umbral
        self.historial = []
        registro.info("📊 Detector de deriva inicializado")
    
    def detectar(self, datos_antiguos: pd.DataFrame, 
                 datos_nuevos: pd.DataFrame) -> Dict[str, Any]:
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
                        'estadistico': stat,
                        'tiene_deriva': p_value < self.umbral
                    }
        
        # Registrar en historial
        self.historial.append({
            'timestamp': iso_peru(),  # ← HORA PERÚ
            'resultados': resultados,
            'total_columnas': len(resultados),
            'columnas_con_deriva': sum(1 for r in resultados.values() if r['tiene_deriva'])
        })
        
        if any(r['tiene_deriva'] for r in resultados.values()):
            registro.warning(f"⚠️ Deriva detectada en {sum(1 for r in resultados.values() if r['tiene_deriva'])} columnas")
        
        return resultados
    
    def obtener_historial(self, ultimos: int = 10) -> list:
        """Retorna el historial de detecciones"""
        return self.historial[-ultimos:]
    
    def limpiar_historial(self):
        """Limpia el historial"""
        self.historial = []
        registro.info("🗑️ Historial de deriva limpiado")