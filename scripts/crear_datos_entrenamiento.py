# scripts/crear_datos_entrenamiento.py
"""
Crea datos de entrenamiento COMBINANDO:
- Features: desde datos/procesados/puntajes_latest.parquet
- Labels: desde datos/retroalimentacion/inspecciones/ (inspecciones reales)

IMPORTANTE:
- Solo lee inspecciones REALES
- Si no hay inspecciones, FALLA con error claro
- NO genera labels sintéticos en producción

Zona horaria: Perú (UTC-5)
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

sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
import json
from src.utilidades.registrador import registro
from src.utilidades.tiempo import ahora_peru, iso_peru


# ============================================================
# MAPEO DE RESULTADOS A LABELS
# ============================================================

LABEL_MAP = {
    # Positivos (hurto)
    'hurto confirmado': 1,
    'anomalía': 1,
    'anomalia': 1,
    # Negativos (no hurto)
    'normal': 0,
    'falso positivo': 0,
}


def normalizar_resultado(resultado):
    """Normaliza el resultado para mapeo consistente"""
    if pd.isna(resultado):
        return None
    
    resultado_str = str(resultado).lower().strip()
    
    # Eliminar tildes
    resultado_str = (
        resultado_str
        .replace('á', 'a')
        .replace('é', 'e')
        .replace('í', 'i')
        .replace('ó', 'o')
        .replace('ú', 'u')
        .replace('ñ', 'n')
    )
    
    return resultado_str


# ============================================================
# CARGAR INSPECCIONES
# ============================================================

def cargar_inspecciones():
    """
    Carga inspecciones desde las carpetas oficiales
    
    Prioridad:
    1. datos/retroalimentacion/inspecciones/
    2. datos/brutos/inspecciones/
    3. datos_pasados/inspecciones/
    """
    ubicaciones = [
        Path('datos/retroalimentacion/inspecciones'),
        Path('datos/brutos/inspecciones'),
        Path('datos_pasados/inspecciones'),
    ]
    
    for ubicacion in ubicaciones:
        if not ubicacion.exists():
            continue
        
        # Buscar CSV
        archivos_csv = list(ubicacion.glob('*.csv'))
        if archivos_csv:
            try:
                dfs = [pd.read_csv(f) for f in archivos_csv]
                df = pd.concat(dfs, ignore_index=True)
                registro.info(f"📂 Inspecciones: {ubicacion} ({len(archivos_csv)} archivos, {len(df)} registros)")
                return df, str(ubicacion)
            except Exception as e:
                registro.warning(f"⚠️ Error cargando {ubicacion}: {e}")
        
        # Buscar Parquet
        archivos_parquet = list(ubicacion.glob('*.parquet'))
        if archivos_parquet:
            try:
                dfs = [pd.read_parquet(f) for f in archivos_parquet]
                df = pd.concat(dfs, ignore_index=True)
                registro.info(f"📂 Inspecciones: {ubicacion} ({len(archivos_parquet)} archivos, {len(df)} registros)")
                return df, str(ubicacion)
            except Exception as e:
                registro.warning(f"⚠️ Error cargando {ubicacion}: {e}")
    
    return None, None


# ============================================================
# CREAR DATOS DE ENTRENAMIENTO
# ============================================================

def crear_datos_entrenamiento() -> bool:
    """
    Crea datos_etiquetados.parquet combinando features + labels
    """
    registro.info("=" * 70)
    registro.info("📊 CREANDO DATOS DE ENTRENAMIENTO")
    registro.info(f"🕐 Hora Perú: {ahora_peru().strftime('%Y-%m-%d %H:%M:%S')}")
    registro.info("=" * 70)
    
    train_dir = Path('datos/retroalimentacion/entrenamiento')
    train_dir.mkdir(parents=True, exist_ok=True)
    train_path = train_dir / 'datos_etiquetados.parquet'
    
    # ============================================================
    # 1. CARGAR FEATURES
    # ============================================================
    
    puntajes_path = Path('datos/procesados/puntajes_latest.parquet')
    if not puntajes_path.exists():
        registro.error(f"❌ No existe: {puntajes_path}")
        registro.info("   Ejecuta primero: python scripts/ejecutar_tuberia_diaria.py")
        return False
    
    features = pd.read_parquet(puntajes_path)
    registro.info(f"\n📂 Features cargadas: {len(features)} registros")
    registro.info(f"   📊 Columnas ({len(features.columns)}): {features.columns.tolist()[:10]}...")
    
    # ============================================================
    # 2. CARGAR INSPECCIONES
    # ============================================================
    
    inspecciones, fuente = cargar_inspecciones()
    
    if inspecciones is None or inspecciones.empty:
        registro.error("=" * 70)
        registro.error("❌ NO HAY INSPECCIONES DISPONIBLES")
        registro.error("=" * 70)
        registro.error("")
        registro.error("📌 Ubicaciones buscadas:")
        registro.error("   1. datos/retroalimentacion/inspecciones/")
        registro.error("   2. datos/brutos/inspecciones/")
        registro.error("   3. datos_pasados/inspecciones/")
        registro.error("")
        registro.error("💡 Solución:")
        registro.error("   - Ejecuta el flujo completo para generar inspecciones")
        registro.error("   - O coloca un archivo CSV con inspecciones reales")
        registro.error("=" * 70)
        return False
    
    registro.info(f"\n📂 Inspecciones: {len(inspecciones)} registros")
    registro.info(f"   📊 Columnas: {inspecciones.columns.tolist()}")
    registro.info(f"   📊 Fuente: {fuente}")
    
    # ============================================================
    # 3. VALIDAR COLUMNAS
    # ============================================================
    
    if 'id_cliente' not in inspecciones.columns:
        registro.error("❌ Inspecciones no tienen columna 'id_cliente'")
        return False
    
    # Buscar columna de resultado
    columna_resultado = None
    for col in ['resultado', 'RESULTADO', 'Resultado']:
        if col in inspecciones.columns:
            columna_resultado = col
            break
    
    if columna_resultado is None:
        registro.error("❌ Inspecciones no tienen columna de resultado")
        return False
    
    registro.info(f"   📊 Columna de resultado: {columna_resultado}")
    
    # ============================================================
    # 4. MAPEAR RESULTADOS A LABELS
    # ============================================================
    
    # Normalizar id_cliente
    inspecciones['id_cliente_norm'] = (
        inspecciones['id_cliente']
        .astype(str)
        .str.strip()
        .str.upper()
    )
    
    features['id_cliente_norm'] = (
        features['id_cliente']
        .astype(str)
        .str.strip()
        .str.upper()
    )
    
    # Normalizar resultado y mapear a label
    inspecciones['resultado_norm'] = inspecciones[columna_resultado].apply(normalizar_resultado)
    inspecciones['label'] = inspecciones['resultado_norm'].map(LABEL_MAP)
    
    # Reportar valores no mapeados
    no_mapeados = inspecciones['label'].isna()
    if no_mapeados.any():
        valores_no_mapeados = inspecciones[no_mapeados][columna_resultado].unique()
        registro.warning(f"⚠️ {no_mapeados.sum()} resultados no reconocidos")
        registro.warning(f"   Valores: {valores_no_mapeados[:5]}")
    
    # Eliminar los no mapeados
    inspecciones = inspecciones.dropna(subset=['label'])
    inspecciones['label'] = inspecciones['label'].astype(int)
    
    registro.info(f"\n📊 Labels mapeados:")
    registro.info(f"   ✅ Positivos (hurto): {(inspecciones['label'] == 1).sum()}")
    registro.info(f"   ❌ Negativos (normal): {(inspecciones['label'] == 0).sum()}")
    
    # ============================================================
    # 5. AGRUPAR POR CLIENTE
    # ============================================================
    
    # Si un cliente tiene múltiples inspecciones, tomar el label máximo
    # (si hurto alguna vez, cuenta como hurto)
    labels_agrupados = inspecciones.groupby('id_cliente_norm').agg({
        'label': 'max'
    }).reset_index()
    
    registro.info(f"\n📊 Clientes únicos con label: {len(labels_agrupados)}")
    registro.info(f"   ✅ Positivos: {(labels_agrupados['label'] == 1).sum()}")
    registro.info(f"   ❌ Negativos: {(labels_agrupados['label'] == 0).sum()}")
    
    # ============================================================
    # 6. COMBINAR FEATURES + LABELS
    # ============================================================
    
    datos_entrenamiento = features.merge(
        labels_agrupados,
        on='id_cliente_norm',
        how='left'
    )
    
    # Clientes sin inspección se consideran NO HURTO (label=0)
    # Esto es correcto porque no hay evidencia de hurto
    sin_label = datos_entrenamiento['label'].isna().sum()
    datos_entrenamiento['label'] = datos_entrenamiento['label'].fillna(0).astype(int)
    
    registro.info(f"\n📊 Datos combinados:")
    registro.info(f"   📊 Total: {len(datos_entrenamiento)} registros")
    registro.info(f"   ✅ Positivos: {(datos_entrenamiento['label'] == 1).sum()}")
    registro.info(f"   ❌ Negativos: {(datos_entrenamiento['label'] == 0).sum()}")
    registro.info(f"   ℹ️ Sin inspección previa (label=0): {sin_label}")
    
    # ============================================================
    # 7. VALIDAR QUE HAYA AMBAS CLASES
    # ============================================================
    
    positivos = int(datos_entrenamiento['label'].sum())
    negativos = len(datos_entrenamiento) - positivos
    
    if positivos == 0:
        registro.error("❌ No hay casos positivos (hurto) en los datos")
        registro.error("   Se necesitan al menos algunos casos de hurto")
        return False
    
    if negativos == 0:
        registro.error("❌ No hay casos negativos (normal) en los datos")
        return False
    
    # Advertir si hay muy pocos positivos
    ratio_positivos = positivos / len(datos_entrenamiento)
    if ratio_positivos < 0.05:
        registro.warning(f"⚠️ Muy pocos positivos ({ratio_positivos*100:.1f}%)")
        registro.warning(f"   El modelo puede tener problemas de desbalanceo")
    
    # ============================================================
    # 8. SELECCIONAR FEATURES PARA EL MODELO
    # ============================================================
    
    from src.caracteristicas.selector import SelectorCaracteristicas
    
    selector = SelectorCaracteristicas()
    features_modelo = selector.obtener_features_modelo()
    
    # Filtrar las que existan
    features_disponibles = [f for f in features_modelo if f in datos_entrenamiento.columns]
    features_faltantes = [f for f in features_modelo if f not in datos_entrenamiento.columns]
    
    if features_faltantes:
        registro.warning(f"⚠️ Features faltantes: {features_faltantes}")
    
    registro.info(f"\n📊 Features para el modelo: {len(features_disponibles)}")
    for f in features_disponibles:
        registro.info(f"   - {f}")
    
    # ============================================================
    # 9. GUARDAR
    # ============================================================
    
    # Agregar fecha de procesamiento
    datos_entrenamiento['fecha_procesamiento'] = ahora_peru()
    
    # Guardar
    datos_entrenamiento.to_parquet(train_path, index=False)
    
    registro.info(f"\n💾 Guardado: {train_path}")
    registro.info(f"   📊 Total registros: {len(datos_entrenamiento)}")
    registro.info(f"   📊 Total columnas: {len(datos_entrenamiento.columns)}")
    
    # ============================================================
    # 10. ACTUALIZAR ESTADO DEL BUCLE
    # ============================================================
    
    estado_path = train_dir / 'estado_bucle.json'
    
    if estado_path.exists():
        try:
            with open(estado_path, 'r', encoding='utf-8') as f:
                estado = json.load(f)
        except:
            estado = {}
    else:
        estado = {}
    
    estado.update({
        'total_muestras': len(datos_entrenamiento),
        'total_positivos': positivos,
        'total_negativos': negativos,
        'features_modelo': features_disponibles,
        'ultima_actualizacion': iso_peru(),
        'fuente_inspecciones': fuente
    })
    
    if 'ultimo_reentrenamiento' not in estado:
        estado['ultimo_reentrenamiento'] = None
    if 'version_actual' not in estado:
        estado['version_actual'] = 'v0.0.0'
    if 'metricas_historial' not in estado:
        estado['metricas_historial'] = []
    
    with open(estado_path, 'w', encoding='utf-8') as f:
        json.dump(estado, f, indent=2, default=str, ensure_ascii=False)
    
    registro.info(f"💾 Estado del bucle actualizado: {estado_path}")
    
    registro.info("=" * 70)
    registro.info("✅ DATOS DE ENTRENAMIENTO CREADOS")
    registro.info("=" * 70)
    
    return True


def main():
    """Función principal"""
    if crear_datos_entrenamiento():
        registro.info("✅ Proceso completado")
    else:
        registro.error("❌ Proceso falló")
        sys.exit(1)


if __name__ == "__main__":
    main()