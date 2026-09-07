# src/priorizacion/fase2_rentabilidad.py
"""
Fase 2: Puntuador por Rentabilidad Económica (ROI)
"""

import pandas as pd
import numpy as np
from src.priorizacion.puntuador import PuntuadorBase
from src.utilidades.registrador import registro
from src.utilidades.configuracion import configuracion

class PuntuadorRentabilidad(PuntuadorBase):
    """
    Puntuador por Rentabilidad Económica - Fase 2
    """
    
    def __init__(self):
        super().__init__(nombre="puntuador_rentabilidad")
        self.costo_inspeccion = configuracion.obtener('economia.costo_inspeccion', 30.0)
        self.ganancia_promedio = configuracion.obtener('economia.ganancia_promedio', 300.0)
        registro.info(f"💰 Fase 2 - Puntuador de Rentabilidad")
    
    def calcular_puntajes(self, df: pd.DataFrame, 
                          probabilidades: np.ndarray) -> pd.DataFrame:
        registro.info("💰 Calculando puntajes por rentabilidad (Fase 2)...")
        
        puntajes = pd.DataFrame()
        puntajes['id_cliente'] = df['id_cliente']
        puntajes['probabilidad'] = probabilidades
        puntajes['factor_impacto'] = self._calcular_factor_impacto(df)
        
        puntajes['ganancia_esperada'] = (
            probabilidades * 
            self.ganancia_promedio * 
            (1 + puntajes['factor_impacto'])
        )
        
        puntajes['rentabilidad_esperada'] = puntajes['ganancia_esperada'] - self.costo_inspeccion
        
        max_rentabilidad = puntajes['rentabilidad_esperada'].max()
        if max_rentabilidad > 0:
            puntajes['puntaje_prioridad'] = puntajes['rentabilidad_esperada'] / max_rentabilidad
        else:
            puntajes['puntaje_prioridad'] = np.zeros(len(puntajes))
        
        puntajes['prioridad'] = self._asignar_prioridad(puntajes)
        puntajes = puntajes.sort_values('puntaje_prioridad', ascending=False)
        
        registro.info(f"✅ Puntajes calculados para {len(puntajes)} suministros")
        return puntajes
    
    def _calcular_factor_impacto(self, df: pd.DataFrame) -> pd.Series:
        if 'consumo_promedio' in df.columns:
            max_consumo = df['consumo_promedio'].max()
            if max_consumo > 0:
                return df['consumo_promedio'] / max_consumo
        return pd.Series(np.zeros(len(df)))
    
    def _asignar_prioridad(self, puntajes: pd.DataFrame) -> pd.Series:
        def get_priority(row):
            if row['rentabilidad_esperada'] > self.costo_inspeccion * 2:
                return 'ALTA'
            elif row['rentabilidad_esperada'] > 0:
                return 'MEDIA'
            else:
                return 'BAJA'
        return puntajes.apply(get_priority, axis=1)