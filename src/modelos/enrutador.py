# src/modelos/enrutador.py
"""
Router inteligente para selección dinámica de modelos
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from src.utilidades.registrador import registro

class EnrutadorModelos:
    """
    Decide qué modelo usar para cada suministro según sus características
    """
    
    def __init__(self):
        self.umbrales = {
            'n_etiquetas': 100,
            'n_etiquetas_conjunto': 500,
            'calidad_datos': 0.7,
            'confianza_minima': 0.5
        }
        
        self.historial_seleccion = {
            'bosque_aislamiento': 0,
            'bosque_aleatorio': 0,
            'conjunto': 0
        }
        
        self.nombres_modelos = {
            'bosque_aislamiento': 'Bosque de Aislamiento (Isolation Forest)',
            'bosque_aleatorio': 'Bosque Aleatorio (Random Forest)',
            'conjunto': 'Conjunto (Ensemble XGBoost + LightGBM)'
        }
        
        registro.info("🧠 Enrutador de modelos inicializado")
    
    def evaluar_suministro(self, datos_suministro: pd.Series, 
                          n_etiquetas: int = 0) -> Dict[str, Any]:
        puntajes = self._calcular_puntajes(datos_suministro)
        seleccionado = self._seleccionar_modelo(puntajes, n_etiquetas)
        seleccionado = self._balancear_seleccion(seleccionado)
        justificacion = self._generar_justificacion(puntajes, seleccionado, n_etiquetas)
        
        return {
            'modelo_seleccionado': seleccionado,
            'nombre_modelo': self.nombres_modelos.get(seleccionado, seleccionado),
            'puntajes': puntajes,
            'justificacion': justificacion,
            'confianza': self._calcular_confianza(puntajes),
            'n_etiquetas': n_etiquetas
        }
    
    def _calcular_puntajes(self, datos_suministro: pd.Series) -> Dict[str, float]:
        puntajes = {
            'disponibilidad_datos': 0.0,
            'calidad_datos': 0.0,
            'historial': 0.0
        }
        
        if 'consumo_promedio' in datos_suministro and pd.notna(datos_suministro['consumo_promedio']):
            puntajes['disponibilidad_datos'] += 0.5
        if 'total_alarmas' in datos_suministro and pd.notna(datos_suministro['total_alarmas']):
            puntajes['disponibilidad_datos'] += 0.5
        
        nulos = datos_suministro.isnull().sum()
        total_columnas = len(datos_suministro)
        puntajes['calidad_datos'] = 1 - (nulos / max(total_columnas, 1))
        
        if 'inspecciones_previas' in datos_suministro and datos_suministro['inspecciones_previas'] > 0:
            puntajes['historial'] = min(datos_suministro['inspecciones_previas'] / 5, 1.0)
        
        return puntajes
    
    def _seleccionar_modelo(self, puntajes: Dict[str, float], n_etiquetas: int) -> str:
        if n_etiquetas < self.umbrales['n_etiquetas']:
            return 'bosque_aislamiento'
        
        if n_etiquetas >= self.umbrales['n_etiquetas_conjunto'] and puntajes['calidad_datos'] >= 0.8:
            return 'conjunto'
        
        if n_etiquetas >= self.umbrales['n_etiquetas']:
            return 'bosque_aleatorio'
        
        return 'bosque_aislamiento'
    
    def _balancear_seleccion(self, seleccionado: str) -> str:
        total = sum(self.historial_seleccion.values())
        
        if total > 100:
            ratio = self.historial_seleccion[seleccionado] / total
            if ratio > 0.6:
                registro.info(f"⚠️ Modelo {seleccionado} sobreutilizado. Balanceando...")
                opciones = [m for m in self.historial_seleccion.keys() if m != seleccionado]
                if opciones:
                    seleccionado = np.random.choice(opciones)
        
        self.historial_seleccion[seleccionado] += 1
        return seleccionado
    
    def _generar_justificacion(self, puntajes: Dict[str, float], 
                               seleccionado: str, n_etiquetas: int) -> str:
        justificaciones = {
            'bosque_aislamiento': f"🧠 Bosque de Aislamiento: sin etiquetas suficientes ({n_etiquetas} < {self.umbrales['n_etiquetas']})",
            'bosque_aleatorio': f"🌳 Bosque Aleatorio: etiquetas moderadas ({n_etiquetas} >= {self.umbrales['n_etiquetas']})",
            'conjunto': f"⚡ Conjunto: muchas etiquetas ({n_etiquetas} >= {self.umbrales['n_etiquetas_conjunto']})"
        }
        detalles = f" | Calidad datos: {puntajes['calidad_datos']:.2f}"
        return justificaciones.get(seleccionado, 'Modelo por defecto') + detalles
    
    def _calcular_confianza(self, puntajes: Dict[str, float]) -> float:
        confianza = (
            puntajes.get('disponibilidad_datos', 0) * 0.4 +
            puntajes.get('calidad_datos', 0) * 0.4 +
            puntajes.get('historial', 0) * 0.2
        )
        return min(confianza, 1.0)
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        total = sum(self.historial_seleccion.values())
        if total == 0:
            return {'total': 0, 'detalle': 'Sin selecciones aún'}
        
        return {
            'total': total,
            'detalle': {
                modelo: {
                    'cantidad': count,
                    'porcentaje': f"{count/total*100:.1f}%"
                }
                for modelo, count in self.historial_seleccion.items()
            }
        }