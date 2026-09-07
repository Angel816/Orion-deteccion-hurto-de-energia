# src/datos/limpiador.py
"""
Limpieza automática de datos para Orion
"""

import pandas as pd
from typing import Dict
from src.utilidades.registrador import registro

class LimpiadorDatos:
    """
    Limpia datos automáticamente antes del procesamiento
    """
    
    def __init__(self):
        self.config = {
            'metodo_nulos': 'mediana',
            'metodo_outliers': 'winsorizar',
            'cuantil_outliers': 0.01,
            'eliminar_negativos': True
        }
        registro.info("🧹 Limpiador de datos inicializado")
    
    def limpiar_consumo(self, df: pd.DataFrame) -> pd.DataFrame:
        registro.info("🧹 Limpiando datos de consumo...")
        df_limpio = df.copy()
        n_registros = len(df_limpio)
        
        if 'consumo_kwh' in df_limpio.columns:
            nulos = df_limpio['consumo_kwh'].isnull().sum()
            if nulos > 0:
                if self.config['metodo_nulos'] == 'mediana':
                    valor_relleno = df_limpio['consumo_kwh'].median()
                else:
                    valor_relleno = df_limpio['consumo_kwh'].mean()
                df_limpio['consumo_kwh'] = df_limpio['consumo_kwh'].fillna(valor_relleno)
                registro.info(f"   📊 {nulos} valores nulos imputados")
        
        if 'consumo_kwh' in df_limpio.columns and len(df_limpio) > 10:
            if self.config['metodo_outliers'] == 'winsorizar':
                inferior = df_limpio['consumo_kwh'].quantile(self.config['cuantil_outliers'])
                superior = df_limpio['consumo_kwh'].quantile(1 - self.config['cuantil_outliers'])
                original_max = df_limpio['consumo_kwh'].max()
                df_limpio['consumo_kwh'] = df_limpio['consumo_kwh'].clip(inferior, superior)
                if original_max > superior:
                    registro.info(f"   📊 Outliers limitados: max {original_max:.0f} → {superior:.0f}")
        
        if self.config['eliminar_negativos'] and 'consumo_kwh' in df_limpio.columns:
            negativos = (df_limpio['consumo_kwh'] < 0).sum()
            if negativos > 0:
                df_limpio.loc[df_limpio['consumo_kwh'] < 0, 'consumo_kwh'] = 0
                registro.info(f"   📊 {negativos} valores negativos → 0")
        
        if 'fecha' in df_limpio.columns:
            try:
                df_limpio['fecha'] = pd.to_datetime(df_limpio['fecha'])
            except Exception as e:
                registro.warning(f"   ⚠️ No se pudieron estandarizar fechas: {e}")
        
        if 'id_cliente' in df_limpio.columns and 'fecha' in df_limpio.columns:
            duplicados = df_limpio.duplicated(subset=['id_cliente', 'fecha']).sum()
            if duplicados > 0:
                df_limpio = df_limpio.drop_duplicates(subset=['id_cliente', 'fecha'])
                registro.info(f"   🗑️ {duplicados} registros duplicados eliminados")
        
        registros_limpios = len(df_limpio)
        registro.info(f"✅ Datos de consumo limpios: {registros_limpios} registros ({(registros_limpios/n_registros)*100:.1f}%)")
        return df_limpio
    
    def limpiar_alarmas(self, df: pd.DataFrame) -> pd.DataFrame:
        registro.info("🧹 Limpiando datos de alarmas...")
        df_limpio = df.copy()
        
        if 'tipo_alarma' in df_limpio.columns:
            mapa_alarmas = {
                'Tapa Abierta': ['Tapa Abierta', 'TAPA', 'Apertura'],
                'Precinto Roto': ['Precinto Roto', 'PRECINTO', 'Roto'],
                'Consumo Cero': ['Consumo Cero', 'CERO'],
                'Error Comunicación': ['Error Comunicación', 'ERROR', 'COM'],
                'Caída Brusca': ['Caída Brusca', 'CAIDA', 'BRUSCA'],
                'Bypass Detectado': ['Bypass', 'BYPASS', 'BY'],
                'Magneto Detectado': ['Magneto', 'MAGNETO', 'IMAN']
            }
            for estandar, variantes in mapa_alarmas.items():
                df_limpio.loc[df_limpio['tipo_alarma'].isin(variantes), 'tipo_alarma'] = estandar
        
        if 'gravedad' in df_limpio.columns:
            mapa_gravedad = {
                'Baja': ['Baja', 'BAJA', 'B'],
                'Media': ['Media', 'MEDIA', 'M'],
                'Alta': ['Alta', 'ALTA', 'A'],
                'Crítica': ['Crítica', 'CRITICA', 'C']
            }
            for estandar, variantes in mapa_gravedad.items():
                df_limpio.loc[df_limpio['gravedad'].isin(variantes), 'gravedad'] = estandar
        
        if 'fecha' in df_limpio.columns:
            try:
                df_limpio['fecha'] = pd.to_datetime(df_limpio['fecha'])
            except:
                pass
        
        registro.info(f"✅ Datos de alarmas limpios: {len(df_limpio)} registros")
        return df_limpio
    
    def limpiar_clientes(self, df: pd.DataFrame) -> pd.DataFrame:
        registro.info("🧹 Limpiando datos de clientes...")
        df_limpio = df.copy()
        
        if 'tipo_cliente' in df_limpio.columns:
            mapa_tipos = {
                'Residencial': ['Residencial', 'RES', 'Res', 'R'],
                'Comercial': ['Comercial', 'COM', 'Com', 'C'],
                'Industrial': ['Industrial', 'IND', 'Ind', 'I'],
                'Restaurante': ['Restaurante', 'REST'],
                'Fabrica': ['Fabrica', 'FAB']
            }
            for estandar, variantes in mapa_tipos.items():
                df_limpio.loc[df_limpio['tipo_cliente'].isin(variantes), 'tipo_cliente'] = estandar
        
        if 'sector' in df_limpio.columns:
            df_limpio['sector'] = df_limpio['sector'].str.strip().str.title()
        
        if 'id_cliente' in df_limpio.columns:
            duplicados = df_limpio.duplicated(subset=['id_cliente']).sum()
            if duplicados > 0:
                df_limpio = df_limpio.drop_duplicates(subset=['id_cliente'])
                registro.info(f"   🗑️ {duplicados} clientes duplicados eliminados")
        
        registro.info(f"✅ Datos de clientes limpios: {len(df_limpio)} registros")
        return df_limpio
    
    def limpiar_facturacion(self, df: pd.DataFrame) -> pd.DataFrame:
        registro.info("🧹 Limpiando datos de facturación...")
        df_limpio = df.copy()
        
        for col in ['monto_total', 'monto_pagado']:
            if col in df_limpio.columns:
                nulos = df_limpio[col].isnull().sum()
                if nulos > 0:
                    df_limpio[col] = df_limpio[col].fillna(0)
                    registro.info(f"   📊 {nulos} nulos en {col} → 0")
        
        if 'monto_total' in df_limpio.columns and 'monto_pagado' in df_limpio.columns:
            if 'monto_pendiente' not in df_limpio.columns:
                df_limpio['monto_pendiente'] = df_limpio['monto_total'] - df_limpio['monto_pagado']
        
        if 'estado_pago' in df_limpio.columns:
            mapa_estado = {
                'Pagado': ['Pagado', 'PAGADO', 'P', 'Pag'],
                'Pendiente': ['Pendiente', 'PENDIENTE', 'Pen'],
                'Vencido': ['Vencido', 'VENCIDO', 'V']
            }
            for estandar, variantes in mapa_estado.items():
                df_limpio.loc[df_limpio['estado_pago'].isin(variantes), 'estado_pago'] = estandar
        
        if 'fecha_vencimiento' in df_limpio.columns:
            try:
                df_limpio['fecha_vencimiento'] = pd.to_datetime(df_limpio['fecha_vencimiento'])
                hoy = pd.Timestamp.now()
                df_limpio['dias_mora'] = (hoy - df_limpio['fecha_vencimiento']).dt.days
                df_limpio.loc[df_limpio['dias_mora'] < 0, 'dias_mora'] = 0
            except:
                pass
        
        for col in ['fecha_emision', 'fecha_vencimiento']:
            if col in df_limpio.columns:
                try:
                    df_limpio[col] = pd.to_datetime(df_limpio[col])
                except:
                    pass
        
        registro.info(f"✅ Datos de facturación limpios: {len(df_limpio)} registros")
        return df_limpio
    
    def limpiar_todo(self, df: pd.DataFrame, tipo: str) -> pd.DataFrame:
        metodos = {
            'consumo': self.limpiar_consumo,
            'alarmas': self.limpiar_alarmas,
            'clientes': self.limpiar_clientes,
            'facturacion': self.limpiar_facturacion
        }
        
        metodo = metodos.get(tipo)
        if metodo is None:
            registro.warning(f"⚠️ Tipo '{tipo}' no reconocido. Devolviendo datos sin cambios.")
            return df
        
        return metodo(df)