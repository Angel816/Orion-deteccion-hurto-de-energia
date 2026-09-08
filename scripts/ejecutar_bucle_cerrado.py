# scripts/ejecutar_bucle_cerrado.py
"""
Ejecuta el bucle cerrado de Orion
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.tuberias.bucle_cerrado import BucleCerrado
from src.utilidades.registrador import registro

def main():
    registro.info("🔄 Iniciando bucle cerrado de Orion...")
    
    # Verificar que existen datos procesados
    processed_dir = Path('datos/procesados')
    if not processed_dir.exists():
        registro.error("❌ No hay datos procesados. Ejecuta primero la tubería diaria.")
        return
    
    archivos = list(processed_dir.glob('puntajes_*.parquet'))
    if not archivos:
        registro.error("❌ No hay puntajes disponibles. Ejecuta primero la tubería diaria.")
        return
    
    bucle = BucleCerrado()
    evaluacion = bucle.evaluar_modelo()
    
    if 'error' in evaluacion:
        registro.warning(f"⚠️ {evaluacion['error']}")
    
    if bucle.debe_reentrenar(evaluacion):
        resultado = bucle.reentrenar_modelo()
        registro.info(f"✅ Modelo reentrenado: {resultado.get('version', 'desconocida')}")
    else:
        registro.info("⏳ No se requiere reentrenamiento")
    
    estado = bucle.obtener_estado()
    registro.info("📊 Estado del bucle cerrado:")
    registro.info(f"   Total muestras: {estado['total_muestras_entrenamiento']}")
    registro.info(f"   Versión actual: {estado['version_actual']}")

if __name__ == "__main__":
    main()