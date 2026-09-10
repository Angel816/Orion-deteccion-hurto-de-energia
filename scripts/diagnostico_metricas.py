# scripts/diagnostico_metricas.py
"""
Diagnóstico de métricas para el dashboard
"""

from pathlib import Path
import json

print("=" * 60)
print("🔍 DIAGNÓSTICO DE MÉTRICAS")
print("=" * 60)

# 1. Verificar métricas del modelo
metrics_path = Path('modelos/actual/metrics.json')
print(f"\n1️⃣ Métricas del modelo ({metrics_path}):")
if metrics_path.exists():
    with open(metrics_path, 'r', encoding='utf-8') as f:
        metricas = json.load(f)
    print(f"   ✅ Existe")
    print(f"   📊 Contenido: {json.dumps(metricas, indent=6)}")
else:
    print(f"   ❌ NO EXISTE")
    print(f"   📁 Contenido de modelos/actual/:")
    modelos_dir = Path('modelos/actual')
    if modelos_dir.exists():
        for archivo in modelos_dir.glob('*'):
            print(f"      - {archivo.name}")
    else:
        print(f"      ⚠️ La carpeta modelos/actual/ no existe")

# 2. Verificar estado del bucle cerrado
bucle_path = Path('datos/retroalimentacion/entrenamiento/estado_bucle.json')
print(f"\n2️⃣ Estado del bucle cerrado ({bucle_path}):")
if bucle_path.exists():
    with open(bucle_path, 'r', encoding='utf-8') as f:
        estado = json.load(f)
    print(f"   ✅ Existe")
    print(f"   📊 Contenido: {json.dumps(estado, indent=6, default=str)}")
else:
    print(f"   ❌ NO EXISTE")

# 3. Verificar inspecciones históricas
insp_dir = Path('datos/retroalimentacion/inspecciones')
print(f"\n3️⃣ Inspecciones históricas ({insp_dir}):")
if insp_dir.exists():
    archivos = list(insp_dir.glob('*.csv'))
    print(f"   ✅ {len(archivos)} archivos encontrados")
    for archivo in archivos:
        print(f"      - {archivo.name} ({archivo.stat().st_size / 1024:.1f} KB)")
else:
    print(f"   ❌ NO EXISTE")

# 4. Verificar inspecciones en brutos (por si acaso)
insp_brutos = Path('datos/brutos/inspecciones')
print(f"\n4️⃣ Inspecciones en brutos ({insp_brutos}):")
if insp_brutos.exists():
    archivos = list(insp_brutos.glob('*.parquet'))
    print(f"   ✅ {len(archivos)} archivos encontrados")
    for archivo in archivos:
        print(f"      - {archivo.name}")
else:
    print(f"   ❌ NO EXISTE")

# 5. Verificar datos procesados
proc_dir = Path('datos/procesados')
print(f"\n5️⃣ Datos procesados ({proc_dir}):")
if proc_dir.exists():
    archivos = list(proc_dir.glob('*'))
    print(f"   ✅ {len(archivos)} archivos encontrados")
    for archivo in archivos[:10]:
        print(f"      - {archivo.name}")

# 6. Verificar modelos/actual
modelos_actual = Path('modelos/actual')
print(f"\n6️⃣ Modelos actuales ({modelos_actual}):")
if modelos_actual.exists():
    archivos = list(modelos_actual.glob('*'))
    if archivos:
        print(f"   ✅ {len(archivos)} archivos encontrados")
        for archivo in archivos:
            print(f"      - {archivo.name}")
    else:
        print(f"   ⚠️ Carpeta vacía")

print("\n" + "=" * 60)