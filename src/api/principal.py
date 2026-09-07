# src/api/principal.py
"""
Aplicación principal de la API de Orion
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.rutas import router
from src.utilidades.registrador import registro

app = FastAPI(
    title="Orion - API de Detección de Hurto de Energía",
    description="API para detección y priorización de hurto de energía",
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

@app.on_event("shutdown")
async def shutdown_event():
    registro.info("🛑 Cerrando API de Orion...")

@app.get("/")
async def root():
    return {
        "nombre": "Orion",
        "version": "1.0.0",
        "endpoints": [
            "/api/v1/health",
            "/api/v1/predict",
            "/api/v1/batch",
            "/api/v1/priority",
            "/api/v1/status"
        ]
    }