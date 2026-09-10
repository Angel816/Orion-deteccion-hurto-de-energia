# src/api/rutas.py
"""
Endpoints de la API de Orion
Zona horaria: Perú (UTC-5)
Moneda: Nuevo Sol Peruano (S/)
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
from src.utilidades.tiempo import ahora_peru, iso_peru
from src.utilidades.metricas import MetricasModelo, MetricasNegocio, FormateadorMetricas

# ============================================================
# MODELOS DE DATOS
# ============================================================

class SuministroPrediccion(BaseModel):
    """Modelo para predicción de un suministro"""
    id_cliente: str = Field(..., description="ID del cliente")
    consumo_promedio: float = Field(..., description="Consumo promedio en kWh")
    total_alarmas: int = Field(0, description="Total de alarmas")
    inspecciones_previas: int = Field(0, description="Inspecciones previas")
    sector: Optional[str] = Field(None, description="Sector geográfico")
    tipo_cliente: Optional[str] = Field(None, description="Tipo de cliente")


class RespuestaPrediccion(BaseModel):
    """Respuesta de predicción individual"""
    id_cliente: str
    probabilidad: float = Field(..., ge=0, le=1, description="Probabilidad de hurto (0-1)")
    es_sospechoso: bool
    prioridad: str = Field(..., description="Prioridad: ALTA, MEDIA, BAJA")
    timestamp: str = Field(default_factory=lambda: iso_peru())


class RespuestaPrioridad(BaseModel):
    """Respuesta de priorización"""
    id_cliente: str
    puntaje_prioridad: float
    prioridad: str
    probabilidad: float


class RespuestaMetricasModelo(BaseModel):
    """Métricas del modelo"""
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: Optional[float] = None
    n_muestras: Optional[int] = None
    timestamp: str = Field(default_factory=lambda: iso_peru())


class RespuestaMetricasNegocio(BaseModel):
    """Métricas de negocio en Nuevos Soles Peruanos"""
    tasa_exito: float
    tasa_falsos_positivos: float
    roi: float
    tasa_reincidencia: float
    recuperacion_total: float = Field(..., description="Monto en Nuevos Soles (S/)")
    costo_total: float = Field(..., description="Monto en Nuevos Soles (S/)")
    rentabilidad: float = Field(..., description="Monto en Nuevos Soles (S/)")
    n_inspecciones: int
    moneda: str = Field(default="PEN", description="Código ISO de moneda")
    simbolo_moneda: str = Field(default="S/", description="Símbolo de moneda")
    timestamp: str = Field(default_factory=lambda: iso_peru())


class RespuestaMetricasCompletas(BaseModel):
    """Respuesta completa de métricas"""
    metricas_modelo: dict
    metricas_negocio: dict
    moneda: str = "PEN"
    simbolo_moneda: str = "S/"
    timestamp: str = Field(default_factory=lambda: iso_peru())


class RespuestaHora(BaseModel):
    """Respuesta de hora actual"""
    hora_peru: str
    timestamp_iso: str
    zona_horaria: str = "America/Lima"
    offset: str = "-05:00"


# ============================================================
# INSTANCIA DEL ROUTER
# ============================================================

router = APIRouter(prefix="/api/v1", tags=["Orion"])
adaptador = AdaptadorAPI()
enrutador = EnrutadorModelos()
modelo_actual = BosqueAislamiento()
puntuador = PuntuadorSimple()


# ============================================================
# ENDPOINTS BÁSICOS
# ============================================================

@router.get("/health")
async def health():
    """
    Verifica el estado del sistema
    """
    return {
        "status": "healthy",
        "timestamp": iso_peru(),
        "version": "1.0.0",
        "zona_horaria": "America/Lima",
        "moneda": "PEN",
        "simbolo_moneda": "S/"
    }


@router.get("/hora")
async def obtener_hora():
    """
    Obtiene la hora actual en Perú
    """
    return {
        "hora_peru": ahora_peru().strftime('%Y-%m-%d %H:%M:%S'),
        "timestamp_iso": iso_peru(),
        "zona_horaria": "America/Lima",
        "offset": "-05:00"
    }


# ============================================================
# ENDPOINTS DE PREDICCIÓN
# ============================================================

@router.post("/predict", response_model=RespuestaPrediccion)
async def predecir(suministro: SuministroPrediccion):
    """
    Predice la probabilidad de hurto para un suministro
    """
    try:
        # 1. Convertir a DataFrame
        df = adaptador.adaptar_solicitud(suministro.dict())
        
        # 2. Preparar características
        caracteristicas = df[['consumo_promedio', 'total_alarmas']].values
        
        # 3. Predecir
        probabilidad = modelo_actual.predecir(caracteristicas)[0]
        
        # 4. Obtener prioridad
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
    """
    Predice en lote para múltiples suministros
    """
    try:
        # 1. Convertir a DataFrame
        datos = [s.dict() for s in suministros]
        df = adaptador.adaptar_solicitud(datos)
        
        # 2. Preparar características
        caracteristicas = df[['consumo_promedio', 'total_alarmas']].values
        
        # 3. Predecir
        probabilidades = modelo_actual.predecir(caracteristicas)
        
        # 4. Formatear respuesta
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


# ============================================================
# ENDPOINTS DE PRIORIZACIÓN
# ============================================================

@router.get("/priority", response_model=List[RespuestaPrioridad])
async def obtener_prioridades(top_n: int = 100):
    """
    Obtiene la lista de suministros priorizados
    """
    try:
        # Simular datos (en producción vendrían de la base de datos)
        np.random.seed(42)
        n = 200
        df = pd.DataFrame({
            'id_cliente': [f'CL_{i:04d}' for i in range(n)],
            'consumo_promedio': np.random.uniform(50, 500, n),
            'total_alarmas': np.random.randint(0, 10, n),
            'inspecciones_previas': np.random.randint(0, 5, n)
        })
        
        # Simular probabilidades
        probabilidades = np.random.uniform(0, 1, n)
        
        # Calcular puntajes
        puntajes = puntuador.calcular_puntajes(df, probabilidades)
        
        # Obtener top N
        top = puntajes.head(top_n)
        
        # Formatear respuesta
        return adaptador.adaptar_prioridades(top)
    except Exception as e:
        registro.error(f"❌ Error obteniendo prioridades: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# ENDPOINTS DE ESTADO Y MÉTRICAS
# ============================================================

@router.get("/status")
async def estado_sistema():
    """
    Obtiene el estado del sistema y los modelos
    """
    return {
        "modelo_actual": modelo_actual.nombre,
        "modelo_entrenado": modelo_actual.entrenado,
        "metricas": modelo_actual.metricas,
        "enrutador": enrutador.obtener_estadisticas(),
        "timestamp": iso_peru(),
        "zona_horaria": "America/Lima",
        "moneda": "PEN",
        "simbolo_moneda": "S/"
    }


@router.get("/metricas", response_model=RespuestaMetricasCompletas)
async def obtener_metricas():
    """
    Obtiene las métricas del sistema (modelo y negocio)
    
    Las métricas de negocio se expresan en Nuevos Soles Peruanos (S/)
    """
    try:
        # ============================================================
        # MÉTRICAS DEL MODELO
        # ============================================================
        metricas_modelo = {
            'accuracy': modelo_actual.metricas.get('accuracy', 0.0),
            'precision': modelo_actual.metricas.get('precision', 0.0),
            'recall': modelo_actual.metricas.get('recall', 0.0),
            'f1': modelo_actual.metricas.get('f1', 0.0),
            'roc_auc': modelo_actual.metricas.get('roc_auc', 0.0),
            'n_muestras': modelo_actual.metricas.get('n_muestras', 0),
            'timestamp': iso_peru()
        }
        
        # ============================================================
        # MÉTRICAS DE NEGOCIO (en Nuevos Soles)
        # ============================================================
        
        # Datos simulados (en producción vendrían de inspecciones_hist)
        inspecciones_simuladas = pd.DataFrame({
            'resultado': ['Hurto Confirmado', 'Normal', 'Hurto Confirmado', 
                         'Falso Positivo', 'Hurto Confirmado', 'Normal'],
            'monto_recuperar': [378.00, 0.00, 250.00, 0.00, 420.00, 0.00]
        })
        
        historico_simulado = pd.DataFrame({
            'id_cliente': ['CL-001', 'CL-001', 'CL-002', 'CL-003', 'CL-001', 'CL-004'],
            'prioridad': ['ALTA', 'ALTA', 'ALTA', 'ALTA', 'MEDIA', 'ALTA']
        })
        
        metricas_negocio = MetricasNegocio.calcular_todas(
            inspecciones_simuladas,
            historico_simulado,
            costo_unitario=30.0
        )
        
        # Calcular rentabilidad
        rentabilidad = metricas_negocio['recuperacion_total'] - metricas_negocio['costo_total']
        
        # ============================================================
        # RESPUESTA
        # ============================================================
        return {
            'metricas_modelo': metricas_modelo,
            'metricas_negocio': {
                'tasa_exito': metricas_negocio['tasa_exito'],
                'tasa_falsos_positivos': metricas_negocio['tasa_falsos_positivos'],
                'roi': metricas_negocio['roi'],
                'tasa_reincidencia': metricas_negocio['tasa_reincidencia'],
                'recuperacion_total': metricas_negocio['recuperacion_total'],
                'costo_total': metricas_negocio['costo_total'],
                'rentabilidad': rentabilidad,
                'n_inspecciones': metricas_negocio['n_inspecciones'],
                'moneda': 'PEN',
                'simbolo_moneda': 'S/',
                'timestamp': iso_peru()
            },
            'moneda': 'PEN',
            'simbolo_moneda': 'S/',
            'timestamp': iso_peru()
        }
    
    except Exception as e:
        registro.error(f"❌ Error obteniendo métricas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metricas/modelo", response_model=RespuestaMetricasModelo)
async def obtener_metricas_modelo():
    """
    Obtiene solo las métricas del modelo
    """
    try:
        return RespuestaMetricasModelo(
            accuracy=modelo_actual.metricas.get('accuracy', 0.0),
            precision=modelo_actual.metricas.get('precision', 0.0),
            recall=modelo_actual.metricas.get('recall', 0.0),
            f1=modelo_actual.metricas.get('f1', 0.0),
            roc_auc=modelo_actual.metricas.get('roc_auc'),
            n_muestras=modelo_actual.metricas.get('n_muestras')
        )
    except Exception as e:
        registro.error(f"❌ Error obteniendo métricas del modelo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metricas/negocio", response_model=RespuestaMetricasNegocio)
async def obtener_metricas_negocio():
    """
    Obtiene solo las métricas de negocio (en Nuevos Soles Peruanos)
    """
    try:
        # Datos simulados (en producción vendrían de inspecciones_hist)
        inspecciones_simuladas = pd.DataFrame({
            'resultado': ['Hurto Confirmado', 'Normal', 'Hurto Confirmado', 
                         'Falso Positivo', 'Hurto Confirmado', 'Normal'],
            'monto_recuperar': [378.00, 0.00, 250.00, 0.00, 420.00, 0.00]
        })
        
        historico_simulado = pd.DataFrame({
            'id_cliente': ['CL-001', 'CL-001', 'CL-002', 'CL-003', 'CL-001', 'CL-004'],
            'prioridad': ['ALTA', 'ALTA', 'ALTA', 'ALTA', 'MEDIA', 'ALTA']
        })
        
        metricas = MetricasNegocio.calcular_todas(
            inspecciones_simuladas,
            historico_simulado,
            costo_unitario=30.0
        )
        
        rentabilidad = metricas['recuperacion_total'] - metricas['costo_total']
        
        return RespuestaMetricasNegocio(
            tasa_exito=metricas['tasa_exito'],
            tasa_falsos_positivos=metricas['tasa_falsos_positivos'],
            roi=metricas['roi'],
            tasa_reincidencia=metricas['tasa_reincidencia'],
            recuperacion_total=metricas['recuperacion_total'],
            costo_total=metricas['costo_total'],
            rentabilidad=rentabilidad,
            n_inspecciones=metricas['n_inspecciones'],
            moneda="PEN",
            simbolo_moneda="S/"
        )
    except Exception as e:
        registro.error(f"❌ Error obteniendo métricas de negocio: {e}")
        raise HTTPException(status_code=500, detail=str(e))