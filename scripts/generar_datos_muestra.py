# scripts/generar_datos_muestra.py
"""
Generación de datos de muestra para el Proyecto Orion
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

N_CLIENTES = 50
N_DIAS = 365
FECHA_INICIO = datetime(2024, 1, 1)

def generar_clientes(n: int) -> pd.DataFrame:
    tipos_cliente = ['Residencial', 'Comercial', 'Industrial']
    prob_tipos = [0.65, 0.25, 0.10]
    sectores = ['Norte', 'Sur', 'Este', 'Oeste', 'Centro']
    tarifas = ['T1', 'T2', 'T3', 'T4']
    
    clientes = []
    for i in range(n):
        tipo = np.random.choice(tipos_cliente, p=prob_tipos)
        potencia = round(np.random.uniform(3, 10), 1) if tipo == 'Residencial' else round(np.random.uniform(10, 30), 1) if tipo == 'Comercial' else round(np.random.uniform(30, 100), 1)
        cliente = {
            'id_cliente': f'CL{i+1:04d}',
            'nombre': f'Cliente_{i+1}',
            'tipo_cliente': tipo,
            'potencia_contratada': potencia,
            'sector': np.random.choice(sectores),
            'tarifa': np.random.choice(tarifas),
            'fecha_alta': FECHA_INICIO - timedelta(days=np.random.randint(365, 1095))
        }
        clientes.append(cliente)
    return pd.DataFrame(clientes)

def generar_consumo(clientes_df: pd.DataFrame, n_dias: int) -> pd.DataFrame:
    registros = []
    for dia in range(n_dias):
        fecha = FECHA_INICIO + timedelta(days=dia)
        mes = fecha.month
        estacional = 1.0 + 0.2 * np.sin(2 * np.pi * (mes - 6) / 12)
        for _, cliente in clientes_df.iterrows():
            tipo = cliente['tipo_cliente']
            base = np.random.uniform(5, 15) if tipo == 'Residencial' else np.random.uniform(20, 50) if tipo == 'Comercial' else np.random.uniform(60, 150)
            ruido = np.random.normal(0, base * 0.15)
            consumo = max(0.1, base * estacional + ruido)
            if random.random() < 0.15 and dia > 60 and dia < n_dias - 30:
                consumo = consumo * (1 - np.random.uniform(0.3, 0.6))
            registros.append({
                'id_cliente': cliente['id_cliente'],
                'fecha': fecha,
                'consumo_kwh': round(consumo, 2),
                'tipo_lectura': 'Real' if random.random() < 0.85 else 'Estimada'
            })
    return pd.DataFrame(registros)

def generar_alarmas(clientes_df: pd.DataFrame, n_dias: int) -> pd.DataFrame:
    tipos_alarma = ['Tapa Abierta', 'Precinto Roto', 'Consumo Cero', 'Error Comunicación', 'Caída Brusca', 'Bypass Detectado']
    gravedad = ['Baja', 'Media', 'Alta', 'Crítica']
    prob_gravedad = [0.4, 0.3, 0.2, 0.1]
    alarmas = []
    for dia in range(n_dias):
        fecha = FECHA_INICIO + timedelta(days=dia)
        if random.random() < 0.05:
            cliente = clientes_df.sample(1).iloc[0]
            alarmas.append({
                'id_cliente': cliente['id_cliente'],
                'fecha': fecha,
                'tipo_alarma': np.random.choice(tipos_alarma),
                'gravedad': np.random.choice(gravedad, p=prob_gravedad)
            })
    return pd.DataFrame(alarmas)

def generar_facturacion(clientes_df: pd.DataFrame) -> pd.DataFrame:
    facturas = []
    for _, cliente in clientes_df.iterrows():
        for _ in range(np.random.randint(4, 13)):
            dias_aleatorios = np.random.randint(1, 365)
            fecha_emision = FECHA_INICIO + timedelta(days=dias_aleatorios)
            fecha_vencimiento = fecha_emision + timedelta(days=30)
            consumo_mensual = np.random.uniform(200, 800)
            tarifa = cliente['tarifa']
            precio_kwh = {'T1': 0.15, 'T2': 0.18, 'T3': 0.22, 'T4': 0.25}[tarifa]
            monto_total = consumo_mensual * precio_kwh + np.random.uniform(0, 50)
            estados = ['Pagado', 'Pendiente', 'Vencido']
            prob_estados = [0.7, 0.2, 0.1]
            estado = np.random.choice(estados, p=prob_estados)
            facturas.append({
                'id_cliente': cliente['id_cliente'],
                'fecha_emision': fecha_emision,
                'fecha_vencimiento': fecha_vencimiento,
                'consumo_kwh': round(consumo_mensual, 2),
                'monto_total': round(monto_total, 2),
                'monto_pagado': round(monto_total * (0.5 + np.random.random() * 0.5), 2),
                'estado_pago': estado
            })
    return pd.DataFrame(facturas)

def generar_inspecciones(clientes_df: pd.DataFrame) -> pd.DataFrame:
    resultados = ['Hurto Confirmado', 'Anomalía', 'Normal', 'Falso Positivo']
    prob_resultados = [0.10, 0.15, 0.65, 0.10]
    tipos_irregularidad = ['Bypass', 'Cable Rajado', 'Manipulación Medidor', 'Conexión Clandestina', 'N/A']
    inspecciones = []
    for _, cliente in clientes_df.iterrows():
        for _ in range(np.random.randint(0, 3)):
            fecha = FECHA_INICIO + timedelta(days=np.random.randint(30, 365))
            resultado = np.random.choice(resultados, p=prob_resultados)
            if resultado in ['Hurto Confirmado', 'Anomalía']:
                tipo = np.random.choice(tipos_irregularidad)
                cnr = round(np.random.uniform(500, 5000), 2)
            else:
                tipo = 'N/A'
                cnr = 0
            inspecciones.append({
                'id_cliente': cliente['id_cliente'],
                'fecha_inspeccion': fecha,
                'resultado': resultado,
                'tipo_irregularidad': tipo,
                'cnr_estimado': cnr,
                'inspector': f'Inspector_{np.random.randint(1, 6)}'
            })
    return pd.DataFrame(inspecciones)

def main():
    print("=" * 60)
    print("🌌 PROYECTO ORION - GENERACIÓN DE DATOS DE MUESTRA")
    print("=" * 60)
    
    sample_dir = Path('datos/muestra')
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n📋 Generando clientes...")
    clientes = generar_clientes(N_CLIENTES)
    clientes.to_csv(sample_dir / 'clientes_muestra.csv', index=False)
    print(f"   ✅ {len(clientes)} clientes generados")
    
    print("\n⚡ Generando consumo...")
    consumo = generar_consumo(clientes, N_DIAS)
    consumo.to_csv(sample_dir / 'consumo_muestra.csv', index=False)
    print(f"   ✅ {len(consumo)} registros de consumo generados")
    
    print("\n🔔 Generando alarmas...")
    alarmas = generar_alarmas(clientes, N_DIAS)
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
    
    print("\n" + "=" * 60)
    print("✅ DATOS DE MUESTRA GENERADOS CORRECTAMENTE")
    print(f"📁 Ubicación: {sample_dir.absolute()}")
    print("=" * 60)

if __name__ == "__main__":
    main()