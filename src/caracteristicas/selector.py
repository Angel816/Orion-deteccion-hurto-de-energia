# src/caracteristicas/selector.py
"""
Selector de características CAUSALES para detección de hurto
Proyecto Orion

ESTRUCTURA:
- EVIDENCIA (features de entrada): 17 variables que evidencian hurto
- MODELO (features de salida): 4 variables generadas por el modelo
- METADATA: id_cliente, prioridad

Total: 23 columnas (17 evidencia + 4 modelo + 2 metadata)
"""

import pandas as pd
from typing import List, Optional
from src.utilidades.registrador import registro


class SelectorCaracteristicas:
    """
    Selecciona las features CAUSALES y las de MODELO
    """
    
    def __init__(self):
        # ============================================================
        # EVIDENCIA (Features de entrada - CAUSALES de hurto)
        # ============================================================
        
        self.features_evidencia = [
            # EVIDENCIA FÍSICA (6)
            'alarmas_tipo_bypass',        # Bypass/magneto
            'alarmas_precinto_roto',      # Precinto manipulado
            'alarmas_tapa_abierta',       # Medidor abierto
            'alarmas_inversion_fases',    # Fases invertidas
            'alarmas_ultimos_30_dias',    # Alarmas recientes
            'score_evidencia_fisica',     # Score compuesto físico
            
            # EVIDENCIA DE CONSUMO (6)
            'caida_brusca',               # Caída reciente
            'meses_con_caida',            # Persistencia
            'consumo_vs_similares',       # Anomalía vs pares
            'consumo_minimo_sostenido',   # Bypass sostenido
            'ratio_consumo_nocturno',     # Patrón nocturno
            'score_evidencia_consumo',    # Score compuesto consumo
            
            # EVIDENCIA DE HISTORIAL (5)
            'hurto_confirmado_previo',    # Reincidencia
            'inspecciones_previas',       # N° inspecciones
            'tasa_exito_historica',       # Tasa de hurto
            'meses_desde_ultima_inspeccion', # Recencia
            'score_reincidencia',         # Score compuesto historial
        ]
        
        # ============================================================
        # MODELO (Features de salida - generadas por el modelo)
        # ============================================================
        
        self.features_modelo_salida = [
            'probabilidad',               # Predicción del modelo
            'impacto_economico',          # Impacto económico (S/)
            'historial',                  # Score de historial
            'puntaje_prioridad',          # Score final
        ]
        
        # ============================================================
        # METADATA (2 columnas)
        # ============================================================
        
        self.features_metadata = [
            'id_cliente',
            'prioridad'
        ]
        
        # ============================================================
        # LISTA COMPLETA (para guardar en parquet)
        # ============================================================
        
        self.features_principales = (
            self.features_metadata[:1] +      # id_cliente
            self.features_evidencia +          # 17 features de evidencia
            self.features_modelo_salida +      # 4 features de modelo
            self.features_metadata[1:]         # prioridad
        )
        
        # ============================================================
        # FEATURES PARA EL MODELO (solo las de entrada + salida)
        # ============================================================
        
        self.features_para_modelo = (
            self.features_evidencia +          # 17 features de entrada
            self.features_modelo_salida        # 4 features de salida
        )
        
        registro.info(f"📋 Selector inicializado:")
        registro.info(f"   📊 Evidencia: {len(self.features_evidencia)}")
        registro.info(f"   📊 Modelo: {len(self.features_modelo_salida)}")
        registro.info(f"   📊 Metadata: {len(self.features_metadata)}")
        registro.info(f"   📊 Total: {len(self.features_principales)}")
    
    def seleccionar(self, df: pd.DataFrame,
                    features_custom: Optional[List[str]] = None) -> pd.DataFrame:
        """Selecciona las features del DataFrame"""
        features = features_custom or self.features_principales
        
        columnas_disponibles = [col for col in features if col in df.columns]
        columnas_faltantes = [col for col in features if col not in df.columns]
        
        if columnas_faltantes:
            registro.warning(f"⚠️ Features faltantes ({len(columnas_faltantes)}): {columnas_faltantes}")
        
        df_seleccionado = df[columnas_disponibles].copy()
        
        n_antes = len(df.columns)
        n_despues = len(df_seleccionado.columns)
        
        registro.info(f"✅ Features seleccionadas: {n_despues}/{n_antes}")
        
        return df_seleccionado
    
    def obtener_features_modelo(self) -> List[str]:
        """Retorna las features para ENTRENAR el modelo (solo evidencia)"""
        return self.features_evidencia.copy()
    
    def obtener_todas_features(self) -> List[str]:
        """Retorna TODAS las features (evidencia + modelo)"""
        return self.features_principales.copy()
    
    def obtener_features_dashboard(self) -> List[str]:
        """Retorna las features para mostrar en el dashboard"""
        return self.features_principales.copy()
    
    def generar_reporte(self, df: pd.DataFrame) -> dict:
        """Genera reporte del selector"""
        return {
            'total_features_originales': len(df.columns),
            'total_features_seleccionadas': len(self.features_principales),
            'features_evidencia': [f for f in self.features_evidencia if f in df.columns],
            'features_modelo': [f for f in self.features_modelo_salida if f in df.columns],
            'features_metadata': [f for f in self.features_metadata if f in df.columns],
            'features_faltantes': [f for f in self.features_principales if f not in df.columns]
        }