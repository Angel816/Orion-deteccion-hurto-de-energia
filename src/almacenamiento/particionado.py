# src/almacenamiento/particionado.py
"""
Almacenamiento particionado por fecha
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from src.utilidades.registrador import registro

class AlmacenamientoParticionado:
    """
    Almacena datos en particiones por fecha
    """
    
    def __init__(self, base_path: str = 'datos/particionados'):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def guardar(self, df: pd.DataFrame, dataset: str, fecha_col: str = 'fecha'):
        """
        Guarda datos particionados por fecha
        """
        if fecha_col not in df.columns:
            registro.warning(f"Columna {fecha_col} no encontrada")
            return 0
        
        df[fecha_col] = pd.to_datetime(df[fecha_col])
        guardados = 0
        
        for fecha, grupo in df.groupby(pd.Grouper(key=fecha_col, freq='D')):
            if pd.isna(fecha):
                continue
            
            ruta = self.base_path / dataset / fecha.strftime('%Y/%m/%d')
            ruta.mkdir(parents=True, exist_ok=True)
            grupo.to_parquet(ruta / 'data.parquet')
            guardados += len(grupo)
        
        registro.info(f"💾 {guardados} registros guardados en {dataset}")
        return guardados
    
    def cargar(self, dataset: str, inicio: datetime = None, fin: datetime = None) -> pd.DataFrame:
        """
        Carga datos de un rango de fechas
        """
        ruta = self.base_path / dataset
        if not ruta.exists():
            return pd.DataFrame()
        
        dataframes = []
        inicio = inicio or datetime(2020, 1, 1)
        fin = fin or datetime.now()
        
        actual = inicio
        while actual <= fin:
            particion = ruta / actual.strftime('%Y/%m/%d') / 'data.parquet'
            if particion.exists():
                dataframes.append(pd.read_parquet(particion))
            actual += timedelta(days=1)
        
        if dataframes:
            return pd.concat(dataframes, ignore_index=True)
        return pd.DataFrame()