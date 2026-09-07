# src/datos/cargador.py
"""
Carga incremental de datos para Orion
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import json
from src.utilidades.registrador import registro
from src.utilidades.configuracion import configuracion

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
            with open(self.archivo_metadatos, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'ultima_fecha': None,
            'ultimo_archivo': None,
            'procesados': 0
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
        
        ultimo_archivo = self.metadatos.get(f'ultimo_{conjunto}_archivo')
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
            
            self.metadatos[f'ultimo_{conjunto}_archivo'] = archivos_nuevos[-1].name
            self.metadatos['ultima_fecha'] = datetime.now().isoformat()
            self.metadatos['procesados'] += len(resultado)
            self._guardar_metadatos()
            
            registro.info(f"✅ {len(resultado)} registros cargados de {conjunto}")
            return resultado
        
        return pd.DataFrame()
    
    def cargar_muestra(self, conjunto: str) -> pd.DataFrame:
        ruta_muestra = Path(configuracion.obtener('datos.ruta_muestra', 'datos/muestra'))
        archivo = ruta_muestra / f"{conjunto}_muestra.csv"
        
        if not archivo.exists():
            registro.warning(f"⚠️ Archivo de muestra {archivo} no existe")
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(archivo)
            registro.info(f"📂 Cargada muestra de {conjunto}: {len(df)} registros")
            return df
        except Exception as e:
            registro.error(f"❌ Error cargando muestra de {conjunto}: {e}")
            return pd.DataFrame()