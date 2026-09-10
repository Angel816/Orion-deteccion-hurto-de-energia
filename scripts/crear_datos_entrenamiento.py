# scripts/crear_datos_entrenamiento.py
"""
Crea datos de entrenamiento COMBINANDO features (puntajes) con labels (inspecciones)
Zona horaria: Perú (UTC-5)

Lee inspecciones desde carpetas oficiales:
1. datos/retroalimentacion/inspecciones/  (prioridad 1)
2. datos/brutos/inspecciones/             (prioridad 2)
3. datos_pasados/inspecciones/            (prioridad 3)

NO usa datos/muestra/
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
import json
from src.utilidades.registrador import registro
from src.utilidades.tiempo import ahora_peru, iso_peru


def cargar_inspecciones() -> tuple:
    """
    Carga inspecciones desde las carpetas oficiales
    
    Retorna:
        (DataFrame, fuente) o (None, None) si no hay
    """
    # 1. Prioridad 1: retroalimentación
    insp_feedback = Path('datos/retroalimentacion/inspecciones')
    if insp_feedback.exists():
        archivos = list(insp_feedback.glob('*.csv'))
        if archivos:
            try:
                dfs = [pd.read_csv(f) for f in archivos]
                df = pd.concat(dfs, ignore_index=True)
                registro.info(f"📂 Inspecciones cargadas desde: {insp_feedback} ({len(archivos)} archivos)")
                return df, str(insp_feedback)
            except Exception as e:
                registro.warning(f"⚠️ Error cargando {insp_feedback}: {e}")
    
    # 2. Prioridad 2: brutos
    insp_brutos = Path('datos/brutos/inspecciones')
    if insp_brutos.exists():
        archivos = list(insp_brutos.glob('*.parquet'))
        if archivos:
            try:
                dfs = [pd.read_parquet(f) for f in archivos]
                df = pd.concat(dfs, ignore_index=True)
                registro.info(f"📂 Inspecciones cargadas desde: {insp_brutos} ({len(archivos)} archivos)")
                return df, str(insp_brutos)
            except Exception as e:
                registro.warning(f"⚠️ Error cargando {insp_brutos}: {e}")
    
    # 3. Prioridad 3: datos_pasados
    insp_pasados = Path('datos_pasados/inspecciones')
    if insp_pasados.exists():
        archivos = list(insp_pasados.glob('*.parquet'))
        if archivos:
            try:
                dfs = [pd.read_parquet(f) for f in archivos]
                df = pd.concat(dfs, ignore_index=True)
                registro.info(f"📂 Inspecciones cargadas desde: {insp_pasados} ({len(archivos)} archivos)")
                return df, str(insp_pasados)
            except Exception as e:
                registro.warning(f"⚠️ Error cargando {insp_pasados}: {e}")
    
    return None, None


def crear_datos_entrenamiento() -> bool:
    """
    Crea el archivo datos_etiquetados.parquet combinando:
    - Features: desde datos/procesados/puntajes_latest.parquet
    - Labels: desde carpetas oficiales de inspecciones
    """
    registro.info("📊 Creando datos de entrenamiento...")
    registro.info(f"🕐 Hora Perú: {ahora_peru().strftime('%Y-%m-%d %H:%M:%S')}")
    
    train_dir = Path('datos/retroalimentacion/entrenamiento')
    train_dir.mkdir(parents=True, exist_ok=True)
    train_path = train_dir / 'datos_etiquetados.parquet'
    
    # ============================================================
    # 1. CARGAR FEATURES (PUNTAJES)
    # ============================================================
    
    puntajes_path = Path('datos/procesados/puntajes_latest.parquet')
    if not puntajes_path.exists():
        registro.error(f"❌ No existe: {puntajes_path}")
        registro.info("   Ejecuta primero: python scripts/ejecutar_tuberia_diaria.py")
        return False
    
    features = pd.read_parquet(puntajes_path)
    registro.info(f"📂 Features cargadas: {len(features)} registros")
    registro.info(f"   📊 Columnas: {features.columns.tolist()}")
    
    # ============================================================
    # 2. CARGAR INSPECCIONES (LABELS)
    # ============================================================
    
    inspecciones, fuente = cargar_inspecciones()
    
    # Si no hay inspecciones, generar labels sintéticos
    if inspecciones is None or inspecciones.empty:
        registro.warning("⚠️ No hay inspecciones disponibles en carpetas oficiales")
        registro.info("📊 Generando labels sintéticos para entrenamiento...")
        
        np.random.seed(42)
        inspecciones = pd.DataFrame({
            'id_cliente': features['id_cliente'],
            'resultado': np.random.choice(
                ['Hurto Confirmado', 'Normal', 'Anomalía'],
                size=len(features),
                p=[0.2, 0.6, 0.2]
            )
        })
        fuente = 'sintetico'
        registro.info(f"   ✅ Labels sintéticos generados: {len(inspecciones)} registros")
    
    registro.info(f"   📊 Inspecciones: {len(inspecciones)} registros")
    registro.info(f"   📊 Columnas: {inspecciones.columns.tolist()}")
    
    # ============================================================
    # 3. NORMALIZAR ID_CLIENTE (por si hay formatos diferentes)
    # ============================================================
    
    # Limpiar id_cliente en inspecciones
    if 'id_cliente' in inspecciones.columns:
        inspecciones['id_cliente'] = inspecciones['id_cliente'].astype(str).str.strip().str.upper()
        inspecciones['id_cliente'] = inspecciones['id_cliente'].str.replace(' ', '')
    
    # Limpiar id_cliente en features
    if 'id_cliente' in features.columns:
        features['id_cliente'] = features['id_cliente'].astype(str).str.strip().str.upper()
        features['id_cliente'] = features['id_cliente'].str.replace(' ', '')
    
    # ============================================================
    # 4. MAPEAR RESULTADOS A LABELS
    # ============================================================
    
    label_map = {
        'HURTO CONFIRMADO': 1,
        'Hurto Confirmado': 1,
        'ANOMALÍA': 1,
        'Anomalía': 1,
        'ANOMALIA': 1,
        'Anomalia': 1,
        'NORMAL': 0,
        'Normal': 0,
        'FALSO POSITIVO': 0,
        'Falso Positivo': 0,
    }
    
    if 'resultado' in inspecciones.columns:
        # Normalizar texto
        inspecciones['resultado_limpio'] = inspecciones['resultado'].astype(str).str.strip()
        inspecciones['label'] = inspecciones['resultado_limpio'].map(label_map)
        
        # Si hay valores sin mapear, intentar con mayúsculas
        if inspecciones['label'].isna().any():
            inspecciones['label'] = inspecciones['label'].fillna(
                inspecciones['resultado_limpio'].str.upper().map(label_map)
            )
        
        # Rellenar NaN con 0
        inspecciones['label'] = inspecciones['label'].fillna(0).astype(int)
    elif 'label' in inspecciones.columns:
        inspecciones['label'] = inspecciones['label'].fillna(0).astype(int)
    else:
        registro.warning("⚠️ No hay columna 'resultado' ni 'label', asignando 0")
        inspecciones['label'] = 0
    
    # ============================================================
    # 5. COMBINAR FEATURES + LABELS
    # ============================================================
    
    if 'id_cliente' not in inspecciones.columns:
        registro.error("❌ Inspecciones no tienen id_cliente")
        return False
    
    # Agrupar inspecciones por id_cliente (tomar label máximo)
    labels_agrupados = inspecciones.groupby('id_cliente').agg({
        'label': 'max'
    }).reset_index()
    
    registro.info(f"📊 Clientes con labels: {len(labels_agrupados)}")
    registro.info(f"   📊 Positivos: {int(labels_agrupados['label'].sum())}")
    registro.info(f"   📊 Negativos: {len(labels_agrupados) - int(labels_agrupados['label'].sum())}")
    
    # Merge con features
    datos_entrenamiento = features.merge(
        labels_agrupados,
        on='id_cliente',
        how='left'
    )
    
    # Rellenar labels faltantes con 0
    datos_entrenamiento['label'] = datos_entrenamiento['label'].fillna(0).astype(int)
    
    # Agregar fecha de procesamiento
    datos_entrenamiento['fecha_procesamiento'] = ahora_peru()
    
    registro.info(f"✅ Datos combinados: {len(datos_entrenamiento)} registros")
    
    # ============================================================
    # 6. SELECCIONAR FEATURES PARA EL MODELO
    # ============================================================
    
    features_modelo = []
    
    # Features base de puntajes
    features_base = ['probabilidad', 'impacto_economico', 'historial', 'puntaje_prioridad']
    for col in features_base:
        if col in datos_entrenamiento.columns:
            features_modelo.append(col)
    
    # Features adicionales si existen
    features_extra = [
        'consumo_promedio', 'consumo_std', 'consumo_media', 
        'consumo_desviacion', 'total_alarmas', 'alarmas_total',
        'consumo_cv', 'consumo_rango', 'caida_brusca'
    ]
    for col in features_extra:
        if col in datos_entrenamiento.columns:
            features_modelo.append(col)
    
    registro.info(f"📊 Features para el modelo: {features_modelo}")
    
    # ============================================================
    # 7. GUARDAR DATOS DE ENTRENAMIENTO
    # ============================================================
    
    datos_entrenamiento.to_parquet(train_path, index=False)
    registro.info(f"💾 Datos guardados en: {train_path}")
    registro.info(f"   📊 Total: {len(datos_entrenamiento)} registros")
    
    positivos = int(datos_entrenamiento['label'].sum())
    negativos = len(datos_entrenamiento) - positivos
    registro.info(f"   📊 Positivos: {positivos}")
    registro.info(f"   📊 Negativos: {negativos}")
    
    # ============================================================
    # 8. ACTUALIZAR ESTADO DEL BUCLE CERRADO
    # ============================================================
    
    estado_path = train_dir / 'estado_bucle.json'
    
    # Cargar estado existente o crear nuevo
    if estado_path.exists():
        try:
            with open(estado_path, 'r', encoding='utf-8') as f:
                estado = json.load(f)
        except:
            estado = {}
    else:
        estado = {}
    
    # Actualizar
    estado.update({
        'total_muestras': len(datos_entrenamiento),
        'features_modelo': features_modelo,
        'ultima_actualizacion': iso_peru(),
        'fuente_inspecciones': fuente
    })
    
    # Asegurar campos requeridos
    if 'ultimo_reentrenamiento' not in estado:
        estado['ultimo_reentrenamiento'] = None
    if 'version_actual' not in estado:
        estado['version_actual'] = 'v0.0.0'
    if 'metricas_historial' not in estado:
        estado['metricas_historial'] = []
    
    with open(estado_path, 'w', encoding='utf-8') as f:
        json.dump(estado, f, indent=2, default=str, ensure_ascii=False)
    
    registro.info(f"✅ Estado del bucle guardado: {estado_path}")
    
    return True


def main():
    """Función principal"""
    registro.info("🚀 Iniciando creación de datos de entrenamiento...")
    registro.info(f"🕐 Hora Perú: {ahora_peru().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if crear_datos_entrenamiento():
        registro.info("✅ Proceso completado correctamente")
    else:
        registro.error("❌ Proceso falló")


if __name__ == "__main__":
    main()