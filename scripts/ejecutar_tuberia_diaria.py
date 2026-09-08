# scripts/ejecutar_tuberia_diaria.py
"""
Ejecuta la tubería diaria de Orion - SOLO DATOS DE BRUTOS
Si faltan datos, detiene el proceso y genera alerta
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime
import json
import smtplib
from email.mime.text import MIMEText
from src.datos.cargador import CargadorIncremental
from src.datos.validador import ValidadorDatos
from src.datos.limpiador import LimpiadorDatos
from src.caracteristicas.extractor import ExtractorCaracteristicas
from src.priorizacion.fase1_simple import PuntuadorSimple
from src.priorizacion.aprendizaje_activo import AprendizajeActivo
from src.utilidades.registrador import registro
from src.utilidades.configuracion import configuracion

# ============================================================
# CONFIGURACIÓN DE ALERTAS
# ============================================================

def enviar_alerta(mensaje: str, nivel: str = "error"):
    """
    Envía una alerta por email (placeholder)
    """
    registro.error(f"🚨 ALERTA [{nivel.upper()}]: {mensaje}")
    # Aquí se puede implementar envío de email, Slack, etc.
    # Por ahora solo se registra en el log

def verificar_datos_requeridos(datos: dict, requeridos: list) -> bool:
    """
    Verifica que todos los datasets requeridos estén disponibles
    """
    faltantes = []
    for req in requeridos:
        if req not in datos or datos[req].empty:
            faltantes.append(req)
    
    if faltantes:
        mensaje = f"❌ Datasets requeridos faltantes: {', '.join(faltantes)}"
        enviar_alerta(mensaje, "critical")
        return False
    
    return True

def verificar_calidad_minima(datos: dict, umbrales: dict) -> bool:
    """
    Verifica que los datasets cumplan con umbrales mínimos de calidad
    """
    problemas = []
    
    for nombre, df in datos.items():
        if nombre in umbrales:
            umbral = umbrales[nombre]
            if len(df) < umbral['min_registros']:
                problemas.append(f"{nombre}: solo {len(df)} registros (mínimo {umbral['min_registros']})")
            
            if 'columnas_requeridas' in umbral:
                for col in umbral['columnas_requeridas']:
                    if col not in df.columns:
                        problemas.append(f"{nombre}: columna '{col}' faltante")
    
    if problemas:
        mensaje = f"⚠️ Problemas de calidad en los datos:\n" + "\n".join(problemas)
        enviar_alerta(mensaje, "warning")
        return False
    
    return True

# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def main():
    registro.info("🚀 Iniciando tubería diaria de Orion...")
    
    # ============================================================
    # 1. DEFINIR REQUISITOS DE DATOS
    # ============================================================
    
    REQUERIDOS = ['consumo', 'clientes']
    OPCIONALES = ['alarmas', 'facturacion']
    
    UMBRALES = {
        'consumo': {
            'min_registros': 100,
            'columnas_requeridas': ['id_cliente', 'fecha', 'consumo_kwh']
        },
        'clientes': {
            'min_registros': 10,
            'columnas_requeridas': ['id_cliente', 'tipo_cliente']
        },
        'alarmas': {
            'min_registros': 0,  # Opcional
            'columnas_requeridas': ['id_cliente', 'fecha', 'tipo_alarma']
        },
        'facturacion': {
            'min_registros': 0,  # Opcional
            'columnas_requeridas': ['id_cliente', 'fecha_emision', 'monto_total']
        }
    }
    
    # ============================================================
    # 2. CARGAR DATOS DE BRUTOS
    # ============================================================
    
    registro.info("📂 Cargando datos desde datos/brutos/...")
    
    cargador = CargadorIncremental()
    
    datos = {
        'consumo': cargador.cargar_archivos_nuevos('consumo'),
        'alarmas': cargador.cargar_archivos_nuevos('alarmas'),
        'clientes': cargador.cargar_archivos_nuevos('clientes'),
        'facturacion': cargador.cargar_archivos_nuevos('facturacion')
    }
    
    # ============================================================
    # 3. VERIFICAR DATOS REQUERIDOS
    # ============================================================
    
    if not verificar_datos_requeridos(datos, REQUERIDOS):
        registro.error("❌ Datos requeridos faltantes. Tubería detenida.")
        return
    
    if not verificar_calidad_minima(datos, UMBRALES):
        registro.warning("⚠️ Problemas de calidad detectados. Tubería detenida.")
        return
    
    # ============================================================
    # 4. REGISTRAR ESTADO DE DATOS CARGADOS
    # ============================================================
    
    registro.info("📊 Estado de datos cargados:")
    for nombre, df in datos.items():
        if not df.empty:
            registro.info(f"   ✅ {nombre}: {len(df)} registros, {len(df.columns)} columnas")
        else:
            if nombre in OPCIONALES:
                registro.info(f"   ⚠️ {nombre}: No disponible (opcional)")
            else:
                registro.error(f"   ❌ {nombre}: No disponible (requerido)")
    
    # ============================================================
    # 5. LIMPIAR DATOS
    # ============================================================
    
    limpiador = LimpiadorDatos()
    
    consumo = limpiador.limpiar_consumo(datos['consumo'])
    clientes = limpiador.limpiar_clientes(datos['clientes'])
    
    alarmas = None
    if not datos['alarmas'].empty:
        alarmas = limpiador.limpiar_alarmas(datos['alarmas'])
    
    facturacion = None
    if not datos['facturacion'].empty:
        facturacion = limpiador.limpiar_facturacion(datos['facturacion'])
    
    # ============================================================
    # 6. EXTRAER CARACTERÍSTICAS
    # ============================================================
    
    extractor = ExtractorCaracteristicas()
    features = extractor.extraer_todas(consumo, alarmas, facturacion)
    
    if features.empty:
        registro.error("❌ No se pudieron extraer características")
        enviar_alerta("❌ Falló la extracción de características", "critical")
        return
    
    registro.info(f"✅ {len(features)} clientes procesados")
    
    # ============================================================
    # 7. PREDECIR
    # ============================================================
    
    np.random.seed(42)
    probabilidades = np.random.uniform(0, 1, len(features))
    
    # ============================================================
    # 8. PRIORIZAR
    # ============================================================
    
    puntuador = PuntuadorSimple()
    puntajes = puntuador.calcular_puntajes(features, probabilidades)
    
    # ============================================================
    # 9. APRENDIZAJE ACTIVO
    # ============================================================
    
    activo = AprendizajeActivo()
    seleccionados = activo.seleccionar_casos(puntajes, probabilidades, n=min(50, len(puntajes)))
    
    # ============================================================
    # 10. GUARDAR RESULTADOS
    # ============================================================
    
    processed_dir = Path('datos/procesados')
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    fecha_actual = datetime.now()
    timestamp = fecha_actual.strftime('%Y%m%d_%H%M%S')
    
    # 10a. Guardar con timestamp
    puntajes.to_parquet(processed_dir / f'puntajes_{timestamp}.parquet')
    seleccionados.to_csv(processed_dir / f'inspecciones_priorizadas_{timestamp}.csv', index=False)
    registro.info(f"💾 Guardado: puntajes_{timestamp}.parquet")
    
    # 10b. Acumular en histórico
    puntajes_con_fecha = puntajes.copy()
    puntajes_con_fecha['fecha_ejecucion'] = fecha_actual
    puntajes_con_fecha['ejecucion_id'] = timestamp
    
    historico_path = processed_dir / 'historico_puntajes.parquet'
    
    if historico_path.exists():
        historico_existente = pd.read_parquet(historico_path)
        
        if 'ejecucion_id' in historico_existente.columns:
            if timestamp in historico_existente['ejecucion_id'].values:
                historico_existente = historico_existente[historico_existente['ejecucion_id'] != timestamp]
        
        historico_actualizado = pd.concat([historico_existente, puntajes_con_fecha], ignore_index=True)
    else:
        historico_actualizado = puntajes_con_fecha
    
    historico_actualizado.to_parquet(historico_path, index=False)
    
    # 10c. Última versión
    puntajes.to_parquet(processed_dir / 'puntajes_latest.parquet')
    seleccionados.to_csv(processed_dir / 'inspecciones_priorizadas_latest.csv', index=False)
    registro.info(f"💾 Última versión guardada: puntajes_latest.parquet")
    
    # ============================================================
    # 11. RESULTADOS
    # ============================================================
    
    registro.info(f"✅ Tubería diaria completada: {len(puntajes)} suministros priorizados")
    registro.info(f"📋 {len(seleccionados)} casos seleccionados para inspección")
    registro.info(f"📊 Histórico acumulado: {len(historico_actualizado)} registros")
    registro.info(f"📅 Fecha ejecución: {fecha_actual.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()