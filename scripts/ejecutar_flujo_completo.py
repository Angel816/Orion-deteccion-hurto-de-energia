# scripts/ejecutar_flujo_completo.py
"""
Ejecuta el flujo completo de Orion:
1. Generar datos realistas
2. Procesar cola de datos
3. Crear datos de entrenamiento
4. Ejecutar tubería diaria
5. Ejecutar bucle cerrado

Zona horaria: Perú (UTC-5)
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import subprocess
import time
from src.utilidades.registrador import registro
from src.utilidades.tiempo import ahora_peru


# ============================================================
# EJECUTOR DE PASOS
# ============================================================

def ejecutar_paso(nombre: str, script: str, argumentos: list = None) -> bool:
    """
    Ejecuta un script de Python y maneja errores
    
    Parámetros:
        nombre: Nombre descriptivo del paso
        script: Ruta del script a ejecutar
        argumentos: Lista de argumentos adicionales
    
    Retorna:
        True si se ejecutó correctamente, False si falló
    """
    registro.info("")
    registro.info("=" * 70)
    registro.info(f"🚀 PASO: {nombre}")
    registro.info("=" * 70)
    
    comando = [sys.executable, script]
    if argumentos:
        comando.extend(argumentos)
    
    inicio = time.time()
    
    try:
        result = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        duracion = time.time() - inicio
        
        # Mostrar salida
        if result.stdout:
            print(result.stdout)
        
        if result.returncode == 0:
            registro.info(f"✅ {nombre} completado en {duracion:.2f}s")
            return True
        else:
            registro.error(f"❌ {nombre} falló después de {duracion:.2f}s")
            if result.stderr:
                print(result.stderr)
            return False
    
    except Exception as e:
        registro.error(f"❌ Error ejecutando {nombre}: {e}")
        return False


# ============================================================
# VERIFICACIONES
# ============================================================

def verificar_estructura() -> bool:
    """
    Verifica que la estructura de carpetas necesaria exista
    """
    registro.info("🔍 Verificando estructura de carpetas...")
    
    carpetas_necesarias = [
        'datos/cola/pendientes',
        'datos/cola/procesando',
        'datos/cola/errores',
        'datos/brutos/consumo',
        'datos/brutos/clientes',
        'datos/brutos/alarmas',
        'datos/brutos/facturacion',
        'datos/procesados',
        'datos/muestra',
        'datos/metadatos',
        'datos/retroalimentacion/entrenamiento',
        'datos/retroalimentacion/inspecciones',
        'datos_pasados/consumo',
        'datos_pasados/clientes',
        'datos_pasados/alarmas',
        'datos_pasados/facturacion',
        'modelos/actual',
        'modelos/historico'
    ]
    
    for carpeta in carpetas_necesarias:
        Path(carpeta).mkdir(parents=True, exist_ok=True)
    
    registro.info(f"✅ {len(carpetas_necesarias)} carpetas verificadas")
    return True


# ============================================================
# FLUJO PRINCIPAL
# ============================================================

def main():
    """
    Ejecuta el flujo completo de Orion
    """
    inicio_total = time.time()
    
    print("")
    print("=" * 70)
    print("🌌 PROYECTO ORION - FLUJO COMPLETO")
    print(f"🕐 Hora Perú: {ahora_peru().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # ============================================================
    # PASO 0: VERIFICAR ESTRUCTURA
    # ============================================================
    verificar_estructura()
    
    # ============================================================
    # PASO 1: GENERAR DATOS REALISTAS
    # ============================================================
    if not ejecutar_paso(
        "Generar datos realistas",
        "scripts/generar_datos_realistas.py"
    ):
        registro.error("❌ Flujo detenido en: Generar datos realistas")
        return
    
    # ============================================================
    # PASO 2: PROCESAR COLA DE DATOS
    # ============================================================
    if not ejecutar_paso(
        "Procesar cola de datos",
        "scripts/procesar_cola_datos.py",
        ["--procesar"]
    ):
        registro.error("❌ Flujo detenido en: Procesar cola de datos")
        return
    
    # ============================================================
    # PASO 3: CREAR DATOS DE ENTRENAMIENTO
    # ============================================================
    if not ejecutar_paso(
        "Crear datos de entrenamiento",
        "scripts/crear_datos_entrenamiento.py"
    ):
        registro.error("❌ Flujo detenido en: Crear datos de entrenamiento")
        return
    
    # ============================================================
    # PASO 4: EJECUTAR TUBERÍA DIARIA
    # ============================================================
    if not ejecutar_paso(
        "Ejecutar tubería diaria",
        "scripts/ejecutar_tuberia_diaria.py"
    ):
        registro.error("❌ Flujo detenido en: Ejecutar tubería diaria")
        return
    
    # ============================================================
    # PASO 5: EJECUTAR BUCLE CERRADO
    # ============================================================
    if not ejecutar_paso(
        "Ejecutar bucle cerrado",
        "scripts/ejecutar_bucle_cerrado.py"
    ):
        registro.error("❌ Flujo detenido en: Ejecutar bucle cerrado")
        return
    
    # ============================================================
    # RESUMEN FINAL
    # ============================================================
    duracion_total = time.time() - inicio_total
    
    print("")
    print("=" * 70)
    print("✅ FLUJO COMPLETO COMPLETADO")
    print("=" * 70)
    print(f"🕐 Hora Perú: {ahora_peru().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️  Duración total: {duracion_total:.2f}s ({duracion_total/60:.1f} min)")
    print("")
    print("📊 VERIFICACIONES:")
    
    # Verificar modelo
    modelo_path = Path('modelos/actual/modelo_actual.pkl')
    metrics_path = Path('modelos/actual/metrics.json')
    if modelo_path.exists() and metrics_path.exists():
        print("   ✅ Modelo entrenado y métricas guardadas")
    else:
        print("   ⚠️ Modelo no encontrado")
    
    # Verificar histórico
    historico_path = Path('datos/procesados/historico_puntajes.parquet')
    if historico_path.exists():
        import pandas as pd
        df = pd.read_parquet(historico_path)
        print(f"   ✅ Histórico: {len(df)} registros")
    
    # Verificar datos de entrenamiento
    train_path = Path('datos/retroalimentacion/entrenamiento/datos_etiquetados.parquet')
    if train_path.exists():
        import pandas as pd
        df = pd.read_parquet(train_path)
        print(f"   ✅ Datos de entrenamiento: {len(df)} registros")
    
    # Verificar estado del bucle
    bucle_path = Path('datos/retroalimentacion/entrenamiento/estado_bucle.json')
    if bucle_path.exists():
        print(f"   ✅ Estado del bucle cerrado guardado")
    
    print("")
    print("📋 PRÓXIMOS PASOS:")
    print("   Para ver el dashboard:")
    print("   streamlit run scripts/tablero_orion.py")
    print("")
    print("=" * 70)


if __name__ == "__main__":
    main()