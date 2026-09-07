# src/modelos/isolation_forest.py
"""
Bosque de Aislamiento - Detección no supervisada (Isolation Forest)
Fase 1 del Proyecto Orion
"""

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from src.modelos.detector import DetectorBase
from src.utilidades.registrador import registro

class BosqueAislamiento(DetectorBase):
    """
    Isolation Forest para detección de anomalías sin etiquetas
    """
    
    def __init__(self, contaminacion: float = 0.08, n_estimadores: int = 200):
        super().__init__(nombre="bosque_aislamiento")
        self.contaminacion = contaminacion
        self.n_estimadores = n_estimadores
        self.modelo = IsolationForest(
            contamination=contaminacion,
            random_state=42,
            n_estimators=n_estimadores,
            max_samples='auto'
        )
        self.escalador = StandardScaler()
        registro.info(f"🌲 Bosque de Aislamiento: {n_estimadores} árboles")
    
    def entrenar(self, X: np.ndarray, y: np.ndarray = None):
        registro.info("🧠 Entrenando Bosque de Aislamiento...")
        X_escalado = self.escalador.fit_transform(X)
        self.modelo.fit(X_escalado)
        self.entrenado = True
        
        if y is not None:
            self._calcular_metricas(X_escalado, y)
        
        registro.info(f"✅ Bosque de Aislamiento entrenado con {len(X)} muestras")
    
    def predecir(self, X: np.ndarray) -> np.ndarray:
        if not self.entrenado:
            return np.ones(len(X)) * 0.5
        
        X_escalado = self.escalador.transform(X)
        scores = self.modelo.decision_function(X_escalado)
        prob = 1 - (scores + 0.5) / 1.0
        return np.clip(prob, 0, 1)
    
    def _calcular_metricas(self, X: np.ndarray, y: np.ndarray):
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        pred = self.modelo.predict(X)
        pred_bin = np.where(pred == -1, 1, 0)
        self.metricas = {
            'accuracy': accuracy_score(y, pred_bin),
            'precision': precision_score(y, pred_bin, zero_division=0),
            'recall': recall_score(y, pred_bin, zero_division=0),
            'f1': f1_score(y, pred_bin, zero_division=0)
        }