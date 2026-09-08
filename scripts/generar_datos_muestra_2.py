# scripts/generar_datos_muestra.py
"""
Generación de datos de muestra para el Proyecto Orion
Versión 2 - Datos más realistas con zonas de riesgo
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import random

# ============================================================
# CONFIGURACIÓN
# ============================================================

np.random.seed(99)
random.seed(99)

N_CLIENTES = 120
N_DIAS = 180
FECHA_INICIO = datetime(2024, 1, 1)

# ============================================================
# TIPOS DE CLIENTES
# ============================================================

TIPOS_CLIENTE = {
    'Residencial': {'prob': 0.60, 'consumo_base': (8, 25), 'potencia': (3, 10)},
    'Comercial': {'prob': 0.25, 'consumo_base': (30, 80), 'potencia': (10, 30)},
    'Industrial': {'prob': 0.10, 'consumo_base': (100, 300), 'potencia': (30, 100)},
    'Restaurante': {'prob': 0.03, 'consumo_base': (40, 100), 'potencia': (15, 40)},
    'Fabrica': {'prob': 0.02, 'consumo_base': (200, 500), 'potencia': (50, 200)}
}

SECTORES = ['Norte', 'Sur', 'Este', 'Oeste', 'Centro']
TARIFAS = ['T1', 'T2', 'T3', 'T4']
ZONAS_RIESGO = ['Alto Trujillo', 'La Esperanza', 'Máncora', 'Piura', 'Huaral']

# ============================================================
# FUNCIONES
# ============================================================

def generar_clientes(n: int) -> pd.DataFrame:
    tipos = list(TIPOS_CLIENTE.keys())
    probs = [TIPOS_CLIENTE[t]['prob'] for t in tipos]
    clientes = []
    
    for i in range(n):
        tipo = np.random.choice(tipos, p=probs)
        sector = np.random.choice(SECTORES)
        es_riesgo = sector in ZONAS_RIESGO
        
        cliente = {
            'id_cliente': f'CL{i+1:04d}',
            'nombre': f'Cliente_{i+1}',
            'tipo_cliente': tipo,
            'potencia_contratada': round(np.random.uniform(*TIPOS_CLIENTE[tipo]['potencia']), 1),
            'sector': sector,
            'tarifa': np.random.choice(TARIFAS),
            'zona_riesgo': es_riesgo,
            'fecha_alta': FECHA_INICIO - timedelta(days=np.random.randint(365, 1095))
        }
        clientes.append(cliente)
    
    return pd.DataFrame(clientes)


def generar_consumo(clientes_df: pd.DataFrame) -> pd.DataFrame:
    registros = []
    
    for _, cliente in clientes_df.iterrows():
        id_cliente = cliente['id_cliente']
        tipo = cliente['tipo_cliente']
        base = np.random.uniform(*TIPOS_CLIENTE[tipo]['consumo_base'])
        es_riesgo = cliente['zona_riesgo']
        
        for dia in range(N_DIAS):
            fecha = FECHA_INICIO + timedelta(days=dia)
            mes = fecha.month
            estacional = 1.0 + 0.3 * np.sin(2 * np.pi * (mes - 6) / 12)
            
            dia_semana = fecha.weekday()
            if tipo == 'Residencial':
                dia_factor = 1.3 if dia_semana >= 5 else 0.9
            else:
                dia_factor = 0.8 if dia_semana >= 5 else 1.1
            
            ruido = np.random.normal(0, base * 0.2)
            consumo = base * estacional * dia_factor + ruido
            consumo = max(0.5, consumo)
            
            prob_hurto = 0.20 if es_riesgo else 0.08
            if random.random() < prob_hurto and dia > 30 and dia < N_DIAS - 30:
                reduccion = np.random.uniform(0.3, 0.7)
                consumo = consumo * (1 - reduccion)
            
            tipo_lectura = 'Real' if random.random() < 0.90 else 'Estimada'
            
            registros.append({
                'id_cliente': id_cliente,
                'fecha': fecha,
                'consumo_kwh': round(consumo, 2),
                'tipo_lectura': tipo_lectura
            })
    
    return pd.DataFrame(registros)


def generar_alarmas(clientes_df: pd.DataFrame) -> pd.DataFrame:
    tipos_alarma = ['Tapa Abierta', 'Precinto Roto', 'Consumo Cero', 'Error Comunicación', 'Caída Brusca', 'Bypass Detectado', 'Magneto Detectado']
    gravedad_map = {'Baja': 0.4, 'Media': 0.3, 'Alta': 0.2, 'Crítica': 0.1}
    alarmas = []
    
    for _, cliente in clientes_df.iterrows():
        id_cliente = cliente['id_cliente']
        es_riesgo = cliente['zona_riesgo']
        tipo = cliente['tipo_cliente']
        
        if es_riesgo:
            n_alarmas = np.random.poisson(1.5)
        elif tipo in ['Industrial', 'Fabrica']:
            n_alarmas = np.random.poisson(0.8)
        else:
            n_alarmas = np.random.poisson(0.3)
        
        for _ in range(min(n_alarmas, 20)):
            fecha = FECHA_INICIO + timedelta(days=np.random.randint(0, N_DIAS))
            alarmas.append({
                'id_cliente': id_cliente,
                'fecha': fecha,
                'tipo_alarma': np.random.choice(tipos_alarma),
                'gravedad': np.random.choice(list(gravedad_map.keys()), p=list(gravedad_map.values()))
            })
    
    return pd.DataFrame(alarmas)


def generar_facturacion(clientes_df: pd.DataFrame) -> pd.DataFrame:
    facturas = []
    
    for _, cliente in clientes_df.iterrows():
        id_cliente = cliente['id_cliente']
        tarifa = cliente['tarifa']
        precio_kwh = {'T1': 0.15, 'T2': 0.18, 'T3': 0.22, 'T4': 0.25}[tarifa]
        
        for mes in range(6):
            fecha_emision = FECHA_INICIO + timedelta(days=mes * 30 + np.random.randint(1, 10))
            fecha_vencimiento = fecha_emision + timedelta(days=30)
            consumo_mensual = np.random.uniform(200, 800) * (0.8 + 0.4 * np.random.random())
            monto_total = consumo_mensual * precio_kwh + np.random.uniform(5, 30)
            monto_pagado = monto_total * np.random.uniform(0.5, 1.0)
            
            if monto_pagado < monto_total * 0.8:
                estado = 'Pendiente'
            elif monto_pagado == 0:
                estado = 'Vencido'
            else:
                estado = 'Pagado'
            
            facturas.append({
                'id_cliente': id_cliente,
                'fecha_emision': fecha_emision,
                'fecha_vencimiento': fecha_vencimiento,
                'consumo_kwh': round(consumo_mensual, 2),
                'monto_total': round(monto_total, 2),
                'monto_pagado': round(monto_pagado, 2),
                'estado_pago': estado,
                'dias_mora': max(0, (datetime.now() - fecha_vencimiento).days) if estado != 'Pagado' else 0
            })
    
    return pd.DataFrame(facturas)


def generar_inspecciones(clientes_df: pd.DataFrame) -> pd.DataFrame:
    resultados = ['Hurto Confirmado', 'Anomalía', 'Normal', 'Falso Positivo']
    prob_resultados = [0.12, 0.18, 0.60, 0.10]
    tipos_irregularidad = ['Bypass', 'Cable Rajado', 'Manipulación Medidor', 'Conexión Clandestina', 'Auto-reconexión', 'N/A']
    inspecciones = []
    
    for _, cliente in clientes_df.iterrows():
        id_cliente = cliente['id_cliente']
        es_riesgo = cliente['zona_riesgo']
        n_inspecciones = np.random.poisson(0.8 if es_riesgo else 0.3)
        
        for _ in range(min(n_inspecciones, 5)):
            fecha = FECHA_INICIO + timedelta(days=np.random.randint(30, N_DIAS))
            resultado = np.random.choice(resultados, p=prob_resultados)
            
            if resultado in ['Hurto Confirmado', 'Anomalía']:
                tipo = np.random.choice([t for t in tipos_irregularidad if t != 'N/A'])
                cnr = round(np.random.uniform(500, 8000), 2)
            else:
                tipo = 'N/A'
                cnr = 0
            
            inspecciones.append({
                'id_cliente': id_cliente,
                'fecha_inspeccion': fecha,
                'resultado': resultado,
                'tipo_irregularidad': tipo,
                'cnr_estimado': cnr,
                'inspector': f'Inspector_{np.random.randint(1, 6)}'
            })
    
    return pd.DataFrame(inspecciones)


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🌌 PROYECTO ORION - GENERACIÓN DE DATOS DE MUESTRA V2")
    print("=" * 70)
    print(f"📊 {N_CLIENTES} clientes, {N_DIAS} días de consumo")
    print("=" * 70)
    
    sample_dir = Path('datos/muestra')
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n📋 Generando clientes...")
    clientes = generar_clientes(N_CLIENTES)
    clientes.to_csv(sample_dir / 'clientes_muestra.csv', index=False)
    print(f"   ✅ {len(clientes)} clientes generados")
    print(f"   📊 Zonas de riesgo: {clientes['zona_riesgo'].sum()} clientes")
    
    print("\n⚡ Generando consumo...")
    consumo = generar_consumo(clientes)
    consumo.to_csv(sample_dir / 'consumo_muestra.csv', index=False)
    print(f"   ✅ {len(consumo)} registros de consumo generados")
    
    print("\n🔔 Generando alarmas...")
    alarmas = generar_alarmas(clientes)
    alarmas.to_csv(sample_dir / 'alarmas_muestra.csv', index=False)
    print(f"   ✅ {len(alarmas)} registros de alarmas generados")
    
    print("\n💰 Generando facturación...")
    facturacion = generar_facturacion(clientes)
    facturacion.to_csv(sample_dir / 'facturacion_muestra.csv', index=False)
    print(f"   ✅ {len(facturacion)} registros de facturación generados")
    
    print("\n📋 Generando inspecciones...")
    inspecciones = generar_inspecciones(clientes)
    inspecciones.to_csv(sample_dir / 'inspecciones_muestra.csv', index=False)
    print(f"   ✅ {len(inspecciones)} registros de inspecciones generados")
    
    print("\n" + "=" * 70)
    print("✅ DATOS DE MUESTRA V2 GENERADOS CORRECTAMENTE")
    print(f"📁 Ubicación: {sample_dir.absolute()}")
    print("=" * 70)

if __name__ == "__main__":
    main()