# scripts/limpiar_sistema.py
"""
Limpia completamente el sistema Orion
Elimina datos procesados, modelos, logs, metadatos y colas de inspección
"""

import shutil
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.utilidades.registrador import registro

def limpiar_sistema():
    """
    Limpia todos los datos generados por el sistema
    """
    print("=" * 70)
    print("🧹 LIMPIANDO SISTEMA ORION")
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
    # 2. METADATOS DE INGESTA (NUEVO)
    # ============================================================
    print("\n📂 Limpiando metadatos de ingesta...")
    
    metadatos_ingesta = Path('datos/procesados/metadatos_ingesta.json')
    if metadatos_ingesta.exists():
        metadatos_ingesta.unlink()
        print(f"   ✅ {metadatos_ingesta} eliminado")
    else:
        print(f"   ℹ️ {metadatos_ingesta} no existe")
    
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
    else:
        print(f"   ℹ️ {metadatos_dir} no existe")
    
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
        else:
            print(f"   ℹ️ {dir_path} no existe")
    
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
    else:
        print(f"   ℹ️ {registros} no existe")
    
    # ============================================================
    # 5. RETROALIMENTACIÓN (inspecciones y entrenamiento)
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
        else:
            print(f"   ℹ️ {dir_path} no existe")
    
    # ============================================================
    # 6. MODELOS ENTRENADOS
    # ============================================================
    print("\n📂 Limpiando modelos...")
    
    modelos = Path('modelos/actual')
    if modelos.exists():
        eliminados = 0
        for archivo in modelos.glob('*'):
            try:
                archivo.unlink()
                eliminados += 1
            except:
                pass
        print(f"   ✅ {modelos} limpiado ({eliminados} archivos)")
    else:
        print(f"   ℹ️ {modelos} no existe")
    
    modelos_hist = Path('modelos/historico')
    if modelos_hist.exists():
        eliminados = 0
        for archivo in modelos_hist.glob('*'):
            try:
                archivo.unlink()
                eliminados += 1
            except:
                pass
        print(f"   ✅ {modelos_hist} limpiado ({eliminados} archivos)")
    else:
        print(f"   ℹ️ {modelos_hist} no existe")
    
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
    else:
        print(f"   ℹ️ {reportes} no existe")
    
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
    else:
        print(f"   ℹ️ {logs} no existe")
    
    # ============================================================
    # 9. DATOS BRUTOS (opcional - preguntar)
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
                    try:
                        conjunto.rmdir()
                    except:
                        pass
            print(f"   ✅ {brutos} limpiado")
        else:
            print(f"   ℹ️ {brutos} no existe")
    else:
        print("   ℹ️ Datos brutos conservados")
    
    # ============================================================
    # 10. RESUMEN
    # ============================================================
    print("\n" + "=" * 70)
    print("✅ SISTEMA LIMPIADO COMPLETAMENTE")
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