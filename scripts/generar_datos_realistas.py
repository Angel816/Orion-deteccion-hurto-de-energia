# scripts/generar_datos_realistas.py
"""
Genera datos realistas CON ETIQUETAS CAUSALES
Los hurtos se asignan según variables que EVIDENCIAN hurto,
para que el modelo pueda aprender patrones reales.

Zona horaria: Perú (UTC-5)
"""

import sys
import io
import os
from pathlib import Path

# ============================================================
# CONFIGURAR UTF-8
# ============================================================

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

os.environ['PYTHONIOENCODING'] = 'utf-8'

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json

sys.path.append(str(Path(__file__).parent.parent))

from src.utilidades.registrador import registro
from src.utilidades.tiempo import ahora_peru, timestamp_peru


# ============================================================
# CONFIGURACIÓN
# ============================================================

np.random.seed(2026)
random.seed(2026)

N_CLIENTES = 200
N_DIAS = 365
FECHA_INICIO = datetime(2025, 1, 1)

TIPOS_CLIENTE = {
    'Residencial': {'prob': 0.65, 'consumo_base': (8, 25), 'potencia': (3, 10)},
    'Comercial': {'prob': 0.20, 'consumo_base': (30, 80), 'potencia': (10, 30)},
    'Industrial': {'prob': 0.08, 'consumo_base': (100, 300), 'potencia': (30, 100)},
    'Restaurante': {'prob': 0.04, 'consumo_base': (40, 100), 'potencia': (15, 40)},
    'Fabrica': {'prob': 0.03, 'consumo_base': (200, 500), 'potencia': (50, 200)}
}

SECTORES = [
    'Alto Trujillo', 'La Esperanza', 'Máncora', 'Piura', 'Huaral',
    'Tumbes', 'Huánuco', 'Villa El Salvador', 'San Juan de Lurigancho',
    'Ate', 'Comas', 'Independencia', 'Los Olivos', 'Callao'
]

ZONAS_ALTO_RIESGO = ['Alto Trujillo', 'La Esperanza', 'Máncora', 'Piura', 'Huaral']

# ============================================================
# TIPOS DE HURTO Y SUS SEÑALES
# ============================================================

TIPOS_HURTO = {
    'Bypass': {
        'prob': 0.30,
        'descripcion': 'Puentes en base socket',
        'reduccion_consumo': (0.7, 0.9),    # Reduce 70-90% del consumo
        'alarmas': ['Bypass Detectado', 'Magneto Detectado', 'Precinto Roto'],
        'n_alarmas': (3, 6),
        'cnr_promedio': 2500
    },
    'Cable Rajado': {
        'prob': 0.25,
        'descripcion': 'Derivación antes del medidor',
        'reduccion_consumo': (0.3, 0.5),
        'alarmas': ['Tapa Abierta', 'Caída Brusca', 'Consumo Cero'],
        'n_alarmas': (1, 3),
        'cnr_promedio': 1200
    },
    'Manipulación Medidor': {
        'prob': 0.20,
        'descripcion': 'Alteración de medición',
        'reduccion_consumo': (0.5, 0.75),
        'alarmas': ['Precinto Roto', 'Tapa Abierta', 'Inversión de Fases'],
        'n_alarmas': (2, 4),
        'cnr_promedio': 1800
    },
    'Conexión Clandestina': {
        'prob': 0.15,
        'descripcion': 'Conexión directa a red',
        'reduccion_consumo': (0.85, 1.0),   # Casi elimina el consumo
        'alarmas': ['Consumo Cero', 'Error Comunicación'],
        'n_alarmas': (2, 5),
        'cnr_promedio': 3500
    },
    'Auto-reconexión': {
        'prob': 0.10,
        'descripcion': 'Reconexión tras corte',
        'reduccion_consumo': (0.2, 0.4),
        'alarmas': ['Tapa Abierta', 'Precinto Roto'],
        'n_alarmas': (1, 3),
        'cnr_promedio': 900
    }
}


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def generar_id_cliente(i):
    return f"CL-{i:05d}"


def obtener_tipo_cliente():
    tipos = list(TIPOS_CLIENTE.keys())
    probs = [TIPOS_CLIENTE[t]['prob'] for t in tipos]
    return np.random.choice(tipos, p=probs)


def obtener_tipo_hurto():
    tipos = list(TIPOS_HURTO.keys())
    probs = [TIPOS_HURTO[t]['prob'] for t in tipos]
    return np.random.choice(tipos, p=probs)


# ============================================================
# GENERADOR DE CLIENTES CON HURTO CAUSAL
# ============================================================

def generar_clientes(n: int) -> pd.DataFrame:
    """
    Genera clientes CON DECISIÓN DE HURTO CAUSAL
    
    La decisión de hurto se basa en:
    - Zona de riesgo (más hurto en zonas de alto riesgo)
    - Tipo de cliente (industrial hurta más)
    - Historial simulado (algunos clientes ya hurtaron antes)
    """
    registro.info(f"📋 Generando {n} clientes con hurto causal...")
    
    clientes = []
    
    for i in range(1, n + 1):
        tipo = obtener_tipo_cliente()
        sector = np.random.choice(SECTORES)
        es_zona_riesgo = sector in ZONAS_ALTO_RIESGO
        tipo_data = TIPOS_CLIENTE[tipo]
        potencia = round(np.random.uniform(*tipo_data['potencia']), 1)
        
        # ============================================================
        # DECISIÓN DE HURTO CAUSAL
        # ============================================================
        # Probabilidad base
        prob_hurto = 0.08
        
        # Factor 1: Zona de riesgo (+15%)
        if es_zona_riesgo:
            prob_hurto += 0.15
        
        # Factor 2: Tipo de cliente
        if tipo in ['Industrial', 'Fabrica']:
            prob_hurto += 0.10
        elif tipo == 'Comercial':
            prob_hurto += 0.05
        
        # Factor 3: Reincidencia (5% ya hurtaron antes)
        es_reincidente = random.random() < 0.05
        if es_reincidente:
            prob_hurto += 0.30
        
        # Decisión final
        tiene_hurto = random.random() < prob_hurto
        
        # Tipo de hurto si aplica
        tipo_hurto = None
        if tiene_hurto:
            tipo_hurto = obtener_tipo_hurto()
        
        cliente = {
            'id_cliente': generar_id_cliente(i),
            'nombre': f"Cliente {i}" if tipo == 'Residencial' else f"Empresa {sector} S.A.C.",
            'tipo_cliente': tipo,
            'potencia_contratada': potencia,
            'sector': sector,
            'tarifa': np.random.choice(['BT5B', 'BT5A', 'BT4', 'MT2', 'MT3']),
            'fecha_alta': FECHA_INICIO - timedelta(days=np.random.randint(365, 1825)),
            'estado': 'Activo' if random.random() > 0.05 else 'Suspendido',
            # ============================================================
            # ETIQUETAS CAUSALES (GROUND TRUTH)
            # ============================================================
            'tiene_hurto': tiene_hurto,           # ← ETIQUETA PRINCIPAL
            'tipo_hurto': tipo_hurto,              # ← Tipo de hurto
            'es_zona_riesgo': es_zona_riesgo,      # ← Feature causal
            'es_reincidente': es_reincidente       # ← Feature causal
        }
        clientes.append(cliente)
    
    df = pd.DataFrame(clientes)
    
    n_hurto = df['tiene_hurto'].sum()
    registro.info(f"✅ {len(df)} clientes generados")
    registro.info(f"   🚨 Con hurto: {n_hurto} ({n_hurto/len(df)*100:.1f}%)")
    registro.info(f"   📍 En zona de riesgo: {df['es_zona_riesgo'].sum()}")
    registro.info(f"   🔄 Reincidentes: {df['es_reincidente'].sum()}")
    
    return df


# ============================================================
# GENERADOR DE CONSUMO
# ============================================================

def generar_consumo(clientes_df: pd.DataFrame) -> pd.DataFrame:
    """
    Genera consumo COHERENTE con la decisión de hurto.
    Si el cliente hurta, su consumo baja.
    """
    registro.info(f"⚡ Generando consumo...")
    
    registros = []
    
    for _, cliente in clientes_df.iterrows():
        id_cliente = cliente['id_cliente']
        tipo = cliente['tipo_cliente']
        tipo_data = TIPOS_CLIENTE[tipo]
        base = np.random.uniform(*tipo_data['consumo_base'])
        tiene_hurto = cliente['tiene_hurto']
        tipo_hurto = cliente['tipo_hurto']
        
        # Si hurta, definir cuándo empieza (día 60-250)
        if tiene_hurto:
            dia_inicio_hurto = np.random.randint(60, 250)
            duracion = np.random.randint(60, 200)
            reduccion = TIPOS_HURTO[tipo_hurto]['reduccion_consumo']
            factor_reduccion = np.random.uniform(*reduccion)
        else:
            dia_inicio_hurto = None
            duracion = 0
            factor_reduccion = 0
        
        for dia in range(N_DIAS):
            fecha = FECHA_INICIO + timedelta(days=dia)
            mes = fecha.month
            dia_semana = fecha.weekday()
            
            # Estacionalidad
            estacional = 1.0 + 0.2 * np.sin(2 * np.pi * (mes - 6) / 12)
            
            # Fin de semana
            if tipo in ['Residencial', 'Restaurante']:
                dia_factor = 1.3 if dia_semana >= 5 else 1.0
            else:
                dia_factor = 0.7 if dia_semana >= 5 else 1.0
            
            # Consumo base + ruido
            consumo = max(0.5, base * estacional * dia_factor + np.random.normal(0, base * 0.15))
            
            # Aplicar hurto si corresponde
            if tiene_hurto and dia_inicio_hurto is not None:
                if dia_inicio_hurto <= dia < dia_inicio_hurto + duracion:
                    consumo *= (1 - factor_reduccion)
            
            # Tipo de lectura
            tipo_lectura = random.choices(
                ['Real', 'Estimada'],
                weights=[0.9, 0.1]
            )[0]
            
            registros.append({
                'id_cliente': id_cliente,
                'fecha': fecha,
                'consumo_kwh': round(max(0, consumo), 2),
                'tipo_lectura': tipo_lectura
            })
    
    df = pd.DataFrame(registros)
    registro.info(f"✅ {len(df)} registros de consumo")
    
    return df


# ============================================================
# GENERADOR DE ALARMAS
# ============================================================

def generar_alarmas(clientes_df: pd.DataFrame) -> pd.DataFrame:
    """
    Genera alarmas COHERENTES con el tipo de hurto.
    Si el cliente hurta, tiene alarmas del tipo correspondiente.
    """
    registro.info(f"🔔 Generando alarmas...")
    
    alarmas = []
    
    for _, cliente in clientes_df.iterrows():
        id_cliente = cliente['id_cliente']
        tiene_hurto = cliente['tiene_hurto']
        tipo_hurto = cliente['tipo_hurto']
        es_zona_riesgo = cliente['es_zona_riesgo']
        
        # Determinar número de alarmas
        if tiene_hurto:
            # Cliente con hurto: tiene las alarmas del tipo de hurto
            n_alarmas_min, n_alarmas_max = TIPOS_HURTO[tipo_hurto]['n_alarmas']
            n_alarmas = np.random.randint(n_alarmas_min, n_alarmas_max + 1)
            tipos_posibles = TIPOS_HURTO[tipo_hurto]['alarmas']
        elif es_zona_riesgo:
            # Zona de riesgo pero sin hurto: pocas alarmas
            n_alarmas = np.random.poisson(1.0)
            tipos_posibles = ['Tapa Abierta', 'Error Comunicación', 'Caída Brusca']
        else:
            # Cliente normal: casi sin alarmas
            n_alarmas = np.random.poisson(0.2)
            tipos_posibles = ['Error Comunicación', 'Tapa Abierta']
        
        for _ in range(n_alarmas):
            # Fecha de alarma (si hurta, en el período de hurto)
            if tiene_hurto:
                dia = np.random.randint(60, 300)
            else:
                dia = np.random.randint(0, N_DIAS)
            
            fecha = FECHA_INICIO + timedelta(days=dia)
            tipo_alarma = np.random.choice(tipos_posibles)
            
            # Gravedad según tipo
            if tipo_alarma in ['Bypass Detectado', 'Magneto Detectado', 'Precinto Roto']:
                gravedad = np.random.choice(['Alta', 'Crítica'], p=[0.6, 0.4])
            elif tipo_alarma in ['Tapa Abierta', 'Inversión de Fases']:
                gravedad = np.random.choice(['Media', 'Alta'], p=[0.5, 0.5])
            else:
                gravedad = np.random.choice(['Baja', 'Media'], p=[0.7, 0.3])
            
            alarmas.append({
                'id_cliente': id_cliente,
                'fecha': fecha,
                'tipo_alarma': tipo_alarma,
                'gravedad': gravedad
            })
    
    df = pd.DataFrame(alarmas)
    registro.info(f"✅ {len(df)} alarmas")
    
    return df


# ============================================================
# GENERADOR DE FACTURACIÓN
# ============================================================

def generar_facturacion(clientes_df: pd.DataFrame, 
                        consumo_df: pd.DataFrame) -> pd.DataFrame:
    """Genera facturación coherente con el consumo"""
    registro.info(f"💰 Generando facturación...")
    
    facturas = []
    precios = {'BT5B': 0.85, 'BT5A': 0.75, 'BT4': 0.65, 'MT2': 0.55, 'MT3': 0.45}
    
    for _, cliente in clientes_df.iterrows():
        id_cliente = cliente['id_cliente']
        tarifa = cliente['tarifa']
        precio_kwh = precios.get(tarifa, 0.75)
        
        for mes in range(12):
            fecha_emision = FECHA_INICIO + timedelta(days=mes * 30 + np.random.randint(1, 10))
            fecha_vencimiento = fecha_emision + timedelta(days=30)
            
            # Consumo del mes
            inicio_mes = fecha_emision.replace(day=1)
            fin_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            consumo_mes = consumo_df[
                (consumo_df['id_cliente'] == id_cliente) &
                (consumo_df['fecha'] >= inicio_mes) &
                (consumo_df['fecha'] <= fin_mes)
            ]['consumo_kwh'].sum()
            
            if consumo_mes == 0:
                consumo_mes = np.random.uniform(50, 200)
            
            monto_total = consumo_mes * precio_kwh + np.random.uniform(5, 15)
            
            # Estado de pago
            if random.random() < 0.75:
                estado = 'Pagado'
                monto_pagado = monto_total
            elif random.random() < 0.85:
                estado = 'Pendiente'
                monto_pagado = monto_total * np.random.uniform(0.3, 0.7)
            else:
                estado = 'Vencido'
                monto_pagado = 0
            
            dias_mora = max(0, (ahora_peru().replace(tzinfo=None) - fecha_vencimiento).days) if estado != 'Pagado' else 0
            
            facturas.append({
                'id_cliente': id_cliente,
                'fecha_emision': fecha_emision,
                'fecha_vencimiento': fecha_vencimiento,
                'consumo_kwh': round(consumo_mes, 2),
                'monto_total': round(monto_total, 2),
                'monto_pagado': round(monto_pagado, 2),
                'estado_pago': estado,
                'dias_mora': dias_mora
            })
    
    df = pd.DataFrame(facturas)
    registro.info(f"✅ {len(df)} facturas")
    
    return df


# ============================================================
# GENERADOR DE INSPECCIONES (CRÍTICO)
# ============================================================

def generar_inspecciones(clientes_df: pd.DataFrame) -> pd.DataFrame:
    """
    Genera inspecciones COHERENTES con la decisión de hurto.
    
    - Clientes CON hurto → inspección con 'Hurto Confirmado'
    - Clientes SIN hurto pero en zona riesgo → 'Normal' o 'Falso Positivo'
    - Clientes SIN hurto normales → 'Normal'
    """
    registro.info(f"📋 Generando inspecciones COHERENTES...")
    
    inspecciones = []
    
    for _, cliente in clientes_df.iterrows():
        id_cliente = cliente['id_cliente']
        tiene_hurto = cliente['tiene_hurto']
        tipo_hurto = cliente['tipo_hurto']
        es_zona_riesgo = cliente['es_zona_riesgo']
        es_reincidente = cliente['es_reincidente']
        
        # ============================================================
        # CLIENTES CON HURTO → Confirmado
        # ============================================================
        if tiene_hurto:
            n_inspecciones = 1 if not es_reincidente else np.random.randint(2, 4)
            
            for _ in range(n_inspecciones):
                fecha = FECHA_INICIO + timedelta(days=np.random.randint(150, 350))
                cnr = TIPOS_HURTO[tipo_hurto]['cnr_promedio'] * np.random.uniform(0.7, 1.5)
                
                inspecciones.append({
                    'id_cliente': id_cliente,
                    'fecha_inspeccion': fecha,
                    'resultado': 'Hurto Confirmado',
                    'tipo_irregularidad': tipo_hurto,
                    'descripcion': TIPOS_HURTO[tipo_hurto]['descripcion'],
                    'cnr_estimado': round(cnr, 2),
                    'inspector': f"Inspector_{np.random.randint(1, 11)}"
                })
        
        # ============================================================
        # CLIENTES SIN HURTO → Normal / Falso Positivo
        # ============================================================
        else:
            # Solo inspeccionar ~30% de los clientes sin hurto
            if random.random() < 0.3:
                fecha = FECHA_INICIO + timedelta(days=np.random.randint(30, 350))
                
                # En zona de riesgo → más probable 'Falso Positivo'
                if es_zona_riesgo:
                    resultado = np.random.choice(
                        ['Normal', 'Falso Positivo'],
                        p=[0.7, 0.3]
                    )
                else:
                    resultado = 'Normal'
                
                inspecciones.append({
                    'id_cliente': id_cliente,
                    'fecha_inspeccion': fecha,
                    'resultado': resultado,
                    'tipo_irregularidad': 'N/A',
                    'descripcion': 'Sin irregularidad',
                    'cnr_estimado': 0,
                    'inspector': f"Inspector_{np.random.randint(1, 11)}"
                })
    
    df = pd.DataFrame(inspecciones)
    
    # Resumen
    registro.info(f"✅ {len(df)} inspecciones generadas")
    registro.info(f"   📊 Distribución: {df['resultado'].value_counts().to_dict()}")
    
    return df


# ============================================================
# ENVIAR A COLA
# ============================================================

def enviar_a_cola(clientes, consumo, alarmas, facturacion, inspecciones):
    """Envía datos a la cola con formatos variados"""
    registro.info("📤 Enviando datos a la cola...")
    
    cola_dir = Path('datos/cola/pendientes')
    cola_dir.mkdir(parents=True, exist_ok=True)
    
    # Limpiar cola previa
    for archivo in cola_dir.glob('*'):
        try:
            archivo.unlink()
        except:
            pass
    
    # 1. CLIENTES (CSV, columnas renombradas)
    clientes.rename(columns={
        'id_cliente': 'CODIGO_CLIENTE',
        'tipo_cliente': 'TIPO',
        'sector': 'ZONA',
        'potencia_contratada': 'POTENCIA_KW',
        'tarifa': 'TARIFA_CODIGO'
    })[['CODIGO_CLIENTE', 'TIPO', 'ZONA', 'POTENCIA_KW', 'TARIFA_CODIGO']].to_csv(
        cola_dir / 'clientes.csv', index=False, encoding='utf-8'
    )
    registro.info(f"   ✅ clientes.csv")
    
    # 2. CONSUMO (CSV)
    consumo.rename(columns={
        'id_cliente': 'CLIENTE',
        'fecha': 'FECHA_LECTURA',
        'consumo_kwh': 'CONSUMO',
        'tipo_lectura': 'TIPO_LECTURA'
    }).to_csv(cola_dir / 'consumo.csv', index=False, encoding='utf-8')
    registro.info(f"   ✅ consumo.csv")
    
    # 3. ALARMAS (JSON)
    alarmas.to_json(
        cola_dir / 'alarmas.json',
        orient='records',
        indent=2,
        force_ascii=False,
        date_format='iso'
    )
    registro.info(f"   ✅ alarmas.json")
    
    # 4. FACTURACIÓN (CSV)
    facturacion.to_csv(cola_dir / 'facturacion.csv', index=False, encoding='utf-8')
    registro.info(f"   ✅ facturacion.csv")
    
    # 5. INSPECCIONES (CSV) - CRÍTICO
    inspecciones.rename(columns={
        'id_cliente': 'CLIENTE',
        'fecha_inspeccion': 'FECHA_INSPECCION',
        'resultado': 'RESULTADO',
        'tipo_irregularidad': 'TIPO_IRREGULARIDAD',
        'cnr_estimado': 'CNR',
        'inspector': 'INSPECTOR'
    }).to_csv(cola_dir / 'inspecciones.csv', index=False, encoding='utf-8')
    registro.info(f"   ✅ inspecciones.csv")
    
    # 6. GUARDAR ETIQUETAS GROUND TRUTH (para referencia, NO entra a la cola)
    labels_path = Path('datos/muestra/ground_truth_labels.csv')
    labels_path.parent.mkdir(parents=True, exist_ok=True)
    clientes[['id_cliente', 'tiene_hurto', 'tipo_hurto', 
              'es_zona_riesgo', 'es_reincidente']].to_csv(
        labels_path, index=False, encoding='utf-8'
    )
    registro.info(f"   💾 Ground truth guardado en: {labels_path}")
    
    archivos = list(cola_dir.glob('*'))
    registro.info(f"\n📊 {len(archivos)} archivos en la cola")


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def main():
    print("=" * 70)
    print("🌌 PROYECTO ORION - GENERACIÓN DE DATOS CON ETIQUETAS CAUSALES")
    print(f"🕐 Hora Perú: {ahora_peru().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print(f"📊 {N_CLIENTES} clientes, {N_DIAS} días de consumo")
    print("=" * 70)
    
    # 1. Generar clientes con hurto causal
    clientes = generar_clientes(N_CLIENTES)
    
    # 2. Generar datos coherentes
    consumo = generar_consumo(clientes)
    alarmas = generar_alarmas(clientes)
    facturacion = generar_facturacion(clientes, consumo)
    inspecciones = generar_inspecciones(clientes)
    
    # 3. Enviar a la cola
    enviar_a_cola(clientes, consumo, alarmas, facturacion, inspecciones)
    
    # Resumen
    print("\n" + "=" * 70)
    print("✅ DATOS GENERADOS Y ENVIADOS A LA COLA")
    print("=" * 70)
    print(f"👥 Clientes: {len(clientes)}")
    print(f"🚨 Con hurto: {clientes['tiene_hurto'].sum()} ({clientes['tiene_hurto'].mean()*100:.1f}%)")
    print(f"⚡ Consumo: {len(consumo)} registros")
    print(f"🔔 Alarmas: {len(alarmas)}")
    print(f"💰 Facturas: {len(facturacion)}")
    print(f"📋 Inspecciones: {len(inspecciones)}")
    print("=" * 70)
    print("\n📋 PRÓXIMOS PASOS:")
    print("   1. Procesar cola: python scripts/procesar_cola_datos.py --procesar")
    print("   2. Crear datos de entrenamiento: python scripts/crear_datos_entrenamiento.py")
    print("   3. Ejecutar flujo completo: python scripts/ejecutar_flujo_completo.py")


if __name__ == "__main__":
    main()