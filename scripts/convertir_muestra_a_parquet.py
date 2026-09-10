# scripts/convertir_muestra_a_parquet.py
"""
Convierte los datos de muestra de CSV a Parquet
Zona horaria: Perú (UTC-5)
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
from src.utilidades.registrador import registro
from src.utilidades.tiempo import ahora_peru, timestamp_peru


def main():
    registro.info("🔄 Convirtiendo datos de muestra a Parquet...")
    registro.info(f"🕐 Hora Perú: {ahora_peru().strftime('%Y-%m-%d %H:%M:%S')}")
    
    muestra_dir = Path('datos/muestra')
    brutos_dir = Path('datos/brutos')
    
    # Timestamp con hora Perú
    timestamp = timestamp_peru()
    
    # 1. Consumo
    consumo_path = muestra_dir / 'consumo_muestra.csv'
    if consumo_path.exists():
        df = pd.read_csv(consumo_path)
        df['fecha'] = pd.to_datetime(df['fecha'])
        
        consumo_dir = brutos_dir / 'consumo'
        consumo_dir.mkdir(parents=True, exist_ok=True)
        df.to_parquet(consumo_dir / f'consumo_{timestamp}.parquet')
        registro.info(f"✅ Consumo: {len(df)} registros -> consumo_{timestamp}.parquet")
    
    # 2. Alarmas
    alarmas_path = muestra_dir / 'alarmas_muestra.csv'
    if alarmas_path.exists():
        df = pd.read_csv(alarmas_path)
        df['fecha'] = pd.to_datetime(df['fecha'])
        
        alarmas_dir = brutos_dir / 'alarmas'
        alarmas_dir.mkdir(parents=True, exist_ok=True)
        df.to_parquet(alarmas_dir / f'alarmas_{timestamp}.parquet')
        registro.info(f"✅ Alarmas: {len(df)} registros -> alarmas_{timestamp}.parquet")
    
    # 3. Clientes
    clientes_path = muestra_dir / 'clientes_muestra.csv'
    if clientes_path.exists():
        df = pd.read_csv(clientes_path)
        
        clientes_dir = brutos_dir / 'clientes'
        clientes_dir.mkdir(parents=True, exist_ok=True)
        df.to_parquet(clientes_dir / f'clientes_{timestamp}.parquet')
        registro.info(f"✅ Clientes: {len(df)} registros -> clientes_{timestamp}.parquet")
    
    # 4. Facturación
    facturacion_path = muestra_dir / 'facturacion_muestra.csv'
    if facturacion_path.exists():
        df = pd.read_csv(facturacion_path)
        df['fecha_emision'] = pd.to_datetime(df['fecha_emision'])
        df['fecha_vencimiento'] = pd.to_datetime(df['fecha_vencimiento'])
        
        facturacion_dir = brutos_dir / 'facturacion'
        facturacion_dir.mkdir(parents=True, exist_ok=True)
        df.to_parquet(facturacion_dir / f'facturacion_{timestamp}.parquet')
        registro.info(f"✅ Facturación: {len(df)} registros -> facturacion_{timestamp}.parquet")
    
    # 5. Inspecciones
    inspecciones_path = muestra_dir / 'inspecciones_muestra.csv'
    if inspecciones_path.exists():
        df = pd.read_csv(inspecciones_path)
        df['fecha_inspeccion'] = pd.to_datetime(df['fecha_inspeccion'])
        
        feedback_dir = Path('datos/retroalimentacion/inspecciones')
        feedback_dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(feedback_dir / f'inspecciones_{timestamp}.csv', index=False)
        registro.info(f"✅ Inspecciones: {len(df)} registros -> inspecciones_{timestamp}.csv")
    
    registro.info("✅ Conversión completada")
    registro.info(f"🕐 Finalizado: {ahora_peru().strftime('%Y-%m-%d %H:%M:%S')} (Perú)")


if __name__ == "__main__":
    main()