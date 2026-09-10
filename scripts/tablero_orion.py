# scripts/tablero_orion.py
"""
Dashboard de Orion - Monitoreo Continuo con Buscador de Clientes y Métricas
Zona horaria: Perú (UTC-5)
Moneda: Nuevo Sol Peruano (S/)

Lee inspecciones desde carpetas oficiales:
1. datos/retroalimentacion/inspecciones/
2. datos/brutos/inspecciones/
3. datos_pasados/inspecciones/
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sys
from pathlib import Path
import time
import subprocess
import json

# Agregar src al path
sys.path.append(str(Path(__file__).parent.parent))

from src.utilidades.tiempo import ahora_peru, formatear_fecha, iso_peru
from src.utilidades.metricas import (
    MetricasModelo,
    MetricasNegocio,
    MetricasSistema,
    FormateadorMetricas,
    metricas_sistema
)

# ============================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================

st.set_page_config(
    page_title="🌌 Orion - Monitoreo Continuo",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# FUNCIONES DE CARGA DE DATOS
# ============================================================

def cargar_datos():
    """
    Carga los datos para el dashboard:
    - Histórico acumulado (TODOS los datos)
    - Última ejecución (para KPIs actuales)
    """
    processed_dir = Path('datos/procesados')
    resultado = {
        'historico': None,
        'ultimos': None,
        'total_registros': 0,
        'total_ejecuciones': 0,
        'ultima_actualizacion': None,
        'alta_prioridad_acumulada': 0
    }
    
    # 1. Cargar histórico acumulado
    historico_path = processed_dir / 'historico_puntajes.parquet'
    if historico_path.exists():
        df_historico = pd.read_parquet(historico_path)
        resultado['historico'] = df_historico
        resultado['total_registros'] = len(df_historico)
        
        if 'ejecucion_id' in df_historico.columns:
            resultado['total_ejecuciones'] = df_historico['ejecucion_id'].nunique()
        
        if 'fecha_ejecucion' in df_historico.columns:
            resultado['ultima_actualizacion'] = df_historico['fecha_ejecucion'].max()
        
        if 'prioridad' in df_historico.columns:
            resultado['alta_prioridad_acumulada'] = len(
                df_historico[df_historico['prioridad'] == 'ALTA']
            )
    
    # 2. Cargar última ejecución
    latest_path = processed_dir / 'puntajes_latest.parquet'
    if latest_path.exists():
        resultado['ultimos'] = pd.read_parquet(latest_path)
    
    # 3. Si no hay histórico, usar última versión
    if resultado['total_registros'] == 0 and resultado['ultimos'] is not None:
        resultado['total_registros'] = len(resultado['ultimos'])
        resultado['total_ejecuciones'] = 1
    
    return resultado


def cargar_inspecciones():
    """
    Carga inspecciones desde carpetas oficiales (NO desde muestra)
    """
    # 1. Prioridad 1: retroalimentación
    insp_feedback = Path('datos/retroalimentacion/inspecciones')
    if insp_feedback.exists():
        archivos = list(insp_feedback.glob('*.csv'))
        if archivos:
            try:
                dfs = [pd.read_csv(f) for f in archivos]
                df = pd.concat(dfs, ignore_index=True)
                return df, str(insp_feedback)
            except Exception as e:
                pass
    
    # 2. Prioridad 2: brutos
    insp_brutos = Path('datos/brutos/inspecciones')
    if insp_brutos.exists():
        archivos = list(insp_brutos.glob('*.parquet'))
        if archivos:
            try:
                dfs = [pd.read_parquet(f) for f in archivos]
                df = pd.concat(dfs, ignore_index=True)
                return df, str(insp_brutos)
            except Exception as e:
                pass
    
    # 3. Prioridad 3: datos_pasados
    insp_pasados = Path('datos_pasados/inspecciones')
    if insp_pasados.exists():
        archivos = list(insp_pasados.glob('*.parquet'))
        if archivos:
            try:
                dfs = [pd.read_parquet(f) for f in archivos]
                df = pd.concat(dfs, ignore_index=True)
                return df, str(insp_pasados)
            except Exception as e:
                pass
    
    return None, None


def cargar_metricas_modelo():
    """Carga las métricas del modelo actual"""
    metrics_path = Path('modelos/actual/metrics.json')
    if metrics_path.exists():
        try:
            with open(metrics_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}


def cargar_estado_bucle():
    """Carga el estado del bucle cerrado"""
    estado_path = Path('datos/retroalimentacion/entrenamiento/estado_bucle.json')
    if estado_path.exists():
        try:
            with open(estado_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}


# ============================================================
# INICIALIZAR ESTADO DE SESIÓN
# ============================================================

if 'datos' not in st.session_state:
    st.session_state.datos = None
if 'inspecciones' not in st.session_state:
    st.session_state.inspecciones = None
if 'fuente_inspecciones' not in st.session_state:
    st.session_state.fuente_inspecciones = None
if 'metricas_modelo' not in st.session_state:
    st.session_state.metricas_modelo = None
if 'estado_bucle' not in st.session_state:
    st.session_state.estado_bucle = None
if 'cliente_buscado' not in st.session_state:
    st.session_state.cliente_buscado = None

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🌌 Orion")
st.sidebar.markdown("---")

auto_refresh = st.sidebar.checkbox("🔄 Actualización automática", value=True)
refresh_interval = st.sidebar.slider("Intervalo (segundos)", 5, 60, 15)

st.sidebar.markdown("---")
st.sidebar.caption(f"v2.0.0 | {ahora_peru().strftime('%H:%M:%S')} (Perú)")

if st.sidebar.button("🔄 Refrescar ahora"):
    st.cache_data.clear()
    st.session_state.datos = None
    st.session_state.inspecciones = None
    st.session_state.fuente_inspecciones = None
    st.session_state.metricas_modelo = None
    st.session_state.estado_bucle = None
    st.session_state.cliente_buscado = None
    st.rerun()

# ============================================================
# CARGA DE DATOS
# ============================================================

st.title("🌌 Orion - Monitoreo Continuo")
st.markdown("### Sistema de Detección y Priorización de Hurto de Energía")

# Cargar datos
if st.session_state.datos is None:
    st.session_state.datos = cargar_datos()

if st.session_state.inspecciones is None:
    inspecciones, fuente = cargar_inspecciones()
    st.session_state.inspecciones = inspecciones
    st.session_state.fuente_inspecciones = fuente

if st.session_state.metricas_modelo is None:
    st.session_state.metricas_modelo = cargar_metricas_modelo()

if st.session_state.estado_bucle is None:
    st.session_state.estado_bucle = cargar_estado_bucle()

# Asignar variables
datos = st.session_state.datos
inspecciones = st.session_state.inspecciones
fuente_inspecciones = st.session_state.fuente_inspecciones
metricas_modelo = st.session_state.metricas_modelo
estado_bucle = st.session_state.estado_bucle

# Verificar si hay datos
if datos['ultimos'] is None:
    st.warning("⚠️ No hay datos de puntajes disponibles.")
    st.info("📌 Ejecuta primero el flujo completo:")
    st.code("python scripts/ejecutar_flujo_completo.py", language="bash")
    
    if st.button("🚀 Ejecutar flujo completo ahora"):
        with st.spinner("Ejecutando flujo completo..."):
            result = subprocess.run(
                ["python", "scripts/ejecutar_flujo_completo.py"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            if result.returncode == 0:
                st.success("✅ Flujo completo ejecutado correctamente")
                st.rerun()
            else:
                st.error(f"❌ Error: {result.stderr}")
    st.stop()

ultimos_datos = datos['ultimos']
historico = datos['historico']

# ============================================================
# FECHA DE ACTUALIZACIÓN
# ============================================================

if datos['ultima_actualizacion']:
    if hasattr(datos['ultima_actualizacion'], 'strftime'):
        fecha_str = formatear_fecha(datos['ultima_actualizacion'])
    else:
        fecha_str = str(datos['ultima_actualizacion'])
    st.markdown(f"### 📊 Última actualización: {fecha_str} (Perú)")

st.markdown(f"🕐 **Hora actual (Perú):** {ahora_peru().strftime('%Y-%m-%d %H:%M:%S')}")
st.markdown("---")

# ============================================================
# KPIS GLOBALES - ACUMULADOS
# ============================================================

st.subheader("📊 Resumen Acumulado del Sistema")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📊 Total Registros (Acumulado)", datos['total_registros'])

with col2:
    st.metric("🔄 Total Ejecuciones", datos['total_ejecuciones'])

with col3:
    if historico is not None and 'prioridad' in historico.columns:
        st.metric("⚡ Alta Prioridad (Acumulado)", datos['alta_prioridad_acumulada'])
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
# MÉTRICAS DEL SISTEMA
# ============================================================

st.markdown("---")
st.subheader("📊 Métricas del Sistema")

# ============================================================
# MÉTRICAS DEL MODELO
# ============================================================

if metricas_modelo:
    st.markdown("#### 🧠 Métricas del Modelo")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        accuracy = metricas_modelo.get('accuracy', 0)
        st.metric("🎯 Accuracy", FormateadorMetricas.formatear_porcentaje(accuracy))
    
    with col2:
        precision = metricas_modelo.get('precision', 0)
        st.metric("📊 Precision", FormateadorMetricas.formatear_porcentaje(precision))
    
    with col3:
        recall = metricas_modelo.get('recall', 0)
        st.metric("📈 Recall", FormateadorMetricas.formatear_porcentaje(recall))
    
    with col4:
        f1 = metricas_modelo.get('f1', 0)
        st.metric("⚡ F1-Score", FormateadorMetricas.formatear_porcentaje(f1))
    
    with col5:
        version = metricas_modelo.get('version', 'N/A')
        st.metric("📦 Versión", version)

# ============================================================
# MÉTRICAS DE NEGOCIO (desde inspecciones oficiales)
# ============================================================

if inspecciones is not None and not inspecciones.empty:
    st.markdown("#### 💰 Métricas de Negocio (en Nuevos Soles)")
    
    # Mostrar fuente
    with st.expander(f"📂 Fuente: {fuente_inspecciones} ({len(inspecciones)} registros)"):
        st.dataframe(inspecciones.head(10))
    
    try:
        total = len(inspecciones)
        
        # ============================================================
        # CALCULAR MÉTRICAS
        # ============================================================
        
        # Normalizar texto de resultado
        if 'resultado' in inspecciones.columns:
            resultados_norm = inspecciones['resultado'].astype(str).str.strip().str.title()
            
            confirmados = len(resultados_norm[resultados_norm == 'Hurto Confirmado'])
            tasa_exito = confirmados / total if total > 0 else 0
            
            falsos = len(resultados_norm[resultados_norm == 'Falso Positivo'])
            tasa_fp = falsos / total if total > 0 else 0
        else:
            tasa_exito = 0
            tasa_fp = 0
        
        # Recuperación (en Soles)
        if 'monto_recuperar' in inspecciones.columns:
            recuperacion = pd.to_numeric(
                inspecciones['monto_recuperar'], 
                errors='coerce'
            ).sum()
            if pd.isna(recuperacion):
                recuperacion = 0
        else:
            recuperacion = 0
        
        # Costo (S/ 30 por inspección)
        costo_unitario = 30.0
        costo = total * costo_unitario
        
        # ROI
        roi = (recuperacion - costo) / costo if costo > 0 else 0
        
        # Rentabilidad
        rentabilidad = recuperacion - costo
        
        # CNR Total
        if 'cnr_estimado' in inspecciones.columns:
            cnr_total = pd.to_numeric(
                inspecciones['cnr_estimado'], 
                errors='coerce'
            ).sum()
            if pd.isna(cnr_total):
                cnr_total = 0
        else:
            cnr_total = 0
        
        # ============================================================
        # MOSTRAR MÉTRICAS
        # ============================================================
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("✅ Tasa de Éxito", FormateadorMetricas.formatear_porcentaje(tasa_exito))
        
        with col2:
            st.metric("💰 Recuperación", FormateadorMetricas.formatear_moneda(recuperacion))
        
        with col3:
            st.metric("💸 Costo Total", FormateadorMetricas.formatear_moneda(costo))
        
        with col4:
            st.metric("📈 ROI", FormateadorMetricas.formatear_porcentaje(roi))
        
        # Segunda fila
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("❌ Falsos Positivos", FormateadorMetricas.formatear_porcentaje(tasa_fp))
        
        with col2:
            st.metric("📋 Inspecciones", total)
        
        with col3:
            st.metric("💵 Rentabilidad", FormateadorMetricas.formatear_moneda(rentabilidad))
        
        with col4:
            st.metric("⚡ CNR Total", f"{cnr_total:,.0f} kWh")
    
    except Exception as e:
        st.error(f"❌ Error calculando métricas: {e}")

else:
    st.info("ℹ️ No hay inspecciones disponibles para calcular métricas de negocio.")
    st.info("💡 Ejecuta el flujo completo para generar inspecciones:")
    st.code("python scripts/ejecutar_flujo_completo.py", language="bash")

# ============================================================
# BUSCADOR DE CLIENTES
# ============================================================

st.markdown("---")
st.subheader("🔍 Buscar Historial de Cliente")

col1, col2 = st.columns([3, 1])

with col1:
    id_cliente_buscar = st.text_input(
        "Ingresa el ID del cliente (ej: CL-00001)",
        placeholder="Escribe el ID del cliente...",
        key="buscador_cliente",
        value=st.session_state.cliente_buscado if st.session_state.cliente_buscado else ""
    )

with col2:
    buscar = st.button("🔍 Buscar", use_container_width=True)

# Mostrar resultados si se busca
if buscar and id_cliente_buscar:
    id_cliente_buscar = id_cliente_buscar.strip().upper()
    st.session_state.cliente_buscado = id_cliente_buscar
    
    if historico is not None and 'id_cliente' in historico.columns:
        # Normalizar id_cliente en histórico
        historico_temp = historico.copy()
        historico_temp['id_cliente_norm'] = historico_temp['id_cliente'].astype(str).str.strip().str.upper()
        
        historial_cliente = historico_temp[
            historico_temp['id_cliente_norm'] == id_cliente_buscar
        ]
        
        if not historial_cliente.empty:
            st.success(f"✅ Cliente encontrado: {id_cliente_buscar}")
            
            st.markdown("---")
            st.markdown(f"### 📊 Historial de {id_cliente_buscar}")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📊 Total Registros", len(historial_cliente))
            
            with col2:
                if 'prioridad' in historial_cliente.columns:
                    alta_count = len(
                        historial_cliente[historial_cliente['prioridad'] == 'ALTA']
                    )
                    st.metric("⚠️ Alertas Altas", alta_count)
                else:
                    st.metric("⚠️ Alertas Altas", "N/A")
            
            with col3:
                if 'puntaje_prioridad' in historial_cliente.columns:
                    puntaje_max = historial_cliente['puntaje_prioridad'].max()
                    st.metric("📈 Puntaje Máximo", f"{puntaje_max:.3f}")
                else:
                    st.metric("📈 Puntaje Máximo", "N/A")
            
            with col4:
                if 'fecha_ejecucion' in historial_cliente.columns:
                    ultima = historial_cliente['fecha_ejecucion'].max()
                    if hasattr(ultima, 'strftime'):
                        fecha_str = formatear_fecha(ultima, '%Y-%m-%d %H:%M')
                    else:
                        fecha_str = str(ultima)
                    st.metric("📅 Última Actualización", fecha_str)
                else:
                    st.metric("📅 Última Actualización", "N/A")
            
            # Mostrar evolución del cliente
            if 'fecha_ejecucion' in historial_cliente.columns:
                st.markdown("---")
                st.markdown("### 📈 Evolución del Cliente")
                
                historial_ordenado = historial_cliente.sort_values('fecha_ejecucion')
                
                fig = px.line(
                    historial_ordenado,
                    x='fecha_ejecucion',
                    y='puntaje_prioridad',
                    title=f'Evolución del Puntaje de Prioridad - {id_cliente_buscar}',
                    markers=True,
                    labels={
                        'puntaje_prioridad': 'Puntaje de Prioridad',
                        'fecha_ejecucion': 'Fecha de Ejecución (Perú)'
                    }
                )
                fig.add_hline(
                    y=0.7,
                    line_dash="dash",
                    line_color="red",
                    annotation_text="Umbral ALTA"
                )
                fig.add_hline(
                    y=0.4,
                    line_dash="dash",
                    line_color="orange",
                    annotation_text="Umbral MEDIA"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Mostrar tabla completa del cliente
            st.markdown("---")
            st.markdown("### 📋 Detalle de Registros")
            
            columnas_mostrar = [
                'fecha_ejecucion',
                'prioridad',
                'puntaje_prioridad',
                'probabilidad'
            ]
            if 'ejecucion_id' in historial_ordenado.columns:
                columnas_mostrar.insert(0, 'ejecucion_id')
            
            columnas_mostrar = [
                col for col in columnas_mostrar
                if col in historial_ordenado.columns
            ]
            
            st.dataframe(
                historial_ordenado[columnas_mostrar],
                use_container_width=True,
                height=300
            )
            
            if st.button(f"📥 Exportar Historial de {id_cliente_buscar}"):
                csv = historial_ordenado.to_csv(index=False)
                st.download_button(
                    label="Descargar CSV",
                    data=csv,
                    file_name=f"historial_cliente_{id_cliente_buscar}_{ahora_peru().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        else:
            st.warning(f"⚠️ No se encontró el cliente: {id_cliente_buscar}")
            st.info("💡 Sugerencias:")
            st.info("- Verifica que el ID esté escrito correctamente")
            st.info("- El ID debe estar en mayúsculas (ej: CL-00001)")
    else:
        st.warning("⚠️ No hay datos históricos disponibles para buscar clientes")

# ============================================================
# LISTA DE CLIENTES RECOMENDADOS
# ============================================================

if historico is not None and 'id_cliente' in historico.columns:
    with st.expander("💡 Clientes con más alertas (para pruebas)"):
        if 'prioridad' in historico.columns:
            top_clientes = historico[
                historico['prioridad'] == 'ALTA'
            ]['id_cliente'].value_counts().head(10)
            
            st.write("**Clientes con más alertas de ALTA prioridad:**")
            for cliente, count in top_clientes.items():
                st.write(f"- `{cliente}`: {count} alertas")
            
            if not top_clientes.empty:
                cliente_ejemplo = top_clientes.index[0]
                if st.button(f"🔍 Buscar {cliente_ejemplo}"):
                    st.session_state.cliente_buscado = cliente_ejemplo
                    st.rerun()
        else:
            top_clientes = historico['id_cliente'].value_counts().head(10)
            st.write("**Clientes con más registros históricos:**")
            for cliente, count in top_clientes.items():
                st.write(f"- `{cliente}`: {count} registros")

# ============================================================
# SECCIÓN DE DIAGNÓSTICO
# ============================================================

with st.expander("🔍 Ver datos cargados (diagnóstico)"):
    st.write("**Histórico:**")
    if historico is not None:
        st.write(f"- Total registros: {len(historico)}")
        if 'ejecucion_id' in historico.columns:
            st.write(f"- Ejecuciones: {historico['ejecucion_id'].nunique()}")
        if 'fecha_ejecucion' in historico.columns:
            st.write(f"- Fechas: {historico['fecha_ejecucion'].unique()}")
        st.dataframe(historico.head(10))
    else:
        st.warning("No hay histórico")
    
    st.write("**Últimos datos:**")
    st.write(f"- Total registros: {len(ultimos_datos)}")
    st.dataframe(ultimos_datos.head(10))
    
    st.write("**Inspecciones:**")
    if inspecciones is not None:
        st.write(f"- Fuente: {fuente_inspecciones}")
        st.write(f"- Total: {len(inspecciones)}")
        st.dataframe(inspecciones.head(10))
    else:
        st.warning("No hay inspecciones")
    
    st.write("**Métricas del modelo:**")
    st.json(metricas_modelo)
    
    st.write("**Estado del bucle cerrado:**")
    st.json(estado_bucle)

# ============================================================
# EVOLUCIÓN HISTÓRICA
# ============================================================

if historico is not None and 'fecha_ejecucion' in historico.columns:
    st.markdown("---")
    st.subheader("📈 Evolución Histórica de Prioridades")
    
    col1, col2 = st.columns(2)
    
    with col1:
        evolucion = historico.groupby(
            ['fecha_ejecucion', 'prioridad']
        ).size().reset_index(name='count')
        
        fig = px.line(
            evolucion,
            x='fecha_ejecucion',
            y='count',
            color='prioridad',
            title='Evolución de Prioridades por Ejecución',
            color_discrete_map={
                'ALTA': '#ff6b6b',
                'MEDIA': '#ffd93d',
                'BAJA': '#6bcb77'
            },
            markers=True
        )
        fig.update_layout(
            xaxis_title='Fecha de Ejecución (Perú)',
            yaxis_title='Número de Suministros'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        total_por_ejecucion = historico.groupby(
            'fecha_ejecucion'
        ).size().reset_index(name='total')
        
        fig = px.bar(
            total_por_ejecucion,
            x='fecha_ejecucion',
            y='total',
            title='Total de Suministros por Ejecución',
            color='total',
            color_continuous_scale='Blues'
        )
        fig.update_layout(
            xaxis_title='Fecha de Ejecución (Perú)',
            yaxis_title='Total de Suministros'
        )
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# GRÁFICOS DE LA ÚLTIMA EJECUCIÓN
# ============================================================

st.markdown("---")
st.subheader("📊 Análisis de la Última Ejecución")

col1, col2 = st.columns(2)

with col1:
    fig = px.pie(
        ultimos_datos,
        names='prioridad',
        title='Distribución de Prioridades',
        color='prioridad',
        color_discrete_map={
            'ALTA': '#ff6b6b',
            'MEDIA': '#ffd93d',
            'BAJA': '#6bcb77'
        },
        hole=0.3
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.scatter(
        ultimos_datos,
        x='probabilidad',
        y='puntaje_prioridad',
        color='prioridad',
        color_discrete_map={
            'ALTA': '#ff6b6b',
            'MEDIA': '#ffd93d',
            'BAJA': '#6bcb77'
        },
        hover_data=['id_cliente'],
        title='Probabilidad vs Puntaje de Prioridad'
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# LISTA DE INSPECCIÓN
# ============================================================

st.markdown("---")
st.subheader("📋 Lista de Inspección Priorizada")

top = ultimos_datos.nlargest(20, 'puntaje_prioridad')
st.dataframe(
    top[['id_cliente', 'probabilidad', 'puntaje_prioridad', 'prioridad']],
    use_container_width=True,
    height=400
)

col1, col2 = st.columns(2)

with col1:
    if st.button("📥 Exportar Lista Completa"):
        csv = ultimos_datos.to_csv(index=False)
        st.download_button(
            label="Descargar CSV",
            data=csv,
            file_name=f"orion_lista_inspeccion_{ahora_peru().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

with col2:
    if inspecciones is not None and not inspecciones.empty:
        st.download_button(
            label="📥 Exportar Inspecciones",
            data=inspecciones.to_csv(index=False),
            file_name=f"orion_inspecciones_{ahora_peru().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

# ============================================================
# HISTÓRICO COMPLETO
# ============================================================

if historico is not None:
    st.markdown("---")
    st.subheader("📚 Histórico Acumulado Completo")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total Registros", len(historico))
    
    with col2:
        if 'id_cliente' in historico.columns:
            st.metric("👥 Clientes Únicos", historico['id_cliente'].nunique())
    
    with col3:
        if 'ejecucion_id' in historico.columns:
            st.metric("🔄 Ejecuciones", historico['ejecucion_id'].nunique())
    
    with col4:
        if 'prioridad' in historico.columns:
            alta_hist = len(historico[historico['prioridad'] == 'ALTA'])
            st.metric("⚡ Alta Prioridad", alta_hist)
    
    with st.expander("📋 Ver histórico completo"):
        st.dataframe(historico, use_container_width=True)
        
        if st.button("📥 Exportar Histórico Completo"):
            csv = historico.to_csv(index=False)
            st.download_button(
                label="Descargar CSV",
                data=csv,
                file_name=f"orion_historico_{ahora_peru().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

# ============================================================
# ESTADÍSTICAS DEL SISTEMA
# ============================================================

st.markdown("---")
st.subheader("⚙️ Estadísticas del Sistema")

col1, col2, col3 = st.columns(3)

with col1:
    if historico is not None and 'fecha_ejecucion' in historico.columns:
        primera = historico['fecha_ejecucion'].min()
        if hasattr(primera, 'strftime'):
            fecha_str = formatear_fecha(primera, '%Y-%m-%d %H:%M')
        else:
            fecha_str = str(primera)
        st.metric("📅 Primera Ejecución", fecha_str)
    else:
        st.metric("📅 Primera Ejecución", "N/A")

with col2:
    if datos['ultima_actualizacion']:
        if hasattr(datos['ultima_actualizacion'], 'strftime'):
            fecha_str = formatear_fecha(
                datos['ultima_actualizacion'],
                '%Y-%m-%d %H:%M'
            )
        else:
            fecha_str = str(datos['ultima_actualizacion'])
        st.metric("📅 Última Ejecución", fecha_str)
    else:
        st.metric("📅 Última Ejecución", "N/A")

with col3:
    if historico is not None:
        st.metric("📊 Total Registros", len(historico))
    else:
        st.metric("📊 Total Registros", "N/A")

# ============================================================
# ESTADO DEL BUCLE CERRADO
# ============================================================

if estado_bucle:
    st.markdown("---")
    st.subheader("🔄 Estado del Bucle Cerrado")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        version = estado_bucle.get('version_actual', 'v0.0.0')
        st.metric("📦 Versión del Modelo", version)
    
    with col2:
        ultimo = estado_bucle.get('ultimo_reentrenamiento')
        if ultimo:
            try:
                fecha_retrain = datetime.fromisoformat(ultimo)
                fecha_str = formatear_fecha(fecha_retrain, '%Y-%m-%d %H:%M')
            except:
                fecha_str = str(ultimo)
            st.metric("🔄 Último Reentrenamiento", fecha_str)
        else:
            st.metric("🔄 Último Reentrenamiento", "N/A")
    
    with col3:
        total_muestras = estado_bucle.get('total_muestras', 0)
        st.metric("📊 Total Muestras", total_muestras)
    
    with col4:
        historial = estado_bucle.get('metricas_historial', [])
        st.metric("📈 Versiones", len(historial))

# ============================================================
# ACTUALIZACIÓN AUTOMÁTICA
# ============================================================

st.markdown("---")
st.caption(
    f"🌌 Orion - Detección de Hurto de Energía | v2.0.0 | "
    f"{ahora_peru().strftime('%Y-%m-%d %H:%M:%S')} (Perú)"
)

if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()