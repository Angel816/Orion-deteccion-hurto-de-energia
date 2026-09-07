# src/priorizacion/fase1_simple.py
"""
Fase 1: Puntuador Simple (Probabilidad + Impacto + Historial)
"""

import pandas as pd
import numpy as np
from typing import Dict
from src.priorizacion.puntuador import PuntuadorBase
from src.utilidades.registrador import registro

class PuntuadorSimple(PuntuadorBase):
    """
    Puntuador Simple - Fase 1 del Proyecto Orion
    """
    
    def __init__(self, pesos: Dict[str, float] = None):
        super().__init__(nombre="puntuador_simple")
        self.pesos = pesos or {
            'probability': 0.6,
            'economic_impact': 0.3,
            'history': 0.1
        }
        registro.info(f"📊 Fase 1 - Puntuador Simple: pesos {self.pesos}")
    
    def calcular_puntajes(self, df: pd.DataFrame, 
                          probabilidades: np.ndarray) -> pd.DataFrame:
        registro.info("🎯 Calculando puntajes (Fase 1 - Simple)...")
        
        puntajes = pd.DataFrame()
        puntajes['id_cliente'] = df['id_cliente']
        puntajes['probabilidad'] = probabilidades
        puntajes['impacto_economico'] = self._calcular_impacto(df)
        puntajes['historial'] = self._calcular_historial(df)
        
        puntajes['puntaje_prioridad'] = (
            puntajes['probabilidad'] * self.pesos['probability'] +
            puntajes['impacto_economico'] * self.pesos['economic_impact'] +
            puntajes['historial'] * self.pesos['history']
        )
        
        puntajes['prioridad'] = pd.qcut(
            puntajes['puntaje_prioridad'],
            q=3,
            labels=['BAJA', 'MEDIA', 'ALTA'],
            duplicates='drop'
        )
        
        puntajes = puntajes.sort_values('puntaje_prioridad', ascending=False)
        
        registro.info(f"✅ Puntajes calculados para {len(puntajes)} suministros")
        return puntajes
    
    def _calcular_impacto(self, df: pd.DataFrame) -> pd.Series:
        precio_kwh = 0.18
        factor_perdida = 0.3
        
        if 'consumo_promedio' in df.columns:
            perdida_mensual = df['consumo_promedio'] * 30 * factor_perdida * precio_kwh
        else:
            perdida_mensual = pd.Series(np.ones(len(df)) * 50)
        
        max_perdida = perdida_mensual.max()
        if max_perdida > 0:
            return perdida_mensual / max_perdida
        return pd.Series(np.zeros(len(df)))
    
    def _calcular_historial(self, df: pd.DataFrame) -> pd.Series:
        historial = pd.Series(np.zeros(len(df)))
        
        if 'inspecciones_previas' in df.columns:
            max_inspecciones = df['inspecciones_previas'].max()
            if max_inspecciones > 0:
                historial += df['inspecciones_previas'] / max_inspecciones * 0.5
        
        if 'total_alarmas' in df.columns:
            max_alarmas = df['total_alarmas'].max()
            if max_alarmas > 0:
                historial += df['total_alarmas'] / max_alarmas * 0.3
        
        if 'dias_mora' in df.columns:
            max_mora = df['dias_mora'].max()
            if max_mora > 0:
                historial += df['dias_mora'] / max_mora * 0.2
        
        return historial