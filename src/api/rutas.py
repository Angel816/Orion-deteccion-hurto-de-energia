# src/api/rutas.py
"""
Endpoints de la API de Orion
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import numpy as np
import pandas as pd

from src.api.adaptador import AdaptadorAPI
from src.modelos.enrutador import EnrutadorModelos
from src.modelos.isolation_forest import BosqueAislamiento
from src.priorizacion.fase1_simple import PuntuadorSimple
from src.utilidades.registrador import registro

# ============================================================
# MODELOS DE DATOS
# ============================================================

class SuministroPrediccion(BaseModel):
    id_cliente: str
    consumo_promedio: float
    total_alarmas: int = 0
    inspecciones_previas: int = 0
    sector: Optional[str] = None
    tipo_cliente: Optional[str] = None

class RespuestaPrediccion(BaseModel):
    id_cliente: str
    probabilidad: float
    es_sospechoso: bool
    prioridad: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class RespuestaPrioridad(BaseModel):
    id_cliente: str
    puntaje_prioridad: float
    prioridad: str
    probabilidad: float

# ============================================================
# INSTANCIA DEL ROUTER
# ============================================================

router = APIRouter(prefix="/api/v1", tags=["Orion"])
adaptador = AdaptadorAPI()
enrutador = EnrutadorModelos()
modelo_actual = BosqueAislamiento()
puntuador = PuntuadorSimple()

# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@router.post("/predict", response_model=RespuestaPrediccion)
async def predecir(suministro: SuministroPrediccion):
    try:
        df = adaptador.adaptar_solicitud(suministro.dict())
        caracteristicas = df[['consumo_promedio', 'total_alarmas']].values
        probabilidad = modelo_actual.predecir(caracteristicas)[0]
        prioridad = adaptador._obtener_prioridad(probabilidad)
        
        return RespuestaPrediccion(
            id_cliente=suministro.id_cliente,
            probabilidad=float(probabilidad),
            es_sospechoso=probabilidad > 0.7,
            prioridad=prioridad
        )
    except Exception as e:
        registro.error(f"❌ Error en predicción: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch", response_model=List[RespuestaPrediccion])
async def predecir_lote(suministros: List[SuministroPrediccion]):
    try:
        datos = [s.dict() for s in suministros]
        df = adaptador.adaptar_solicitud(datos)
        caracteristicas = df[['consumo_promedio', 'total_alarmas']].values
        probabilidades = modelo_actual.predecir(caracteristicas)
        
        resultados = []
        for idx, prob in enumerate(probabilidades):
            resultados.append(RespuestaPrediccion(
                id_cliente=df.iloc[idx]['id_cliente'],
                probabilidad=float(prob),
                es_sospechoso=prob > 0.7,
                prioridad=adaptador._obtener_prioridad(prob)
            ))
        
        return resultados
    except Exception as e:
        registro.error(f"❌ Error en predicción por lote: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/priority", response_model=List[RespuestaPrioridad])
async def obtener_prioridades(top_n: int = 100):
    try:
        np.random.seed(42)
        n = 200
        df = pd.DataFrame({
            'id_cliente': [f'CL_{i:04d}' for i in range(n)],
            'consumo_promedio': np.random.uniform(50, 500, n),
            'total_alarmas': np.random.randint(0, 10, n),
            'inspecciones_previas': np.random.randint(0, 5, n)
        })
        probabilidades = np.random.uniform(0, 1, n)
        puntajes = puntuador.calcular_puntajes(df, probabilidades)
        top = puntajes.head(top_n)
        return adaptador.adaptar_prioridades(top)
    except Exception as e:
        registro.error(f"❌ Error obteniendo prioridades: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def estado_sistema():
    return {
        "modelo_actual": modelo_actual.nombre,
        "modelo_entrenado": modelo_actual.entrenado,
        "metricas": modelo_actual.metricas,
        "enrutador": enrutador.obtener_estadisticas(),
        "timestamp": datetime.now().isoformat()
    }