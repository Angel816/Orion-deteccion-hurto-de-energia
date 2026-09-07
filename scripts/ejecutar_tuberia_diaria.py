# scripts/ejecutar_tuberia_diaria.py
"""
Ejecuta la tubería diaria de Orion
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime
from src.datos.cargador import CargadorIncremental
from src.datos.validador import ValidadorDatos
from src.datos.limpiador import LimpiadorDatos
from src.caracteristicas.extractor import ExtractorCaracteristicas
from src.modelos.enrutador import EnrutadorModelos
from src.priorizacion.fase1_simple import PuntuadorSimple
from src.priorizacion.aprendizaje_activo import AprendizajeActivo
from src.utilidades.registrador import registro

def main():
    registro.info("🚀 Iniciando tubería diaria de Orion...")
    
    cargador = CargadorIncremental()
    consumo = cargador.cargar_archivos_nuevos('consumo')
    
    if consumo.empty:
        registro.warning("⚠️ No hay datos nuevos. Finalizando.")
        return
    
    validador = ValidadorDatos()
    reporte = validador.generar_reporte_calidad(consumo, 'consumo')
    registro.info(f"📊 Calidad: {reporte['validacion']['estado']}")
    
    limpiador = LimpiadorDatos()
    consumo = limpiador.limpiar_consumo(consumo)
    
    extractor = ExtractorCaracteristicas()
    features = extractor.extraer_consumo(consumo)
    
    if features.empty:
        registro.error("❌ No se pudieron extraer características")
        return
    
    np.random.seed(42)
    probabilidades = np.random.uniform(0, 1, len(features))
    
    puntuador = PuntuadorSimple()
    puntajes = puntuador.calcular_puntajes(features, probabilidades)
    
    activo = AprendizajeActivo()
    seleccionados = activo.seleccionar_casos(puntajes, probabilidades, n=50)
    
    processed_dir = Path('datos/procesados')
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    fecha = datetime.now().strftime('%Y%m%d')
    puntajes.to_parquet(processed_dir / f'puntajes_{fecha}.parquet')
    seleccionados.to_csv(processed_dir / f'inspecciones_priorizadas_{fecha}.csv', index=False)
    
    registro.info(f"✅ Tubería diaria completada: {len(puntajes)} suministros priorizados")

if __name__ == "__main__":
    main()