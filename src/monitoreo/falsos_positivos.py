# src/monitoreo/falsos_positivos.py
"""
Monitoreo de falsos positivos
Zona horaria: Perú (UTC-5)
"""

import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from src.utilidades.registrador import registro
from src.utilidades.tiempo import ahora_peru


class MonitorFalsosPositivos:
    """
    Monitorea la tasa de falsos positivos
    """
    
    def __init__(self):
        self.umbral = 0.10
        self.ruta_inspecciones = Path('datos/retroalimentacion/inspecciones')
        registro.info("📊 Monitor de falsos positivos inicializado")
    
    def calcular_tasa(self, dias: int = 30) -> float:
        """Calcula la tasa de falsos positivos en los últimos N días"""
        if not self.ruta_inspecciones.exists():
            return 0.0
        
        # Usar hora Perú para el corte
        corte = ahora_peru().replace(tzinfo=None) - timedelta(days=dias)
        archivos = list(self.ruta_inspecciones.glob('*.csv'))
        
        if not archivos:
            return 0.0
        
        dataframes = []
        for archivo in archivos:
            try:
                df = pd.read_csv(archivo)
                if 'fecha_inspeccion' in df.columns:
                    df['fecha_inspeccion'] = pd.to_datetime(df['fecha_inspeccion'])
                    # Convertir a naive para comparar
                    df_filtrado = df[
                        df['fecha_inspeccion'].dt.tz_localize(None) > corte
                    ] if df['fecha_inspeccion'].dt.tz is not None else df[
                        df['fecha_inspeccion'] > corte
                    ]
                    dataframes.append(df_filtrado)
            except Exception as e:
                registro.warning(f"⚠️ Error leyendo {archivo}: {e}")
        
        if not dataframes:
            return 0.0
        
        todos = pd.concat(dataframes, ignore_index=True)
        total = len(todos)
        
        if total == 0:
            return 0.0
        
        fp = len(todos[todos['resultado'] == 'Falso Positivo'])
        tasa = fp / total
        
        registro.info(f"📊 Tasa de FP (últimos {dias} días): {tasa*100:.1f}% ({fp}/{total})")
        return tasa
    
    def verificar(self) -> dict:
        """Verifica si la tasa de FP supera el umbral"""
        tasa = self.calcular_tasa()
        
        resultado = {
            'tasa_fp': tasa,
            'umbral': self.umbral,
            'supera_umbral': tasa > self.umbral,
            'timestamp': ahora_peru().isoformat()  # ← HORA PERÚ
        }
        
        if resultado['supera_umbral']:
            registro.warning(f"⚠️ Tasa de falsos positivos alta: {tasa*100:.1f}%")
        
        return resultado
    
    def obtener_estadisticas(self) -> dict:
        """Retorna estadísticas de falsos positivos"""
        tasa = self.calcular_tasa()
        
        return {
            'tasa_actual': tasa,
            'umbral': self.umbral,
            'estado': 'crítico' if tasa > self.umbral else 'normal',
            'timestamp': ahora_peru().isoformat()
        }