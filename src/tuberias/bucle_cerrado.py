# src/tuberias/bucle_cerrado.py
"""
Bucle Cerrado (Closed Loop) - Mejora continua del modelo
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import joblib
from src.utilidades.registrador import registro
from src.utilidades.configuracion import configuracion
from src.modelos.isolation_forest import BosqueAislamiento
from src.modelos.random_forest import BosqueAleatorio
from src.modelos.ensemble import Conjunto

class BucleCerrado:
    """
    Gestiona el ciclo de mejora continua del modelo
    """
    
    def __init__(self):
        self.ruta_entrenamiento = Path(configuracion.obtener('datos.ruta_retroalimentacion', 'datos/retroalimentacion/entrenamiento'))
        self.ruta_modelos = Path(configuracion.obtener('modelos.ruta', 'modelos/actual'))
        self.ruta_historico = Path(configuracion.obtener('modelos.ruta_historico', 'modelos/historico'))
        
        self.ruta_entrenamiento.mkdir(parents=True, exist_ok=True)
        self.ruta_modelos.mkdir(parents=True, exist_ok=True)
        self.ruta_historico.mkdir(parents=True, exist_ok=True)
        
        self.min_muestras = configuracion.obtener('bucle_cerrado.minimo_muestras', 50)
        self.max_dias = configuracion.obtener('bucle_cerrado.maximo_dias', 30)
        self.umbral_precision = configuracion.obtener('bucle_cerrado.umbral_precision', 0.85)
        
        self.estado = self._cargar_estado()
        registro.info("🔄 Bucle Cerrado inicializado")
    
    def _cargar_estado(self) -> dict:
        archivo_estado = self.ruta_entrenamiento / 'estado_bucle.json'
        if archivo_estado.exists():
            with open(archivo_estado, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'ultimo_reentrenamiento': None,
            'total_muestras': 0,
            'version_actual': 'v0.0.0',
            'metricas_historial': []
        }
    
    def _guardar_estado(self):
        archivo_estado = self.ruta_entrenamiento / 'estado_bucle.json'
        with open(archivo_estado, 'w', encoding='utf-8') as f:
            json.dump(self.estado, f, indent=2, default=str)
    
    def recolectar_feedback(self, resultados: pd.DataFrame) -> dict:
        registro.info("📥 Recolectando feedback de inspecciones...")
        
        requeridos = ['id_cliente', 'resultado', 'label']
        for col in requeridos:
            if col not in resultados.columns:
                raise ValueError(f"Columna requerida faltante: {col}")
        
        resultados['fecha_procesamiento'] = datetime.now()
        
        archivo_entrenamiento = self.ruta_entrenamiento / 'datos_etiquetados.parquet'
        if archivo_entrenamiento.exists():
            existente = pd.read_parquet(archivo_entrenamiento)
            combinado = pd.concat([existente, resultados], ignore_index=True)
        else:
            combinado = resultados
        
        combinado.to_parquet(archivo_entrenamiento, index=False)
        self.estado['total_muestras'] = len(combinado)
        self._guardar_estado()
        
        stats = {
            'nuevos': len(resultados),
            'total_acumulado': len(combinado),
            'confirmados': len(resultados[resultados['label'] == 1])
        }
        registro.info(f"✅ {stats['nuevos']} nuevos registros")
        return stats
    
    def evaluar_modelo(self) -> dict:
        registro.info("📊 Evaluando modelo actual...")
        
        archivo_entrenamiento = self.ruta_entrenamiento / 'datos_etiquetados.parquet'
        if not archivo_entrenamiento.exists():
            return {'error': 'No hay datos etiquetados'}
        
        df = pd.read_parquet(archivo_entrenamiento)
        archivo_modelo = self.ruta_modelos / 'modelo_actual.pkl'
        if not archivo_modelo.exists():
            return {'error': 'No hay modelo actual'}
        
        modelo = joblib.load(archivo_modelo)
        columnas_excluir = ['id_cliente', 'resultado', 'label', 'fecha_inspeccion', 'fecha_procesamiento']
        columnas_features = [col for col in df.columns if col not in columnas_excluir]
        X = df[columnas_features].values
        y = df['label'].values
        
        try:
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            y_pred = modelo.predecir(X) > 0.5
            metricas = {
                'accuracy': accuracy_score(y, y_pred),
                'precision': precision_score(y, y_pred, zero_division=0),
                'recall': recall_score(y, y_pred, zero_division=0),
                'f1': f1_score(y, y_pred, zero_division=0),
                'n_muestras': len(y),
                'positivos': int(y.sum()),
                'negativos': int(len(y) - y.sum())
            }
            registro.info(f"📊 Accuracy: {metricas['accuracy']:.3f}, F1: {metricas['f1']:.3f}")
            return metricas
        except Exception as e:
            registro.error(f"❌ Error evaluando: {e}")
            return {'error': str(e)}
    
    def debe_reentrenar(self, evaluacion: dict) -> bool:
        registro.info("🤔 Evaluando necesidad de reentrenamiento...")
        
        if 'error' in evaluacion:
            return False
        
        archivo_entrenamiento = self.ruta_entrenamiento / 'datos_etiquetados.parquet'
        if not archivo_entrenamiento.exists():
            return False
        
        df = pd.read_parquet(archivo_entrenamiento)
        ultima_fecha = self.estado.get('ultimo_reentrenamiento')
        if ultima_fecha:
            ultima_fecha = datetime.fromisoformat(ultima_fecha)
            nuevas = len(df[df['fecha_procesamiento'] > ultima_fecha])
        else:
            nuevas = len(df)
        
        if ultima_fecha:
            dias_desde = (datetime.now() - ultima_fecha).days
        else:
            dias_desde = 999
        
        decision = {
            'nuevas_muestras': nuevas,
            'dias_desde': dias_desde,
            'debe_reentrenar': False
        }
        
        if nuevas >= self.min_muestras:
            decision['debe_reentrenar'] = True
            decision['razon'] = f'Suficientes nuevas muestras ({nuevas})'
        elif dias_desde >= self.max_dias:
            decision['debe_reentrenar'] = True
            decision['razon'] = f'Ha pasado suficiente tiempo ({dias_desde} días)'
        elif evaluacion.get('accuracy', 1) < self.umbral_precision:
            decision['debe_reentrenar'] = True
            decision['razon'] = f'Precisión por debajo del umbral'
        else:
            decision['razon'] = 'No se cumplen condiciones'
        
        registro.info(f"📊 Decisión: {'✅ Reentrenar' if decision['debe_reentrenar'] else '⏳ Esperar'}")
        return decision['debe_reentrenar']
    
    def reentrenar_modelo(self) -> dict:
        registro.info("🧠 Iniciando reentrenamiento del modelo...")
        
        archivo_entrenamiento = self.ruta_entrenamiento / 'datos_etiquetados.parquet'
        if not archivo_entrenamiento.exists():
            return {'error': 'No hay datos etiquetados'}
        
        df = pd.read_parquet(archivo_entrenamiento)
        registro.info(f"📊 Datos totales: {len(df)} registros")
        
        columnas_excluir = ['id_cliente', 'resultado', 'label', 'fecha_inspeccion', 'fecha_procesamiento']
        columnas_features = [col for col in df.columns if col not in columnas_excluir]
        X = df[columnas_features].values
        y = df['label'].values
        
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
        detector.entrenar(X, y)
        
        archivo_modelo = self.ruta_modelos / 'modelo_actual.pkl'
        detector.guardar(str(archivo_modelo))
        
        version = self._incrementar_version()
        self.estado['ultimo_reentrenamiento'] = datetime.now().isoformat()
        self.estado['version_actual'] = version
        self.estado['metricas_historial'].append({
            'version': version,
            'fecha': datetime.now().isoformat(),
            'metricas': detector.metricas,
            'n_muestras': len(df),
            'tipo_modelo': tipo_modelo
        })
        self._guardar_estado()
        
        registro.info(f"✅ Modelo reentrenado: {version}")
        return {
            'version': version,
            'tipo_modelo': tipo_modelo,
            'n_muestras': len(df),
            'metricas': detector.metricas
        }
    
    def _incrementar_version(self) -> str:
        actual = self.estado.get('version_actual', 'v0.0.0')
        mayor, menor, parche = actual[1:].split('.')
        return f'v{mayor}.{menor}.{int(parche) + 1}'
    
    def ejecutar_ciclo_completo(self) -> dict:
        registro.info("🔄 Ejecutando ciclo completo...")
        evaluacion = self.evaluar_modelo()
        
        if self.debe_reentrenar(evaluacion):
            resultado = self.reentrenar_modelo()
            resultado['accion'] = 'reentrenado'
            resultado['evaluacion_antes'] = evaluacion
            return resultado
        
        registro.info("⏳ No se requiere reentrenamiento")
        return {'accion': 'omitido', 'evaluacion': evaluacion}
    
    def obtener_estado(self) -> dict:
        archivo_entrenamiento = self.ruta_entrenamiento / 'datos_etiquetados.parquet'
        if archivo_entrenamiento.exists():
            df = pd.read_parquet(archivo_entrenamiento)
            total_muestras = len(df)
            positivos = df['label'].sum() if 'label' in df.columns else 0
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
            'umbral_precision': self.umbral_precision
        }