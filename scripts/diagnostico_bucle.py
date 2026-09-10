# scripts/diagnostico_bucle.py
"""
Diagnóstico del bucle cerrado
"""

from pathlib import Path
import pandas as pd
import json

print("=" * 70)
print("🔍 DIAGNÓSTICO DEL BUCLE CERRADO")
print("=" * 70)

# 1. Verificar datos de entrenamiento
train_path = Path('datos/retroalimentacion/entrenamiento/datos_etiquetados.parquet')
print(f"\n1️⃣ Datos de entrenamiento ({train_path}):")
if train_path.exists():
    df = pd.read_parquet(train_path)
    print(f"   ✅ Existe: {len(df)} registros")
    print(f"   📊 Columnas: {df.columns.tolist()}")
    if 'label' in df.columns:
        print(f"   📊 Labels: {df['label'].value_counts().to_dict()}")
    if 'fecha_procesamiento' in df.columns:
        print(f"   📅 Fecha procesamiento: {df['fecha_procesamiento'].max()}")
else:
    print(f"   ❌ NO EXISTE")
    # Ver qué hay en la carpeta
    parent = train_path.parent
    if parent.exists():
        print(f"   📁 Contenido de {parent}:")
        for f in parent.glob('*'):
            print(f"      - {f.name}")
    else:
        print(f"   ⚠️ La carpeta {parent} no existe")

# 2. Verificar estado del bucle
estado_path = Path('datos/retroalimentacion/entrenamiento/estado_bucle.json')
print(f"\n2️⃣ Estado del bucle ({estado_path}):")
if estado_path.exists():
    with open(estado_path, 'r', encoding='utf-8') as f:
        estado = json.load(f)
    print(f"   ✅ Existe")
    print(f"   📊 Contenido: {json.dumps(estado, indent=6, default=str)}")
else:
    print(f"   ❌ NO EXISTE")

# 3. Verificar modelo actual
modelo_path = Path('modelos/actual/modelo_actual.pkl')
metrics_path = Path('modelos/actual/metrics.json')
print(f"\n3️⃣ Modelo actual ({modelo_path}):")
if modelo_path.exists():
    print(f"   ✅ Modelo existe")
else:
    print(f"   ❌ Modelo NO EXISTE")

print(f"\n4️⃣ Métricas del modelo ({metrics_path}):")
if metrics_path.exists():
    with open(metrics_path, 'r', encoding='utf-8') as f:
        metrics = json.load(f)
    print(f"   ✅ Métricas existen")
    print(f"   📊 Contenido: {json.dumps(metrics, indent=6, default=str)}")
else:
    print(f"   ❌ Métricas NO EXISTEN")

# 5. Verificar puntajes
puntajes_path = Path('datos/procesados/puntajes_latest.parquet')
print(f"\n5️⃣ Puntajes latest ({puntajes_path}):")
if puntajes_path.exists():
    df = pd.read_parquet(puntajes_path)
    print(f"   ✅ Existe: {len(df)} registros")
    print(f"   📊 Columnas: {df.columns.tolist()}")
else:
    print(f"   ❌ NO EXISTE")

print("\n" + "=" * 70)