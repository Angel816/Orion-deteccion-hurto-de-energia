# scripts/ejecutar_tuberia_diaria.py
"""
Ejecuta la tubería diaria de Orion - SOLO DATOS DE BRUTOS
Zona horaria: Perú (UTC-5)
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime
import json
from src.datos.cargador import CargadorIncremental
from src.datos.validador import ValidadorDatos
from src.datos.limpiador import LimpiadorDatos
from src.caracteristicas.extractor import ExtractorCaracteristicas
from src.priorizacion.fase1_simple import PuntuadorSimple
from src.priorizacion.aprendizaje_activo import AprendizajeActivo
from src.utilidades.registrador import registro
from src.utilidades.configuracion import configuracion
from src.utilidades.tiempo import ahora_peru, timestamp_peru, iso_peru

# ============================================================
# CONFIGURACIÓN DE ALERTAS
# ============================================================

def enviar_alerta(mensaje: str, nivel: str = "error"):
    """Envía una alerta por email (placeholder)"""
    registro.error(f"🚨 ALERTA [{nivel.upper()}]: {mensaje}")

def verificar_datos_requeridos(datos: dict, requeridos: list) -> bool:
    """Verifica que todos los datasets requeridos estén disponibles"""
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
    """Verifica que los datasets cumplan con umbrales mínimos de calidad"""
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
    registro.info(f"🕐 Hora Perú: {ahora_peru().strftime('%Y-%m-%d %H:%M:%S')}")
    
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
            'min_registros': 0,
            'columnas_requeridas': ['id_cliente', 'fecha', 'tipo_alarma']
        },
        'facturacion': {
            'min_registros': 0,
            'columnas_requeridas': ['id_cliente', 'fecha_emision', 'monto_total']
        }
    }
    
    registro.info("📂 Cargando datos desde datos/brutos/...")
    
    cargador = CargadorIncremental()
    
    datos = {
        'consumo': cargador.cargar_archivos_nuevos('consumo'),
        'alarmas': cargador.cargar_archivos_nuevos('alarmas'),
        'clientes': cargador.cargar_archivos_nuevos('clientes'),
        'facturacion': cargador.cargar_archivos_nuevos('facturacion')
    }
    
    if not verificar_datos_requeridos(datos, REQUERIDOS):
        registro.error("❌ Datos requeridos faltantes. Tubería detenida.")
        return
    
    if not verificar_calidad_minima(datos, UMBRALES):
        registro.warning("⚠️ Problemas de calidad detectados. Tubería detenida.")
        return
    
    registro.info("📊 Estado de datos cargados:")
    for nombre, df in datos.items():
        if not df.empty:
            registro.info(f"   ✅ {nombre}: {len(df)} registros, {len(df.columns)} columnas")
        else:
            if nombre in OPCIONALES:
                registro.info(f"   ⚠️ {nombre}: No disponible (opcional)")
            else:
                registro.error(f"   ❌ {nombre}: No disponible (requerido)")
    
    limpiador = LimpiadorDatos()
    
    consumo = limpiador.limpiar_consumo(datos['consumo'])
    clientes = limpiador.limpiar_clientes(datos['clientes'])
    
    alarmas = None
    if not datos['alarmas'].empty:
        alarmas = limpiador.limpiar_alarmas(datos['alarmas'])
    
    facturacion = None
    if not datos['facturacion'].empty:
        facturacion = limpiador.limpiar_facturacion(datos['facturacion'])
    
    extractor = ExtractorCaracteristicas()
    features = extractor.extraer_todas(consumo, alarmas, facturacion)
    
    if features.empty:
        registro.error("❌ No se pudieron extraer características")
        enviar_alerta("❌ Falló la extracción de características", "critical")
        return
    
    registro.info(f"✅ {len(features)} clientes procesados")
    
    np.random.seed(42)
    probabilidades = np.random.uniform(0, 1, len(features))
    
    puntuador = PuntuadorSimple()
    puntajes = puntuador.calcular_puntajes(features, probabilidades)
    
    activo = AprendizajeActivo()
    seleccionados = activo.seleccionar_casos(puntajes, probabilidades, n=min(50, len(puntajes)))
    
    processed_dir = Path('datos/procesados')
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    fecha_actual = ahora_peru()
    timestamp = timestamp_peru()
    
    puntajes.to_parquet(processed_dir / f'puntajes_{timestamp}.parquet')
    seleccionados.to_csv(processed_dir / f'inspecciones_priorizadas_{timestamp}.csv', index=False)
    registro.info(f"💾 Guardado: puntajes_{timestamp}.parquet")
    
    # ACUMULAR EN HISTÓRICO
    puntajes_con_fecha = puntajes.copy()
    puntajes_con_fecha['fecha_ejecucion'] = fecha_actual
    puntajes_con_fecha['ejecucion_id'] = timestamp
    puntajes_con_fecha['tipo_dato'] = 'puntaje'
    
    historico_path = processed_dir / 'historico_puntajes.parquet'
    
    if historico_path.exists():
        historico_existente = pd.read_parquet(historico_path)
        registro.info(f"📊 Histórico existente: {len(historico_existente)} registros")
        
        if 'ejecucion_id' in historico_existente.columns:
            if timestamp in historico_existente['ejecucion_id'].values:
                registro.warning(f"⚠️ La ejecución {timestamp} ya existe en el histórico")
                historico_existente = historico_existente[historico_existente['ejecucion_id'] != timestamp]
        
        historico_actualizado = pd.concat([historico_existente, puntajes_con_fecha], ignore_index=True)
        registro.info(f"📊 Histórico actualizado: {len(historico_actualizado)} registros (+{len(puntajes_con_fecha)})")
    else:
        historico_actualizado = puntajes_con_fecha
        registro.info(f"📊 Histórico creado: {len(historico_actualizado)} registros")
    
    historico_actualizado.to_parquet(historico_path, index=False)
    
    puntajes.to_parquet(processed_dir / 'puntajes_latest.parquet')
    seleccionados.to_csv(processed_dir / 'inspecciones_priorizadas_latest.csv', index=False)
    registro.info(f"💾 Última versión guardada: puntajes_latest.parquet")
    
    stats = {
        'timestamp': timestamp,
        'fecha': fecha_actual.isoformat(),
        'zona_horaria': 'America/Lima',
        'total_suministros': len(puntajes),
        'alta_prioridad': len(puntajes[puntajes['prioridad'] == 'ALTA']),
        'media_prioridad': len(puntajes[puntajes['prioridad'] == 'MEDIA']),
        'baja_prioridad': len(puntajes[puntajes['prioridad'] == 'BAJA']),
        'total_seleccionados': len(seleccionados),
        'total_historico': len(historico_actualizado)
    }
    
    stats_path = processed_dir / f'estadisticas_{timestamp}.json'
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, default=str, ensure_ascii=False)
    
    registro.info(f"✅ Tubería diaria completada: {len(puntajes)} suministros priorizados")
    registro.info(f"📋 {len(seleccionados)} casos seleccionados para inspección")
    registro.info(f"📊 Histórico acumulado: {len(historico_actualizado)} registros")
    registro.info(f"📅 Fecha ejecución: {fecha_actual.strftime('%Y-%m-%d %H:%M:%S')} (Perú)")
    if 'id_cliente' in historico_actualizado.columns:
        registro.info(f"📊 Total histórico de suministros: {len(historico_actualizado['id_cliente'].unique())}")

if __name__ == "__main__":
    main()