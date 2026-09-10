# scripts/procesar_cola_datos.py
"""
Procesa automáticamente los archivos en la cola de datos
Zona horaria: Perú (UTC-5)
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import argparse
from src.datos.normalizador_cola import NormalizadorCola
from src.utilidades.tiempo import ahora_peru


def main():
    parser = argparse.ArgumentParser(description='Procesar cola de datos Orion')
    parser.add_argument('--estado', action='store_true', help='Mostrar estado de la cola')
    parser.add_argument('--historial', action='store_true', help='Mostrar estado del historial')
    parser.add_argument('--agregar', type=str, help='Agregar archivo a la cola')
    parser.add_argument('--procesar', action='store_true', help='Procesar la cola')
    parser.add_argument('--limpiar', action='store_true', help='Limpiar carpeta de procesando')
    
    args = parser.parse_args()
    
    normalizador = NormalizadorCola()
    
    if args.estado:
        estado = normalizador.obtener_estado_cola()
        print("\n📊 ESTADO DE LA COLA DE DATOS")
        print("=" * 40)
        print(f"📥 Pendientes:  {estado['pendientes']}")
        print(f"🔄 Procesando:  {estado['procesando']}")
        print(f"❌ Errores:     {estado['errores']}")
        print("=" * 40)
        print(f"🕐 Hora Perú: {ahora_peru().strftime('%Y-%m-%d %H:%M:%S')}")
    
    elif args.historial:
        historial = normalizador.obtener_estado_historial()
        print("\n📚 ESTADO DEL HISTORIAL (datos_pasados)")
        print("=" * 40)
        for tipo, cantidad in historial.items():
            print(f"   {tipo}: {cantidad} archivos")
        print("=" * 40)
        print(f"🕐 Hora Perú: {ahora_peru().strftime('%Y-%m-%d %H:%M:%S')}")
    
    elif args.agregar:
        archivo = Path(args.agregar)
        if normalizador.agregar_a_cola(archivo):
            print(f"✅ Archivo agregado a la cola: {archivo.name}")
            print(f"🕐 Hora Perú: {ahora_peru().strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"❌ Error al agregar archivo: {archivo.name}")
    
    elif args.procesar:
        print(f"🔄 Procesando cola de datos...")
        print(f"🕐 Hora Perú: {ahora_peru().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        resultados = normalizador.procesar_cola()
        
        print("\n📊 RESULTADOS")
        print("=" * 40)
        print(f"📂 Total:        {resultados['total']}")
        print(f"✅ Procesados:   {resultados['procesados']}")
        print(f"❌ Errores:      {resultados['errores']}")
        print("=" * 40)
        
        for detalle in resultados['detalles']:
            if detalle['estado'] == 'exito':
                print(f"   ✅ {detalle['archivo']} → {detalle['tipo']} ({detalle['registros']} registros)")
            else:
                print(f"   ❌ {detalle['archivo']}: {detalle['mensaje']}")
        
        print(f"\n🕐 Finalizado: {ahora_peru().strftime('%Y-%m-%d %H:%M:%S')} (Perú)")
    
    elif args.limpiar:
        normalizador.limpiar_procesando()
        print(f"🗑️ Carpeta de procesando limpiada")
        print(f"🕐 Hora Perú: {ahora_peru().strftime('%Y-%m-%d %H:%M:%S')}")
    
    else:
        print(f"""
📋 COMANDOS DISPONIBLES (Hora Perú: {ahora_peru().strftime('%Y-%m-%d %H:%M:%S')})
  --estado          Ver estado de la cola
  --historial       Ver estado del historial
  --agregar ARCHIVO Agregar archivo a la cola
  --procesar        Procesar todos los archivos en cola
  --limpiar         Limpiar carpeta de procesando

Ejemplos:
  python scripts/procesar_cola_datos.py --estado
  python scripts/procesar_cola_datos.py --historial
  python scripts/procesar_cola_datos.py --agregar C:/Users/datos/consumo.csv
  python scripts/procesar_cola_datos.py --procesar
  python scripts/procesar_cola_datos.py --limpiar
        """)


if __name__ == "__main__":
    main()