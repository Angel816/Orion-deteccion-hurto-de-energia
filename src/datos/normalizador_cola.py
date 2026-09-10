# src/datos/normalizador_cola.py
"""
Sistema de normalización de datos en cola con historial
Zona horaria: Perú (UTC-5)

Características:
- Procesa archivos con diferentes formatos (CSV, Excel, JSON)
- Detecta el tipo de dato automáticamente
- Normaliza columnas, fechas, números y textos
- Maneja errores y datos sucios
- Guarda en datos/brutos/ (para el sistema)
- Guarda en datos_pasados/ (historial)
- Guarda inspecciones en datos/retroalimentacion/inspecciones/
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
        self.retroalimentacion_dir = self.base_dir / 'retroalimentacion' / 'inspecciones'
        
        # Crear carpetas
        for dir_path in [self.pendientes_dir, self.procesando_dir, 
                        self.errores_dir, self.brutos_dir, 
                        self.datos_pasados_dir, self.metadatos_dir,
                        self.retroalimentacion_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Crear subcarpetas en brutos y datos_pasados
        subcarpetas = ['consumo', 'clientes', 'alarmas', 'facturacion', 'inspecciones']
        for sub in subcarpetas:
            (self.brutos_dir / sub).mkdir(parents=True, exist_ok=True)
            (self.datos_pasados_dir / sub).mkdir(parents=True, exist_ok=True)
        
        self.normalizador = NormalizadorDatos()
        
        # Estadísticas de procesamiento
        self.stats = {
            'archivos_procesados': 0,
            'archivos_con_error': 0,
            'registros_totales': 0,
            'registros_por_tipo': {},
            'errores_encontrados': []
        }
        
        registro.info("📋 Normalizador de cola con historial inicializado")
    
    # ============================================================
    # PROCESAMIENTO PRINCIPAL
    # ============================================================
    
    def procesar_cola(self) -> Dict[str, Any]:
        """
        Procesa todos los archivos en la cola de pendientes
        """
        resultados = {
            'total': 0,
            'procesados': 0,
            'errores': 0,
            'detalles': [],
            'estadisticas': {}
        }
        
        archivos = list(self.pendientes_dir.glob('*'))
        
        if not archivos:
            registro.info("ℹ️ No hay archivos en la cola de pendientes")
            return resultados
        
        registro.info(f"📂 {len(archivos)} archivos en la cola")
        registro.info(f"🕐 Hora Perú: {ahora_peru().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Resetear estadísticas
        self.stats = {
            'archivos_procesados': 0,
            'archivos_con_error': 0,
            'registros_totales': 0,
            'registros_por_tipo': {},
            'errores_encontrados': []
        }
        
        for archivo in archivos:
            resultados['total'] += 1
            resultado = self._procesar_archivo(archivo)
            resultados['detalles'].append(resultado)
            
            if resultado['estado'] == 'exito':
                resultados['procesados'] += 1
                self.stats['archivos_procesados'] += 1
                self.stats['registros_totales'] += resultado['registros']
                
                tipo = resultado['tipo']
                if tipo not in self.stats['registros_por_tipo']:
                    self.stats['registros_por_tipo'][tipo] = 0
                self.stats['registros_por_tipo'][tipo] += resultado['registros']
            else:
                resultados['errores'] += 1
                self.stats['archivos_con_error'] += 1
                self.stats['errores_encontrados'].append({
                    'archivo': archivo.name,
                    'error': resultado['mensaje']
                })
        
        resultados['estadisticas'] = self.stats
        
        # Guardar reporte de procesamiento
        self._guardar_reporte_procesamiento(resultados)
        
        registro.info(f"✅ Cola procesada: {resultados['procesados']} éxitos, {resultados['errores']} errores")
        
        return resultados
    
    def _procesar_archivo(self, archivo: Path) -> Dict[str, Any]:
        """
        Procesa un archivo individual
        """
        resultado = {
            'archivo': archivo.name,
            'estado': 'error',
            'mensaje': '',
            'tipo': None,
            'registros': 0,
            'destino_brutos': None,
            'destino_historial': None,
            'advertencias': []
        }
        
        try:
            # 1. Mover a procesando
            destino_procesando = self.procesando_dir / archivo.name
            archivo.rename(destino_procesando)
            registro.info(f"\n📄 Procesando: {archivo.name}")
            
            # 2. Cargar y detectar
            df, tipo = self._cargar_y_detectar(destino_procesando)
            
            if df is None:
                resultado['mensaje'] = "No se pudo cargar el archivo"
                self._mover_a_error(destino_procesando, resultado['mensaje'])
                return resultado
            
            resultado['tipo'] = tipo
            resultado['registros'] = len(df)
            
            registro.info(f"   📊 Tipo detectado: {tipo}")
            registro.info(f"   📊 Registros: {len(df)}")
            registro.info(f"   📊 Columnas: {df.columns.tolist()}")
            
            # 3. Normalizar
            df_normalizado, reporte = self.normalizador.normalizar(df, tipo)
            
            # Agregar advertencias del reporte
            resultado['advertencias'] = reporte.get('advertencias', [])
            
            if reporte.get('errores'):
                for error in reporte['errores']:
                    registro.warning(f"   ⚠️ {error}")
            
            # 4. Guardar en brutos
            destino_brutos = self._guardar_en_brutos(df_normalizado, tipo, archivo.stem)
            resultado['destino_brutos'] = str(destino_brutos)
            registro.info(f"   💾 Guardado en brutos: {destino_brutos.name}")
            
            # 5. Guardar en historial
            destino_historial = self._guardar_en_historial(df_normalizado, tipo, archivo.stem)
            resultado['destino_historial'] = str(destino_historial)
            registro.info(f"   📚 Guardado en historial: {destino_historial.name}")
            
            # 6. Si es inspecciones, guardar en retroalimentación
            if tipo == 'inspecciones':
                self._guardar_en_retroalimentacion(df_normalizado, archivo.stem)
                registro.info(f"   📋 Inspecciones guardadas en retroalimentación")
            
            # 7. Guardar reporte de normalización
            self._guardar_reporte_normalizacion(reporte, archivo.stem, tipo)
            
            # 8. Eliminar archivo de procesando
            destino_procesando.unlink()
            
            resultado['estado'] = 'exito'
            resultado['mensaje'] = f"Normalizado y guardado en brutos + historial"
            
            registro.info(f"   ✅ {archivo.name} completado")
            
        except Exception as e:
            resultado['mensaje'] = str(e)
            registro.error(f"   ❌ Error procesando {archivo.name}: {e}")
            
            # Mover a errores si existe el archivo
            archivo_error = self.procesando_dir / archivo.name
            if archivo_error.exists():
                self._mover_a_error(archivo_error, str(e))
        
        return resultado
    
    # ============================================================
    # CARGA Y DETECCIÓN
    # ============================================================
    
    def _cargar_y_detectar(self, archivo: Path) -> Tuple[Optional[pd.DataFrame], str]:
        """
        Carga un archivo y detecta su tipo
        """
        try:
            # Cargar según extensión
            if archivo.suffix == '.csv':
                # Intentar con diferentes encodings
                try:
                    df = pd.read_csv(archivo, encoding='utf-8')
                except UnicodeDecodeError:
                    df = pd.read_csv(archivo, encoding='latin1')
            elif archivo.suffix in ['.parquet', '.pqt']:
                df = pd.read_parquet(archivo)
            elif archivo.suffix in ['.xlsx', '.xls']:
                df = pd.read_excel(archivo)
            elif archivo.suffix == '.json':
                # Intentar diferentes orientaciones
                try:
                    df = pd.read_json(archivo, orient='records')
                except:
                    df = pd.read_json(archivo)
            else:
                return None, 'desconocido'
            
            # Detectar tipo
            tipo = self._detectar_tipo(df)
            
            return df, tipo
            
        except Exception as e:
            registro.error(f"❌ Error cargando {archivo.name}: {e}")
            return None, 'desconocido'
    
    def _detectar_tipo(self, df: pd.DataFrame) -> str:
        """
        Detecta el tipo de dato basándose en las columnas
        """
        columnas_lower = [c.lower() for c in df.columns]
        
        # Detectar inspecciones
        if any('resultado' in c for c in columnas_lower):
            return 'inspecciones'
        if any('tipo_irregularidad' in c for c in columnas_lower):
            return 'inspecciones'
        if any('cnr' in c for c in columnas_lower):
            return 'inspecciones'
        
        # Detectar facturación
        if any('monto' in c or 'importe' in c for c in columnas_lower):
            if any('factura' in c or 'emision' in c or 'vencimiento' in c for c in columnas_lower):
                return 'facturacion'
        
        # Detectar alarmas
        if any('alarma' in c or 'evento' in c for c in columnas_lower):
            return 'alarmas'
        if any('gravedad' in c or 'nivel' in c for c in columnas_lower):
            return 'alarmas'
        
        # Detectar clientes
        if any('tipo_cliente' in c or 'potencia' in c for c in columnas_lower):
            return 'clientes'
        
        # Detectar consumo
        if any('consumo' in c or 'kwh' in c for c in columnas_lower):
            return 'consumo'
        
        # Usar el normalizador para detectar
        deteccion = self.normalizador.detectar_tipo_dato(df)
        return deteccion['tipo']
    
    # ============================================================
    # GUARDADO
    # ============================================================
    
    def _guardar_en_brutos(self, df: pd.DataFrame, tipo: str, nombre_base: str) -> Path:
        """
        Guarda en datos/brutos/
        """
        ts = timestamp_peru()
        nombre = f"{nombre_base}_{ts}.parquet"
        
        # Asegurar que existe la carpeta
        destino_dir = self.brutos_dir / tipo
        destino_dir.mkdir(parents=True, exist_ok=True)
        
        destino = destino_dir / nombre
        df.to_parquet(destino, index=False)
        
        return destino
    
    def _guardar_en_historial(self, df: pd.DataFrame, tipo: str, nombre_base: str) -> Path:
        """
        Guarda en datos_pasados/ (historial)
        """
        ts = timestamp_peru()
        nombre = f"{nombre_base}_{ts}.parquet"
        
        destino_dir = self.datos_pasados_dir / tipo
        destino_dir.mkdir(parents=True, exist_ok=True)
        
        destino = destino_dir / nombre
        df.to_parquet(destino, index=False)
        
        return destino
    
    def _guardar_en_retroalimentacion(self, df: pd.DataFrame, nombre_base: str):
        """
        Guarda inspecciones en datos/retroalimentacion/inspecciones/
        """
        ts = timestamp_peru()
        nombre = f"inspecciones_{ts}.csv"
        
        destino = self.retroalimentacion_dir / nombre
        df.to_csv(destino, index=False, encoding='utf-8')
        
        registro.info(f"   📋 Guardado en retroalimentación: {nombre}")
    
    def _guardar_reporte_normalizacion(self, reporte: Dict, nombre_base: str, tipo: str):
        """
        Guarda el reporte de normalización en datos/metadatos/
        """
        ts = timestamp_peru()
        nombre = f"normalizacion_{nombre_base}_{ts}.json"
        
        reporte['timestamp'] = iso_peru()
        reporte['archivo_original'] = nombre_base
        reporte['tipo'] = tipo
        
        destino = self.metadatos_dir / nombre
        with open(destino, 'w', encoding='utf-8') as f:
            json.dump(reporte, f, indent=2, default=str, ensure_ascii=False)
    
    def _guardar_reporte_procesamiento(self, resultados: Dict):
        """
        Guarda un reporte del procesamiento completo de la cola
        """
        ts = timestamp_peru()
        nombre = f"procesamiento_cola_{ts}.json"
        
        reporte = {
            'timestamp': iso_peru(),
            'hora_peru': ahora_peru().strftime('%Y-%m-%d %H:%M:%S'),
            'total_archivos': resultados['total'],
            'procesados': resultados['procesados'],
            'errores': resultados['errores'],
            'estadisticas': resultados.get('estadisticas', {}),
            'detalles': resultados['detalles']
        }
        
        destino = self.metadatos_dir / nombre
        with open(destino, 'w', encoding='utf-8') as f:
            json.dump(reporte, f, indent=2, default=str, ensure_ascii=False)
        
        registro.info(f"📄 Reporte de procesamiento guardado: {nombre}")
    
    # ============================================================
    # MANEJO DE ERRORES
    # ============================================================
    
    def _mover_a_error(self, archivo: Path, motivo: str):
        """
        Mueve un archivo a la carpeta de errores
        """
        destino = self.errores_dir / archivo.name
        
        # Si ya existe, agregar timestamp
        if destino.exists():
            ts = timestamp_peru()
            destino = self.errores_dir / f"{archivo.stem}_{ts}{archivo.suffix}"
        
        archivo.rename(destino)
        
        # Guardar motivo del error
        error_file = self.errores_dir / f"{archivo.stem}_error.txt"
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write(f"Archivo: {archivo.name}\n")
            f.write(f"Fecha: {iso_peru()}\n")
            f.write(f"Error: {motivo}\n")
    
    # ============================================================
    # UTILIDADES
    # ============================================================
    
    def agregar_a_cola(self, ruta_archivo: Path) -> bool:
        """
        Agrega un archivo a la cola de pendientes
        """
        if not ruta_archivo.exists():
            registro.error(f"❌ Archivo no encontrado: {ruta_archivo}")
            return False
        
        destino = self.pendientes_dir / ruta_archivo.name
        
        # Si ya existe, agregar timestamp
        if destino.exists():
            ts = timestamp_peru()
            nuevo_nombre = f"{ruta_archivo.stem}_{ts}{ruta_archivo.suffix}"
            destino = self.pendientes_dir / nuevo_nombre
        
        shutil.copy2(ruta_archivo, destino)
        registro.info(f"📥 Archivo agregado a la cola: {destino.name}")
        return True
    
    def obtener_estado_cola(self) -> Dict[str, int]:
        """
        Retorna el estado actual de la cola
        """
        return {
            'pendientes': len(list(self.pendientes_dir.glob('*'))),
            'procesando': len(list(self.procesando_dir.glob('*'))),
            'errores': len(list(self.errores_dir.glob('*')))
        }
    
    def obtener_estado_historial(self) -> Dict[str, int]:
        """
        Retorna el estado del historial (datos_pasados)
        """
        historial = {}
        for tipo in ['consumo', 'clientes', 'alarmas', 'facturacion', 'inspecciones']:
            historial[tipo] = len(list((self.datos_pasados_dir / tipo).glob('*.parquet')))
        return historial
    
    def obtener_estado_brutos(self) -> Dict[str, int]:
        """
        Retorna el estado de los datos en brutos
        """
        brutos = {}
        for tipo in ['consumo', 'clientes', 'alarmas', 'facturacion', 'inspecciones']:
            brutos[tipo] = len(list((self.brutos_dir / tipo).glob('*.parquet')))
        return brutos
    
    def limpiar_procesando(self):
        """
        Limpia la carpeta de procesando (archivos huérfanos)
        """
        archivos = list(self.procesando_dir.glob('*'))
        for archivo in archivos:
            try:
                archivo.unlink()
            except:
                pass
        
        if archivos:
            registro.info(f"🗑️ {len(archivos)} archivos huérfanos eliminados de procesando")
        else:
            registro.info("ℹ️ No hay archivos en procesando")
    
    def limpiar_errores(self):
        """
        Limpia la carpeta de errores
        """
        archivos = list(self.errores_dir.glob('*'))
        for archivo in archivos:
            try:
                archivo.unlink()
            except:
                pass
        
        if archivos:
            registro.info(f"🗑️ {len(archivos)} archivos de error eliminados")
        else:
            registro.info("ℹ️ No hay archivos en errores")