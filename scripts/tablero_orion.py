# scripts/tablero_orion.py
"""
Dashboard de Orion - Monitoreo Continuo con Datos Acumulados
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import sys
from pathlib import Path
import time
import subprocess

# Configurar página
st.set_page_config(
    page_title="🌌 Orion - Monitoreo Continuo",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# FUNCIONES DE CARGA DE DATOS
# ============================================================

def cargar_datos_acumulados():
    """Carga los datos acumulados de todas las ejecuciones"""
    processed_dir = Path('datos/procesados')
    historico_path = processed_dir / 'historico_puntajes.parquet'
    
    if historico_path.exists():
        df = pd.read_parquet(historico_path)
        return df
    return None

def cargar_ultima_ejecucion():
    """Carga la última ejecución"""
    processed_dir = Path('datos/procesados')
    latest_path = processed_dir / 'puntajes_latest.parquet'
    
    if latest_path.exists():
        df = pd.read_parquet(latest_path)
        return df, latest_path.stat().st_mtime
    
    archivos = list(processed_dir.glob('puntajes_*.parquet'))
    archivos = [f for f in archivos if 'latest' not in f.name and 'historico' not in f.name]
    
    if archivos:
        archivo = max(archivos, key=lambda x: x.stat().st_mtime)
        df = pd.read_parquet(archivo)
        return df, archivo.stat().st_mtime
    
    return None, None

def cargar_ejecuciones():
    """Carga todas las ejecuciones disponibles"""
    processed_dir = Path('datos/procesados')
    archivos = list(processed_dir.glob('puntajes_*.parquet'))
    archivos = [f for f in archivos if 'latest' not in f.name and 'historico' not in f.name]
    
    if not archivos:
        return None
    
    ejecuciones = []
    for archivo in archivos:
        try:
            nombre = archivo.stem
            partes = nombre.split('_')
            if len(partes) >= 2:
                timestamp = partes[1]
                fecha = datetime.strptime(timestamp, '%Y%m%d_%H%M%S')
                ejecuciones.append({
                    'archivo': archivo.name,
                    'fecha': fecha,
                    'timestamp': timestamp
                })
        except Exception as e:
            print(f"Error procesando {archivo}: {e}")
    
    if ejecuciones:
        return pd.DataFrame(ejecuciones).sort_values('fecha')
    return None

def cargar_inspecciones_latest():
    """Carga la última lista de inspecciones"""
    processed_dir = Path('datos/procesados')
    latest_path = processed_dir / 'inspecciones_priorizadas_latest.csv'
    
    if latest_path.exists():
        df = pd.read_csv(latest_path)
        return df
    return None

# ============================================================
# INICIALIZAR ESTADO DE SESIÓN
# ============================================================

if 'datos_acumulados' not in st.session_state:
    st.session_state.datos_acumulados = None
if 'ultimos_datos' not in st.session_state:
    st.session_state.ultimos_datos = None
if 'ultima_actualizacion' not in st.session_state:
    st.session_state.ultima_actualizacion = None
if 'ejecuciones' not in st.session_state:
    st.session_state.ejecuciones = None
if 'inspecciones' not in st.session_state:
    st.session_state.inspecciones = None

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🌌 Orion")
st.sidebar.markdown("---")

# Controles de actualización
auto_refresh = st.sidebar.checkbox("🔄 Actualización automática", value=True)
refresh_interval = st.sidebar.slider("Intervalo (segundos)", 5, 60, 15)

st.sidebar.markdown("---")
st.sidebar.caption(f"v2.0.0 | {datetime.now().strftime('%H:%M:%S')}")

if st.sidebar.button("🔄 Refrescar ahora"):
    st.cache_data.clear()
    st.session_state.datos_acumulados = None
    st.session_state.ultimos_datos = None
    st.session_state.ejecuciones = None
    st.session_state.inspecciones = None
    st.rerun()

# ============================================================
# CARGA DE DATOS
# ============================================================

st.title("🌌 Orion - Monitoreo Continuo")
st.markdown("### Sistema de Detección y Priorización de Hurto de Energía")

# Cargar todos los datos
if st.session_state.datos_acumulados is None:
    st.session_state.datos_acumulados = cargar_datos_acumulados()

if st.session_state.ultimos_datos is None:
    datos, mtime = cargar_ultima_ejecucion()
    if datos is not None:
        st.session_state.ultimos_datos = datos
        st.session_state.ultima_actualizacion = mtime

if st.session_state.ejecuciones is None:
    st.session_state.ejecuciones = cargar_ejecuciones()

if st.session_state.inspecciones is None:
    st.session_state.inspecciones = cargar_inspecciones_latest()

# Verificar si hay datos
if st.session_state.ultimos_datos is None:
    st.warning("⚠️ No hay datos de puntajes disponibles.")
    st.info("📌 Ejecuta primero la tubería diaria:")
    st.code("python scripts/ejecutar_tuberia_diaria.py", language="bash")
    
    if st.button("🚀 Ejecutar tubería ahora"):
        with st.spinner("Ejecutando tubería..."):
            result = subprocess.run(["python", "scripts/ejecutar_tuberia_diaria.py"], capture_output=True, text=True)
            if result.returncode == 0:
                st.success("✅ Tubería ejecutada correctamente")
                st.rerun()
            else:
                st.error(f"❌ Error: {result.stderr}")
    st.stop()

# Asignar variables
datos_acumulados = st.session_state.datos_acumulados
ultimos_datos = st.session_state.ultimos_datos
ejecuciones = st.session_state.ejecuciones
inspecciones = st.session_state.inspecciones

# ============================================================
# ESTADO DE DATOS DISPONIBLES
# ============================================================

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Estado de Datos")

# Verificar disponibilidad de datos en brutos
brutos_dir = Path('datos/brutos')
if brutos_dir.exists():
    for dataset in ['consumo', 'alarmas', 'clientes', 'facturacion']:
        path = brutos_dir / dataset
        if path.exists():
            archivos = list(path.glob('*.parquet'))
            if archivos:
                st.sidebar.success(f"✅ {dataset}: {len(archivos)} archivos")
            else:
                st.sidebar.warning(f"⚠️ {dataset}: sin archivos")
        else:
            st.sidebar.error(f"❌ {dataset}: no existe")
else:
    st.sidebar.error("❌ datos/brutos/ no existe")

# ============================================================
# FECHA DE ACTUALIZACIÓN
# ============================================================

if st.session_state.ultima_actualizacion:
    fecha_actual = datetime.fromtimestamp(st.session_state.ultima_actualizacion).strftime('%Y-%m-%d %H:%M:%S')
    st.markdown(f"### 📊 Última actualización: {fecha_actual}")
st.markdown("---")

# ============================================================
# KPIS GLOBALES - ACUMULADOS
# ============================================================

st.subheader("📊 Resumen Acumulado del Sistema")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if datos_acumulados is not None:
        total_suministros = datos_acumulados['id_cliente'].nunique() if 'id_cliente' in datos_acumulados.columns else len(datos_acumulados)
        st.metric("📊 Total Suministros (Acumulado)", total_suministros)
    else:
        st.metric("📊 Total Suministros (Acumulado)", len(ultimos_datos))

with col2:
    if datos_acumulados is not None and 'fecha_ejecucion' in datos_acumulados.columns:
        n_ejecuciones = datos_acumulados['fecha_ejecucion'].nunique()
        st.metric("🔄 Total Ejecuciones", n_ejecuciones)
    else:
        st.metric("🔄 Total Ejecuciones", "N/A")

with col3:
    if datos_acumulados is not None and 'prioridad' in datos_acumulados.columns:
        alta_acumulado = len(datos_acumulados[datos_acumulados['prioridad'] == 'ALTA'])
        st.metric("⚡ Alta Prioridad (Acumulado)", alta_acumulado)
    else:
        st.metric("⚡ Alta Prioridad (Acumulado)", "N/A")

with col4:
    st.metric("📊 Última Ejecución", len(ultimos_datos))

# ============================================================
# KPIS DE LA ÚLTIMA EJECUCIÓN
# ============================================================

st.subheader("📈 Distribución de Prioridades - Última Ejecución")

col1, col2, col3 = st.columns(3)

with col1:
    alta = len(ultimos_datos[ultimos_datos['prioridad'] == 'ALTA'])
    st.metric("⚡ Alta Prioridad", alta, delta=f"{alta/len(ultimos_datos)*100:.1f}%")

with col2:
    media = len(ultimos_datos[ultimos_datos['prioridad'] == 'MEDIA'])
    st.metric("📊 Media Prioridad", media, delta=f"{media/len(ultimos_datos)*100:.1f}%")

with col3:
    baja = len(ultimos_datos[ultimos_datos['prioridad'] == 'BAJA'])
    st.metric("📉 Baja Prioridad", baja, delta=f"{baja/len(ultimos_datos)*100:.1f}%")

# ============================================================
# EVOLUCIÓN HISTÓRICA (Si hay datos acumulados)
# ============================================================

if datos_acumulados is not None and 'fecha_ejecucion' in datos_acumulados.columns:
    st.markdown("---")
    st.subheader("📈 Evolución Histórica de Prioridades")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Evolución de prioridades por ejecución
        evolucion = datos_acumulados.groupby(['fecha_ejecucion', 'prioridad']).size().reset_index(name='count')
        
        fig = px.line(
            evolucion,
            x='fecha_ejecucion',
            y='count',
            color='prioridad',
            title='Evolución de Prioridades por Ejecución',
            color_discrete_map={'ALTA': '#ff6b6b', 'MEDIA': '#ffd93d', 'BAJA': '#6bcb77'},
            markers=True
        )
        fig.update_layout(xaxis_title='Fecha de Ejecución', yaxis_title='Número de Suministros')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Total de suministros por ejecución
        total_por_ejecucion = datos_acumulados.groupby('fecha_ejecucion').size().reset_index(name='total')
        
        fig = px.bar(
            total_por_ejecucion,
            x='fecha_ejecucion',
            y='total',
            title='Total de Suministros por Ejecución',
            color='total',
            color_continuous_scale='Blues'
        )
        fig.update_layout(xaxis_title='Fecha de Ejecución', yaxis_title='Total de Suministros')
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# GRÁFICOS DE LA ÚLTIMA EJECUCIÓN
# ============================================================

st.markdown("---")
st.subheader("📊 Análisis de la Última Ejecución")

col1, col2 = st.columns(2)

with col1:
    # Distribución de prioridades
    fig = px.pie(
        ultimos_datos,
        names='prioridad',
        title='Distribución de Prioridades',
        color='prioridad',
        color_discrete_map={'ALTA': '#ff6b6b', 'MEDIA': '#ffd93d', 'BAJA': '#6bcb77'},
        hole=0.3
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Probabilidad vs Puntaje de Prioridad
    fig = px.scatter(
        ultimos_datos,
        x='probabilidad',
        y='puntaje_prioridad',
        color='prioridad',
        color_discrete_map={'ALTA': '#ff6b6b', 'MEDIA': '#ffd93d', 'BAJA': '#6bcb77'},
        hover_data=['id_cliente'],
        title='Probabilidad vs Puntaje de Prioridad'
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# LISTA DE INSPECCIÓN
# ============================================================

st.markdown("---")
st.subheader("📋 Lista de Inspección Priorizada")

# Mostrar top 20 de la última ejecución
top = ultimos_datos.nlargest(20, 'puntaje_prioridad')
st.dataframe(
    top[['id_cliente', 'probabilidad', 'puntaje_prioridad', 'prioridad']],
    use_container_width=True,
    height=400
)

# Botón de exportación
col1, col2 = st.columns(2)

with col1:
    if st.button("📥 Exportar Lista Completa"):
        csv = ultimos_datos.to_csv(index=False)
        st.download_button(
            label="Descargar CSV",
            data=csv,
            file_name=f"orion_lista_inspeccion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

with col2:
    if inspecciones is not None and not inspecciones.empty:
        st.download_button(
            label="📥 Exportar Inspecciones",
            data=inspecciones.to_csv(index=False),
            file_name=f"orion_inspecciones_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

# ============================================================
# HISTÓRICO COMPLETO (Expandible)
# ============================================================

if datos_acumulados is not None:
    st.markdown("---")
    st.subheader("📚 Histórico Acumulado Completo")
    
    with st.expander("📋 Ver histórico completo"):
        st.dataframe(datos_acumulados, use_container_width=True)
        
        if st.button("📥 Exportar Histórico Completo"):
            csv = datos_acumulados.to_csv(index=False)
            st.download_button(
                label="Descargar CSV",
                data=csv,
                file_name=f"orion_historico_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

# ============================================================
# ESTADÍSTICAS DEL SISTEMA
# ============================================================

st.markdown("---")
st.subheader("⚙️ Estadísticas del Sistema")

col1, col2, col3 = st.columns(3)

with col1:
    if ejecuciones is not None:
        primera = ejecuciones['fecha'].min().strftime('%Y-%m-%d %H:%M')
        st.metric("📅 Primera Ejecución", primera)
    else:
        st.metric("📅 Primera Ejecución", "N/A")

with col2:
    if ejecuciones is not None:
        ultima = ejecuciones['fecha'].max().strftime('%Y-%m-%d %H:%M')
        st.metric("📅 Última Ejecución", ultima)
    else:
        st.metric("📅 Última Ejecución", "N/A")

with col3:
    if datos_acumulados is not None:
        registros = len(datos_acumulados)
        st.metric("📊 Total Registros", registros)
    else:
        st.metric("📊 Total Registros", "N/A")

# ============================================================
# ACTUALIZACIÓN AUTOMÁTICA
# ============================================================

st.markdown("---")
st.caption("🌌 Orion - Detección de Hurto de Energía | v2.0.0")

if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()