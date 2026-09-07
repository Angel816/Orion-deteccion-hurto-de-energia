# scripts/sincronizar_google_sheets.py
"""
Sincronización con Google Sheets para inspecciones
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.inspeccion.gestor_cola import GestorCola
from src.utilidades.registrador import registro

def main():
    registro.info("📤 Sincronizando con Google Sheets...")
    
    cola = GestorCola()
    items = cola.obtener_pendientes()
    
    if not items:
        registro.info("ℹ️ No hay items pendientes")
        return
    
    registro.info(f"📤 {len(items)} items pendientes")
    
    for item in items:
        try:
            cola.mover_a_procesando(item['id'])
            cola.marcar_completado(item['id'])
            registro.info(f"   ✅ Item {item['id']} sincronizado")
        except Exception as e:
            cola.marcar_fallido(item['id'], str(e))
            registro.error(f"   ❌ Error: {e}")
    
    stats = cola.obtener_estadisticas()
    registro.info("📊 Estado final:")
    for k, v in stats.items():
        registro.info(f"   {k}: {v}")

if __name__ == "__main__":
    main()