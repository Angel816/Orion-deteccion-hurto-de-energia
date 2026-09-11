# scripts/test_extractor.py
"""
Test rápido del extractor de características
"""

import sys
import io
import os
from pathlib import Path

# Configurar UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.environ['PYTHONIOENCODING'] = 'utf-8'

sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
from src.caracteristicas.extractor import ExtractorCaracteristicas

print("=" * 70)
print("🧪 TEST DEL EXTRACTOR DE CARACTERÍSTICAS")
print("=" * 70)

# 1. Cargar datos
print("\n📂 Cargando datos...")

consumo = None
consumo_path = Path('datos/brutos/consumo')
if consumo_path.exists():
    archivos = list(consumo_path.glob('*.parquet'))
    if archivos:
        consumo = pd.concat([pd.read_parquet(f) for f in archivos], ignore_index=True)
        print(f"   ✅ Consumo: {len(consumo)} registros")
        print(f"      Columnas: {consumo.columns.tolist()}")

alarmas = None
alarmas_path = Path('datos/brutos/alarmas')
if alarmas_path.exists():
    archivos = list(alarmas_path.glob('*.parquet'))
    if archivos:
        alarmas = pd.concat([pd.read_parquet(f) for f in archivos], ignore_index=True)
        print(f"   ✅ Alarmas: {len(alarmas)} registros")
        print(f"      Columnas: {alarmas.columns.tolist()}")

facturacion = None
fact_path = Path('datos/brutos/facturacion')
if fact_path.exists():
    archivos = list(fact_path.glob('*.parquet'))
    if archivos:
        facturacion = pd.concat([pd.read_parquet(f) for f in archivos], ignore_index=True)
        print(f"   ✅ Facturación: {len(facturacion)} registros")

inspecciones = None
insp_path = Path('datos/brutos/inspecciones')
if insp_path.exists():
    archivos = list(insp_path.glob('*.parquet'))
    if archivos:
        inspecciones = pd.concat([pd.read_parquet(f) for f in archivos], ignore_index=True)
        print(f"   ✅ Inspecciones: {len(inspecciones)} registros")

# 2. Extraer características
print("\n" + "=" * 70)
print("📊 EXTRAYENDO CARACTERÍSTICAS")
print("=" * 70)

extractor = ExtractorCaracteristicas()

# Verificar el método
import inspect
sig = inspect.signature(extractor.extraer_todas)
print(f"\n📋 Firma del método extraer_todas: {sig}")

features = extractor.extraer_todas(
    consumo=consumo,
    alarmas=alarmas,
    facturacion=facturacion,
    inspecciones=inspecciones
)

print(f"\n📊 Total features: {len(features.columns)}")
print(f"📊 Total clientes: {len(features)}")
print(f"\n📋 Columnas generadas:")
for col in features.columns:
    print(f"   - {col}")

# 3. Verificar features específicas
print("\n" + "=" * 70)
print("🔍 VERIFICACIÓN DE FEATURES ESPECÍFICAS")
print("=" * 70)

features_esperadas = [
    'consumo_promedio', 'consumo_media',
    'total_alarmas', 'alarmas_total',
    'inspecciones_previas', 'dias_mora'
]

for feat in features_esperadas:
    if feat in features.columns:
        print(f"   ✅ {feat} = {features[feat].mean():.2f} (promedio)")
    else:
        print(f"   ❌ {feat} NO EXISTE")