# scripts/ejecutar_sincronizador.py
"""
Ejecuta el sincronizador de inspecciones
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import argparse
from src.inspeccion.sincronizador import SincronizadorInspeccion
from src.inspeccion.gestor_cola import GestorCola
from src.utilidades.registrador import registro

def main():
    parser = argparse.ArgumentParser(description='Orion - Sincronizador de Inspecciones')
    parser.add_argument('command', choices=['start', 'sync', 'status', 'retry', 'cleanup'])
    parser.add_argument('--dias', type=int, default=30)
    
    args = parser.parse_args()
    
    sincronizador = SincronizadorInspeccion()
    cola = GestorCola()
    
    if args.command == 'start':
        sincronizador.ejecutar_continuo()
    elif args.command == 'sync':
        resultados = sincronizador.sincronizar_todo()
        print(f"\n📊 Resultados: {resultados.get('sincronizados', 0)} OK, {resultados.get('fallidos', 0)} fallidos")
    elif args.command == 'status':
        stats = cola.obtener_estadisticas()
        print("\n📊 Estado de la Cola:")
        for k, v in stats.items():
            print(f"   {k}: {v}")
    elif args.command == 'retry':
        reintentados = cola.reintentar_fallidos()
        print(f"🔄 Reintentando {len(reintentados)} items")
    elif args.command == 'cleanup':
        eliminados = cola.limpiar_completados(args.dias)
        print(f"🗑️ Limpiados {eliminados} items")

if __name__ == "__main__":
    main()