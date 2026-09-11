# scripts/diagnostico_features.py
"""
Diagnóstico de features disponibles en el sistema
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
from src.utilidades.registrador import registro


def diagnosticar():
    """Diagnostica las features disponibles"""
    
    print("=" * 70)
    print("🔍 DIAGNÓSTICO DE FEATURES")
    print("=" * 70)
    
    # ============================================================
    # 1. VERIFICAR PUNTAJES LATEST
    # ============================================================
    
    print("\n1️⃣ PUNTAJES LATEST (datos/procesados/puntajes_latest.parquet)")
    print("-" * 70)
    
    puntajes_path = Path('datos/procesados/puntajes_latest.parquet')
    
    if puntajes_path.exists():
        df = pd.read_parquet(puntajes_path)
        print(f"   ✅ Existe: {len(df)} registros")
        print(f"   📊 Columnas ({len(df.columns)}):")
        for col in df.columns:
            dtype = str(df[col].dtype)
            nulos = df[col].isna().sum()
            unicos = df[col].nunique()
            
            if df[col].dtype in ['float64', 'int64']:
                min_val = df[col].min()
                max_val = df[col].max()
                print(f"      - {col:30s} | {dtype:10s} | únicos: {unicos:5d} | min: {min_val:8.2f} | max: {max_val:8.2f}")
            else:
                print(f"      - {col:30s} | {dtype:10s} | únicos: {unicos:5d}")
    else:
        print(f"   ❌ NO EXISTE")
    
    # ============================================================
    # 2. VERIFICAR HISTÓRICO
    # ============================================================
    
    print("\n2️⃣ HISTÓRICO (datos/procesados/historico_puntajes.parquet)")
    print("-" * 70)
    
    historico_path = Path('datos/procesados/historico_puntajes.parquet')
    
    if historico_path.exists():
        df = pd.read_parquet(historico_path)
        print(f"   ✅ Existe: {len(df)} registros")
        print(f"   📊 Columnas ({len(df.columns)}):")
        for col in df.columns:
            print(f"      - {col}")
    else:
        print(f"   ❌ NO EXISTE")
    
    # ============================================================
    # 3. VERIFICAR DATOS DE ENTRENAMIENTO
    # ============================================================
    
    print("\n3️⃣ DATOS DE ENTRENAMIENTO (datos/retroalimentacion/entrenamiento/datos_etiquetados.parquet)")
    print("-" * 70)
    
    train_path = Path('datos/retroalimentacion/entrenamiento/datos_etiquetados.parquet')
    
    if train_path.exists():
        df = pd.read_parquet(train_path)
        print(f"   ✅ Existe: {len(df)} registros")
        print(f"   📊 Columnas ({len(df.columns)}):")
        for col in df.columns:
            print(f"      - {col}")
        
        if 'label' in df.columns:
            print(f"\n   📊 Labels: {df['label'].value_counts().to_dict()}")
    else:
        print(f"   ❌ NO EXISTE")
    
    # ============================================================
    # 4. VERIFICAR MÉTRICAS DEL MODELO
    # ============================================================
    
    print("\n4️⃣ MÉTRICAS DEL MODELO (modelos/actual/metrics.json)")
    print("-" * 70)
    
    import json
    metrics_path = Path('modelos/actual/metrics.json')
    
    if metrics_path.exists():
        with open(metrics_path, 'r', encoding='utf-8') as f:
            metricas = json.load(f)
        print(f"   ✅ Existe")
        for key, value in metricas.items():
            if isinstance(value, list):
                print(f"      {key}: {value}")
            else:
                print(f"      {key}: {value}")
    else:
        print(f"   ❌ NO EXISTE")
    
    # ============================================================
    # 5. VERIFICAR FEATURES EN DATOS BRUTOS
    # ============================================================
    
    print("\n5️⃣ FEATURES EN DATOS BRUTOS")
    print("-" * 70)
    
    for tipo in ['consumo', 'alarmas', 'clientes', 'facturacion']:
        tipo_dir = Path(f'datos/brutos/{tipo}')
        if tipo_dir.exists():
            archivos = list(tipo_dir.glob('*.parquet'))
            if archivos:
                df = pd.concat([pd.read_parquet(f) for f in archivos[:1]], ignore_index=True)
                print(f"\n   📂 {tipo}: {len(df)} registros")
                print(f"      Columnas: {df.columns.tolist()}")
    
    # ============================================================
    # 6. ANÁLISIS DE CORRELACIÓN
    # ============================================================
    
    print("\n6️⃣ ANÁLISIS DE CORRELACIÓN")
    print("-" * 70)
    
    if puntajes_path.exists():
        df = pd.read_parquet(puntajes_path)
        
        # Identificar columnas numéricas
        columnas_excluir = ['id_cliente', 'prioridad']
        features_num = [col for col in df.columns 
                        if col not in columnas_excluir 
                        and df[col].dtype in ['float64', 'int64', 'float32', 'int32']]
        
        if len(features_num) > 1:
            print(f"\n   Features numéricas: {features_num}")
            corr = df[features_num].corr()
            print(f"\n   📊 Matriz de correlación:")
            print(corr.to_string())
    
    # ============================================================
    # 7. VERIFICAR CARACTERÍSTICAS ESPECÍFICAS
    # ============================================================
    
    print("\n7️⃣ VERIFICACIÓN DE CARACTERÍSTICAS ESPECÍFICAS")
    print("-" * 70)
    
    features_necesarias = [
        'consumo_promedio',
        'consumo_media',
        'total_alarmas',
        'alarmas_total',
        'inspecciones_previas',
        'dias_mora',
        'impacto_economico',
        'historial',
        'probabilidad',
        'puntaje_prioridad'
    ]
    
    if puntajes_path.exists():
        df = pd.read_parquet(puntajes_path)
        print("\n   📊 Features en puntajes_latest:")
        for feat in features_necesarias:
            if feat in df.columns:
                print(f"      ✅ {feat}")
            else:
                print(f"      ❌ {feat} (NO EXISTE)")
    
    print("\n" + "=" * 70)
    print("✅ DIAGNÓSTICO COMPLETADO")
    print("=" * 70)


if __name__ == "__main__":
    diagnosticar()