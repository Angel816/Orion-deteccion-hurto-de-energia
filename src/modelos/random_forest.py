# src/modelos/random_forest.py
"""
Bosque Aleatorio - Detección supervisada (Random Forest)
Fase 2 del Proyecto Orion
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from src.modelos.detector import DetectorBase
from src.utilidades.registrador import registro

class BosqueAleatorio(DetectorBase):
    """
    Random Forest para detección supervisada de hurto
    """
    
    def __init__(self, n_estimadores: int = 200, profundidad_maxima: int = 15):
        super().__init__(nombre="bosque_aleatorio")
        self.n_estimadores = n_estimadores
        self.profundidad_maxima = profundidad_maxima
        self.modelo = RandomForestClassifier(
            n_estimators=n_estimadores,
            max_depth=profundidad_maxima,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        )
        self.escalador = StandardScaler()
        registro.info(f"🌳 Bosque Aleatorio: {n_estimadores} árboles")
    
    def entrenar(self, X: np.ndarray, y: np.ndarray):
        if y is None:
            raise ValueError("Bosque Aleatorio requiere etiquetas")
        
        registro.info("🧠 Entrenando Bosque Aleatorio...")
        X_escalado = self.escalador.fit_transform(X)
        self.modelo.fit(X_escalado, y)
        self.entrenado = True
        self._calcular_metricas(X_escalado, y)
        self._calcular_importancia()
        registro.info(f"✅ Bosque Aleatorio entrenado con {len(X)} muestras")
    
    def predecir(self, X: np.ndarray) -> np.ndarray:
        if not self.entrenado:
            return np.ones(len(X)) * 0.5
        X_escalado = self.escalador.transform(X)
        return self.modelo.predict_proba(X_escalado)[:, 1]
    
    def _calcular_metricas(self, X: np.ndarray, y: np.ndarray):
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        y_pred = self.modelo.predict(X)
        self.metricas = {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred, zero_division=0),
            'recall': recall_score(y, y_pred, zero_division=0),
            'f1': f1_score(y, y_pred, zero_division=0)
        }
        registro.info(f"📊 Accuracy={self.metricas['accuracy']:.3f}, F1={self.metricas['f1']:.3f}")
    
    def _calcular_importancia(self):
        if hasattr(self.modelo, 'feature_importances_'):
            self.importancia = self.modelo.feature_importances_