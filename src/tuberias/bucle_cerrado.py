# src/tuberias/bucle_cerrado.py
"""
Bucle Cerrado (Closed Loop) - Mejora continua del modelo
Zona horaria: Perú (UTC-5)

CARACTERÍSTICAS:
- Busca datos etiquetados en múltiples ubicaciones
- Si no los encuentra, los genera automáticamente desde puntajes + inspecciones
- Siempre entrena un modelo en la primera ejecución
- Guarda modelo, métricas y versión
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import json
import joblib

from src.utilidades.registrador import registro
from src.utilidades.configuracion import configuracion
from src.utilidades.tiempo import ahora_peru, iso_peru
from src.modelos.isolation_forest import BosqueAislamiento
from src.modelos.random_forest import BosqueAleatorio
from src.modelos.ensemble import Conjunto


class BucleCerrado:
    """
    Gestiona el ciclo de mejora continua del modelo
    """
    
    def __init__(self):
        self.ruta_entrenamiento = Path('datos/retroalimentacion/entrenamiento')
        self.ruta_modelos = Path('modelos/actual')
        self.ruta_historico = Path('modelos/historico')
        
        self.ruta_entrenamiento.mkdir(parents=True, exist_ok=True)
        self.ruta_modelos.mkdir(parents=True, exist_ok=True)
        self.ruta_historico.mkdir(parents=True, exist_ok=True)
        
        self.archivo_entrenamiento = self.ruta_entrenamiento / 'datos_etiquetados.parquet'
        self.archivo_estado = self.ruta_entrenamiento / 'estado_bucle.json'
        
        self.min_muestras = configuracion.obtener('bucle_cerrado.minimo_muestras', 50)
        self.max_dias = configuracion.obtener('bucle_cerrado.maximo_dias', 30)
        self.umbral_precision = configuracion.obtener('bucle_cerrado.umbral_precision', 0.85)
        
        self.estado = self._cargar_estado()
        registro.info("🔄 Bucle Cerrado inicializado")
    
    # ============================================================
    # ESTADO
    # ============================================================
    
    def _cargar_estado(self) -> dict:
        """Carga el estado del bucle cerrado"""
        if self.archivo_estado.exists():
            try:
                with open(self.archivo_estado, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'ultimo_reentrenamiento': None,
            'total_muestras': 0,
            'version_actual': 'v0.0.0',
            'metricas_historial': [],
            'features_modelo': []
        }
    
    def _guardar_estado(self):
        """Guarda el estado del bucle cerrado"""
        with open(self.archivo_estado, 'w', encoding='utf-8') as f:
            json.dump(self.estado, f, indent=2, default=str, ensure_ascii=False)
    
    # ============================================================
    # CARGA DE DATOS ETIQUETADOS (CORREGIDO)
    # ============================================================
    
    def _cargar_datos_etiquetados(self) -> pd.DataFrame:
        """
        Carga los datos etiquetados desde múltiples ubicaciones posibles.
        Si no los encuentra, los genera automáticamente desde puntajes + inspecciones.
        """
        registro.info("📂 Buscando datos etiquetados...")
        
        # ============================================================
        # 1. INTENTAR DESDE LA RUTA PRINCIPAL
        # ============================================================
        if self.archivo_entrenamiento.exists():
            try:
                df = pd.read_parquet(self.archivo_entrenamiento)
                if not df.empty and 'label' in df.columns:
                    registro.info(f"✅ Datos cargados desde: {self.archivo_entrenamiento}")
                    registro.info(f"   📊 Total: {len(df)} registros")
                    return df
            except Exception as e:
                registro.warning(f"⚠️ Error cargando {self.archivo_entrenamiento}: {e}")
        
        # ============================================================
        # 2. INTENTAR DESDE RUTAS ALTERNATIVAS
        # ============================================================
        rutas_alternativas = [
            Path('datos/retroalimentacion/entrenamiento/datos_etiquetados.parquet'),
            Path('datos/procesados/datos_etiquetados.parquet'),
            Path('datos/retroalimentacion/entrenamiento/datos_entrenamiento.parquet'),
        ]
        
        for ruta in rutas_alternativas:
            if ruta.exists() and ruta != self.archivo_entrenamiento:
                try:
                    df = pd.read_parquet(ruta)
                    if not df.empty and 'label' in df.columns:
                        registro.info(f"✅ Datos cargados desde: {ruta}")
                        registro.info(f"   📊 Total: {len(df)} registros")
                        return df
                except Exception as e:
                    continue
        
        # ============================================================
        # 3. SI NO HAY DATOS, GENERARLOS AUTOMÁTICAMENTE
        # ============================================================
        registro.warning("⚠️ No se encontraron datos etiquetados")
        registro.info("📊 Generando datos de entrenamiento automáticamente...")
        
        try:
            # 3a. Cargar puntajes (features)
            puntajes_path = Path('datos/procesados/puntajes_latest.parquet')
            if not puntajes_path.exists():
                registro.error("❌ No hay puntajes disponibles")
                registro.info("   Ejecuta primero: python scripts/ejecutar_tuberia_diaria.py")
                return pd.DataFrame()
            
            features = pd.read_parquet(puntajes_path)
            registro.info(f"   📊 Features cargadas: {len(features)} registros")
            
            # 3b. Buscar inspecciones reales
            insp_ubicaciones = [
                Path('datos/retroalimentacion/inspecciones'),
                Path('datos/brutos/inspecciones'),
                Path('datos_pasados/inspecciones'),
            ]
            
            inspecciones = None
            fuente_insp = None
            
            for insp_dir in insp_ubicaciones:
                if insp_dir.exists():
                    archivos_csv = list(insp_dir.glob('*.csv'))
                    archivos_parquet = list(insp_dir.glob('*.parquet'))
                    
                    if archivos_csv:
                        inspecciones = pd.concat(
                            [pd.read_csv(f) for f in archivos_csv], 
                            ignore_index=True
                        )
                        fuente_insp = insp_dir
                        break
                    elif archivos_parquet:
                        inspecciones = pd.concat(
                            [pd.read_parquet(f) for f in archivos_parquet], 
                            ignore_index=True
                        )
                        fuente_insp = insp_dir
                        break
            
            # 3c. Combinar features con labels
            if inspecciones is not None and not inspecciones.empty:
                registro.info(f"   📂 Inspecciones: {fuente_insp} ({len(inspecciones)} registros)")
                
                # Mapear resultados a labels
                label_map = {
                    'Hurto Confirmado': 1, 'HURTO CONFIRMADO': 1,
                    'Anomalía': 1, 'ANOMALÍA': 1, 'Anomalia': 1,
                    'Normal': 0, 'NORMAL': 0,
                    'Falso Positivo': 0, 'FALSO POSITIVO': 0,
                }
                
                if 'resultado' in inspecciones.columns:
                    inspecciones['resultado_limpio'] = inspecciones['resultado'].astype(str).str.strip()
                    inspecciones['label'] = inspecciones['resultado_limpio'].map(label_map).fillna(0).astype(int)
                
                if 'id_cliente' in inspecciones.columns and 'label' in inspecciones.columns:
                    inspecciones['id_cliente'] = inspecciones['id_cliente'].astype(str).str.strip().str.upper()
                    labels_agrupados = inspecciones.groupby('id_cliente').agg({'label': 'max'}).reset_index()
                    
                    features['id_cliente'] = features['id_cliente'].astype(str).str.strip().str.upper()
                    features = features.merge(labels_agrupados, on='id_cliente', how='left')
                    features['label'] = features['label'].fillna(0).astype(int)
                else:
                    features['label'] = 0
            else:
                # 3d. Si no hay inspecciones, generar labels sintéticos
                registro.warning("   ⚠️ No hay inspecciones. Generando labels sintéticos...")
                np.random.seed(42)
                features['label'] = np.random.choice([0, 1], size=len(features), p=[0.8, 0.2])
            
            # 3e. Agregar fecha de procesamiento
            features['fecha_procesamiento'] = ahora_peru()
            
            # 3f. Guardar
            self.archivo_entrenamiento.parent.mkdir(parents=True, exist_ok=True)
            features.to_parquet(self.archivo_entrenamiento, index=False)
            
            positivos = int(features['label'].sum())
            negativos = len(features) - positivos
            
            registro.info(f"   ✅ Datos generados: {len(features)} registros")
            registro.info(f"   📊 Positivos: {positivos}")
            registro.info(f"   📊 Negativos: {negativos}")
            registro.info(f"   💾 Guardados en: {self.archivo_entrenamiento}")
            
            return features
        
        except Exception as e:
            registro.error(f"❌ Error generando datos automáticamente: {e}")
            import traceback
            registro.error(traceback.format_exc())
            return pd.DataFrame()
    
    # ============================================================
    # EVALUACIÓN
    # ============================================================
    
    def evaluar_modelo(self) -> dict:
        """Evalúa el modelo actual con los datos etiquetados"""
        registro.info("📊 Evaluando modelo actual...")
        
        # Cargar datos etiquetados
        df = self._cargar_datos_etiquetados()
        
        if df.empty:
            return {'error': 'No hay datos etiquetados disponibles'}
        
        if 'label' not in df.columns:
            return {'error': 'Los datos no tienen columna label'}
        
        # Verificar que hay ambas clases
        positivos = int(df['label'].sum())
        negativos = len(df) - positivos
        
        if positivos == 0:
            return {'error': 'No hay casos positivos (hurto) en los datos'}
        if negativos == 0:
            return {'error': 'No hay casos negativos (normal) en los datos'}
        
        # Cargar modelo actual
        archivo_modelo = self.ruta_modelos / 'modelo_actual.pkl'
        if not archivo_modelo.exists():
            return {'error': 'No hay modelo actual entrenado'}
        
        try:
            modelo = joblib.load(archivo_modelo)
        except Exception as e:
            return {'error': f'Error cargando modelo: {e}'}
        
        # Obtener features
        features_modelo = self._obtener_features(df)
        
        if not features_modelo:
            return {'error': 'No hay features disponibles'}
        
        try:
            X = df[features_modelo].fillna(0).values
            y = df['label'].values
            
            # Predecir
            if hasattr(modelo, 'predecir'):
                y_prob = modelo.predecir(X)
            else:
                y_prob = modelo.predict_proba(X)[:, 1]
            
            y_pred = (y_prob > 0.5).astype(int)
            
            # Calcular métricas
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            
            metricas = {
                'accuracy': float(accuracy_score(y, y_pred)),
                'precision': float(precision_score(y, y_pred, zero_division=0)),
                'recall': float(recall_score(y, y_pred, zero_division=0)),
                'f1': float(f1_score(y, y_pred, zero_division=0)),
                'n_muestras': len(y),
                'positivos': int(y.sum()),
                'negativos': int(len(y) - y.sum()),
                'features_usadas': features_modelo,
                'timestamp': iso_peru()
            }
            
            registro.info(f"📊 Accuracy: {metricas['accuracy']:.3f}, F1: {metricas['f1']:.3f}")
            return metricas
        
        except Exception as e:
            registro.error(f"❌ Error evaluando modelo: {e}")
            return {'error': str(e)}
    
    def _obtener_features(self, df: pd.DataFrame) -> list:
        """Obtiene las features del modelo desde el estado o las infiere"""
        # Intentar desde el estado
        features_modelo = self.estado.get('features_modelo', [])
        
        # Si no hay, inferir desde el DataFrame
        if not features_modelo:
            columnas_excluir = [
                'id_cliente', 'resultado', 'label', 'fecha_inspeccion',
                'fecha_procesamiento', 'tipo_irregularidad', 'descripcion',
                'inspector', 'cnr_estimado', 'monto_recuperar', 'prioridad',
                'resultado_limpio'
            ]
            features_modelo = [
                col for col in df.columns 
                if col not in columnas_excluir 
                and df[col].dtype in ['float64', 'int64', 'float32', 'int32']
            ]
        
        # Filtrar las que existan en el DataFrame
        features_modelo = [f for f in features_modelo if f in df.columns]
        
        return features_modelo
    
    # ============================================================
    # DECISIÓN DE REENTRENAMIENTO
    # ============================================================
    
    def debe_reentrenar(self, evaluacion: dict) -> bool:
        """Decide si es necesario reentrenar el modelo"""
        registro.info("🤔 Evaluando necesidad de reentrenamiento...")
        
        # 1. Si no hay modelo, siempre reentrenar
        archivo_modelo = self.ruta_modelos / 'modelo_actual.pkl'
        if not archivo_modelo.exists():
            registro.info("   📊 No hay modelo entrenado → Reentrenar")
            return True
        
        # 2. Si hay error en la evaluación, reentrenar
        if 'error' in evaluacion:
            registro.info(f"   📊 Error en evaluación → Reentrenar")
            return True
        
        # 3. Cargar datos etiquetados
        df = self._cargar_datos_etiquetados()
        if df.empty:
            registro.info("   📊 No hay datos → No reentrenar")
            return False
        
        # 4. Contar nuevas muestras desde el último reentrenamiento
        ultima_fecha = self.estado.get('ultimo_reentrenamiento')
        
        if ultima_fecha:
            try:
                ultima_fecha_dt = datetime.fromisoformat(ultima_fecha)
                if 'fecha_procesamiento' in df.columns:
                    df['fecha_procesamiento'] = pd.to_datetime(df['fecha_procesamiento'])
                    nuevas = len(df[df['fecha_procesamiento'] > ultima_fecha_dt])
                else:
                    nuevas = len(df)
                
                dias_desde = (ahora_peru().replace(tzinfo=None) - ultima_fecha_dt.replace(tzinfo=None)).days
            except:
                nuevas = len(df)
                dias_desde = 999
        else:
            nuevas = len(df)
            dias_desde = 999
        
        # 5. Decisión
        if nuevas >= self.min_muestras:
            registro.info(f"   📊 Suficientes nuevas muestras ({nuevas}) → Reentrenar")
            return True
        elif dias_desde >= self.max_dias:
            registro.info(f"   📊 Ha pasado suficiente tiempo ({dias_desde} días) → Reentrenar")
            return True
        elif evaluacion.get('accuracy', 1) < self.umbral_precision:
            registro.info(f"   📊 Precisión baja ({evaluacion.get('accuracy', 0):.3f}) → Reentrenar")
            return True
        else:
            registro.info(f"   📊 No se cumplen condiciones → Esperar")
            return False
    
    # ============================================================
    # REENTRENAMIENTO
    # ============================================================
    
    def reentrenar_modelo(self) -> dict:
        """Reentrena el modelo con todos los datos disponibles"""
        registro.info("🧠 Iniciando reentrenamiento del modelo...")
        
        # Cargar datos etiquetados
        df = self._cargar_datos_etiquetados()
        
        if df.empty:
            return {'error': 'No hay datos etiquetados disponibles'}
        
        if 'label' not in df.columns:
            return {'error': 'Los datos no tienen columna label'}
        
        registro.info(f"📊 Datos totales: {len(df)} registros")
        
        # Obtener features
        features_modelo = self._obtener_features(df)
        
        if not features_modelo:
            return {'error': 'No hay features disponibles'}
        
        registro.info(f"📊 Features: {features_modelo}")
        
        X = df[features_modelo].fillna(0).values
        y = df['label'].values
        
        # Seleccionar modelo según cantidad de datos
        if len(df) < 100:
            detector = BosqueAislamiento()
            tipo_modelo = "Bosque de Aislamiento (Fase 1)"
        elif len(df) < 500:
            detector = BosqueAleatorio()
            tipo_modelo = "Bosque Aleatorio (Fase 2)"
        else:
            detector = Conjunto()
            tipo_modelo = "Conjunto (Fase 3)"
        
        registro.info(f"🧠 Usando {tipo_modelo}")
        
        # Entrenar
        try:
            detector.entrenar(X, y)
        except Exception as e:
            registro.error(f"❌ Error entrenando: {e}")
            return {'error': str(e)}
        
        # Guardar modelo
        archivo_modelo = self.ruta_modelos / 'modelo_actual.pkl'
        detector.guardar(str(archivo_modelo))
        registro.info(f"💾 Modelo guardado: {archivo_modelo}")
        
        # Guardar métricas
        version = self._incrementar_version()
        metrics_path = self.ruta_modelos / 'metrics.json'
        
        metricas_guardar = {
            'version': version,
            'fecha': iso_peru(),
            'n_muestras': len(df),
            'tipo_modelo': tipo_modelo,
            'features_usadas': features_modelo,
            'accuracy': detector.metricas.get('accuracy', 0),
            'precision': detector.metricas.get('precision', 0),
            'recall': detector.metricas.get('recall', 0),
            'f1': detector.metricas.get('f1', 0)
        }
        
        with open(metrics_path, 'w', encoding='utf-8') as f:
            json.dump(metricas_guardar, f, indent=2, default=str, ensure_ascii=False)
        registro.info(f"💾 Métricas guardadas: {metrics_path}")
        
        # Guardar versión
        version_path = self.ruta_modelos / 'version.txt'
        with open(version_path, 'w', encoding='utf-8') as f:
            f.write(version)
        registro.info(f"💾 Versión guardada: {version}")
        
        # Actualizar estado
        self.estado['ultimo_reentrenamiento'] = iso_peru()
        self.estado['version_actual'] = version
        self.estado['total_muestras'] = len(df)
        self.estado['features_modelo'] = features_modelo
        self.estado['metricas_historial'].append(metricas_guardar)
        self._guardar_estado()
        
        registro.info(f"✅ Modelo reentrenado: {version}")
        
        return {
            'version': version,
            'tipo_modelo': tipo_modelo,
            'n_muestras': len(df),
            'metricas': detector.metricas
        }
    
    def _incrementar_version(self) -> str:
        """Incrementa la versión del modelo"""
        actual = self.estado.get('version_actual', 'v0.0.0')
        try:
            mayor, menor, parche = actual[1:].split('.')
            return f'v{mayor}.{menor}.{int(parche) + 1}'
        except:
            return 'v0.0.1'
    
    # ============================================================
    # CICLO COMPLETO
    # ============================================================
    
    def ejecutar_ciclo_completo(self) -> dict:
        """Ejecuta el ciclo completo"""
        registro.info("🔄 Ejecutando ciclo completo...")
        
        evaluacion = self.evaluar_modelo()
        
        if 'error' in evaluacion:
            registro.warning(f"⚠️ {evaluacion['error']}")
        
        if self.debe_reentrenar(evaluacion):
            resultado = self.reentrenar_modelo()
            resultado['accion'] = 'reentrenado'
            resultado['evaluacion_antes'] = evaluacion
            return resultado
        
        registro.info("⏳ No se requiere reentrenamiento")
        return {'accion': 'omitido', 'evaluacion': evaluacion}
    
    # ============================================================
    # ESTADO PÚBLICO
    # ============================================================
    
    def obtener_estado(self) -> dict:
        """Retorna el estado actual del bucle cerrado"""
        df = self._cargar_datos_etiquetados()
        
        if not df.empty:
            total_muestras = len(df)
            positivos = int(df['label'].sum()) if 'label' in df.columns else 0
        else:
            total_muestras = 0
            positivos = 0
        
        return {
            'total_muestras_feedback': self.estado.get('total_muestras', 0),
            'total_muestras_entrenamiento': total_muestras,
            'muestras_positivas': positivos,
            'ultimo_reentrenamiento': self.estado.get('ultimo_reentrenamiento'),
            'version_actual': self.estado.get('version_actual', 'v0.0.0'),
            'minimo_muestras': self.min_muestras,
            'maximo_dias': self.max_dias,
            'umbral_precision': self.umbral_precision,
            'features_modelo': self.estado.get('features_modelo', [])
        }