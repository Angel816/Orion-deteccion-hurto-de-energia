# src/monitoreo/alertas.py
"""
Sistema de alertas automáticas
"""

import pandas as pd
from datetime import datetime
from src.utilidades.registrador import registro

class SistemaAlertas:
    """
    Genera alertas cuando se detectan condiciones anómalas
    """
    
    def __init__(self):
        self.alertas = []
        self.umbrales = {
            'precision': 0.85,
            'tasa_exito': 0.20,
            'falsos_positivos': 0.10
        }
    
    def verificar(self, metricas: dict) -> list:
        """
        Verifica las métricas y genera alertas si es necesario
        """
        alertas_generadas = []
        
        if metricas.get('precision', 1) < self.umbrales['precision']:
            alertas_generadas.append({
                'tipo': 'precision_baja',
                'mensaje': f"Precisión baja: {metricas['precision']*100:.1f}%",
                'timestamp': datetime.now().isoformat()
            })
        
        if metricas.get('tasa_exito', 1) < self.umbrales['tasa_exito']:
            alertas_generadas.append({
                'tipo': 'tasa_exito_baja',
                'mensaje': f"Tasa de éxito baja: {metricas['tasa_exito']*100:.1f}%",
                'timestamp': datetime.now().isoformat()
            })
        
        self.alertas.extend(alertas_generadas)
        return alertas_generadas
    
    def obtener_alertas(self, ultimas: int = 10) -> list:
        """Retorna las últimas N alertas"""
        return self.alertas[-ultimas:]