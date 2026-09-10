# src/almacenamiento/particionado.py
"""
Almacenamiento particionado por fecha
Zona horaria: Perú (UTC-5)
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from src.utilidades.registrador import registro
from src.utilidades.tiempo import ahora_peru


class AlmacenamientoParticionado:
    """
    Almacena datos en particiones por fecha
    """
    
    def __init__(self, base_path: str = 'datos/particionados'):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        registro.info("📂 Almacenamiento particionado inicializado")
    
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
    
    def cargar(self, dataset: str, inicio: datetime = None, 
               fin: datetime = None) -> pd.DataFrame:
        """
        Carga datos de un rango de fechas
        """
        ruta = self.base_path / dataset
        if not ruta.exists():
            return pd.DataFrame()
        
        dataframes = []
        # Usar hora Perú para fechas por defecto
        inicio = inicio or datetime(2020, 1, 1)
        fin = fin or ahora_peru().replace(tzinfo=None)  # ← HORA PERÚ
        
        actual = inicio
        while actual <= fin:
            particion = ruta / actual.strftime('%Y/%m/%d') / 'data.parquet'
            if particion.exists():
                dataframes.append(pd.read_parquet(particion))
            actual += timedelta(days=1)
        
        if dataframes:
            return pd.concat(dataframes, ignore_index=True)
        return pd.DataFrame()
    
    def limpiar_antiguos(self, dataset: str, dias: int = 365) -> int:
        """
        Elimina particiones antiguas
        """
        ruta = self.base_path / dataset
        if not ruta.exists():
            return 0
        
        # Usar hora Perú para el corte
        corte = ahora_peru().replace(tzinfo=None) - timedelta(days=dias)
        eliminados = 0
        
        for year_dir in ruta.iterdir():
            if not year_dir.is_dir():
                continue
            for month_dir in year_dir.iterdir():
                if not month_dir.is_dir():
                    continue
                for day_dir in month_dir.iterdir():
                    if not day_dir.is_dir():
                        continue
                    try:
                        fecha_str = f"{year_dir.name}-{month_dir.name}-{day_dir.name}"
                        fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
                        if fecha < corte:
                            import shutil
                            shutil.rmtree(day_dir)
                            eliminados += 1
                    except:
                        continue
        
        registro.info(f"🗑️ {eliminados} particiones antiguas eliminadas")
        return eliminados