# scripts/diagnostico_completo.py
"""
Diagnóstico completo de compatibilidad del sistema Orion
"""

import sys
from pathlib import Path

# Agregar src al path
sys.path.append(str(Path(__file__).parent.parent))

print("=" * 70)
print("🔍 DIAGNÓSTICO COMPLETO DE COMPATIBILIDAD")
print("=" * 70)

errores = []
advertencias = []

# ============================================================
# 1. VERIFICAR IMPORTS DE MÓDULOS
# ============================================================

print("\n1️⃣ VERIFICANDO IMPORTS DE MÓDULOS...")

modulos = [
    ('src.utilidades.configuracion', 'configuracion'),
    ('src.utilidades.registrador', 'registro'),
    ('src.utilidades.tiempo', 'ahora_peru, iso_peru, timestamp_peru, formatear_fecha'),
    ('src.utilidades.metricas', 'MetricasModelo, MetricasNegocio, FormateadorMetricas'),
    ('src.datos.cargador', 'CargadorIncremental'),
    ('src.datos.validador', 'ValidadorDatos'),
    ('src.datos.limpiador', 'LimpiadorDatos'),
    ('src.datos.normalizador', 'NormalizadorDatos'),
    ('src.datos.normalizador_cola', 'NormalizadorCola'),
    ('src.caracteristicas.extractor', 'ExtractorCaracteristicas'),
    ('src.modelos.isolation_forest', 'BosqueAislamiento'),
    ('src.modelos.random_forest', 'BosqueAleatorio'),
    ('src.modelos.ensemble', 'Conjunto'),
    ('src.modelos.enrutador', 'EnrutadorModelos'),
    ('src.priorizacion.fase1_simple', 'PuntuadorSimple'),
    ('src.priorizacion.aprendizaje_activo', 'AprendizajeActivo'),
    ('src.inspeccion.gestor_cola', 'GestorCola'),
    ('src.inspeccion.validador_resultados', 'ValidadorResultados'),
    ('src.tuberias.bucle_cerrado', 'BucleCerrado'),
    ('src.monitoreo.alertas', 'SistemaAlertas'),
    ('src.monitoreo.deriva', 'DetectorDeriva'),
    ('src.monitoreo.falsos_positivos', 'MonitorFalsosPositivos'),
    ('src.almacenamiento.particionado', 'AlmacenamientoParticionado'),
    ('src.almacenamiento.compresion', 'CompresorDatos'),
]

for modulo, clases in modulos:
    try:
        __import__(modulo)
        print(f"   ✅ {modulo}")
    except Exception as e:
        print(f"   ❌ {modulo}: {e}")
        errores.append(f"Import {modulo}: {e}")

# ============================================================
# 2. VERIFICAR FUNCIONES DE TIEMPO (PERÚ)
# ============================================================

print("\n2️⃣ VERIFICANDO FUNCIONES DE TIEMPO (PERÚ)...")

try:
    from src.utilidades.tiempo import ahora_peru, iso_peru, timestamp_peru, formatear_fecha
    
    fecha = ahora_peru()
    print(f"   ✅ ahora_peru(): {fecha}")
    print(f"   ✅ iso_peru(): {iso_peru()}")
    print(f"   ✅ timestamp_peru(): {timestamp_peru()}")
    print(f"   ✅ formatear_fecha(): {formatear_fecha(fecha)}")
    
    # Verificar zona horaria
    if 'America/Lima' in str(fecha.tzinfo):
        print(f"   ✅ Zona horaria correcta: {fecha.tzinfo}")
    else:
        print(f"   ⚠️ Zona horaria inesperada: {fecha.tzinfo}")
        advertencias.append("Zona horaria no es America/Lima")
except Exception as e:
    print(f"   ❌ Error: {e}")
    errores.append(f"Tiempo: {e}")

# ============================================================
# 3. VERIFICAR MÉTRICAS (MONEDA SOLES)
# ============================================================

print("\n3️⃣ VERIFICANDO MÉTRICAS (MONEDA SOLES)...")

try:
    from src.utilidades.metricas import FormateadorMetricas
    
    moneda = FormateadorMetricas.formatear_moneda(12450.00)
    print(f"   ✅ formatear_moneda(): {moneda}")
    
    if 'S/' in moneda:
        print(f"   ✅ Símbolo correcto: S/")
    else:
        print(f"   ⚠️ Símbolo incorrecto: {moneda}")
        advertencias.append("Símbolo de moneda incorrecto")
    
    porcentaje = FormateadorMetricas.formatear_porcentaje(0.852)
    print(f"   ✅ formatear_porcentaje(): {porcentaje}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    errores.append(f"Métricas: {e}")

# ============================================================
# 4. VERIFICAR CARPETAS
# ============================================================

print("\n4️⃣ VERIFICANDO CARPETAS...")

carpetas = [
    'datos/cola/pendientes',
    'datos/cola/procesando',
    'datos/cola/errores',
    'datos/brutos/consumo',
    'datos/brutos/clientes',
    'datos/brutos/alarmas',
    'datos/brutos/facturacion',
    'datos/brutos/inspecciones',
    'datos/procesados',
    'datos/metadatos',
    'datos/retroalimentacion/entrenamiento',
    'datos/retroalimentacion/inspecciones',
    'datos_pasados/consumo',
    'datos_pasados/clientes',
    'datos_pasados/alarmas',
    'datos_pasados/facturacion',
    'datos_pasados/inspecciones',
    'modelos/actual',
    'modelos/historico',
]

for carpeta in carpetas:
    path = Path(carpeta)
    if path.exists():
        print(f"   ✅ {carpeta}")
    else:
        print(f"   ⚠️ {carpeta} (creando...)")
        path.mkdir(parents=True, exist_ok=True)
        advertencias.append(f"Carpeta creada: {carpeta}")

# ============================================================
# 5. VERIFICAR ARCHIVOS CLAVE
# ============================================================

print("\n5️⃣ VERIFICANDO ARCHIVOS CLAVE...")

archivos = [
    'scripts/generar_datos_realistas.py',
    'scripts/crear_datos_entrenamiento.py',
    'scripts/ejecutar_tuberia_diaria.py',
    'scripts/ejecutar_bucle_cerrado.py',
    'scripts/procesar_cola_datos.py',
    'scripts/tablero_orion.py',
    'scripts/limpiar_sistema.py',
    'scripts/ejecutar_flujo_completo.py',
    'src/datos/normalizador.py',
    'src/datos/normalizador_cola.py',
    'src/tuberias/bucle_cerrado.py',
]

for archivo in archivos:
    path = Path(archivo)
    if path.exists():
        print(f"   ✅ {archivo}")
    else:
        print(f"   ❌ {archivo} NO EXISTE")
        errores.append(f"Archivo faltante: {archivo}")

# ============================================================
# 6. VERIFICAR DATOS DE EJEMPLO
# ============================================================

print("\n6️⃣ VERIFICANDO DATOS DE EJEMPLO...")

# Verificar datos en cola
cola_dir = Path('datos/cola/pendientes')
if cola_dir.exists():
    archivos_cola = list(cola_dir.glob('*'))
    print(f"   📂 Cola: {len(archivos_cola)} archivos")
    for archivo in archivos_cola:
        print(f"      - {archivo.name}")

# Verificar datos procesados
proc_dir = Path('datos/procesados')
if proc_dir.exists():
    archivos_proc = list(proc_dir.glob('*'))
    print(f"   📂 Procesados: {len(archivos_proc)} archivos")
    for archivo in archivos_proc[:5]:
        print(f"      - {archivo.name}")

# Verificar modelo
modelo_dir = Path('modelos/actual')
if modelo_dir.exists():
    archivos_modelo = list(modelo_dir.glob('*'))
    print(f"   📂 Modelo actual: {len(archivos_modelo)} archivos")
    for archivo in archivos_modelo:
        print(f"      - {archivo.name}")

# ============================================================
# 7. VERIFICAR CONFIGURACIÓN
# ============================================================

print("\n7️⃣ VERIFICANDO CONFIGURACIÓN...")

try:
    from src.utilidades.configuracion import configuracion
    
    proyecto_nombre = configuracion.obtener('proyecto.nombre', 'Orion')
    print(f"   ✅ Proyecto: {proyecto_nombre}")
    
    entorno = configuracion.obtener('proyecto.entorno', 'desarrollo')
    print(f"   ✅ Entorno: {entorno}")
    
    ruta_brutos = configuracion.obtener('datos.ruta_brutos', 'datos/brutos')
    print(f"   ✅ Ruta brutos: {ruta_brutos}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    errores.append(f"Configuración: {e}")

# ============================================================
# 8. VERIFICAR REQUISITOS
# ============================================================

print("\n8️⃣ VERIFICANDO REQUISITOS (requirements.txt)...")

requisitos_path = Path('requirements.txt')
if requisitos_path.exists():
    with open(requisitos_path, 'r', encoding='utf-8') as f:
        requisitos = f.read()
    
    paquetes_clave = ['pandas', 'numpy', 'scikit-learn', 'fastapi', 'streamlit', 
                      'openpyxl', 'xgboost', 'lightgbm', 'shap', 'loguru']
    
    for paquete in paquetes_clave:
        if paquete in requisitos:
            print(f"   ✅ {paquete}")
        else:
            print(f"   ⚠️ {paquete} no encontrado en requirements.txt")
            advertencias.append(f"Paquete {paquete} no está en requirements.txt")

# ============================================================
# 9. VERIFICAR DEPENDENCIAS INSTALADAS
# ============================================================

print("\n9️⃣ VERIFICANDO DEPENDENCIAS INSTALADAS...")

try:
    import pandas
    print(f"   ✅ pandas: {pandas.__version__}")
except:
    print(f"   ❌ pandas no instalado")
    errores.append("pandas no instalado")

try:
    import numpy
    print(f"   ✅ numpy: {numpy.__version__}")
except:
    print(f"   ❌ numpy no instalado")
    errores.append("numpy no instalado")

try:
    import sklearn
    print(f"   ✅ scikit-learn: {sklearn.__version__}")
except:
    print(f"   ❌ scikit-learn no instalado")
    errores.append("scikit-learn no instalado")

try:
    import openpyxl
    print(f"   ✅ openpyxl: {openpyxl.__version__}")
except:
    print(f"   ❌ openpyxl no instalado")
    errores.append("openpyxl no instalado")

try:
    import streamlit
    print(f"   ✅ streamlit: {streamlit.__version__}")
except:
    print(f"   ❌ streamlit no instalado")
    errores.append("streamlit no instalado")

try:
    import fastapi
    print(f"   ✅ fastapi: {fastapi.__version__}")
except:
    print(f"   ❌ fastapi no instalado")
    errores.append("fastapi no instalado")

# ============================================================
# 10. RESUMEN
# ============================================================

print("\n" + "=" * 70)
print("📊 RESUMEN DEL DIAGNÓSTICO")
print("=" * 70)

if errores:
    print(f"\n❌ ERRORES ({len(errores)}):")
    for error in errores:
        print(f"   • {error}")
else:
    print("\n✅ NO HAY ERRORES CRÍTICOS")

if advertencias:
    print(f"\n⚠️ ADVERTENCIAS ({len(advertencias)}):")
    for adv in advertencias:
        print(f"   • {adv}")
else:
    print("\n✅ NO HAY ADVERTENCIAS")

print("\n" + "=" * 70)
print("✅ DIAGNÓSTICO COMPLETADO")
print("=" * 70)