# src/monitoreo/falsos_positivos.py
"""
Monitoreo de falsos positivos
"""

import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from src.utilidades.registrador import registro

class MonitorFalsosPositivos:
    """
    Monitorea la tasa de falsos positivos
    """
    
    def __init__(self):
        self.umbral = 0.10  # 10% de FP máximo
        self.ruta_inspecciones = Path('datos/retroalimentacion/inspecciones')
    
    def calcular_tasa(self, dias: int = 30) -> float:
        """
        Calcula la tasa de falsos positivos en los últimos N días
        """
        if not self.ruta_inspecciones.exists():
            return 0.0
        
        corte = datetime.now() - timedelta(days=dias)
        archivos = list(self.ruta_inspecciones.glob('*.csv'))
        
        if not archivos:
            return 0.0
        
        dataframes = []
        for archivo in archivos:
            df = pd.read_csv(archivo)
            if 'fecha_inspeccion' in df.columns:
                df['fecha_inspeccion'] = pd.to_datetime(df['fecha_inspeccion'])
                df = df[df['fecha_inspeccion'] > corte]
                dataframes.append(df)
        
        if not dataframes:
            return 0.0
        
        todos = pd.concat(dataframes, ignore_index=True)
        total = len(todos)
        
        if total == 0:
            return 0.0
        
        fp = len(todos[todos['resultado'] == 'Falso Positivo'])
        
        return fp / total
    
    def verificar(self) -> dict:
        """
        Verifica si la tasa de FP supera el umbral
        """
        tasa = self.calcular_tasa()
        
        return {
            'tasa_fp': tasa,
            'umbral': self.umbral,
            'supera_umbral': tasa > self.umbral,
            'timestamp': datetime.now().isoformat()
        }