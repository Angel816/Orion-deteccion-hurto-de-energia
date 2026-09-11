# scripts/ejecutar_tuberia_diaria.py
"""
Ejecuta la tubería diaria de Orion CON ENTRENAMIENTO REAL
Zona horaria: Perú (UTC-5)

Flujo:
1. Cargar datos desde datos/brutos/
2. Validar y limpiar datos
3. Extraer características causales
4. ENTRENAR modelo (si no existe o hay nuevos datos)
5. Predecir con el modelo entrenado
6. Priorizar
7. Seleccionar features relevantes
8. Guardar resultados con acumulación de histórico
"""

import sys
import io
import os
from pathlib import Path

# ============================================================
# CONFIGURAR UTF-8
# ============================================================

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'C.UTF-8'
os.environ['LC_ALL'] = 'C.UTF-8'

sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
import json
import joblib

from src.datos.cargador import CargadorIncremental
from src.datos.validador import ValidadorDatos
from src.datos.limpiador import LimpiadorDatos
from src.caracteristicas.extractor import ExtractorCaracteristicas
from src.caracteristicas.selector import SelectorCaracteristicas
from src.priorizacion.fase1_simple import PuntuadorSimple
from src.priorizacion.aprendizaje_activo import AprendizajeActivo
from src.utilidades.registrador import registro
from src.utilidades.tiempo import ahora_peru, timestamp_peru, iso_peru


# ============================================================
# ENTRENAMIENTO DEL MODELO
# ============================================================

def entrenar_modelo(features: pd.DataFrame) -> bool:
    """
    Entrena el modelo usando datos etiquetados (si existen).
    Guarda el modelo en modelos/actual/.
    
    Retorna True si entrenó, False si no hay datos.
    """
    registro.info("🧠 Verificando si hay datos para entrenar modelo...")
    
    train_path = Path('datos/retroalimentacion/entrenamiento/datos_etiquetados.parquet')
    
    if not train_path.exists():
        registro.warning("⚠️ No hay datos etiquetados para entrenar")
        registro.info("   Ejecuta primero: python scripts/crear_datos_entrenamiento.py")
        return False
    
    # Cargar datos de entrenamiento
    df_train = pd.read_parquet(train_path)
    
    if df_train.empty:
        registro.warning("⚠️ Datos de entrenamiento vacíos")
        return False
    
    if 'label' not in df_train.columns:
        registro.warning("⚠️ Datos de entrenamiento no tienen label")
        return False
    
    # Verificar que hay ambas clases
    positivos = int(df_train['label'].sum())
    negativos = len(df_train) - positivos
    
    if positivos == 0 or negativos == 0:
        registro.warning(f"⚠️ Solo hay una clase (pos={positivos}, neg={negativos})")
        return False
    
    registro.info(f"📊 Datos de entrenamiento: {len(df_train)} registros")
    registro.info(f"   ✅ Positivos: {positivos}")
    registro.info(f"   ❌ Negativos: {negativos}")
    
    # Seleccionar features
    selector = SelectorCaracteristicas()
    features_modelo = selector.obtener_features_modelo()
    features_disponibles = [f for f in features_modelo if f in df_train.columns]
    
    if not features_disponibles:
        registro.warning("⚠️ No hay features disponibles para entrenar")
        return False
    
    registro.info(f"📊 Features para entrenar: {len(features_disponibles)}")
    
    X = df_train[features_disponibles].fillna(0).values
    y = df_train['label'].values
    
    # ============================================================
    # SELECCIONAR ALGORITMO SEGÚN CANTIDAD DE DATOS
    # ============================================================
    
    try:
        if len(df_train) < 100:
            from sklearn.ensemble import RandomForestClassifier
            modelo = RandomForestClassifier(
                n_estimators=100,
                max_depth=8,
                class_weight='balanced',
                random_state=42,
                n_jobs=-1
            )
            tipo_modelo = "Random Forest"
        elif len(df_train) < 500:
            from sklearn.ensemble import RandomForestClassifier
            modelo = RandomForestClassifier(
                n_estimators=200,
                max_depth=12,
                class_weight='balanced',
                random_state=42,
                n_jobs=-1
            )
            tipo_modelo = "Random Forest"
        else:
            from xgboost import XGBClassifier
            modelo = XGBClassifier(
                n_estimators=200,
                max_depth=8,
                learning_rate=0.1,
                scale_pos_weight=max(1, negativos / max(1, positivos)),
                random_state=42,
                use_label_encoder=False,
                eval_metric='logloss',
                n_jobs=-1
            )
            tipo_modelo = "XGBoost"
        
        registro.info(f"🧠 Entrenando {tipo_modelo}...")
        
        # Entrenar
        modelo.fit(X, y)
        
        # ============================================================
        # CALCULAR MÉTRICAS
        # ============================================================
        
        from sklearn.metrics import (accuracy_score, precision_score, 
                                      recall_score, f1_score, roc_auc_score)
        
        y_pred = modelo.predict(X)
        y_prob = modelo.predict_proba(X)[:, 1]
        
        metricas = {
            'accuracy': float(accuracy_score(y, y_pred)),
            'precision': float(precision_score(y, y_pred, zero_division=0)),
            'recall': float(recall_score(y, y_pred, zero_division=0)),
            'f1': float(f1_score(y, y_pred, zero_division=0)),
            'roc_auc': float(roc_auc_score(y, y_prob)) if len(set(y)) > 1 else 0.0,
            'n_muestras': len(y),
            'positivos': positivos,
            'negativos': negativos
        }
        
        registro.info(f"📊 Métricas del modelo:")
        registro.info(f"   Accuracy:  {metricas['accuracy']:.3f}")
        registro.info(f"   Precision: {metricas['precision']:.3f}")
        registro.info(f"   Recall:    {metricas['recall']:.3f}")
        registro.info(f"   F1:        {metricas['f1']:.3f}")
        registro.info(f"   ROC-AUC:   {metricas['roc_auc']:.3f}")
        
        # ============================================================
        # GUARDAR MODELO Y MÉTRICAS
        # ============================================================
        
        modelo_dir = Path('modelos/actual')
        modelo_dir.mkdir(parents=True, exist_ok=True)
        
        modelo_path = modelo_dir / 'modelo_actual.pkl'
        joblib.dump(modelo, modelo_path)
        registro.info(f"💾 Modelo guardado: {modelo_path}")
        
        # Guardar métricas
        metrics_path = modelo_dir / 'metrics.json'
        metricas_guardar = {
            'version': 'v1.0.0',
            'fecha': iso_peru(),
            'tipo_modelo': tipo_modelo,
            'features_usadas': features_disponibles,
            **metricas
        }
        
        with open(metrics_path, 'w', encoding='utf-8') as f:
            json.dump(metricas_guardar, f, indent=2, default=str, ensure_ascii=False)
        registro.info(f"💾 Métricas guardadas: {metrics_path}")
        
        # Guardar versión
        version_path = modelo_dir / 'version.txt'
        with open(version_path, 'w', encoding='utf-8') as f:
            f.write('v1.0.0')
        
        return True
    
    except Exception as e:
        registro.error(f"❌ Error entrenando modelo: {e}")
        import traceback
        registro.error(traceback.format_exc())
        return False


# ============================================================
# FUNCIÓN DE PREDICCIÓN
# ============================================================

def generar_predicciones(features: pd.DataFrame) -> np.ndarray:
    """
    Genera predicciones usando el modelo entrenado.
    Si no existe, entrena uno primero.
    Si aún así no hay modelo, usa fallback.
    """
    modelo_path = Path('modelos/actual/modelo_actual.pkl')
    
    # Si no hay modelo, intentar entrenar
    if not modelo_path.exists():
        registro.info("🧠 No hay modelo entrenado. Intentando entrenar...")
        entrenar_modelo(features)
    
    # Si ya hay modelo, usarlo
    if modelo_path.exists():
        try:
            registro.info("🧠 Cargando modelo entrenado...")
            modelo = joblib.load(modelo_path)
            
            # Obtener features del modelo
            metrics_path = Path('modelos/actual/metrics.json')
            features_modelo = []
            
            if metrics_path.exists():
                with open(metrics_path, 'r', encoding='utf-8') as f:
                    metrics = json.load(f)
                    features_modelo = metrics.get('features_usadas', [])
            
            # Si no hay, usar las del selector
            if not features_modelo:
                selector = SelectorCaracteristicas()
                features_modelo = selector.obtener_features_modelo()
            
            # Filtrar disponibles
            features_disponibles = [f for f in features_modelo if f in features.columns]
            
            if not features_disponibles:
                registro.warning("⚠️ No hay features del modelo disponibles")
                return np.random.uniform(0, 1, len(features))
            
            registro.info(f"📊 Features usadas: {len(features_disponibles)}")
            
            X = features[features_disponibles].fillna(0).values
            
            # Predecir
            if hasattr(modelo, 'predict_proba'):
                probabilidades = modelo.predict_proba(X)[:, 1]
            elif hasattr(modelo, 'predecir'):
                probabilidades = modelo.predecir(X)
            else:
                probabilidades = modelo.predict(X)
            
            probabilidades = np.clip(probabilidades, 0, 1)
            
            registro.info(f"✅ Predicciones generadas con modelo entrenado")
            registro.info(f"   📊 Media: {probabilidades.mean():.3f}")
            registro.info(f"   📊 Min: {probabilidades.min():.3f}")
            registro.info(f"   📊 Max: {probabilidades.max():.3f}")
            registro.info(f"   📊 Std: {probabilidades.std():.3f}")
            
            return probabilidades
        
        except Exception as e:
            registro.warning(f"⚠️ Error usando modelo: {e}")
    
    # Fallback final
    registro.warning("⚠️ Usando predicciones aleatorias (no hay modelo)")
    np.random.seed(42)
    return np.random.uniform(0, 1, len(features))


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def main():
    registro.info("🚀 Iniciando tubería diaria de Orion...")
    registro.info(f"🕐 Hora Perú: {ahora_peru().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ============================================================
    # 1. DEFINIR REQUISITOS
    # ============================================================
    
    REQUERIDOS = ['consumo', 'clientes']
    
    UMBRALES = {
        'consumo': {
            'min_registros': 100,
            'columnas_requeridas': ['id_cliente', 'fecha', 'consumo_kwh']
        },
        'clientes': {
            'min_registros': 10,
            'columnas_requeridas': ['id_cliente', 'tipo_cliente']
        }
    }
    
    # ============================================================
    # 2. CARGAR DATOS
    # ============================================================
    
    registro.info("📂 Cargando datos desde datos/brutos/...")
    
    cargador = CargadorIncremental()
    
    datos = {
        'consumo': cargador.cargar_archivos_nuevos('consumo'),
        'alarmas': cargador.cargar_archivos_nuevos('alarmas'),
        'clientes': cargador.cargar_archivos_nuevos('clientes'),
        'facturacion': cargador.cargar_archivos_nuevos('facturacion'),
        'inspecciones': cargador.cargar_archivos_nuevos('inspecciones')
    }
    
    # Verificar datos requeridos
    for req in REQUERIDOS:
        if req not in datos or datos[req].empty:
            registro.error(f"❌ Dato requerido faltante: {req}")
            return
    
    registro.info("📊 Estado de datos cargados:")
    for nombre, df in datos.items():
        if not df.empty:
            registro.info(f"   ✅ {nombre}: {len(df)} registros")
        else:
            registro.info(f"   ⚠️ {nombre}: No disponible")
    
    # ============================================================
    # 3. LIMPIAR DATOS
    # ============================================================
    
    registro.info("🧹 Limpiando datos...")
    
    limpiador = LimpiadorDatos()
    
    consumo = limpiador.limpiar_consumo(datos['consumo'])
    clientes = limpiador.limpiar_clientes(datos['clientes'])
    
    alarmas = None
    if not datos['alarmas'].empty:
        alarmas = limpiador.limpiar_alarmas(datos['alarmas'])
    
    facturacion = None
    if not datos['facturacion'].empty:
        facturacion = limpiador.limpiar_facturacion(datos['facturacion'])
    
    inspecciones = None
    if not datos['inspecciones'].empty:
        inspecciones = datos['inspecciones']
    
    # ============================================================
    # 4. EXTRAER CARACTERÍSTICAS CAUSALES
    # ============================================================
    
    registro.info("📊 Extrayendo características causales...")
    
    extractor = ExtractorCaracteristicas()
    
    features = extractor.extraer_todas(
        consumo=consumo,
        alarmas=alarmas,
        facturacion=facturacion,
        inspecciones=inspecciones
    )
    
    if features.empty:
        registro.error("❌ No se pudieron extraer características")
        return
    
    registro.info(f"✅ Features extraídas: {len(features)} clientes")
    registro.info(f"   📊 Columnas: {len(features.columns)}")
    
    # ============================================================
    # 5. ENTRENAR MODELO SI NO EXISTE
    # ============================================================
    
    modelo_path = Path('modelos/actual/modelo_actual.pkl')
    
    if not modelo_path.exists():
        registro.info("🧠 No hay modelo. Entrenando...")
        entrenar_modelo(features)
    else:
        registro.info("✅ Modelo ya existe, reutilizando...")
    
    # ============================================================
    # 6. GENERAR PREDICCIONES
    # ============================================================
    
    probabilidades = generar_predicciones(features)
    
    # ============================================================
    # 7. PRIORIZAR
    # ============================================================
    
    registro.info("🎯 Priorizando suministros...")
    
    puntuador = PuntuadorSimple()
    puntajes = puntuador.calcular_puntajes(features, probabilidades)
    
    # ============================================================
    # 8. APRENDIZAJE ACTIVO
    # ============================================================
    
    activo = AprendizajeActivo()
    seleccionados = activo.seleccionar_casos(
        puntajes, probabilidades, 
        n=min(50, len(puntajes))
    )
    
    # ============================================================
    # 9. COMBINAR PUNTAJES + FEATURES
    # ============================================================
    
    registro.info("🔗 Combinando puntajes con features...")
    
    puntajes_completos = puntajes.merge(
        features,
        on='id_cliente',
        how='left',
        suffixes=('', '_feat')
    )
    
    # Eliminar duplicados
    columnas_duplicadas = [col for col in puntajes_completos.columns if col.endswith('_feat')]
    if columnas_duplicadas:
        puntajes_completos = puntajes_completos.drop(columns=columnas_duplicadas)
    
    # Seleccionar features finales
    selector = SelectorCaracteristicas()
    puntajes_finales = selector.seleccionar(puntajes_completos)
    
    registro.info(f"   📊 Columnas finales: {len(puntajes_finales.columns)}")
    
    # ============================================================
    # 10. GUARDAR RESULTADOS
    # ============================================================
    
    registro.info("💾 Guardando resultados...")
    
    processed_dir = Path('datos/procesados')
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    fecha_actual = ahora_peru()
    timestamp = timestamp_peru()
    
    # Guardar con timestamp
    puntajes_finales.to_parquet(processed_dir / f'puntajes_{timestamp}.parquet')
    seleccionados.to_csv(processed_dir / f'inspecciones_priorizadas_{timestamp}.csv', index=False)
    
    # Acumular en histórico
    puntajes_con_fecha = puntajes_finales.copy()
    puntajes_con_fecha['fecha_ejecucion'] = fecha_actual
    puntajes_con_fecha['ejecucion_id'] = timestamp
    puntajes_con_fecha['tipo_dato'] = 'puntaje'
    
    historico_path = processed_dir / 'historico_puntajes.parquet'
    
    if historico_path.exists():
        historico_existente = pd.read_parquet(historico_path)
        
        # Evitar duplicados con el mismo timestamp
        if 'ejecucion_id' in historico_existente.columns:
            if timestamp in historico_existente['ejecucion_id'].values:
                historico_existente = historico_existente[
                    historico_existente['ejecucion_id'] != timestamp
                ]
        
        historico_actualizado = pd.concat([historico_existente, puntajes_con_fecha], ignore_index=True)
        registro.info(f"   📊 Histórico: {len(historico_actualizado)} registros (+{len(puntajes_con_fecha)})")
    else:
        historico_actualizado = puntajes_con_fecha
        registro.info(f"   📊 Histórico creado: {len(historico_actualizado)} registros")
    
    historico_actualizado.to_parquet(historico_path, index=False)
    
    # Guardar última versión
    puntajes_finales.to_parquet(processed_dir / 'puntajes_latest.parquet')
    seleccionados.to_csv(processed_dir / 'inspecciones_priorizadas_latest.csv', index=False)
    
    # ============================================================
    # 11. ESTADÍSTICAS
    # ============================================================
    
    stats = {
        'timestamp': timestamp,
        'fecha': fecha_actual.isoformat(),
        'total_suministros': len(puntajes),
        'alta_prioridad': int((puntajes['prioridad'] == 'ALTA').sum()),
        'media_prioridad': int((puntajes['prioridad'] == 'MEDIA').sum()),
        'baja_prioridad': int((puntajes['prioridad'] == 'BAJA').sum()),
        'total_seleccionados': len(seleccionados),
        'total_historico': len(historico_actualizado),
        'features_usadas': puntajes_finales.columns.tolist()
    }
    
    with open(processed_dir / f'estadisticas_{timestamp}.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, default=str, ensure_ascii=False)
    
    # ============================================================
    # 12. RESUMEN
    # ============================================================
    
    registro.info("=" * 60)
    registro.info("✅ TUBERÍA DIARIA COMPLETADA")
    registro.info("=" * 60)
    registro.info(f"📊 Suministros priorizados: {len(puntajes)}")
    registro.info(f"⚡ Alta prioridad: {stats['alta_prioridad']}")
    registro.info(f"📊 Media prioridad: {stats['media_prioridad']}")
    registro.info(f"📉 Baja prioridad: {stats['baja_prioridad']}")
    registro.info(f"📋 Casos seleccionados: {len(seleccionados)}")
    registro.info(f"📚 Histórico: {len(historico_actualizado)} registros")
    registro.info(f"🔍 Features: {len(puntajes_finales.columns)}")
    registro.info("=" * 60)


if __name__ == "__main__":
    main()