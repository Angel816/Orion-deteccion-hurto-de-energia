# src/datos/normalizador.py
"""
Sistema de normalización de datos entrantes
Detecta automáticamente el formato y lo convierte al estándar Orion
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import re
from typing import Dict, Any, Optional, List, Tuple
from src.utilidades.registrador import registro

class NormalizadorDatos:
    """
    Normaliza datos entrantes al formato estándar de Orion
    """
    
    def __init__(self):
        # Mapeo de nombres de columnas comunes → estándar Orion
        self.mapeo_columnas = {
            'consumo': 'consumo_kwh',
            'consumo_kwh': 'consumo_kwh',
            'kwh': 'consumo_kwh',
            'kw': 'consumo_kwh',
            'energia': 'consumo_kwh',
            'lectura': 'consumo_kwh',
            'valor': 'consumo_kwh',
            'cliente': 'id_cliente',
            'id_cliente': 'id_cliente',
            'id': 'id_cliente',
            'codigo': 'id_cliente',
            'cod_cliente': 'id_cliente',
            'fecha': 'fecha',
            'fecha_lectura': 'fecha',
            'fecha_consumo': 'fecha',
            'dia': 'fecha',
            'fecha_emision': 'fecha_emision',
            'fecha_vencimiento': 'fecha_vencimiento',
            'fecha_inspeccion': 'fecha_inspeccion',
            'alarma': 'tipo_alarma',
            'tipo_alarma': 'tipo_alarma',
            'tipo': 'tipo_alarma',
            'evento': 'tipo_alarma',
            'monto': 'monto_total',
            'monto_total': 'monto_total',
            'total': 'monto_total',
            'importe': 'monto_total',
            'pagado': 'monto_pagado',
            'estado': 'estado_pago',
            'estado_pago': 'estado_pago',
            'tipo_cliente': 'tipo_cliente',
            'sector': 'sector',
            'potencia': 'potencia_contratada',
            'potencia_contratada': 'potencia_contratada',
            'tarifa': 'tarifa',
            'gravedad': 'gravedad'
        }
        
        self.formatos_fecha = [
            '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d',
            '%d-%m-%Y', '%m-%d-%Y', '%d.%m.%Y', '%Y%m%d',
            '%d-%b-%Y', '%b %d, %Y'
        ]
        
        registro.info("📋 Normalizador de datos inicializado")
    
    def detectar_tipo_dato(self, df: pd.DataFrame) -> Dict[str, Any]:
        columnas = df.columns.tolist()
        columnas_lower = [c.lower() for c in columnas]
        
        keywords = {
            'consumo': ['consumo', 'kwh', 'kw', 'lectura', 'energia', 'valor'],
            'clientes': ['cliente', 'nombre', 'tipo_cliente', 'sector', 'tarifa'],
            'alarmas': ['alarma', 'evento', 'gravedad'],
            'facturacion': ['monto', 'pago', 'factura', 'total', 'estado']
        }
        
        puntajes = {tipo: 0 for tipo in keywords.keys()}
        
        for tipo, palabras in keywords.items():
            for col in columnas_lower:
                for palabra in palabras:
                    if palabra in col:
                        puntajes[tipo] += 1
        
        for tipo in puntajes:
            puntajes[tipo] = puntajes[tipo] / len(columnas) if columnas else 0
        
        tipo_principal = max(puntajes, key=puntajes.get)
        
        if puntajes[tipo_principal] == 0:
            tipo_principal = self._inferir_por_estructura(df)
        
        mapeo = self._mapear_columnas(df, tipo_principal)
        
        return {
            'tipo': tipo_principal,
            'puntajes': puntajes,
            'mapeo': mapeo,
            'columnas_originales': columnas
        }
    
    def _inferir_por_estructura(self, df: pd.DataFrame) -> str:
        columnas = df.columns.tolist()
        n_rows = len(df)
        
        if len(columnas) <= 3 and n_rows > 100:
            return 'consumo'
        
        for col in columnas:
            if 'monto' in col.lower() or 'total' in col.lower():
                if 'fecha' in ' '.join(columnas).lower():
                    return 'facturacion'
        
        for col in columnas:
            if 'tipo_cliente' in col.lower() or 'cliente' in col.lower():
                return 'clientes'
        
        for col in columnas:
            if 'alarma' in col.lower() or 'evento' in col.lower():
                return 'alarmas'
        
        return 'consumo'
    
    def _mapear_columnas(self, df: pd.DataFrame, tipo: str) -> Dict[str, str]:
        columnas = df.columns.tolist()
        mapeo = {}
        
        mapeos_especificos = {
            'consumo': {
                'id_cliente': ['cliente', 'id_cliente', 'id', 'codigo', 'cod_cliente'],
                'fecha': ['fecha', 'fecha_lectura', 'fecha_consumo', 'dia'],
                'consumo_kwh': ['consumo', 'consumo_kwh', 'kwh', 'kw', 'energia', 'lectura', 'valor']
            },
            'clientes': {
                'id_cliente': ['cliente', 'id_cliente', 'id', 'codigo', 'cod_cliente'],
                'tipo_cliente': ['tipo_cliente', 'tipo'],
                'sector': ['sector', 'zona', 'distrito'],
                'potencia_contratada': ['potencia', 'potencia_contratada'],
                'tarifa': ['tarifa']
            },
            'alarmas': {
                'id_cliente': ['cliente', 'id_cliente', 'id', 'codigo'],
                'fecha': ['fecha', 'fecha_alarma', 'fecha_evento'],
                'tipo_alarma': ['alarma', 'tipo_alarma', 'tipo', 'evento'],
                'gravedad': ['gravedad']
            },
            'facturacion': {
                'id_cliente': ['cliente', 'id_cliente', 'id', 'codigo'],
                'fecha_emision': ['fecha_emision', 'fecha_factura'],
                'fecha_vencimiento': ['fecha_vencimiento', 'fecha_venc'],
                'monto_total': ['monto', 'monto_total', 'total', 'importe'],
                'monto_pagado': ['pagado', 'monto_pagado', 'abonado'],
                'estado_pago': ['estado', 'estado_pago']
            }
        }
        
        especifico = mapeos_especificos.get(tipo, {})
        
        for columna_estandar, posibles in especifico.items():
            for col in columnas:
                col_lower = col.lower()
                for posible in posibles:
                    if posible == col_lower or posible in col_lower:
                        mapeo[col] = columna_estandar
                        break
        
        for col in columnas:
            if col not in mapeo:
                col_lower = col.lower()
                for original, estandar in self.mapeo_columnas.items():
                    if original == col_lower or original in col_lower:
                        mapeo[col] = estandar
                        break
        
        return mapeo
    
    def normalizar_fechas(self, df: pd.DataFrame, columna: str) -> pd.Series:
        def parse_fecha(valor):
            if pd.isna(valor):
                return pd.NaT
            if isinstance(valor, (pd.Timestamp, datetime)):
                return valor
            valor_str = str(valor).strip()
            for formato in self.formatos_fecha:
                try:
                    return datetime.strptime(valor_str, formato)
                except:
                    continue
            try:
                return pd.to_datetime(valor_str)
            except:
                return pd.NaT
        
        return df[columna].apply(parse_fecha)
    
    def normalizar_numeros(self, df: pd.DataFrame, columna: str) -> pd.Series:
        def parse_numero(valor):
            if pd.isna(valor):
                return np.nan
            if isinstance(valor, (int, float)):
                return float(valor)
            valor_str = str(valor).strip()
            valor_str = re.sub(r'[^\d.,\-]', '', valor_str)
            valor_str = valor_str.replace(',', '.')
            try:
                return float(valor_str)
            except:
                return np.nan
        
        return df[columna].apply(parse_numero)
    
    def normalizar(self, df: pd.DataFrame, tipo: Optional[str] = None) -> Tuple[pd.DataFrame, Dict]:
        reporte = {
            'original': {
                'columnas': df.columns.tolist(),
                'n_rows': len(df)
            },
            'cambios': [],
            'errores': [],
            'advertencias': []
        }
        
        df_normalizado = df.copy()
        
        if tipo is None:
            deteccion = self.detectar_tipo_dato(df)
            tipo = deteccion['tipo']
            reporte['tipo_detectado'] = tipo
            reporte['puntajes'] = deteccion['puntajes']
            mapeo = deteccion['mapeo']
        else:
            mapeo = self._mapear_columnas(df, tipo)
            reporte['tipo_detectado'] = tipo
        
        reporte['mapeo_columnas'] = mapeo
        
        for col_original, col_nueva in mapeo.items():
            if col_original in df_normalizado.columns and col_original != col_nueva:
                df_normalizado = df_normalizado.rename(columns={col_original: col_nueva})
                reporte['cambios'].append(f"Renombrada: {col_original} → {col_nueva}")
        
        for col in df_normalizado.columns:
            if 'fecha' in col.lower():
                try:
                    df_normalizado[col] = self.normalizar_fechas(df_normalizado, col)
                    reporte['cambios'].append(f"Fechas normalizadas: {col}")
                except Exception as e:
                    reporte['errores'].append(f"Error normalizando fechas en {col}: {e}")
        
        columnas_numericas = ['consumo_kwh', 'monto_total', 'monto_pagado', 'potencia_contratada', 'cnr_estimado']
        for col in columnas_numericas:
            if col in df_normalizado.columns:
                try:
                    df_normalizado[col] = self.normalizar_numeros(df_normalizado, col)
                    reporte['cambios'].append(f"Números normalizados: {col}")
                except Exception as e:
                    reporte['errores'].append(f"Error normalizando números en {col}: {e}")
        
        columnas_texto = ['tipo_cliente', 'sector', 'tipo_alarma', 'estado_pago', 'gravedad']
        for col in columnas_texto:
            if col in df_normalizado.columns:
                try:
                    df_normalizado[col] = df_normalizado[col].astype(str).str.strip().str.title()
                    reporte['cambios'].append(f"Textos estandarizados: {col}")
                except Exception as e:
                    reporte['errores'].append(f"Error estandarizando textos en {col}: {e}")
        
        requeridas_por_tipo = {
            'consumo': ['id_cliente', 'fecha', 'consumo_kwh'],
            'clientes': ['id_cliente'],
            'alarmas': ['id_cliente', 'fecha', 'tipo_alarma'],
            'facturacion': ['id_cliente', 'fecha_emision']
        }
        
        requeridas = requeridas_por_tipo.get(tipo, [])
        for col in requeridas:
            if col not in df_normalizado.columns:
                reporte['errores'].append(f"Columna requerida faltante: {col}")
        
        df_normalizado['origen'] = 'normalizado'
        
        reporte['final'] = {
            'columnas': df_normalizado.columns.tolist(),
            'n_rows': len(df_normalizado)
        }
        
        registro.info(f"✅ Normalización completada: {tipo} - {len(df_normalizado)} registros")
        
        return df_normalizado, reporte