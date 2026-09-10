# src/monitoreo/alertas.py
"""
Sistema de alertas automáticas
Zona horaria: Perú (UTC-5)
"""

import pandas as pd
from typing import List, Dict, Any
from src.utilidades.registrador import registro
from src.utilidades.tiempo import ahora_peru, iso_peru


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
        registro.info("🔔 Sistema de alertas inicializado")
    
    def verificar(self, metricas: dict) -> List[Dict[str, Any]]:
        """
        Verifica las métricas y genera alertas si es necesario
        """
        alertas_generadas = []
        fecha_actual = iso_peru()  # ← HORA PERÚ
        
        if metricas.get('precision', 1) < self.umbrales['precision']:
            alertas_generadas.append({
                'tipo': 'precision_baja',
                'mensaje': f"Precisión baja: {metricas['precision']*100:.1f}%",
                'timestamp': fecha_actual,
                'severidad': 'alta'
            })
        
        if metricas.get('tasa_exito', 1) < self.umbrales['tasa_exito']:
            alertas_generadas.append({
                'tipo': 'tasa_exito_baja',
                'mensaje': f"Tasa de éxito baja: {metricas['tasa_exito']*100:.1f}%",
                'timestamp': fecha_actual,
                'severidad': 'media'
            })
        
        if metricas.get('falsos_positivos', 0) > self.umbrales['falsos_positivos']:
            alertas_generadas.append({
                'tipo': 'falsos_positivos_altos',
                'mensaje': f"Falsos positivos altos: {metricas['falsos_positivos']*100:.1f}%",
                'timestamp': fecha_actual,
                'severidad': 'alta'
            })
        
        self.alertas.extend(alertas_generadas)
        
        if alertas_generadas:
            registro.warning(f"⚠️ {len(alertas_generadas)} alertas generadas")
        
        return alertas_generadas
    
    def obtener_alertas(self, ultimas: int = 10) -> List[Dict]:
        """Retorna las últimas N alertas"""
        return self.alertas[-ultimas:]
    
    def limpiar_alertas(self):
        """Limpia el historial de alertas"""
        self.alertas = []
        registro.info("🗑️ Alertas limpiadas")