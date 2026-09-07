# src/caracteristicas/extractor.py
"""
Extracción automática de características para Orion
"""

import pandas as pd
import numpy as np
from src.utilidades.registrador import registro

class ExtractorCaracteristicas:
    """
    Extrae características de los datos para el modelo
    """
    
    def __init__(self):
        registro.info("📊 Extractor de características inicializado")
    
    def extraer_consumo(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extrae características de consumo"""
        registro.info("📊 Extrayendo características de consumo...")
        
        if 'consumo_kwh' not in df.columns or 'id_cliente' not in df.columns:
            registro.warning("⚠️ No se encontraron columnas requeridas para consumo")
            return pd.DataFrame()
        
        caracteristicas = df.groupby('id_cliente')['consumo_kwh'].agg([
            ('consumo_media', 'mean'),
            ('consumo_desviacion', 'std'),
            ('consumo_minimo', 'min'),
            ('consumo_maximo', 'max'),
            ('consumo_mediana', 'median')
        ]).reset_index()
        
        cuartiles = df.groupby('id_cliente')['consumo_kwh'].quantile([0.25, 0.75]).unstack()
        cuartiles.columns = ['consumo_q25', 'consumo_q75']
        caracteristicas = caracteristicas.merge(cuartiles, on='id_cliente', how='left')
        
        caracteristicas['consumo_cv'] = caracteristicas['consumo_desviacion'] / caracteristicas['consumo_media']
        caracteristicas['consumo_cv'] = caracteristicas['consumo_cv'].fillna(0)
        caracteristicas['consumo_rango'] = caracteristicas['consumo_maximo'] - caracteristicas['consumo_minimo']
        caracteristicas = caracteristicas.fillna(0)
        
        # Calcular caída brusca
        df_ordenado = df.sort_values(['id_cliente', 'fecha'])
        ultimos_3 = df_ordenado.groupby('id_cliente').tail(90)
        consumo_reciente = ultimos_3.groupby('id_cliente')['consumo_kwh'].mean().reset_index()
        consumo_reciente.columns = ['id_cliente', 'consumo_reciente']
        caracteristicas = caracteristicas.merge(consumo_reciente, on='id_cliente', how='left')
        caracteristicas['consumo_reciente'] = caracteristicas['consumo_reciente'].fillna(0)
        caracteristicas['caida_brusca'] = (
            (caracteristicas['consumo_media'] - caracteristicas['consumo_reciente']) / 
            (caracteristicas['consumo_media'] + 0.01)
        )
        caracteristicas['caida_brusca'] = caracteristicas['caida_brusca'].clip(0, 1)
        
        registro.info(f"✅ {len(caracteristicas)} clientes procesados")
        return caracteristicas
    
    def extraer_alarmas(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extrae características de alarmas"""
        registro.info("🔔 Extrayendo características de alarmas...")
        
        if 'id_cliente' not in df.columns:
            registro.warning("⚠️ No se encontró columna id_cliente")
            return pd.DataFrame()
        
        caracteristicas = df.groupby('id_cliente').agg({
            'tipo_alarma': 'count',
            'gravedad': lambda x: (x == 'Alta').sum() + (x == 'Crítica').sum()
        }).reset_index()
        caracteristicas.columns = ['id_cliente', 'total_alarmas', 'alarmas_criticas']
        
        if 'tipo_alarma' in df.columns:
            tipos = pd.get_dummies(df['tipo_alarma']).groupby(df['id_cliente']).sum().reset_index()
            tipos.columns = ['id_cliente'] + [f'alarma_{col.lower().replace(" ", "_")}' for col in tipos.columns[1:]]
            caracteristicas = caracteristicas.merge(tipos, on='id_cliente', how='left')
        
        caracteristicas = caracteristicas.fillna(0)
        registro.info(f"✅ {len(caracteristicas)} clientes procesados")
        return caracteristicas
    
    def extraer_facturacion(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extrae características de facturación"""
        registro.info("💰 Extrayendo características de facturación...")
        
        if 'id_cliente' not in df.columns:
            registro.warning("⚠️ No se encontró columna id_cliente")
            return pd.DataFrame()
        
        caracteristicas = df.groupby('id_cliente').agg({
            'monto_total': 'sum',
            'monto_pagado': 'sum',
            'estado_pago': lambda x: (x == 'Vencido').sum()
        }).reset_index()
        caracteristicas.columns = ['id_cliente', 'deuda_total', 'total_pagado', 'facturas_vencidas']
        caracteristicas['ratio_pago'] = caracteristicas['total_pagado'] / (caracteristicas['deuda_total'] + 0.01)
        
        if 'dias_mora' in df.columns:
            mora = df.groupby('id_cliente')['dias_mora'].mean().reset_index()
            mora.columns = ['id_cliente', 'dias_mora_promedio']
            caracteristicas = caracteristicas.merge(mora, on='id_cliente', how='left')
        
        caracteristicas = caracteristicas.fillna(0)
        registro.info(f"✅ {len(caracteristicas)} clientes procesados")
        return caracteristicas
    
    def extraer_todas(self, consumo: pd.DataFrame, 
                      alarmas: pd.DataFrame = None,
                      facturacion: pd.DataFrame = None) -> pd.DataFrame:
        """Extrae todas las características y las combina"""
        registro.info("📊 Extrayendo todas las características...")
        
        if consumo.empty:
            registro.error("❌ No hay datos de consumo para extraer características")
            return pd.DataFrame()
        
        caracteristicas = self.extraer_consumo(consumo)
        
        if alarmas is not None and not alarmas.empty:
            alarmas_feat = self.extraer_alarmas(alarmas)
            caracteristicas = caracteristicas.merge(alarmas_feat, on='id_cliente', how='left')
        
        if facturacion is not None and not facturacion.empty:
            facturacion_feat = self.extraer_facturacion(facturacion)
            caracteristicas = caracteristicas.merge(facturacion_feat, on='id_cliente', how='left')
        
        caracteristicas = caracteristicas.fillna(0)
        registro.info(f"✅ Características extraídas: {len(caracteristicas)} clientes")
        return caracteristicas