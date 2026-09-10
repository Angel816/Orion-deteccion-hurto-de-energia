# src/datos/normalizador.py
"""
Sistema de normalización de datos entrantes
Detecta automáticamente el formato y lo convierte al estándar Orion
Zona horaria: Perú (UTC-5)

Características:
- Detecta tipo de dato automáticamente
- Mapea columnas con nombres diferentes al estándar
- Normaliza fechas (múltiples formatos)
- Normaliza números (comas, puntos, símbolos)
- Estandariza textos (espacios, mayúsculas, tildes)
- Evita columnas duplicadas
- Maneja errores y valores faltantes
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import re
from typing import Dict, Any, Optional, List, Tuple
from src.utilidades.registrador import registro
from src.utilidades.tiempo import iso_peru


class NormalizadorDatos:
    """
    Normaliza datos entrantes al formato estándar de Orion
    """
    
    def __init__(self):
        # Mapeo de nombres de columnas comunes → estándar Orion
        self.mapeo_columnas = {
            # Consumo
            'consumo': 'consumo_kwh',
            'consumo_kwh': 'consumo_kwh',
            'kwh': 'consumo_kwh',
            'kw': 'consumo_kwh',
            'energia': 'consumo_kwh',
            'lectura': 'consumo_kwh',
            'valor': 'consumo_kwh',
            'consumo_facturado': 'consumo_kwh',
            'consumo_mensual': 'consumo_kwh',
            # Clientes
            'cliente': 'id_cliente',
            'id_cliente': 'id_cliente',
            'id': 'id_cliente',
            'codigo': 'id_cliente',
            'cod_cliente': 'id_cliente',
            'codigo_cliente': 'id_cliente',
            'cliente_id': 'id_cliente',
            'cod': 'id_cliente',
            # Fechas
            'fecha': 'fecha',
            'fecha_lectura': 'fecha',
            'fecha_consumo': 'fecha',
            'dia': 'fecha',
            'fecha_emision': 'fecha_emision',
            'fecha_factura': 'fecha_emision',
            'fecha_vencimiento': 'fecha_vencimiento',
            'fecha_venc': 'fecha_vencimiento',
            'fecha_inspeccion': 'fecha_inspeccion',
            'fecha_evento': 'fecha',
            'fecha_alarma': 'fecha',
            'fecha_pago': 'fecha_pago',
            # Alarmas
            'alarma': 'tipo_alarma',
            'tipo_alarma': 'tipo_alarma',
            'tipo': 'tipo_alarma',
            'evento': 'tipo_alarma',
            # Facturación
            'monto': 'monto_total',
            'monto_total': 'monto_total',
            'total': 'monto_total',
            'importe': 'monto_total',
            'importe_total': 'monto_total',
            'pagado': 'monto_pagado',
            'monto_pagado': 'monto_pagado',
            'estado': 'estado_pago',
            'estado_pago': 'estado_pago',
            # Otros
            'tipo_cliente': 'tipo_cliente',
            'sector': 'sector',
            'zona': 'sector',
            'potencia': 'potencia_contratada',
            'potencia_contratada': 'potencia_contratada',
            'potencia_kw': 'potencia_contratada',
            'tarifa': 'tarifa',
            'tarifa_codigo': 'tarifa',
            'gravedad': 'gravedad',
            'nivel': 'gravedad',
            'nombre': 'nombre',
            'razon_social': 'nombre',
            'tipo_lectura': 'tipo_lectura',
            'resultado': 'resultado',
            'tipo_irregularidad': 'tipo_irregularidad',
            'cnr': 'cnr_estimado',
            'cnr_estimado': 'cnr_estimado',
            'monto_recuperar': 'monto_recuperar',
            'inspector': 'inspector',
            'descripcion': 'descripcion',
            'precio_kwh': 'precio_kwh',
            'monto_pendiente': 'monto_pendiente',
            'dias_mora': 'dias_mora',
            'zona_riesgo': 'zona_riesgo',
            'estado_servicio': 'estado',
        }
        
        # Formatos de fecha comunes (incluye formato peruano)
        self.formatos_fecha = [
            '%Y-%m-%d',           # ISO: 2025-01-01
            '%d/%m/%Y',           # Peruano: 01/01/2025
            '%m/%d/%Y',           # Americano: 01/01/2025
            '%Y/%m/%d',           # ISO alternativo
            '%d-%m-%Y',           # Guión: 01-01-2025
            '%m-%d-%Y',           # Americano guión
            '%d.%m.%Y',           # Punto: 01.01.2025
            '%Y%m%d',             # Compacto: 20250101
            '%d-%b-%Y',           # 15-Jan-2025
            '%b %d, %Y',          # Jan 15, 2025
            '%d/%m/%y',           # Peruano corto: 01/01/25
            '%Y-%m-%d %H:%M:%S',  # ISO con hora
            '%d/%m/%Y %H:%M:%S'   # Peruano con hora
        ]
        
        # Columnas a excluir
        self.columnas_excluir = [
            'tiene_hurto', 'origen', 'Unnamed: 0', 'index',
            'level_0', 'tipo_irregularidad_debug', 'resultado_limpio'
        ]
        
        # Columnas numéricas
        self.columnas_numericas = [
            'consumo_kwh', 'monto_total', 'monto_pagado', 'potencia_contratada',
            'cnr_estimado', 'monto_recuperar', 'precio_kwh', 'monto_pendiente',
            'dias_mora', 'impacto_economico', 'historial', 'probabilidad',
            'puntaje_prioridad', 'consumo_promedio', 'consumo_std'
        ]
        
        # Columnas de texto
        self.columnas_texto = [
            'tipo_cliente', 'sector', 'tipo_alarma', 'estado_pago',
            'gravedad', 'tipo_lectura', 'resultado', 'tipo_irregularidad',
            'tipo_documento', 'estado', 'tarifa', 'inspector', 'nombre',
            'descripcion', 'zona_riesgo'
        ]
        
        registro.info("📋 Normalizador de datos inicializado")
    
    # ============================================================
    # DETECCIÓN DE TIPO DE DATO
    # ============================================================
    
    def detectar_tipo_dato(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detecta qué tipo de datos contiene el DataFrame
        """
        columnas = df.columns.tolist()
        columnas_lower = [str(c).lower().strip() for c in columnas]
        
        keywords = {
            'consumo': ['consumo', 'kwh', 'kw', 'lectura', 'energia', 'valor'],
            'clientes': ['cliente', 'nombre', 'tipo_cliente', 'sector', 'tarifa', 'potencia'],
            'alarmas': ['alarma', 'evento', 'gravedad', 'nivel'],
            'facturacion': ['monto', 'pago', 'factura', 'total', 'estado', 'importe'],
            'inspecciones': ['resultado', 'tipo_irregularidad', 'cnr', 'inspector']
        }
        
        puntajes = {tipo: 0 for tipo in keywords.keys()}
        
        for tipo, palabras in keywords.items():
            for col in columnas_lower:
                for palabra in palabras:
                    if palabra in col:
                        puntajes[tipo] += 1
        
        # Normalizar puntajes
        for tipo in puntajes:
            puntajes[tipo] = puntajes[tipo] / len(columnas) if columnas else 0
        
        # Prioridad especial para inspecciones
        if puntajes['inspecciones'] > 0:
            # Si tiene resultado O tipo_irregularidad, es inspecciones
            if any('resultado' in c for c in columnas_lower):
                tipo_principal = 'inspecciones'
            elif any('tipo_irregularidad' in c for c in columnas_lower):
                tipo_principal = 'inspecciones'
            else:
                tipo_principal = max(puntajes, key=puntajes.get)
        else:
            tipo_principal = max(puntajes, key=puntajes.get)
        
        # Si no hay coincidencia, inferir por estructura
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
        """
        Infiere el tipo por estructura del DataFrame
        """
        columnas = df.columns.tolist()
        n_rows = len(df)
        
        # Si tiene pocas columnas y muchas filas, probablemente es consumo
        if len(columnas) <= 4 and n_rows > 100:
            return 'consumo'
        
        # Si tiene columnas de fechas y montos, probablemente es facturación
        for col in columnas:
            if 'monto' in str(col).lower() or 'total' in str(col).lower():
                if 'fecha' in ' '.join([str(c) for c in columnas]).lower():
                    return 'facturacion'
        
        # Si tiene tipo cliente, es clientes
        for col in columnas:
            if 'tipo_cliente' in str(col).lower() or 'cliente' in str(col).lower():
                return 'clientes'
        
        # Si tiene alarmas o eventos, es alarmas
        for col in columnas:
            if 'alarma' in str(col).lower() or 'evento' in str(col).lower():
                return 'alarmas'
        
        return 'consumo'  # Por defecto
    
    # ============================================================
    # MAPEO DE COLUMNAS (EVITA DUPLICADOS)
    # ============================================================
    
    def _mapear_columnas(self, df: pd.DataFrame, tipo: str) -> Dict[str, str]:
        """
        Mapea columnas al estándar Orion
        IMPORTANTE: Solo mapea cada columna estándar UNA VEZ
        """
        columnas = df.columns.tolist()
        mapeo = {}
        columnas_ya_mapeadas = set()
        
        mapeos_especificos = {
            'consumo': {
                'id_cliente': ['cliente', 'id_cliente', 'id', 'codigo', 'cod_cliente', 'cliente_id'],
                'fecha': ['fecha', 'fecha_lectura', 'fecha_consumo', 'dia', 'fecha_lectura'],
                'consumo_kwh': ['consumo', 'consumo_kwh', 'kwh', 'kw', 'energia', 'lectura', 'valor'],
                'tipo_lectura': ['tipo_lectura']
            },
            'clientes': {
                'id_cliente': ['cliente', 'id_cliente', 'id', 'codigo', 'cod_cliente', 'codigo_cliente'],
                'nombre': ['nombre', 'razon_social'],
                'tipo_cliente': ['tipo_cliente', 'tipo'],
                'sector': ['sector', 'zona'],
                'potencia_contratada': ['potencia', 'potencia_contratada', 'potencia_kw'],
                'tarifa': ['tarifa', 'tarifa_codigo']
            },
            'alarmas': {
                'id_cliente': ['cliente', 'id_cliente', 'id', 'codigo', 'cliente_id'],
                'fecha': ['fecha', 'fecha_alarma', 'fecha_evento'],
                'tipo_alarma': ['alarma', 'tipo_alarma', 'tipo', 'evento'],
                'gravedad': ['gravedad', 'nivel']
            },
            'facturacion': {
                'id_cliente': ['cliente', 'id_cliente', 'id', 'codigo', 'cliente_id'],
                'fecha_emision': ['fecha_emision', 'fecha_factura'],
                'fecha_vencimiento': ['fecha_vencimiento', 'fecha_venc'],
                'monto_total': ['monto', 'monto_total', 'total', 'importe', 'importe_total'],
                'monto_pagado': ['pagado', 'monto_pagado'],
                'estado_pago': ['estado', 'estado_pago'],
                'consumo_kwh': ['consumo', 'consumo_kwh', 'consumo_facturado']
            },
            'inspecciones': {
                'id_cliente': ['cliente', 'id_cliente', 'id', 'codigo', 'cliente_id'],
                'fecha_inspeccion': ['fecha_inspeccion', 'fecha'],
                'resultado': ['resultado'],
                'tipo_irregularidad': ['tipo_irregularidad'],
                'descripcion': ['descripcion'],
                'cnr_estimado': ['cnr', 'cnr_estimado'],
                'monto_recuperar': ['monto_recuperar'],
                'inspector': ['inspector']
            }
        }
        
        especifico = mapeos_especificos.get(tipo, {})
        
        # Mapear columnas específicas del tipo
        for columna_estandar, posibles in especifico.items():
            if columna_estandar in columnas_ya_mapeadas:
                continue
            
            for col in columnas:
                if col in mapeo:
                    continue
                
                col_lower = str(col).lower().strip()
                for posible in posibles:
                    if posible == col_lower or posible in col_lower:
                        mapeo[col] = columna_estandar
                        columnas_ya_mapeadas.add(columna_estandar)
                        break
                
                if columna_estandar in columnas_ya_mapeadas:
                    break
        
        # Mapear columnas restantes con el mapeo general
        for col in columnas:
            if col not in mapeo:
                col_lower = str(col).lower().strip()
                for original, estandar in self.mapeo_columnas.items():
                    if estandar in columnas_ya_mapeadas:
                        continue
                    if original == col_lower or original in col_lower:
                        mapeo[col] = estandar
                        columnas_ya_mapeadas.add(estandar)
                        break
        
        return mapeo
    
    # ============================================================
    # NORMALIZACIÓN DE FECHAS
    # ============================================================
    
    def normalizar_fechas(self, df: pd.DataFrame, columna: str) -> pd.Series:
        """
        Normaliza fechas a datetime (maneja múltiples formatos y errores)
        """
        def parse_fecha(valor):
            if pd.isna(valor):
                return pd.NaT
            
            if isinstance(valor, (pd.Timestamp, datetime)):
                return valor
            
            valor_str = str(valor).strip()
            
            # Si está vacío o es texto inválido
            if valor_str == '' or valor_str.lower() in ['n/a', 'na', 'pendiente', 'sin fecha', 'no definido', 'nan', 'none']:
                return pd.NaT
            
            # Intentar con formatos comunes
            for formato in self.formatos_fecha:
                try:
                    return datetime.strptime(valor_str, formato)
                except:
                    continue
            
            # Intentar con pandas (más flexible)
            try:
                return pd.to_datetime(valor_str, errors='coerce')
            except:
                return pd.NaT
        
        return df[columna].apply(parse_fecha)
    
    # ============================================================
    # NORMALIZACIÓN DE NÚMEROS
    # ============================================================
    
    def normalizar_numeros(self, df: pd.DataFrame, columna: str) -> pd.Series:
        """
        Normaliza números (maneja comas, puntos, símbolos, textos)
        """
        def parse_numero(valor):
            if pd.isna(valor):
                return np.nan
            
            if isinstance(valor, (int, float)):
                return float(valor)
            
            valor_str = str(valor).strip()
            
            # Si está vacío o es texto inválido
            if valor_str == '' or valor_str.lower() in ['n/a', 'na', 'pendiente', 'sin dato', 'error', 'nan', 'none']:
                return np.nan
            
            # Limpiar símbolos de moneda y letras
            valor_str = re.sub(r'[S\/\$]', '', valor_str)
            valor_str = valor_str.strip()
            
            # Manejar formato peruano (1,234.56) vs europeo (1.234,56)
            if ',' in valor_str and '.' in valor_str:
                # Si la coma está antes del punto, es formato peruano
                if valor_str.index(',') < valor_str.index('.'):
                    valor_str = valor_str.replace(',', '')
                else:
                    valor_str = valor_str.replace('.', '').replace(',', '.')
            elif ',' in valor_str:
                # Solo coma: podría ser decimal o miles
                partes = valor_str.split(',')
                if len(partes[-1]) == 2:  # 2 decimales
                    valor_str = valor_str.replace(',', '.')
                else:
                    valor_str = valor_str.replace(',', '')
            
            # Limpiar cualquier otro caracter no numérico
            valor_str = re.sub(r'[^\d.\-]', '', valor_str)
            
            try:
                return float(valor_str)
            except:
                return np.nan
        
        return df[columna].apply(parse_numero)
    
    # ============================================================
    # NORMALIZACIÓN PRINCIPAL
    # ============================================================
    
    def normalizar(self, df: pd.DataFrame, tipo: Optional[str] = None) -> Tuple[pd.DataFrame, Dict]:
        """
        Normaliza un DataFrame completo al formato Orion
        """
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
        
        # ============================================================
        # 1. DETECTAR TIPO
        # ============================================================
        
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
        
        # ============================================================
        # 2. RENOMBRAR COLUMNAS (evitando duplicados)
        # ============================================================
        
        if mapeo:
            df_normalizado = df_normalizado.rename(columns=mapeo)
            reporte['cambios'].append(f"Renombradas {len(mapeo)} columnas")
        
        # Eliminar columnas duplicadas (conservar la primera)
        if df_normalizado.columns.duplicated().any():
            duplicados = df_normalizado.columns[df_normalizado.columns.duplicated()].tolist()
            df_normalizado = df_normalizado.loc[:, ~df_normalizado.columns.duplicated()]
            reporte['advertencias'].append(f"Columnas duplicadas eliminadas: {duplicados}")
        
        # ============================================================
        # 3. ELIMINAR COLUMNAS NO DESEADAS
        # ============================================================
        
        for col in self.columnas_excluir:
            if col in df_normalizado.columns:
                df_normalizado = df_normalizado.drop(columns=[col])
                reporte['cambios'].append(f"Columna eliminada: {col}")
        
        # ============================================================
        # 4. NORMALIZAR FECHAS
        # ============================================================
        
        for col in df_normalizado.columns:
            if 'fecha' in col.lower():
                try:
                    df_normalizado[col] = self.normalizar_fechas(df_normalizado, col)
                    n_validas = df_normalizado[col].notna().sum()
                    n_invalidas = df_normalizado[col].isna().sum()
                    reporte['cambios'].append(f"Fechas normalizadas: {col} ({n_validas} válidas, {n_invalidas} inválidas)")
                except Exception as e:
                    reporte['errores'].append(f"Error normalizando fechas en {col}: {e}")
        
        # ============================================================
        # 5. NORMALIZAR NÚMEROS
        # ============================================================
        
        for col in self.columnas_numericas:
            if col in df_normalizado.columns:
                try:
                    df_normalizado[col] = self.normalizar_numeros(df_normalizado, col)
                    reporte['cambios'].append(f"Números normalizados: {col}")
                except Exception as e:
                    reporte['errores'].append(f"Error normalizando números en {col}: {e}")
        
        # ============================================================
        # 6. ESTANDARIZAR TEXTOS
        # ============================================================
        
        for col in self.columnas_texto:
            if col in df_normalizado.columns:
                try:
                    df_normalizado[col] = df_normalizado[col].apply(
                        lambda x: str(x).strip().title() if pd.notna(x) else x
                    )
                    reporte['cambios'].append(f"Textos estandarizados: {col}")
                except Exception as e:
                    reporte['errores'].append(f"Error estandarizando textos en {col}: {e}")
        
        # ============================================================
        # 7. VALIDAR COLUMNAS REQUERIDAS
        # ============================================================
        
        requeridas_por_tipo = {
            'consumo': ['id_cliente', 'fecha', 'consumo_kwh'],
            'clientes': ['id_cliente'],
            'alarmas': ['id_cliente', 'fecha', 'tipo_alarma'],
            'facturacion': ['id_cliente', 'fecha_emision', 'monto_total'],
            'inspecciones': ['id_cliente']
        }
        
        requeridas = requeridas_por_tipo.get(tipo, [])
        for col in requeridas:
            if col not in df_normalizado.columns:
                reporte['errores'].append(f"Columna requerida faltante: {col}")
        
        # ============================================================
        # 8. VERIFICACIÓN FINAL DE DUPLICADOS
        # ============================================================
        
        if df_normalizado.columns.duplicated().any():
            duplicados = df_normalizado.columns[df_normalizado.columns.duplicated()].tolist()
            df_normalizado = df_normalizado.loc[:, ~df_normalizado.columns.duplicated()]
            reporte['advertencias'].append(f"Columnas duplicadas finales eliminadas: {duplicados}")
        
        # ============================================================
        # 9. RESUMEN FINAL
        # ============================================================
        
        reporte['final'] = {
            'columnas': df_normalizado.columns.tolist(),
            'n_rows': len(df_normalizado),
            'timestamp': iso_peru()
        }
        
        registro.info(f"✅ Normalización completada: {tipo} - {len(df_normalizado)} registros")
        
        return df_normalizado, reporte