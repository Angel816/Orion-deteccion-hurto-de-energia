# src/api/adaptador.py
"""
Adaptador de datos entre la API y el sistema
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from src.utilidades.registrador import registro

class AdaptadorAPI:
    """
    Convierte datos entre el formato de la API y el sistema
    """
    
    def __init__(self, max_resultados: int = 1000):
        self.max_resultados = max_resultados
        registro.info("🌐 Adaptador de API inicializado")
    
    def adaptar_solicitud(self, datos: Dict) -> pd.DataFrame:
        try:
            if 'id_cliente' in datos:
                df = pd.DataFrame([datos])
            elif isinstance(datos, list):
                df = pd.DataFrame(datos)
            else:
                raise ValueError("Formato de solicitud inválido")
            
            requeridas = ['consumo_promedio', 'total_alarmas']
            for col in requeridas:
                if col not in df.columns:
                    df[col] = 0
            
            return df
        except Exception as e:
            registro.error(f"❌ Error adaptando solicitud: {e}")
            raise
    
    def adaptar_respuesta(self, predicciones: np.ndarray, 
                          df: pd.DataFrame) -> List[Dict]:
        resultados = []
        
        for idx, prob in enumerate(predicciones):
            if idx >= len(df):
                break
                
            resultado = {
                'id_cliente': df.iloc[idx].get('id_cliente', f'CL_{idx}'),
                'probabilidad': float(prob),
                'es_sospechoso': bool(prob > 0.7),
                'prioridad': self._obtener_prioridad(prob)
            }
            resultados.append(resultado)
        
        if len(resultados) > self.max_resultados:
            resultados = resultados[:self.max_resultados]
        
        return resultados
    
    def _obtener_prioridad(self, probabilidad: float) -> str:
        if probabilidad >= 0.8:
            return 'ALTA'
        elif probabilidad >= 0.5:
            return 'MEDIA'
        else:
            return 'BAJA'
    
    def adaptar_prioridades(self, puntajes: pd.DataFrame) -> List[Dict]:
        resultados = []
        
        for _, row in puntajes.head(self.max_resultados).iterrows():
            resultado = {
                'id_cliente': row.get('id_cliente', ''),
                'puntaje_prioridad': float(row.get('puntaje_prioridad', 0)),
                'prioridad': row.get('prioridad', 'BAJA'),
                'probabilidad': float(row.get('probabilidad', 0))
            }
            resultados.append(resultado)
        
        return resultados