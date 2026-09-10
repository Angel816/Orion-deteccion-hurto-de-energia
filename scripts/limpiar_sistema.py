# scripts/limpiar_sistema.py
"""
Limpia completamente el sistema Orion
Zona horaria: Perú (UTC-5)
"""

import shutil
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.utilidades.registrador import registro
from src.utilidades.tiempo import ahora_peru


def limpiar_sistema():
    """
    Limpia todos los datos generados por el sistema
    """
    print("=" * 70)
    print("🧹 LIMPIANDO SISTEMA ORION")
    print(f"🕐 Hora Perú: {ahora_peru().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # ============================================================
    # 1. DATOS PROCESADOS
    # ============================================================
    print("\n📂 Limpiando datos procesados...")
    
    procesados = Path('datos/procesados')
    if procesados.exists():
        eliminados = 0
        for archivo in procesados.glob('*'):
            try:
                archivo.unlink()
                eliminados += 1
            except Exception as e:
                print(f"   ⚠️ Error eliminando {archivo.name}: {e}")
        print(f"   ✅ {procesados} limpiado ({eliminados} archivos)")
    else:
        print(f"   ℹ️ {procesados} no existe")
    
    # ============================================================
    # 2. METADATOS DE INGESTA
    # ============================================================
    print("\n📂 Limpiando metadatos de ingesta...")
    
    metadatos_ingesta = Path('datos/procesados/metadatos_ingesta.json')
    if metadatos_ingesta.exists():
        metadatos_ingesta.unlink()
        print(f"   ✅ {metadatos_ingesta} eliminado")
    
    metadatos_dir = Path('datos/metadatos')
    if metadatos_dir.exists():
        eliminados = 0
        for archivo in metadatos_dir.glob('*.json'):
            try:
                archivo.unlink()
                eliminados += 1
            except:
                pass
        print(f"   ✅ {metadatos_dir} limpiado ({eliminados} archivos)")
    
    # ============================================================
    # 3. DATOS DE INSPECCIÓN (cola)
    # ============================================================
    print("\n📂 Limpiando cola de inspección...")
    
    cola_dirs = [
        'datos/inspeccion/cola/pendientes',
        'datos/inspeccion/cola/procesando',
        'datos/inspeccion/cola/fallidos',
        'datos/inspeccion/cola/completados'
    ]
    
    for dir_path in cola_dirs:
        path = Path(dir_path)
        if path.exists():
            eliminados = 0
            for archivo in path.glob('*.json'):
                try:
                    archivo.unlink()
                    eliminados += 1
                except:
                    pass
            print(f"   ✅ {dir_path} limpiado ({eliminados} archivos)")
    
    # ============================================================
    # 4. REGISTROS DE INSPECCIÓN
    # ============================================================
    print("\n📂 Limpiando registros de inspección...")
    
    registros = Path('datos/inspeccion/registros')
    if registros.exists():
        eliminados = 0
        for archivo in registros.glob('*'):
            try:
                archivo.unlink()
                eliminados += 1
            except:
                pass
        print(f"   ✅ {registros} limpiado ({eliminados} archivos)")
    
    # ============================================================
    # 5. RETROALIMENTACIÓN
    # ============================================================
    print("\n📂 Limpiando retroalimentación...")
    
    feedback_dirs = [
        'datos/retroalimentacion/inspecciones',
        'datos/retroalimentacion/entrenamiento'
    ]
    
    for dir_path in feedback_dirs:
        path = Path(dir_path)
        if path.exists():
            eliminados = 0
            for archivo in path.glob('*'):
                try:
                    archivo.unlink()
                    eliminados += 1
                except:
                    pass
            print(f"   ✅ {dir_path} limpiado ({eliminados} archivos)")
    
    # ============================================================
    # 6. MODELOS ENTRENADOS
    # ============================================================
    print("\n📂 Limpiando modelos...")
    
    for modelos_dir in ['modelos/actual', 'modelos/historico']:
        path = Path(modelos_dir)
        if path.exists():
            eliminados = 0
            for archivo in path.glob('*'):
                try:
                    archivo.unlink()
                    eliminados += 1
                except:
                    pass
            print(f"   ✅ {modelos_dir} limpiado ({eliminados} archivos)")
    
    # ============================================================
    # 7. REPORTES
    # ============================================================
    print("\n📂 Limpiando reportes...")
    
    reportes = Path('reportes')
    if reportes.exists():
        eliminados = 0
        for archivo in reportes.glob('*'):
            if archivo.name != '.gitkeep':
                try:
                    archivo.unlink()
                    eliminados += 1
                except:
                    pass
        print(f"   ✅ {reportes} limpiado ({eliminados} archivos)")
    
    # ============================================================
    # 8. LOGS
    # ============================================================
    print("\n📂 Limpiando logs...")
    
    logs = Path('registros')
    if logs.exists():
        eliminados = 0
        for archivo in logs.glob('*.log'):
            try:
                archivo.unlink()
                eliminados += 1
            except:
                pass
        print(f"   ✅ {logs} limpiado ({eliminados} archivos)")
    
    # ============================================================
    # 9. DATOS BRUTOS (opcional)
    # ============================================================
    print("\n📂 ¿Eliminar datos brutos? (s/n)")
    respuesta = input("> ").lower().strip()
    
    if respuesta == 's':
        brutos = Path('datos/brutos')
        if brutos.exists():
            for conjunto in brutos.iterdir():
                if conjunto.is_dir():
                    for archivo in conjunto.glob('*'):
                        try:
                            archivo.unlink()
                        except:
                            pass
            print(f"   ✅ {brutos} limpiado")
    else:
        print("   ℹ️ Datos brutos conservados")
    
    # ============================================================
    # 10. RESUMEN
    # ============================================================
    print("\n" + "=" * 70)
    print("✅ SISTEMA LIMPIADO COMPLETAMENTE")
    print(f"🕐 Finalizado: {ahora_peru().strftime('%Y-%m-%d %H:%M:%S')} (Perú)")
    print("=" * 70)
    
    print("\n📋 RESUMEN DE LIMPIEZA:")
    print(f"   📂 datos/procesados/          ✅")
    print(f"   📄 metadatos_ingesta.json     ✅")
    print(f"   📂 datos/metadatos/           ✅")
    print(f"   📂 datos/inspeccion/cola/     ✅")
    print(f"   📂 datos/inspeccion/registros/ ✅")
    print(f"   📂 datos/retroalimentacion/   ✅")
    print(f"   📂 modelos/actual/            ✅")
    print(f"   📂 modelos/historico/         ✅")
    print(f"   📂 reportes/                  ✅")
    print(f"   📂 registros/                 ✅")
    
    if respuesta == 's':
        print(f"   📂 datos/brutos/             ✅")
    
    print("\n🚀 El sistema está limpio y listo para empezar de nuevo.")


if __name__ == "__main__":
    limpiar_sistema()