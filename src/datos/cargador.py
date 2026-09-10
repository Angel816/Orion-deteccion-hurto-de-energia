# src/datos/cargador.py
"""
Carga incremental de datos para Orion
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import json
from typing import Optional, Dict, Any
from src.utilidades.registrador import registro
from src.utilidades.configuracion import configuracion
from src.utilidades.tiempo import ahora_peru, iso_peru

class CargadorIncremental:
    """
    Carga datos de forma incremental, solo archivos nuevos
    """
    
    def __init__(self):
        self.ruta_brutos = Path(configuracion.obtener('datos.ruta_brutos', 'datos/brutos'))
        self.ruta_procesados = Path(configuracion.obtener('datos.ruta_procesados', 'datos/procesados'))
        self.archivo_metadatos = self.ruta_procesados / 'metadatos_ingesta.json'
        
        self.ruta_brutos.mkdir(parents=True, exist_ok=True)
        self.ruta_procesados.mkdir(parents=True, exist_ok=True)
        
        self.metadatos = self._cargar_metadatos()
        
        registro.info("📂 Cargador incremental inicializado")
    
    def _cargar_metadatos(self) -> dict:
        if self.archivo_metadatos.exists():
            try:
                with open(self.archivo_metadatos, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self._crear_metadatos_default()
        return self._crear_metadatos_default()
    
    def _crear_metadatos_default(self) -> dict:
        return {
            'ultima_fecha': None,
            'ultimo_archivo': None,
            'procesados': 0,
            'archivos_procesados': {}
        }
    
    def _guardar_metadatos(self):
        with open(self.archivo_metadatos, 'w', encoding='utf-8') as f:
            json.dump(self.metadatos, f, indent=2, default=str)
    
    def cargar_archivos_nuevos(self, conjunto: str) -> pd.DataFrame:
        directorio = self.ruta_brutos / conjunto
        if not directorio.exists():
            registro.warning(f"⚠️ Directorio {directorio} no existe")
            return pd.DataFrame()
        
        archivos = sorted(directorio.glob('*.parquet'))
        
        if not archivos:
            registro.warning(f"⚠️ No hay archivos en {directorio}")
            return pd.DataFrame()
        
        archivos_procesados = self.metadatos.get('archivos_procesados', {})
        ultimo_archivo = archivos_procesados.get(conjunto)
        indice_inicio = 0
        
        if ultimo_archivo:
            for i, f in enumerate(archivos):
                if f.name == ultimo_archivo:
                    indice_inicio = i + 1
                    break
        
        archivos_nuevos = archivos[indice_inicio:]
        if not archivos_nuevos:
            registro.info(f"ℹ️ No hay archivos nuevos en {conjunto}")
            return pd.DataFrame()
        
        registro.info(f"📂 Cargando {len(archivos_nuevos)} archivos de {conjunto}")
        
        dataframes = []
        for f in archivos_nuevos:
            try:
                df = pd.read_parquet(f)
                dataframes.append(df)
                registro.debug(f"   ✅ {f.name}: {len(df)} registros")
            except Exception as e:
                registro.error(f"   ❌ Error cargando {f.name}: {e}")
        
        if dataframes:
            resultado = pd.concat(dataframes, ignore_index=True)
            
            archivos_procesados[conjunto] = archivos_nuevos[-1].name
            self.metadatos['archivos_procesados'] = archivos_procesados
            self.metadatos['ultima_fecha'] = iso_peru()  # ← HORA PERÚ
            self.metadatos['procesados'] += len(resultado)
            self._guardar_metadatos()
            
            registro.info(f"✅ {len(resultado)} registros cargados de {conjunto}")
            return resultado
        
        return pd.DataFrame()
    
    def cargar_todos_los_archivos(self, conjunto: str) -> pd.DataFrame:
        directorio = self.ruta_brutos / conjunto
        if not directorio.exists():
            registro.warning(f"⚠️ Directorio {directorio} no existe")
            return pd.DataFrame()
        
        archivos = sorted(directorio.glob('*.parquet'))
        
        if not archivos:
            registro.warning(f"⚠️ No hay archivos en {directorio}")
            return pd.DataFrame()
        
        registro.info(f"📂 Cargando todos los archivos de {conjunto} ({len(archivos)} archivos)")
        
        dataframes = []
        for f in archivos:
            try:
                df = pd.read_parquet(f)
                dataframes.append(df)
                registro.debug(f"   ✅ {f.name}: {len(df)} registros")
            except Exception as e:
                registro.error(f"   ❌ Error cargando {f.name}: {e}")
        
        if dataframes:
            resultado = pd.concat(dataframes, ignore_index=True)
            registro.info(f"✅ {len(resultado)} registros cargados de {conjunto}")
            return resultado
        
        return pd.DataFrame()
    
    def cargar_muestra(self, conjunto: str) -> pd.DataFrame:
        ruta_muestra = Path(configuracion.obtener('datos.ruta_muestra', 'datos/muestra'))
        
        archivos_map = {
            'consumo': 'consumo_muestra.csv',
            'alarmas': 'alarmas_muestra.csv',
            'clientes': 'clientes_muestra.csv',
            'facturacion': 'facturacion_muestra.csv'
        }
        
        nombre_archivo = archivos_map.get(conjunto)
        if not nombre_archivo:
            registro.warning(f"⚠️ Conjunto '{conjunto}' no válido para muestra")
            return pd.DataFrame()
        
        archivo = ruta_muestra / nombre_archivo
        
        if not archivo.exists():
            registro.warning(f"⚠️ Archivo de muestra {archivo} no existe")
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(archivo)
            for col in df.columns:
                if 'fecha' in col.lower():
                    try:
                        df[col] = pd.to_datetime(df[col])
                    except:
                        pass
            registro.info(f"📂 Cargada muestra de {conjunto}: {len(df)} registros")
            return df
        except Exception as e:
            registro.error(f"❌ Error cargando muestra de {conjunto}: {e}")
            return pd.DataFrame()
    
    def verificar_disponibilidad(self, conjunto: str) -> Dict[str, Any]:
        directorio = self.ruta_brutos / conjunto
        
        if not directorio.exists():
            return {
                'disponible': False,
                'archivos': 0,
                'registros': 0,
                'mensaje': f"Directorio {directorio} no existe"
            }
        
        archivos = list(directorio.glob('*.parquet'))
        
        if not archivos:
            return {
                'disponible': False,
                'archivos': 0,
                'registros': 0,
                'mensaje': f"No hay archivos .parquet en {directorio}"
            }
        
        registros_totales = 0
        archivos_validos = 0
        for f in archivos:
            try:
                df = pd.read_parquet(f)
                registros_totales += len(df)
                archivos_validos += 1
            except Exception as e:
                registro.warning(f"⚠️ Error leyendo {f.name}: {e}")
        
        return {
            'disponible': True,
            'archivos': len(archivos),
            'archivos_validos': archivos_validos,
            'registros': registros_totales,
            'mensaje': f"{archivos_validos} archivos válidos, {registros_totales} registros"
        }
    
    def obtener_ultimo_archivo(self, conjunto: str) -> Optional[Path]:
        directorio = self.ruta_brutos / conjunto
        if not directorio.exists():
            return None
        
        archivos = list(directorio.glob('*.parquet'))
        if not archivos:
            return None
        
        archivos.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return archivos[0]
    
    def get_estado_ingesta(self) -> Dict[str, Any]:
        return {
            'ultima_fecha': self.metadatos.get('ultima_fecha'),
            'total_procesados': self.metadatos.get('procesados', 0),
            'archivos_procesados': self.metadatos.get('archivos_procesados', {}),
            'rutas': {
                'brutos': str(self.ruta_brutos),
                'procesados': str(self.ruta_procesados)
            }
        }
    
    def resetear_ingesta(self):
        self.metadatos = self._crear_metadatos_default()
        self._guardar_metadatos()
        registro.info("🔄 Metadatos de ingesta reseteados")