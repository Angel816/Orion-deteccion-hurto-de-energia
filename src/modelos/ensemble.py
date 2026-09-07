# src/modelos/ensemble.py
"""
Conjunto (Ensemble) - XGBoost + LightGBM
Fase 3 del Proyecto Orion - Máxima precisión
"""

import numpy as np
import warnings
warnings.filterwarnings('ignore')

from sklearn.preprocessing import StandardScaler
from src.modelos.detector import DetectorBase
from src.utilidades.registrador import registro

class Conjunto(DetectorBase):
    """
    Ensemble de XGBoost + LightGBM
    """
    
    def __init__(self, n_estimadores: int = 200):
        super().__init__(nombre="conjunto")
        self.n_estimadores = n_estimadores
        self.modelo_xgb = None
        self.modelo_lgb = None
        self.escalador = StandardScaler()
        registro.info(f"⚡ Conjunto (Ensemble): XGBoost + LightGBM")
    
    def entrenar(self, X: np.ndarray, y: np.ndarray):
        if y is None:
            raise ValueError("Ensemble requiere etiquetas")
        
        registro.info("🧠 Entrenando Ensemble XGBoost + LightGBM...")
        
        try:
            from xgboost import XGBClassifier
            from lightgbm import LGBMClassifier
        except ImportError:
            registro.error("❌ XGBoost o LightGBM no están instalados")
            raise
        
        X_escalado = self.escalador.fit_transform(X)
        
        registro.info("   📊 Entrenando XGBoost...")
        self.modelo_xgb = XGBClassifier(
            n_estimators=self.n_estimadores,
            max_depth=8,
            learning_rate=0.1,
            scale_pos_weight=3,
            random_state=42,
            use_label_encoder=False,
            eval_metric='logloss',
            n_jobs=-1
        )
        self.modelo_xgb.fit(X_escalado, y)
        
        registro.info("   📊 Entrenando LightGBM...")
        self.modelo_lgb = LGBMClassifier(
            n_estimators=self.n_estimadores,
            max_depth=10,
            learning_rate=0.1,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1,
            verbose=-1
        )
        self.modelo_lgb.fit(X_escalado, y)
        
        self.entrenado = True
        self._calcular_metricas(X_escalado, y)
        registro.info(f"✅ Ensemble entrenado con {len(X)} muestras")
    
    def predecir(self, X: np.ndarray) -> np.ndarray:
        if not self.entrenado:
            return np.ones(len(X)) * 0.5
        X_escalado = self.escalador.transform(X)
        prob_xgb = self.modelo_xgb.predict_proba(X_escalado)[:, 1]
        prob_lgb = self.modelo_lgb.predict_proba(X_escalado)[:, 1]
        return (prob_xgb + prob_lgb) / 2
    
    def _calcular_metricas(self, X: np.ndarray, y: np.ndarray):
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        y_pred = self.predecir(X) > 0.5
        self.metricas = {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred, zero_division=0),
            'recall': recall_score(y, y_pred, zero_division=0),
            'f1': f1_score(y, y_pred, zero_division=0)
        }
        registro.info(f"📊 Ensemble: Accuracy={self.metricas['accuracy']:.3f}, F1={self.metricas['f1']:.3f}")