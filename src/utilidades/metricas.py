# src/utilidades/metricas.py
"""
Módulo centralizado de métricas para Orion
Zona horaria: Perú (UTC-5)
"""

import time
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from src.utilidades.registrador import registro
from src.utilidades.tiempo import ahora_peru, iso_peru


# ============================================================
# MÉTRICAS DE MODELOS
# ============================================================

class MetricasModelo:
    """Métricas para evaluar modelos de detección"""
    
    @staticmethod
    def calcular_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calcula la precisión (accuracy)"""
        from sklearn.metrics import accuracy_score
        return float(accuracy_score(y_true, y_pred))
    
    @staticmethod
    def calcular_precision(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calcula la precisión (precision)"""
        from sklearn.metrics import precision_score
        return float(precision_score(y_true, y_pred, zero_division=0))
    
    @staticmethod
    def calcular_recall(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calcula el recall"""
        from sklearn.metrics import recall_score
        return float(recall_score(y_true, y_pred, zero_division=0))
    
    @staticmethod
    def calcular_f1(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calcula el F1-Score"""
        from sklearn.metrics import f1_score
        return float(f1_score(y_true, y_pred, zero_division=0))
    
    @staticmethod
    def calcular_roc_auc(y_true: np.ndarray, y_prob: np.ndarray) -> float:
        """Calcula el ROC-AUC"""
        from sklearn.metrics import roc_auc_score
        try:
            return float(roc_auc_score(y_true, y_prob))
        except:
            return 0.0
    
    @staticmethod
    def calcular_matriz_confusion(y_true: np.ndarray, y_pred: np.ndarray) -> Dict:
        """Calcula la matriz de confusión"""
        from sklearn.metrics import confusion_matrix
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
        return {
            'verdaderos_positivos': int(tp),
            'falsos_positivos': int(fp),
            'falsos_negativos': int(fn),
            'verdaderos_negativos': int(tn)
        }
    
    @classmethod
    def calcular_todas(cls, y_true: np.ndarray, y_pred: np.ndarray,
                       y_prob: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """Calcula todas las métricas de una vez"""
        metricas = {
            'accuracy': cls.calcular_accuracy(y_true, y_pred),
            'precision': cls.calcular_precision(y_true, y_pred),
            'recall': cls.calcular_recall(y_true, y_pred),
            'f1': cls.calcular_f1(y_true, y_pred),
            'matriz_confusion': cls.calcular_matriz_confusion(y_true, y_pred),
            'n_muestras': len(y_true),
            'positivos': int(y_true.sum()),
            'negativos': int(len(y_true) - y_true.sum()),
            'timestamp': iso_peru()
        }
        
        if y_prob is not None:
            metricas['roc_auc'] = cls.calcular_roc_auc(y_true, y_prob)
        
        return metricas


# ============================================================
# MÉTRICAS DE NEGOCIO
# ============================================================

class MetricasNegocio:
    """Métricas de negocio específicas de Orion"""
    
    @staticmethod
    def calcular_tasa_exito(inspecciones: pd.DataFrame) -> float:
        """Calcula la tasa de éxito de inspecciones"""
        if inspecciones.empty:
            return 0.0
        
        total = len(inspecciones)
        if total == 0:
            return 0.0
        
        confirmados = len(inspecciones[inspecciones['resultado'] == 'Hurto Confirmado'])
        return confirmados / total
    
    @staticmethod
    def calcular_tasa_falsos_positivos(inspecciones: pd.DataFrame) -> float:
        """Calcula la tasa de falsos positivos"""
        if inspecciones.empty:
            return 0.0
        
        total = len(inspecciones)
        if total == 0:
            return 0.0
        
        fp = len(inspecciones[inspecciones['resultado'] == 'Falso Positivo'])
        return fp / total
    
    @staticmethod
    def calcular_roi(recuperacion: float, costo: float) -> float:
        """Calcula el ROI (Return On Investment)"""
        if costo <= 0:
            return 0.0
        return (recuperacion - costo) / costo
    
    @staticmethod
    def calcular_cnr_recuperado(cnr_estimado: float, cnr_real: float) -> float:
        """Calcula el porcentaje de CNR recuperado"""
        if cnr_estimado <= 0:
            return 0.0
        return min(cnr_real / cnr_estimado, 1.0)
    
    @staticmethod
    def calcular_tasa_reincidencia(historico: pd.DataFrame) -> float:
        """Calcula la tasa de reincidencia"""
        if historico.empty or 'id_cliente' not in historico.columns:
            return 0.0
        
        if 'prioridad' not in historico.columns:
            return 0.0
        
        alertas_altas = historico[historico['prioridad'] == 'ALTA']
        if alertas_altas.empty:
            return 0.0
        
        incidentes_por_cliente = alertas_altas.groupby('id_cliente').size()
        reincidentes = len(incidentes_por_cliente[incidentes_por_cliente > 1])
        total_clientes = len(incidentes_por_cliente)
        
        if total_clientes == 0:
            return 0.0
        
        return reincidentes / total_clientes
    
    @staticmethod
    def calcular_recuperacion_total(inspecciones: pd.DataFrame) -> float:
        """Calcula la recuperación total"""
        if inspecciones.empty or 'monto_recuperar' not in inspecciones.columns:
            return 0.0
        return float(inspecciones['monto_recuperar'].sum())
    
    @staticmethod
    def calcular_costo_total(inspecciones: pd.DataFrame, 
                             costo_unitario: float = 30.0) -> float:
        """Calcula el costo total de inspecciones"""
        if inspecciones.empty:
            return 0.0
        return len(inspecciones) * costo_unitario
    
    @classmethod
    def calcular_todas(cls, inspecciones: pd.DataFrame, historico: pd.DataFrame,
                       costo_unitario: float = 30.0) -> Dict[str, Any]:
        """Calcula todas las métricas de negocio"""
        recuperacion = cls.calcular_recuperacion_total(inspecciones)
        costo = cls.calcular_costo_total(inspecciones, costo_unitario)
        
        return {
            'tasa_exito': cls.calcular_tasa_exito(inspecciones),
            'tasa_falsos_positivos': cls.calcular_tasa_falsos_positivos(inspecciones),
            'roi': cls.calcular_roi(recuperacion, costo),
            'tasa_reincidencia': cls.calcular_tasa_reincidencia(historico),
            'recuperacion_total': recuperacion,
            'costo_total': costo,
            'n_inspecciones': len(inspecciones) if not inspecciones.empty else 0,
            'timestamp': iso_peru()
        }


# ============================================================
# MÉTRICAS DE SISTEMA
# ============================================================

class MetricasSistema:
    """Métricas de rendimiento del sistema"""
    
    def __init__(self):
        self.tiempos = {}
        self.contadores = {}
    
    def medir_tiempo(self, operacion: str) -> Callable:
        """Decorador para medir tiempo de ejecución"""
        def decorador(func):
            def wrapper(*args, **kwargs):
                inicio = time.time()
                resultado = func(*args, **kwargs)
                duracion = time.time() - inicio
                
                if operacion not in self.tiempos:
                    self.tiempos[operacion] = []
                self.tiempos[operacion].append(duracion)
                
                registro.debug(f"⏱️ {operacion}: {duracion:.3f}s")
                return resultado
            return wrapper
        return decorador
    
    def incrementar_contador(self, nombre: str, cantidad: int = 1):
        """Incrementa un contador"""
        if nombre not in self.contadores:
            self.contadores[nombre] = 0
        self.contadores[nombre] += cantidad
    
    def obtener_estadisticas(self, operacion: str) -> Dict[str, float]:
        """Obtiene estadísticas de una operación"""
        if operacion not in self.tiempos:
            return {'error': 'Operación no encontrada'}
        
        tiempos = self.tiempos[operacion]
        return {
            'promedio': float(np.mean(tiempos)),
            'minimo': float(np.min(tiempos)),
            'maximo': float(np.max(tiempos)),
            'total': float(np.sum(tiempos)),
            'n_ejecuciones': len(tiempos)
        }
    
    def reporte_rendimiento(self) -> pd.DataFrame:
        """Genera reporte de rendimiento"""
        datos = []
        for operacion, tiempos in self.tiempos.items():
            datos.append({
                'operacion': operacion,
                'promedio_ms': np.mean(tiempos) * 1000,
                'minimo_ms': np.min(tiempos) * 1000,
                'maximo_ms': np.max(tiempos) * 1000,
                'n_ejecuciones': len(tiempos)
            })
        
        if datos:
            return pd.DataFrame(datos)
        return pd.DataFrame()
    
    def obtener_contadores(self) -> Dict[str, int]:
        """Retorna todos los contadores"""
        return self.contadores.copy()
    
    def resetear(self):
        """Resetea todas las métricas"""
        self.tiempos = {}
        self.contadores = {}
        registro.info("🔄 Métricas de sistema reseteadas")


# ============================================================
# FORMATEADOR DE MÉTRICAS
# ============================================================


class FormateadorMetricas:
    """Utilidades para formatear métricas"""
    
    @staticmethod
    def formatear_porcentaje(valor: float, decimales: int = 1) -> str:
        """Formatea un valor como porcentaje"""
        return f"{valor * 100:.{decimales}f}%"
    
    @staticmethod
    def formatear_decimal(valor: float, decimales: int = 3) -> str:
        """Formatea un valor decimal"""
        return f"{valor:.{decimales}f}"
    
    @staticmethod
    def formatear_moneda(valor: float, moneda: str = "S/") -> str:
        """
        Formatea un valor monetario en Nuevos Soles Peruanos
        
        Parámetros:
            valor: Monto a formatear
            moneda: Símbolo de moneda (default: S/)
        
        Retorna:
            String formateado (ej: S/1,234.56)
        """
        return f"{moneda} {valor:,.2f}"
    
    @staticmethod
    def formatear_tiempo(segundos: float) -> str:
        """Formatea un tiempo en segundos"""
        if segundos < 1:
            return f"{segundos * 1000:.0f}ms"
        elif segundos < 60:
            return f"{segundos:.2f}s"
        else:
            minutos = int(segundos // 60)
            segs = segundos % 60
            return f"{minutos}m {segs:.0f}s"
    
    @staticmethod
    def comparar_metricas(actual: float, anterior: float) -> Dict[str, Any]:
        """Compara dos valores de métricas"""
        if anterior == 0:
            cambio = 0.0
        else:
            cambio = (actual - anterior) / anterior
        
        return {
            'actual': actual,
            'anterior': anterior,
            'cambio': cambio,
            'cambio_pct': cambio * 100,
            'mejora': cambio > 0,
            'direccion': '⬆️' if cambio > 0 else '⬇️' if cambio < 0 else '➡️'
        }
    
    @staticmethod
    def generar_resumen(metricas: Dict) -> str:
        """Genera un resumen de texto de las métricas"""
        lineas = []
        lineas.append("=" * 50)
        lineas.append("📊 RESUMEN DE MÉTRICAS")
        lineas.append("=" * 50)
        
        for clave, valor in metricas.items():
            if isinstance(valor, float):
                if 0 <= valor <= 1:
                    lineas.append(f"   {clave}: {valor*100:.1f}%")
                else:
                    lineas.append(f"   {clave}: {valor:.3f}")
            elif isinstance(valor, int):
                lineas.append(f"   {clave}: {valor}")
        
        lineas.append("=" * 50)
        return "\n".join(lineas)

# ============================================================
# INSTANCIA GLOBAL
# ============================================================

metricas_sistema = MetricasSistema()