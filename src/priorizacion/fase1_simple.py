# src/priorizacion/fase1_simple.py
"""
Fase 1: Puntuador Simple (Probabilidad + Impacto + Historial)
Zona horaria: Perú (UTC-5)
"""

import pandas as pd
import numpy as np
from typing import Dict
from src.priorizacion.puntuador import PuntuadorBase
from src.utilidades.registrador import registro


class PuntuadorSimple(PuntuadorBase):
    """
    Puntuador Simple - Fase 1 del Proyecto Orion
    
    Combina:
    - Probabilidad de hurto (del modelo)
    - Impacto económico estimado
    - Historial del suministro
    """
    
    def __init__(self, pesos: Dict[str, float] = None):
        super().__init__(nombre="puntuador_simple")
        
        # Pesos balanceados
        self.pesos = pesos or {
            'probabilidad': 0.5,      # 50% - Feature principal
            'impacto_economico': 0.3,  # 30% - Impacto en Soles
            'historial': 0.2           # 20% - Historial del cliente
        }
        
        # Precio del kWh (S/)
        self.precio_kwh = 0.18
        self.factor_perdida = 0.3
        
        registro.info(f"📊 Fase 1 - Puntuador Simple: pesos {self.pesos}")
    
    def calcular_puntajes(self, df: pd.DataFrame, 
                          probabilidades: np.ndarray) -> pd.DataFrame:
        """
        Calcula puntajes de priorización
        
        Parámetros:
            df: DataFrame con características de los suministros
            probabilidades: Array con probabilidades de hurto
        
        Retorna:
            DataFrame con puntajes calculados
        """
        registro.info("🎯 Calculando puntajes (Fase 1 - Simple)...")
        
        puntajes = pd.DataFrame()
        puntajes['id_cliente'] = df['id_cliente']
        puntajes['probabilidad'] = probabilidades
        
        # 1. Impacto económico
        puntajes['impacto_economico'] = self._calcular_impacto(df)
        
        # 2. Historial
        puntajes['historial'] = self._calcular_historial(df)
        
        # 3. Puntaje combinado
        puntajes['puntaje_prioridad'] = (
            puntajes['probabilidad'] * self.pesos['probabilidad'] +
            puntajes['impacto_economico'] * self.pesos['impacto_economico'] +
            puntajes['historial'] * self.pesos['historial']
        )
        
        # Normalizar puntaje (0-1)
        max_puntaje = puntajes['puntaje_prioridad'].max()
        if max_puntaje > 0:
            puntajes['puntaje_prioridad'] = puntajes['puntaje_prioridad'] / max_puntaje
        
        # 4. Asignar prioridad
        try:
            puntajes['prioridad'] = pd.qcut(
                puntajes['puntaje_prioridad'],
                q=3,
                labels=['BAJA', 'MEDIA', 'ALTA'],
                duplicates='drop'
            )
        except:
            # Si hay pocos datos, asignar por umbrales
            puntajes['prioridad'] = pd.cut(
                puntajes['puntaje_prioridad'],
                bins=[-np.inf, 0.4, 0.7, np.inf],
                labels=['BAJA', 'MEDIA', 'ALTA']
            )
        
        # 5. Ordenar
        puntajes = puntajes.sort_values('puntaje_prioridad', ascending=False)
        
        registro.info(f"✅ Puntajes calculados para {len(puntajes)} suministros")
        registro.info(f"📊 Distribución: {puntajes['prioridad'].value_counts().to_dict()}")
        registro.info(f"📊 Features usadas: probabilidad, impacto_economico, historial")
        
        return puntajes
    
    # ============================================================
    # CÁLCULO DE COMPONENTES
    # ============================================================
    
    def _calcular_impacto(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcula el impacto económico estimado
        
        Busca en orden:
        1. consumo_promedio (alias generado por extractor)
        2. consumo_media (columna original)
        """
        # Buscar la columna correcta
        columna_consumo = None
        for col in ['consumo_promedio', 'consumo_media', 'consumo_kwh']:
            if col in df.columns:
                columna_consumo = col
                break
        
        if columna_consumo is None:
            registro.warning("⚠️ No hay columna de consumo, impacto = 0")
            return pd.Series(np.zeros(len(df)))
        
        # Calcular pérdida mensual estimada
        perdida_mensual = (
            df[columna_consumo] * 30 * self.factor_perdida * self.precio_kwh
        )
        
        # Normalizar entre 0 y 1
        max_perdida = perdida_mensual.max()
        if max_perdida > 0:
            impacto = perdida_mensual / max_perdida
        else:
            impacto = pd.Series(np.zeros(len(df)))
        
        registro.info(f"   💰 Impacto calculado usando '{columna_consumo}'")
        
        return impacto
    
    def _calcular_historial(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcula el score basado en historial
        
        Busca:
        - inspecciones_previas
        - total_alarmas o alarmas_total
        - dias_mora
        """
        historial = pd.Series(np.zeros(len(df)))
        componentes_usados = []
        
        # 1. Inspecciones previas (peso 0.5)
        for col in ['inspecciones_previas', 'inspecciones_con_hurto']:
            if col in df.columns:
                max_val = df[col].max()
                if max_val > 0:
                    historial += (df[col] / max_val) * 0.5
                    componentes_usados.append(col)
                    break
        
        # 2. Alarmas (peso 0.3)
        for col in ['total_alarmas', 'alarmas_total', 'alarmas_criticas']:
            if col in df.columns:
                max_val = df[col].max()
                if max_val > 0:
                    historial += (df[col] / max_val) * 0.3
                    componentes_usados.append(col)
                    break
        
        # 3. Días de mora (peso 0.2)
        for col in ['dias_mora', 'dias_mora_promedio']:
            if col in df.columns:
                max_val = df[col].max()
                if max_val > 0:
                    historial += (df[col] / max_val) * 0.2
                    componentes_usados.append(col)
                    break
        
        # Normalizar
        historial = historial.clip(0, 1)
        
        if componentes_usados:
            registro.info(f"   📊 Historial calculado usando: {componentes_usados}")
        else:
            registro.warning("   ⚠️ No hay features de historial, historial = 0")
        
        return historial