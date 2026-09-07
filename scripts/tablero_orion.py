# scripts/tablero_orion.py
"""
Dashboard de Orion para monitoreo y visualización
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.priorizacion.fase1_simple import PuntuadorSimple

st.set_page_config(page_title="🌌 Orion - Monitoreo", page_icon="🌌", layout="wide")

def generar_datos_demo():
    np.random.seed(42)
    n = 200
    data = pd.DataFrame({
        'id_cliente': [f'CL_{i:04d}' for i in range(n)],
        'consumo_promedio': np.random.uniform(50, 500, n),
        'total_alarmas': np.random.randint(0, 10, n),
        'inspecciones_previas': np.random.randint(0, 5, n)
    })
    probabilidades = np.random.uniform(0, 1, n)
    puntuador = PuntuadorSimple()
    return puntuador.calcular_puntajes(data, probabilidades)

st.sidebar.title("🌌 Orion")
st.sidebar.markdown("---")
st.sidebar.caption(f"v1.0.0 | {datetime.now().strftime('%H:%M')}")

datos = generar_datos_demo()

st.title("🌌 Orion - Monitoreo Continuo")
st.markdown("### Sistema de Detección y Priorización de Hurto de Energía")
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📊 Total Suministros", len(datos))
with col2:
    alta = len(datos[datos['prioridad'] == 'ALTA'])
    st.metric("⚡ Alta Prioridad", alta, delta=f"{alta/len(datos)*100:.1f}%")
with col3:
    media = len(datos[datos['prioridad'] == 'MEDIA'])
    st.metric("📊 Media Prioridad", media, delta=f"{media/len(datos)*100:.1f}%")
with col4:
    baja = len(datos[datos['prioridad'] == 'BAJA'])
    st.metric("📉 Baja Prioridad", baja, delta=f"{baja/len(datos)*100:.1f}%")

st.markdown("---")
st.subheader("📈 Distribución de Prioridades")

col1, col2 = st.columns(2)

with col1:
    fig = px.bar(
        datos['prioridad'].value_counts().reset_index(),
        x='prioridad', y='count',
        color='prioridad',
        color_discrete_map={'ALTA': '#ff6b6b', 'MEDIA': '#ffd93d', 'BAJA': '#6bcb77'}
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.scatter(
        datos, x='probabilidad', y='puntaje_prioridad',
        color='prioridad',
        color_discrete_map={'ALTA': '#ff6b6b', 'MEDIA': '#ffd93d', 'BAJA': '#6bcb77'},
        hover_data=['id_cliente']
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.subheader("📋 Lista de Inspección Priorizada")

top = datos.nlargest(20, 'puntaje_prioridad')
st.dataframe(top[['id_cliente', 'probabilidad', 'puntaje_prioridad', 'prioridad']], use_container_width=True)

if st.button("📥 Exportar Lista Completa"):
    csv = datos.to_csv(index=False)
    st.download_button(
        label="Descargar CSV",
        data=csv,
        file_name=f"orion_lista_inspeccion_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

st.markdown("---")
st.caption("🌌 Orion - Detección de Hurto de Energía")