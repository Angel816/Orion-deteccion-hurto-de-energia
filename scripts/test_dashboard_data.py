# scripts/test_dashboard_data.py
"""
Prueba rápida para ver qué datos carga el dashboard
"""

import pandas as pd
from pathlib import Path

print("=" * 60)
print("🔍 VERIFICANDO DATOS DEL DASHBOARD")
print("=" * 60)

# 1. Verificar histórico
historico_path = Path('datos/procesados/historico_puntajes.parquet')
if historico_path.exists():
    df_historico = pd.read_parquet(historico_path)
    print(f"\n📊 HISTÓRICO:")
    print(f"   Total registros: {len(df_historico)}")
    print(f"   Ejecuciones: {df_historico['ejecucion_id'].nunique()}")
    print(f"   Clientes únicos: {df_historico['id_cliente'].nunique()}")
else:
    print("\n❌ No existe histórico")

# 2. Verificar última versión
latest_path = Path('datos/procesados/puntajes_latest.parquet')
if latest_path.exists():
    df_latest = pd.read_parquet(latest_path)
    print(f"\n📊 ÚLTIMA VERSIÓN:")
    print(f"   Total registros: {len(df_latest)}")
else:
    print("\n❌ No existe última versión")

# 3. Calcular lo que debería mostrar el dashboard
print("\n" + "=" * 60)
print("📋 LO QUE DEBERÍA MOSTRAR EL DASHBOARD:")
print(f"   Total Suministros (Acumulado): {df_historico['id_cliente'].nunique() if historico_path.exists() else 0}")
print(f"   Total Ejecuciones: {df_historico['ejecucion_id'].nunique() if historico_path.exists() else 0}")
print(f"   Última Ejecución: {len(df_latest) if latest_path.exists() else 0}")
print("=" * 60)