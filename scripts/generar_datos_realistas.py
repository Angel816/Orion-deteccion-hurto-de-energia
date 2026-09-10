# scripts/generar_datos_realistas.py
"""
Genera datos de muestra MÁS REALISTAS y ALEATORIOS con errores típicos
para probar la robustez del normalizador y limpiador.

Incluye:
- Datos faltantes
- Formatos inconsistentes (fechas, números)
- Valores atípicos
- Duplicados
- Espacios extra, mayúsculas/minúsculas mezcladas
- Caracteres especiales (tildes, ñ)
- Fechas inválidas
- IDs con formato diferente

Zona horaria: Perú (UTC-5)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import random
import sys
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
FECHA_FIN = FECHA_INICIO + timedelta(days=N_DIAS - 1)

TIPOS_CLIENTE = {
    'Residencial': {'prob': 0.65, 'consumo_base': (8, 25), 'potencia': (3, 10), 'factor_estacional': 0.3, 'factor_fin_semana': 1.3},
    'Comercial': {'prob': 0.20, 'consumo_base': (30, 80), 'potencia': (10, 30), 'factor_estacional': 0.2, 'factor_fin_semana': 0.9},
    'Industrial': {'prob': 0.08, 'consumo_base': (100, 300), 'potencia': (30, 100), 'factor_estacional': 0.1, 'factor_fin_semana': 0.7},
    'Restaurante': {'prob': 0.04, 'consumo_base': (40, 100), 'potencia': (15, 40), 'factor_estacional': 0.25, 'factor_fin_semana': 1.5},
    'Fabrica': {'prob': 0.03, 'consumo_base': (200, 500), 'potencia': (50, 200), 'factor_estacional': 0.15, 'factor_fin_semana': 0.5}
}

SECTORES = [
    'Alto Trujillo', 'La Esperanza', 'Máncora', 'Piura', 'Huaral',
    'Tumbes', 'Huánuco', 'Villa El Salvador', 'San Juan de Lurigancho',
    'Ate', 'Comas', 'Independencia', 'Los Olivos', 'Callao'
]

# Variaciones de nombres de sectores (para simular inconsistencias)
SECTORES_VARIANTES = {
    'Alto Trujillo': ['Alto Trujillo', 'ALTO TRUJILLO', 'alto trujillo', 'Alto  Trujillo', 'AltoTrujillo'],
    'La Esperanza': ['La Esperanza', 'LA ESPERANZA', 'la esperanza', 'La  Esperanza', 'LaEsperanza'],
    'Máncora': ['Máncora', 'MANCORA', 'máncora', 'Mancora', 'MÁNCORA'],
    'Piura': ['Piura', 'PIURA', 'piura', 'Piura ', ' Piura'],
    'Huaral': ['Huaral', 'HUARAL', 'huaral', 'Huaral ', 'Huaral'],
    'Tumbes': ['Tumbes', 'TUMBES', 'tumbes', 'Tumbes ', 'Tumbes'],
    'Huánuco': ['Huánuco', 'HUANUCO', 'huánuco', 'Huanuco', 'HUÁNUCO'],
    'Villa El Salvador': ['Villa El Salvador', 'VILLA EL SALVADOR', 'villa el salvador', 'Villa  El  Salvador'],
    'San Juan de Lurigancho': ['San Juan de Lurigancho', 'SAN JUAN DE LURIGANCHO', 'sjl', 'SJL', 'San Juan de Lurigancho '],
    'Ate': ['Ate', 'ATE', 'ate', 'Ate ', 'ATE '],
    'Comas': ['Comas', 'COMAS', 'comas', 'Comas ', 'Comas'],
    'Independencia': ['Independencia', 'INDEPENDENCIA', 'independencia', 'Independencia '],
    'Los Olivos': ['Los Olivos', 'LOS OLIVOS', 'los olivos', 'Los  Olivos', 'LosOlivos'],
    'Callao': ['Callao', 'CALLAO', 'callao', 'Callao ', 'CALLAO ']
}

TIPOS_IRREGULARIDAD = {
    'Bypass': {'prob': 0.30, 'descripcion': 'Puentes en base socket'},
    'Cable Rajado': {'prob': 0.25, 'descripcion': 'Derivación antes del medidor'},
    'Manipulación Medidor': {'prob': 0.20, 'descripcion': 'Alteración de medición'},
    'Conexión Clandestina': {'prob': 0.15, 'descripcion': 'Conexión directa a red'},
    'Auto-reconexión': {'prob': 0.10, 'descripcion': 'Reconexión tras corte'}
}

# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def generar_id_cliente(i: int) -> str:
    """Genera ID de cliente con posibles variaciones"""
    variantes = [
        f"CL-{i:05d}",
        f"CL{i:05d}",
        f"cl-{i:05d}",
        f"CL_{i:05d}",
        f"CL- {i:05d}",
        f" {i:05d}",
    ]
    return random.choice(variantes)


def generar_dni() -> str:
    """Genera DNI con posibles errores"""
    if random.random() < 0.1:
        # Algunos DNI con formato inválido
        return random.choice([
            f"{random.randint(1000000, 9999999)}",  # 7 dígitos
            f"{random.randint(100000000, 999999999)}",  # 9 dígitos
            f" {random.randint(10000000, 99999999)}",  # con espacio
        ])
    return f"{random.randint(10000000, 99999999)}"


def generar_ruc() -> str:
    """Genera RUC con posibles errores"""
    if random.random() < 0.1:
        return random.choice([
            f"{random.randint(1000000000, 9999999999)}",  # 10 dígitos
            f"{random.randint(100000000000, 999999999999)}",  # 12 dígitos
            f"{random.randint(10000000000, 20999999999)} ",  # con espacio
        ])
    return f"{random.randint(10000000000, 20999999999)}"


def generar_direccion(sector: str) -> str:
    """Genera dirección con posibles errores"""
    calles = ['Av. Principal', 'Jr. Los Álamos', 'Calle Las Flores', 
              'Av. Grau', 'Jr. Puno', 'Calle Comercio', 'Av. Arequipa',
              'Jr. Cusco', 'Calle Lima', 'Av. Bolognesi',
              'AV. PRINCIPAL', 'jr. los alamos', 'CALLE LAS FLORES']
    numero = random.randint(100, 999)
    
    if random.random() < 0.1:
        # Algunas direcciones sin número o con formato inválido
        return random.choice([
            f"{random.choice(calles)}",
            f"{random.choice(calles)} S/N",
            f"{random.choice(calles)} {numero} Dpto {random.randint(1, 20)}",
            f"{random.choice(calles)}  {numero}",  # doble espacio
            f" {random.choice(calles)} {numero} ",  # espacios extra
        ])
    
    return f"{random.choice(calles)} {numero}, {sector}"


def obtener_tipo_cliente() -> str:
    tipos = list(TIPOS_CLIENTE.keys())
    probs = [TIPOS_CLIENTE[t]['prob'] for t in tipos]
    return np.random.choice(tipos, p=probs)


def obtener_tipo_irregularidad() -> str:
    tipos = list(TIPOS_IRREGULARIDAD.keys())
    probs = [TIPOS_IRREGULARIDAD[t]['prob'] for t in tipos]
    return np.random.choice(tipos, p=probs)


def obtener_sector_variante(sector_original: str) -> str:
    """Retorna una variante del sector (para simular inconsistencias)"""
    if sector_original in SECTORES_VARIANTES:
        return random.choice(SECTORES_VARIANTES[sector_original])
    return sector_original


def introducir_error_fecha(fecha: datetime) -> str:
    """Convierte una fecha a string con formato variable (incluyendo errores)"""
    if random.random() < 0.1:
        # 10% de errores en fechas
        error_tipo = random.choice([
            'formato_invalido',
            'formato_peruano',
            'formato_americano',
            'solo_anio_mes',
            'texto',
            'vacio'
        ])
        
        if error_tipo == 'formato_invalido':
            return fecha.strftime('%Y/%m/%d')  # formato diferente
        elif error_tipo == 'formato_peruano':
            return fecha.strftime('%d/%m/%Y')  # formato peruano
        elif error_tipo == 'formato_americano':
            return fecha.strftime('%m/%d/%Y')  # formato americano
        elif error_tipo == 'solo_anio_mes':
            return fecha.strftime('%Y-%m')  # sin día
        elif error_tipo == 'texto':
            return random.choice(['pendiente', 'sin fecha', 'N/A', 'NO DEFINIDO'])
        elif error_tipo == 'vacio':
            return ''
    
    # Formato normal
    return fecha.strftime('%Y-%m-%d')


def introducir_error_numero(valor: float) -> str:
    """Convierte un número a string con formato variable (incluyendo errores)"""
    if random.random() < 0.08:
        # 8% de errores en números
        error_tipo = random.choice([
            'con_comas',
            'con_espacios',
            'con_simbolo',
            'texto',
            'vacio',
            'negativo_extremo'
        ])
        
        if error_tipo == 'con_comas':
            # Formato europeo: 1.234,56
            return f"{valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        elif error_tipo == 'con_espacios':
            return f" {valor:,.2f} "
        elif error_tipo == 'con_simbolo':
            return f"S/ {valor:,.2f}"
        elif error_tipo == 'texto':
            return random.choice(['pendiente', 'sin dato', 'N/A', 'ERROR'])
        elif error_tipo == 'vacio':
            return ''
        elif error_tipo == 'negativo_extremo':
            return str(-valor * 100)  # valor negativo extremo
    
    # Formato normal
    return f"{valor:.2f}"


def introducir_error_texto(texto: str) -> str:
    """Introduce errores en textos (espacios, mayúsculas, tildes)"""
    if random.random() < 0.1:
        error_tipo = random.choice([
            'espacios_extra',
            'mayusculas',
            'minusculas',
            'sin_tilde',
            'con_tilde',
            'vacio'
        ])
        
        if error_tipo == 'espacios_extra':
            return f"  {texto}  "
        elif error_tipo == 'mayusculas':
            return texto.upper()
        elif error_tipo == 'minusculas':
            return texto.lower()
        elif error_tipo == 'sin_tilde':
            return texto.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')
        elif error_tipo == 'con_tilde':
            return texto.replace('a', 'á').replace('e', 'é').replace('i', 'í').replace('o', 'ó').replace('u', 'ú') if 'a' in texto else texto
        elif error_tipo == 'vacio':
            return ''
    
    return texto


def agregar_duplicados(df: pd.DataFrame, porcentaje: float = 0.02) -> pd.DataFrame:
    """Agrega duplicados aleatorios al DataFrame"""
    n_duplicados = int(len(df) * porcentaje)
    if n_duplicados == 0:
        return df
    
    indices = np.random.choice(df.index, n_duplicados, replace=True)
    duplicados = df.loc[indices].copy()
    
    registro.info(f"   🔄 Agregando {n_duplicados} duplicados")
    return pd.concat([df, duplicados], ignore_index=True)


# ============================================================
# GENERADORES
# ============================================================

def generar_clientes(n: int) -> pd.DataFrame:
    registro.info(f"📋 Generando {n} clientes...")
    clientes = []
    
    for i in range(1, n + 1):
        tipo = obtener_tipo_cliente()
        sector_base = np.random.choice(SECTORES)
        sector = obtener_sector_variante(sector_base)
        es_riesgo = sector_base in ['Alto Trujillo', 'La Esperanza', 'Máncora', 'Piura', 'Huaral']
        tipo_data = TIPOS_CLIENTE[tipo]
        potencia = round(np.random.uniform(*tipo_data['potencia']), 1)
        
        if tipo == 'Residencial':
            documento = generar_dni()
            tipo_documento = 'DNI'
            razon_social = f"Cliente {i}"
        else:
            documento = generar_ruc()
            tipo_documento = 'RUC'
            razon_social = introducir_error_texto(f"Empresa {sector_base} S.A.C.")
        
        # Nombre con posibles errores
        nombre = introducir_error_texto(razon_social)
        
        cliente = {
            'id_cliente': generar_id_cliente(i),
            'nombre': nombre,
            'tipo_documento': tipo_documento,
            'documento': documento,
            'tipo_cliente': introducir_error_texto(tipo),
            'potencia_contratada': potencia,
            'sector': sector,
            'direccion': generar_direccion(sector_base),
            'zona_riesgo': es_riesgo,
            'tarifa': np.random.choice(['BT5B', 'BT5A', 'BT4', 'MT2', 'MT3']),
            'fecha_alta': introducir_error_fecha(FECHA_INICIO - timedelta(days=np.random.randint(365, 1825))),
            'estado': introducir_error_texto(random.choice(['Activo', 'Suspendido']))
        }
        clientes.append(cliente)
    
    df = pd.DataFrame(clientes)
    
    # Agregar algunos duplicados
    df = agregar_duplicados(df, 0.01)
    
    # Agregar algunos valores faltantes
    for col in ['nombre', 'tipo_cliente', 'sector']:
        if col in df.columns:
            n_nulos = int(len(df) * 0.02)
            indices = np.random.choice(df.index, n_nulos, replace=False)
            df.loc[indices, col] = np.nan
            registro.info(f"   ⚠️ {n_nulos} valores nulos en {col}")
    
    registro.info(f"✅ {len(df)} clientes generados (con errores)")
    return df


def generar_consumo(clientes_df: pd.DataFrame) -> pd.DataFrame:
    registro.info(f"⚡ Generando consumo...")
    registros = []
    
    for _, cliente in clientes_df.iterrows():
        id_cliente = cliente['id_cliente']
        tipo = cliente['tipo_cliente'] if pd.notna(cliente['tipo_cliente']) else 'Residencial'
        tipo = str(tipo).strip().title()
        if tipo not in TIPOS_CLIENTE:
            tipo = 'Residencial'
        
        tipo_data = TIPOS_CLIENTE[tipo]
        base = np.random.uniform(*tipo_data['consumo_base'])
        es_riesgo = cliente['zona_riesgo']
        estado = str(cliente['estado']).strip().title() if pd.notna(cliente['estado']) else 'Activo'
        
        prob_hurto = 0.25 if es_riesgo else 0.08
        tiene_hurto = random.random() < prob_hurto
        dia_inicio_hurto = np.random.randint(60, N_DIAS - 60) if tiene_hurto else None
        tipo_irregularidad = obtener_tipo_irregularidad() if tiene_hurto else None
        duracion_hurto = np.random.randint(30, 180) if tiene_hurto else 0
        
        for dia in range(N_DIAS):
            fecha = FECHA_INICIO + timedelta(days=dia)
            mes = fecha.month
            dia_semana = fecha.weekday()
            
            estacional = 1.0 + tipo_data['factor_estacional'] * np.sin(2 * np.pi * (mes - 6) / 12)
            dia_factor = tipo_data['factor_fin_semana'] if dia_semana >= 5 else 1.0
            ruido = np.random.normal(0, base * 0.15)
            
            consumo = max(0.5, base * estacional * dia_factor + ruido)
            
            if tiene_hurto and dia_inicio_hurto is not None:
                if dia_inicio_hurto <= dia < dia_inicio_hurto + duracion_hurto:
                    if tipo_irregularidad == 'Bypass':
                        consumo *= np.random.uniform(0.1, 0.3)
                    elif tipo_irregularidad == 'Cable Rajado':
                        consumo *= np.random.uniform(0.3, 0.5)
                    elif tipo_irregularidad == 'Manipulación Medidor':
                        consumo *= np.random.uniform(0.5, 0.75)
                    elif tipo_irregularidad == 'Conexión Clandestina':
                        consumo *= np.random.uniform(0.0, 0.15)
                    elif tipo_irregularidad == 'Auto-reconexión':
                        if dia > dia_inicio_hurto + 30:
                            consumo *= np.random.uniform(0.8, 1.0)
            
            if estado == 'Suspendido' and dia > N_DIAS - 90:
                consumo = 0.0
            
            # ✅ Introducir errores en consumo
            consumo_str = introducir_error_numero(consumo)
            
            # ✅ Introducir errores en tipo_lectura
            tipo_lectura_opciones = ['Real', 'Estimada', 'Promedio']
            tipo_lectura = introducir_error_texto(random.choice(tipo_lectura_opciones))
            
            # ✅ Introducir errores en fecha
            fecha_str = introducir_error_fecha(fecha)
            
            # ✅ Introducir errores en id_cliente (algunos con formato diferente)
            id_cliente_variante = id_cliente
            if random.random() < 0.02:
                id_cliente_variante = id_cliente.replace('-', '').lower()
            
            registros.append({
                'id_cliente': id_cliente_variante,
                'fecha': fecha_str,
                'consumo_kwh': consumo_str,
                'tipo_lectura': tipo_lectura,
                'tiene_hurto': tiene_hurto,
                'tipo_irregularidad': tipo_irregularidad
            })
    
    df = pd.DataFrame(registros)
    
    # Agregar algunos duplicados
    df = agregar_duplicados(df, 0.005)
    
    # Agregar valores faltantes
    n_nulos = int(len(df) * 0.01)
    indices = np.random.choice(df.index, n_nulos, replace=False)
    df.loc[indices, 'consumo_kwh'] = np.nan
    registro.info(f"   ⚠️ {n_nulos} valores nulos en consumo_kwh")
    
    # Agregar valores negativos extremos
    n_negativos = int(len(df) * 0.005)
    indices = np.random.choice(df.index, n_negativos, replace=False)
    df.loc[indices, 'consumo_kwh'] = -np.random.uniform(100, 1000, n_negativos)
    registro.info(f"   ⚠️ {n_negativos} valores negativos extremos")
    
    registro.info(f"✅ {len(df)} registros de consumo (con errores)")
    return df


def generar_alarmas(clientes_df: pd.DataFrame, consumo_df: pd.DataFrame) -> pd.DataFrame:
    registro.info(f"🔔 Generando alarmas...")
    tipos_alarma = ['Tapa Abierta', 'Precinto Roto', 'Consumo Cero', 'Error Comunicación', 
                    'Caída Brusca', 'Bypass Detectado', 'Magneto Detectado', 'Inversión de Fases']
    gravedad_map = {'Baja': 0.4, 'Media': 0.3, 'Alta': 0.2, 'Crítica': 0.1}
    
    alarmas = []
    for _, cliente in clientes_df.iterrows():
        id_cliente = cliente['id_cliente']
        es_riesgo = cliente['zona_riesgo']
        tipo = cliente['tipo_cliente'] if pd.notna(cliente['tipo_cliente']) else 'Residencial'
        tipo = str(tipo).strip().title()
        
        if tipo not in TIPOS_CLIENTE:
            tipo = 'Residencial'
        
        # Buscar si tiene hurto
        cliente_consumo = consumo_df[consumo_df['id_cliente'] == id_cliente]
        tiene_hurto = False
        if len(cliente_consumo) > 0:
            try:
                tiene_hurto = bool(cliente_consumo['tiene_hurto'].iloc[0])
            except:
                tiene_hurto = False
        
        if tiene_hurto:
            n_alarmas = np.random.poisson(3.0)
        elif es_riesgo:
            n_alarmas = np.random.poisson(1.5)
        elif tipo in ['Industrial', 'Fabrica']:
            n_alarmas = np.random.poisson(0.8)
        else:
            n_alarmas = np.random.poisson(0.3)
        
        for _ in range(min(n_alarmas, 20)):
            fecha = FECHA_INICIO + timedelta(days=np.random.randint(0, N_DIAS))
            
            if tiene_hurto:
                tipo_alarma = np.random.choice(['Bypass Detectado', 'Magneto Detectado', 
                                                'Caída Brusca', 'Precinto Roto', 'Tapa Abierta'])
            else:
                tipo_alarma = np.random.choice(tipos_alarma)
            
            gravedad = np.random.choice(list(gravedad_map.keys()), p=list(gravedad_map.values()))
            
            alarmas.append({
                'id_cliente': id_cliente,
                'fecha': introducir_error_fecha(fecha),
                'tipo_alarma': introducir_error_texto(tipo_alarma),
                'gravedad': introducir_error_texto(gravedad)
            })
    
    df = pd.DataFrame(alarmas)
    
    # Agregar valores faltantes
    n_nulos = int(len(df) * 0.03)
    indices = np.random.choice(df.index, n_nulos, replace=False)
    df.loc[indices, 'tipo_alarma'] = np.nan
    registro.info(f"   ⚠️ {n_nulos} valores nulos en tipo_alarma")
    
    registro.info(f"✅ {len(df)} alarmas (con errores)")
    return df


def generar_facturacion(clientes_df: pd.DataFrame, consumo_df: pd.DataFrame) -> pd.DataFrame:
    registro.info(f"💰 Generando facturación...")
    facturas = []
    precios = {'BT5B': 0.85, 'BT5A': 0.75, 'BT4': 0.65, 'MT2': 0.55, 'MT3': 0.45}
    
    for _, cliente in clientes_df.iterrows():
        id_cliente = cliente['id_cliente']
        tarifa = cliente['tarifa']
        if pd.isna(tarifa):
            tarifa = 'BT5B'
        precio_kwh = precios.get(str(tarifa).strip().upper(), 0.75)
        
        for mes in range(12):
            fecha_emision = FECHA_INICIO + timedelta(days=mes * 30 + np.random.randint(1, 10))
            fecha_vencimiento = fecha_emision + timedelta(days=30)
            
            # Buscar consumo del mes
            inicio_mes = fecha_emision.replace(day=1)
            fin_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            try:
                # Intentar leer consumo (algunos pueden ser texto)
                mask = (
                    (consumo_df['id_cliente'] == id_cliente) &
                    (pd.to_datetime(consumo_df['fecha'], errors='coerce') >= inicio_mes) &
                    (pd.to_datetime(consumo_df['fecha'], errors='coerce') <= fin_mes)
                )
                consumo_mes = pd.to_numeric(
                    consumo_df[mask]['consumo_kwh'], 
                    errors='coerce'
                ).sum()
            except:
                consumo_mes = 0
            
            if pd.isna(consumo_mes) or consumo_mes <= 0:
                consumo_mes = np.random.uniform(50, 200)
            
            monto_total = consumo_mes * precio_kwh + np.random.uniform(5, 15)
            
            if random.random() < 0.75:
                estado = 'Pagado'
                monto_pagado = monto_total
                fecha_pago = fecha_emision + timedelta(days=np.random.randint(5, 25))
            elif random.random() < 0.85:
                estado = 'Pendiente'
                monto_pagado = monto_total * np.random.uniform(0.3, 0.7)
                fecha_pago = None
            else:
                estado = 'Vencido'
                monto_pagado = 0
                fecha_pago = None
            
            dias_mora = max(0, (ahora_peru().replace(tzinfo=None) - fecha_vencimiento).days) if estado != 'Pagado' else 0
            
            facturas.append({
                'id_cliente': id_cliente,
                'fecha_emision': introducir_error_fecha(fecha_emision),
                'fecha_vencimiento': introducir_error_fecha(fecha_vencimiento),
                'fecha_pago': introducir_error_fecha(fecha_pago) if fecha_pago else '',
                'consumo_kwh': introducir_error_numero(consumo_mes),
                'precio_kwh': introducir_error_numero(precio_kwh),
                'monto_total': introducir_error_numero(monto_total),
                'monto_pagado': introducir_error_numero(monto_pagado),
                'monto_pendiente': introducir_error_numero(monto_total - monto_pagado),
                'estado_pago': introducir_error_texto(estado),
                'dias_mora': dias_mora,
                'tarifa': introducir_error_texto(tarifa)
            })
    
    df = pd.DataFrame(facturas)
    registro.info(f"✅ {len(df)} facturas (con errores)")
    return df


def generar_inspecciones(clientes_df: pd.DataFrame, consumo_df: pd.DataFrame) -> pd.DataFrame:
    registro.info(f"📋 Generando inspecciones...")
    inspecciones = []
    
    # Identificar clientes con hurto
    clientes_con_hurto = []
    for id_cliente in consumo_df['id_cliente'].unique():
        try:
            tiene_hurto = consumo_df[consumo_df['id_cliente'] == id_cliente]['tiene_hurto'].any()
            if tiene_hurto:
                clientes_con_hurto.append(id_cliente)
        except:
            pass
    
    clientes_sin_hurto = [c for c in clientes_df['id_cliente'].unique() if c not in clientes_con_hurto]
    
    for id_cliente in clientes_con_hurto:
        n_inspecciones = np.random.randint(1, 4)
        for _ in range(n_inspecciones):
            fecha = FECHA_INICIO + timedelta(days=np.random.randint(30, N_DIAS))
            
            # Buscar tipo de irregularidad
            cliente_consumo = consumo_df[consumo_df['id_cliente'] == id_cliente]
            try:
                tipo_irregularidad = cliente_consumo['tipo_irregularidad'].iloc[0]
                if pd.isna(tipo_irregularidad):
                    tipo_irregularidad = 'Bypass'
            except:
                tipo_irregularidad = 'Bypass'
            
            cnr = np.random.uniform(500, 8000)
            
            inspecciones.append({
                'id_cliente': id_cliente,
                'fecha_inspeccion': introducir_error_fecha(fecha),
                'resultado': introducir_error_texto('Hurto Confirmado'),
                'tipo_irregularidad': introducir_error_texto(tipo_irregularidad),
                'descripcion': introducir_error_texto(TIPOS_IRREGULARIDAD.get(tipo_irregularidad, {}).get('descripcion', 'Sin descripción')),
                'cnr_estimado': introducir_error_numero(cnr),
                'monto_recuperar': introducir_error_numero(cnr * 0.85),
                'inspector': introducir_error_texto(f"Inspector_{np.random.randint(1, 11)}")
            })
    
    n_negativas = len(clientes_sin_hurto) // 3
    if n_negativas > 0:
        for id_cliente in np.random.choice(clientes_sin_hurto, min(n_negativas, len(clientes_sin_hurto)), replace=False):
            fecha = FECHA_INICIO + timedelta(days=np.random.randint(30, N_DIAS))
            resultado = np.random.choice(['Normal', 'Anomalía', 'Falso Positivo'], p=[0.6, 0.25, 0.15])
            
            if resultado == 'Anomalía':
                tipo_irregularidad = obtener_tipo_irregularidad()
                cnr = np.random.uniform(200, 1500)
            else:
                tipo_irregularidad = 'N/A'
                cnr = 0
            
            inspecciones.append({
                'id_cliente': id_cliente,
                'fecha_inspeccion': introducir_error_fecha(fecha),
                'resultado': introducir_error_texto(resultado),
                'tipo_irregularidad': introducir_error_texto(tipo_irregularidad),
                'descripcion': introducir_error_texto(TIPOS_IRREGULARIDAD.get(tipo_irregularidad, {}).get('descripcion', 'Sin irregularidad')),
                'cnr_estimado': introducir_error_numero(cnr),
                'monto_recuperar': introducir_error_numero(cnr * 0.85),
                'inspector': introducir_error_texto(f"Inspector_{np.random.randint(1, 11)}")
            })
    
    df = pd.DataFrame(inspecciones)
    
    # Agregar valores faltantes
    n_nulos = int(len(df) * 0.03)
    if n_nulos > 0:
        indices = np.random.choice(df.index, n_nulos, replace=False)
        df.loc[indices, 'resultado'] = np.nan
        registro.info(f"   ⚠️ {n_nulos} valores nulos en resultado")
    
    registro.info(f"✅ {len(df)} inspecciones (con errores)")
    return df


# ============================================================
# ENVIAR A COLA CON ERRORES
# ============================================================

def enviar_a_cola(clientes, consumo, alarmas, facturacion, inspecciones):
    """
    Envía los datos a la cola con diferentes formatos y errores
    """
    registro.info("📤 Enviando datos a la cola con errores controlados...")
    
    cola_dir = Path('datos/cola/pendientes')
    cola_dir.mkdir(parents=True, exist_ok=True)
    
    # Limpiar cola previa
    for archivo in cola_dir.glob('*'):
        try:
            archivo.unlink()
        except:
            pass
    
    # ============================================================
    # CLIENTES - Excel
    # ============================================================
    clientes_renombrados = clientes.rename(columns={
        'id_cliente': 'CODIGO_CLIENTE',
        'nombre': 'NOMBRE',
        'tipo_cliente': 'TIPO',
        'sector': 'ZONA',
        'potencia_contratada': 'POTENCIA_KW',
        'tarifa': 'TARIFA_CODIGO',
        'zona_riesgo': 'ZONA_RIESGO',
        'fecha_alta': 'FECHA_ALTA',
        'estado': 'ESTADO'
    })
    clientes_renombrados = clientes_renombrados.drop(
        columns=['tipo_documento', 'documento', 'direccion', 'zona_riesgo'],
        errors='ignore'
    )
    clientes_renombrados.to_excel(cola_dir / 'clientes_2025.xlsx', index=False)
    registro.info(f"   ✅ clientes_2025.xlsx (Excel)")
    
    # ============================================================
    # CONSUMO - CSV
    # ============================================================
    consumo_renombrado = consumo.rename(columns={
        'id_cliente': 'CLIENTE',
        'fecha': 'FECHA_LECTURA',
        'consumo_kwh': 'CONSUMO',
        'tipo_lectura': 'TIPO_LECTURA'
    })
    consumo_renombrado = consumo_renombrado.drop(
        columns=['tiene_hurto', 'tipo_irregularidad'], 
        errors='ignore'
    )
    consumo_renombrado.to_csv(cola_dir / 'consumo_diario.csv', index=False, encoding='utf-8')
    registro.info(f"   ✅ consumo_diario.csv (CSV)")
    
    # ============================================================
    # ALARMAS - JSON
    # ============================================================
    alarmas_renombradas = alarmas.rename(columns={
        'id_cliente': 'cliente_id',
        'fecha': 'fecha_evento',
        'tipo_alarma': 'alarma',
        'gravedad': 'nivel'
    })
    # Convertir NaN a None para JSON
    alarmas_renombradas = alarmas_renombradas.where(pd.notna(alarmas_renombradas), None)
    
    alarmas_renombradas.to_json(
        cola_dir / 'alarmas_2025.json',
        orient='records',
        indent=2,
        force_ascii=False,
        date_format='iso'
    )
    registro.info(f"   ✅ alarmas_2025.json (JSON)")
    
    # ============================================================
    # FACTURACIÓN - Excel
    # ============================================================
    facturacion_renombrada = facturacion.rename(columns={
        'id_cliente': 'CLIENTE_ID',
        'fecha_emision': 'FECHA_FACTURA',
        'fecha_vencimiento': 'FECHA_VENCIMIENTO',
        'monto_total': 'IMPORTE_TOTAL',
        'monto_pagado': 'PAGADO',
        'estado_pago': 'ESTADO',
        'consumo_kwh': 'CONSUMO_FACTURADO'
    })
    facturacion_renombrada = facturacion_renombrada.drop(
        columns=['fecha_pago', 'precio_kwh', 'monto_pendiente', 'dias_mora', 'tarifa'],
        errors='ignore'
    )
    facturacion_renombrada.to_excel(cola_dir / 'facturacion_2025.xlsx', index=False)
    registro.info(f"   ✅ facturacion_2025.xlsx (Excel)")
    
    # ============================================================
    # INSPECCIONES - CSV
    # ============================================================
    inspecciones_renombradas = inspecciones.rename(columns={
        'id_cliente': 'CLIENTE',
        'fecha_inspeccion': 'FECHA_INSPECCION',
        'resultado': 'RESULTADO',
        'tipo_irregularidad': 'TIPO_IRREGULARIDAD',
        'cnr_estimado': 'CNR',
        'monto_recuperar': 'MONTO_RECUPERAR',
        'inspector': 'INSPECTOR'
    })
    inspecciones_renombradas.to_csv(cola_dir / 'inspecciones_2025.csv', index=False, encoding='utf-8')
    registro.info(f"   ✅ inspecciones_2025.csv (CSV)")
    
    # ============================================================
    # DATOS EXTRA SUCIOS (para probar limpieza)
    # ============================================================
    consumo_sucio = consumo_renombrado.copy()
    
    # Agregar más nulos
    indices_nulos = np.random.choice(consumo_sucio.index, int(len(consumo_sucio) * 0.02), replace=False)
    consumo_sucio.loc[indices_nulos, 'CONSUMO'] = np.nan
    
    # Agregar más negativos
    indices_negativos = np.random.choice(consumo_sucio.index, int(len(consumo_sucio) * 0.01), replace=False)
    consumo_sucio.loc[indices_negativos, 'CONSUMO'] = -np.random.uniform(100, 1000, len(indices_negativos))
    
    consumo_sucio.to_csv(cola_dir / 'consumo_sucio.csv', index=False, encoding='utf-8')
    registro.info(f"   ✅ consumo_sucio.csv (CSV con errores extremos)")
    
    # ============================================================
    # RESUMEN
    # ============================================================
    archivos = list(cola_dir.glob('*'))
    registro.info(f"\n📊 {len(archivos)} archivos enviados a la cola:")
    for archivo in archivos:
        tamaño = archivo.stat().st_size / 1024
        registro.info(f"   📄 {archivo.name} ({tamaño:.1f} KB)")
    
    # Contar errores introducidos
    registro.info("\n📊 ERRORES INTRODUCIDOS:")
    registro.info(f"   ⚠️ Nulos en clientes: ~2%")
    registro.info(f"   ⚠️ Nulos en consumo: ~1%")
    registro.info(f"   ⚠️ Negativos extremos: ~0.5%")
    registro.info(f"   ⚠️ Fechas inválidas: ~10%")
    registro.info(f"   ⚠️ Números con formato incorrecto: ~8%")
    registro.info(f"   ⚠️ Textos con espacios/mayúsculas: ~10%")
    registro.info(f"   ⚠️ Duplicados: ~2%")


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def main():
    """Genera y envía datos a la cola con errores controlados"""
    print("=" * 70)
    print("🌌 PROYECTO ORION - GENERACIÓN DE DATOS REALISTAS CON ERRORES")
    print(f"🕐 Hora Perú: {ahora_peru().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print(f"📊 {N_CLIENTES} clientes, {N_DIAS} días de consumo")
    print(f"📅 Período: {FECHA_INICIO.strftime('%Y-%m-%d')} a {FECHA_FIN.strftime('%Y-%m-%d')}")
    print("=" * 70)
    print("⚠️ Este script introduce errores controlados para probar el normalizador")
    print("=" * 70)
    
    # 1. Generar datos con errores
    print("\n📋 Generando datos con errores controlados...")
    clientes = generar_clientes(N_CLIENTES)
    consumo = generar_consumo(clientes)
    alarmas = generar_alarmas(clientes, consumo)
    facturacion = generar_facturacion(clientes, consumo)
    inspecciones = generar_inspecciones(clientes, consumo)
    
    # 2. Enviar a la cola
    print("\n📤 Enviando datos a la cola...")
    enviar_a_cola(clientes, consumo, alarmas, facturacion, inspecciones)
    
    # ============================================================
    # RESUMEN
    # ============================================================
    print("\n" + "=" * 70)
    print("✅ DATOS GENERADOS Y ENVIADOS A LA COLA (CON ERRORES)")
    print("=" * 70)
    
    print("\n📊 RESUMEN:")
    print(f"   👥 Clientes: {len(clientes)}")
    print(f"   ⚡ Consumo: {len(consumo)} registros")
    print(f"   🔔 Alarmas: {len(alarmas)}")
    print(f"   💰 Facturas: {len(facturacion)}")
    print(f"   📋 Inspecciones: {len(inspecciones)}")
    
    clientes_con_hurto = consumo[consumo['tiene_hurto'] == True]['id_cliente'].nunique()
    print(f"\n   🚨 Clientes con hurto: {clientes_con_hurto} ({clientes_con_hurto/len(clientes)*100:.1f}%)")
    
    print("\n⚠️ ERRORES INTRODUCIDOS PARA PRUEBAS:")
    print("   • Datos faltantes (nulos)")
    print("   • Valores negativos extremos")
    print("   • Fechas en formatos inconsistentes")
    print("   • Números con formato incorrecto")
    print("   • Textos con espacios/mayúsculas/tildes")
    print("   • Duplicados")
    print("   • IDs con formato diferente")
    
    print("\n📋 PRÓXIMOS PASOS:")
    print("   1. Procesar la cola (probar normalizador):")
    print("      python scripts/procesar_cola_datos.py --procesar")
    print("   2. Ver reportes de normalización:")
    print("      Get-ChildItem datos\\metadatos\\")
    print("   3. Ejecutar flujo completo:")
    print("      python scripts/ejecutar_flujo_completo.py")


if __name__ == "__main__":
    main()