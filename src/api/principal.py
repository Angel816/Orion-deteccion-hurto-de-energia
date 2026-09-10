# src/api/principal.py
"""
Aplicación principal de la API de Orion
Zona horaria: Perú (UTC-5)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.rutas import router
from src.utilidades.registrador import registro
from src.utilidades.tiempo import iso_peru

app = FastAPI(
    title="Orion - API de Detección de Hurto de Energía",
    description="API para detección y priorización de hurto de energía (Perú)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
async def startup_event():
    registro.info("🚀 Iniciando API de Orion...")
    registro.info(f"🕐 Hora Perú: {iso_peru()}")


@app.on_event("shutdown")
async def shutdown_event():
    registro.info("🛑 Cerrando API de Orion...")


@app.get("/")
async def root():
    return {
        "nombre": "Orion",
        "version": "1.0.0",
        "descripcion": "API para detección y priorización de hurto de energía",
        "zona_horaria": "America/Lima",
        "moneda": "PEN",
        "simbolo_moneda": "S/",
        "endpoints": [
            "/api/v1/health",
            "/api/v1/hora",
            "/api/v1/predict",
            "/api/v1/batch",
            "/api/v1/priority",
            "/api/v1/status",
            "/api/v1/metricas",
            "/api/v1/metricas/modelo",
            "/api/v1/metricas/negocio"
        ]
    }