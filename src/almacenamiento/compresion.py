# src/almacenamiento/compresion.py
"""
Utilidades de compresión para almacenamiento
"""

import pandas as pd
import zipfile
from pathlib import Path
from src.utilidades.registrador import registro

class CompresorDatos:
    """
    Comprime y descomprime archivos de datos
    """
    
    def comprimir(self, origen: Path, destino: Path = None):
        """
        Comprime un archivo
        """
        if destino is None:
            destino = origen.with_suffix('.zip')
        
        with zipfile.ZipFile(destino, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(origen, origen.name)
        
        registro.info(f"🗜️ Archivo comprimido: {destino}")
        return destino
    
    def descomprimir(self, origen: Path, destino: Path = None):
        """
        Descomprime un archivo
        """
        if destino is None:
            destino = origen.parent / origen.stem
        
        with zipfile.ZipFile(origen, 'r') as zipf:
            zipf.extractall(destino)
        
        registro.info(f"📂 Archivo descomprimido en: {destino}")
        return destino