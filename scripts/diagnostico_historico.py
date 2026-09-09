# scripts/diagnostico_historico.py
"""
Diagnóstico del histórico acumulado
"""

import pandas as pd
from pathlib import Path

def diagnosticar():
    print("=" * 60)
    print("🔍 DIAGNÓSTICO DEL HISTÓRICO")
    print("=" * 60)
    
    historico_path = Path('datos/procesados/historico_puntajes.parquet')
    
    if not historico_path.exists():
        print("❌ No existe el archivo histórico")
        return
    
    df = pd.read_parquet(historico_path)
    
    print(f"\n📊 Total registros: {len(df)}")
    print(f"📋 Columnas: {df.columns.tolist()}")
    
    if 'ejecucion_id' in df.columns:
        ejecuciones = df['ejecucion_id'].unique()
        print(f"\n🔄 Ejecuciones únicas: {len(ejecuciones)}")
        for i, exec_id in enumerate(ejecuciones, 1):
            count = len(df[df['ejecucion_id'] == exec_id])
            print(f"   {i}. {exec_id}: {count} registros")
    else:
        print("\n⚠️ No hay columna 'ejecucion_id'")
    
    if 'fecha_ejecucion' in df.columns:
        fechas = df['fecha_ejecucion'].unique()
        print(f"\n📅 Fechas únicas: {len(fechas)}")
        for fecha in fechas:
            count = len(df[df['fecha_ejecucion'] == fecha])
            print(f"   - {fecha}: {count} registros")
    else:
        print("\n⚠️ No hay columna 'fecha_ejecucion'")
    
    if 'id_cliente' in df.columns:
        total_clientes = df['id_cliente'].nunique()
        print(f"\n👥 Total clientes únicos: {total_clientes}")
    
    print("\n" + "=" * 60)
    
    # Ver si hay duplicados
    if 'ejecucion_id' in df.columns:
        duplicados = df.duplicated(subset=['id_cliente', 'ejecucion_id']).sum()
        if duplicados > 0:
            print(f"⚠️ {duplicados} registros duplicados (id_cliente + ejecucion_id)")

if __name__ == "__main__":
    diagnosticar()