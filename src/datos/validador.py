# src/datos/validador.py
"""
Sistema de validación de calidad de datos
Zona horaria: Perú (UTC-5)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from src.utilidades.registrador import registro
from src.utilidades.tiempo import iso_peru


class ValidadorDatos:
    """
    Valida la calidad de los datos antes de procesarlos
    """
    
    def __init__(self):
        self.esquemas = {
            'consumo': {
                'requeridas': ['id_cliente', 'fecha', 'consumo_kwh'],
                'numericas': ['consumo_kwh'],
                'fechas': ['fecha'],
                'rangos': {'consumo_kwh': (0, 10000)},
                'umbral_nulos': 0.05
            },
            'alarmas': {
                'requeridas': ['id_cliente', 'fecha', 'tipo_alarma'],
                'fechas': ['fecha'],
                'umbral_nulos': 0.10
            },
            'clientes': {
                'requeridas': ['id_cliente', 'tipo_cliente'],
                'umbral_nulos': 0.05
            },
            'facturacion': {
                'requeridas': ['id_cliente', 'fecha_emision', 'monto_total'],
                'numericas': ['monto_total'],
                'fechas': ['fecha_emision'],
                'rangos': {'monto_total': (0, 50000)},
                'umbral_nulos': 0.05
            }
        }
        
        registro.info("🔍 Validador de datos inicializado")
    
    def validar(self, df: pd.DataFrame, conjunto: str) -> Dict[str, Any]:
        """Valida un DataFrame contra el esquema correspondiente"""
        esquema = self.esquemas.get(conjunto, {})
        errores = []
        advertencias = []
        
        for col in esquema.get('requeridas', []):
            if col not in df.columns:
                errores.append(f"Columna requerida faltante: {col}")
        
        if errores:
            return {
                'estado': 'rechazado',
                'errores': errores,
                'advertencias': advertencias,
                'n_filas': len(df),
                'timestamp': iso_peru()  # ← HORA PERÚ
            }
        
        for col in esquema.get('numericas', []):
            if col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col])
                except:
                    advertencias.append(f"Columna {col} no es numérica")
        
        for col in esquema.get('fechas', []):
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col])
                except:
                    advertencias.append(f"Columna {col} no es fecha válida")
        
        for col, (min_val, max_val) in esquema.get('rangos', {}).items():
            if col in df.columns:
                fuera = df[(df[col] < min_val) | (df[col] > max_val)]
                if len(fuera) > 0:
                    advertencias.append(f"{len(fuera)} valores fuera de rango en {col}: [{min_val}, {max_val}]")
        
        for col in esquema.get('requeridas', []):
            if col in df.columns:
                nulos = df[col].isnull().sum()
                if nulos > 0:
                    errores.append(f"{nulos} valores nulos en columna crítica: {col}")
        
        if 'id_cliente' in df.columns and 'fecha' in df.columns:
            duplicados = df.duplicated(subset=['id_cliente', 'fecha']).sum()
            if duplicados > 0:
                advertencias.append(f"{duplicados} registros duplicados (id_cliente + fecha)")
        
        estado = 'rechazado' if errores else ('advertencia' if advertencias else 'aceptado')
        
        return {
            'estado': estado,
            'errores': errores,
            'advertencias': advertencias,
            'n_filas': len(df),
            'timestamp': iso_peru()  # ← HORA PERÚ
        }
    
    def generar_reporte_calidad(self, df: pd.DataFrame, conjunto: str) -> Dict[str, Any]:
        """Genera un reporte completo de calidad de datos"""
        validacion = self.validar(df, conjunto)
        
        estadisticas = {
            'n_filas': len(df),
            'n_columnas': len(df.columns),
            'nulos': df.isnull().sum().to_dict(),
            'tipos': df.dtypes.astype(str).to_dict()
        }
        
        return {
            'conjunto': conjunto,
            'timestamp': iso_peru(),  # ← HORA PERÚ
            'validacion': validacion,
            'estadisticas': estadisticas
        }