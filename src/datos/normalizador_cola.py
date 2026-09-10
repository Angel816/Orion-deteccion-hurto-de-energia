# src/datos/normalizador_cola.py
"""
Sistema de normalización de datos en cola con historial
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import json
import shutil
from typing import Dict, Any, Optional, Tuple
from src.utilidades.registrador import registro
from src.utilidades.tiempo import ahora_peru, timestamp_peru, iso_peru
from src.datos.normalizador import NormalizadorDatos

class NormalizadorCola:
    """
    Procesa archivos en cola, los normaliza y guarda en brutos + historial
    """
    
    def __init__(self):
        self.base_dir = Path('datos')
        self.cola_dir = self.base_dir / 'cola'
        self.pendientes_dir = self.cola_dir / 'pendientes'
        self.procesando_dir = self.cola_dir / 'procesando'
        self.errores_dir = self.cola_dir / 'errores'
        
        self.brutos_dir = self.base_dir / 'brutos'
        self.datos_pasados_dir = Path('datos_pasados')
        self.metadatos_dir = self.base_dir / 'metadatos'
        
        for dir_path in [self.pendientes_dir, self.procesando_dir, 
                        self.errores_dir, self.brutos_dir, 
                        self.datos_pasados_dir, self.metadatos_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        for sub in ['consumo', 'clientes', 'alarmas', 'facturacion']:
            (self.brutos_dir / sub).mkdir(parents=True, exist_ok=True)
            (self.datos_pasados_dir / sub).mkdir(parents=True, exist_ok=True)
        
        self.normalizador = NormalizadorDatos()
        registro.info("📋 Normalizador de cola con historial inicializado")
    
    def procesar_cola(self) -> Dict[str, Any]:
        resultados = {
            'total': 0,
            'procesados': 0,
            'errores': 0,
            'detalles': []
        }
        
        archivos = list(self.pendientes_dir.glob('*'))
        
        if not archivos:
            registro.info("ℹ️ No hay archivos en la cola de pendientes")
            return resultados
        
        registro.info(f"📂 {len(archivos)} archivos en la cola")
        
        for archivo in archivos:
            resultados['total'] += 1
            resultado = self._procesar_archivo(archivo)
            resultados['detalles'].append(resultado)
            
            if resultado['estado'] == 'exito':
                resultados['procesados'] += 1
            else:
                resultados['errores'] += 1
        
        registro.info(f"✅ Cola procesada: {resultados['procesados']} éxitos, {resultados['errores']} errores")
        return resultados
    
    def _procesar_archivo(self, archivo: Path) -> Dict[str, Any]:
        resultado = {
            'archivo': archivo.name,
            'estado': 'error',
            'mensaje': '',
            'tipo': None,
            'registros': 0,
            'destino_brutos': None,
            'destino_historial': None
        }
        
        try:
            destino_procesando = self.procesando_dir / archivo.name
            archivo.rename(destino_procesando)
            
            df, tipo = self._cargar_y_detectar(destino_procesando)
            
            if df is None:
                resultado['mensaje'] = "No se pudo cargar el archivo"
                self._mover_a_error(destino_procesando, resultado['mensaje'])
                return resultado
            
            resultado['tipo'] = tipo
            resultado['registros'] = len(df)
            
            df_normalizado, reporte = self.normalizador.normalizar(df, tipo)
            
            destino_brutos = self._guardar_en_brutos(df_normalizado, tipo, archivo.stem)
            resultado['destino_brutos'] = str(destino_brutos)
            
            destino_historial = self._guardar_en_historial(df_normalizado, tipo, archivo.stem)
            resultado['destino_historial'] = str(destino_historial)
            
            self._guardar_reporte(reporte, archivo.stem, tipo)
            
            destino_procesando.unlink()
            
            resultado['estado'] = 'exito'
            resultado['mensaje'] = f"Normalizado y guardado en brutos + historial"
            
            registro.info(f"✅ {archivo.name} → {tipo}: {len(df)} registros")
            
        except Exception as e:
            resultado['mensaje'] = str(e)
            registro.error(f"❌ Error procesando {archivo.name}: {e}")
            
            archivo_error = self.procesando_dir / archivo.name
            if archivo_error.exists():
                self._mover_a_error(archivo_error, str(e))
        
        return resultado
    
    def _cargar_y_detectar(self, archivo: Path) -> Tuple[Optional[pd.DataFrame], str]:
        try:
            if archivo.suffix == '.csv':
                df = pd.read_csv(archivo)
            elif archivo.suffix in ['.parquet', '.pqt']:
                df = pd.read_parquet(archivo)
            elif archivo.suffix in ['.xlsx', '.xls']:
                df = pd.read_excel(archivo)
            elif archivo.suffix == '.json':
                df = pd.read_json(archivo)
            else:
                return None, 'desconocido'
            
            deteccion = self.normalizador.detectar_tipo_dato(df)
            return df, deteccion['tipo']
            
        except Exception as e:
            registro.error(f"❌ Error cargando {archivo.name}: {e}")
            return None, 'desconocido'
    
    def _guardar_en_brutos(self, df: pd.DataFrame, tipo: str, nombre_base: str) -> Path:
        ts = timestamp_peru()  # ← HORA PERÚ
        nombre = f"{nombre_base}_{ts}.parquet"
        destino = self.brutos_dir / tipo / nombre
        df.to_parquet(destino, index=False)
        return destino
    
    def _guardar_en_historial(self, df: pd.DataFrame, tipo: str, nombre_base: str) -> Path:
        ts = timestamp_peru()  # ← HORA PERÚ
        nombre = f"{nombre_base}_{ts}.parquet"
        destino = self.datos_pasados_dir / tipo / nombre
        df.to_parquet(destino, index=False)
        return destino
    
    def _guardar_reporte(self, reporte: Dict, nombre_base: str, tipo: str):
        ts = timestamp_peru()  # ← HORA PERÚ
        nombre = f"normalizacion_{nombre_base}_{ts}.json"
        
        reporte['timestamp'] = iso_peru()  # ← HORA PERÚ
        reporte['archivo_original'] = nombre_base
        reporte['tipo'] = tipo
        
        destino = self.metadatos_dir / nombre
        with open(destino, 'w', encoding='utf-8') as f:
            json.dump(reporte, f, indent=2, default=str)
    
    def _mover_a_error(self, archivo: Path, motivo: str):
        destino = self.errores_dir / archivo.name
        archivo.rename(destino)
        
        error_file = self.errores_dir / f"{archivo.stem}_error.txt"
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write(f"Archivo: {archivo.name}\n")
            f.write(f"Fecha: {iso_peru()}\n")  # ← HORA PERÚ
            f.write(f"Error: {motivo}\n")
    
    def agregar_a_cola(self, ruta_archivo: Path) -> bool:
        if not ruta_archivo.exists():
            registro.error(f"❌ Archivo no encontrado: {ruta_archivo}")
            return False
        
        destino = self.pendientes_dir / ruta_archivo.name
        
        if destino.exists():
            ts = timestamp_peru()  # ← HORA PERÚ
            nuevo_nombre = f"{ruta_archivo.stem}_{ts}{ruta_archivo.suffix}"
            destino = self.pendientes_dir / nuevo_nombre
        
        shutil.copy2(ruta_archivo, destino)
        registro.info(f"📥 Archivo agregado a la cola: {destino.name}")
        return True
    
    def obtener_estado_cola(self) -> Dict[str, int]:
        return {
            'pendientes': len(list(self.pendientes_dir.glob('*'))),
            'procesando': len(list(self.procesando_dir.glob('*'))),
            'errores': len(list(self.errores_dir.glob('*')))
        }
    
    def obtener_estado_historial(self) -> Dict[str, int]:
        return {
            'consumo': len(list((self.datos_pasados_dir / 'consumo').glob('*.parquet'))),
            'clientes': len(list((self.datos_pasados_dir / 'clientes').glob('*.parquet'))),
            'alarmas': len(list((self.datos_pasados_dir / 'alarmas').glob('*.parquet'))),
            'facturacion': len(list((self.datos_pasados_dir / 'facturacion').glob('*.parquet')))
        }
    
    def limpiar_procesando(self):
        for archivo in self.procesando_dir.glob('*'):
            try:
                archivo.unlink()
            except:
                pass
        registro.info("🗑️ Carpeta de procesando limpiada")