# src/modelos/detector.py
"""
Detector base de hurto de energía
"""

import numpy as np
from typing import Optional
from src.utilidades.registrador import registro

class DetectorBase:
    """
    Clase base para todos los detectores de hurto
    """
    
    def __init__(self, nombre: str = "detector_base"):
        self.nombre = nombre
        self.modelo = None
        self.escalador = None
        self.entrenado = False
        self.metricas = {}
        registro.info(f"🤖 {nombre} inicializado")
    
    def entrenar(self, X: np.ndarray, y: Optional[np.ndarray] = None):
        raise NotImplementedError("Este método debe ser implementado por las subclases")
    
    def predecir(self, X: np.ndarray) -> np.ndarray:
        raise NotImplementedError("Este método debe ser implementado por las subclases")
    
    def guardar(self, ruta: str):
        import joblib
        joblib.dump({
            'modelo': self.modelo,
            'escalador': self.escalador,
            'metricas': self.metricas,
            'nombre': self.nombre
        }, ruta)
        registro.info(f"💾 Modelo guardado en {ruta}")
    
    def cargar(self, ruta: str):
        import joblib
        datos = joblib.load(ruta)
        self.modelo = datos['modelo']
        self.escalador = datos.get('escalador')
        self.metricas = datos.get('metricas', {})
        self.nombre = datos.get('nombre', self.nombre)
        self.entrenado = True
        registro.info(f"📂 Modelo cargado desde {ruta}")