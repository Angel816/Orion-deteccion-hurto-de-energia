# 🌌 Proyecto Orion

## Sistema Integral de Detección y Priorización de Hurto de Energía Eléctrica

### De los Datos a la Acción con Closed Loop

![Versión](https://img.shields.io/badge/versión-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![Licencia](https://img.shields.io/badge/licencia-MIT-yellow)

---

## 📋 ÍNDICE

1. [Descripción General](#descripción-general)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Estructura del Proyecto](#estructura-del-proyecto)
4. [Instalación](#instalación)
5. [Uso Rápido](#uso-rápido)
6. [Flujos de Trabajo](#flujos-de-trabajo)
7. [Variables del Modelo](#variables-del-modelo)
8. [API REST](#api-rest)
9. [GitHub Actions](#github-actions)
10. [Configuración Regional](#configuración-regional)
11. [Solución de Problemas](#solución-de-problemas)
12. [Roadmap](#roadmap)

---

## 🎯 Descripción General

**Orion** es un sistema integral que transforma datos históricos y operativos en acciones concretas para detectar, priorizar y recuperar energía hurtada en redes eléctricas.

### Objetivos del Proyecto

| Objetivo | Métrica de Éxito |
|----------|------------------|
| **Detectar** suministros con alta probabilidad de hurto | Precisión > 85% |
| **Priorizar** inspecciones por impacto económico | Top 100 > 95% de acierto |
| **Recuperar** energía no registrada | CNR > 80% del estimado |
| **Prevenir** reincidencia | Reducción > 30% |

### Enfoque: Dato → Acción → Aprendizaje
┌─────────────────────────────────────────────────────────────────────────────┐
│ DATO → ACCIÓN → APRENDIZAJE │
├─────────────────────────────────────────────────────────────────────────────┤
│ │
│ 🔍 DETECCIÓN 🎯 PRIORIZACIÓN 🛠️ INSPECCIÓN ⚖️ RECUPERACIÓN │
│ (Machine (Scoring (Campo (CNR + │
│ Learning) + Fases) + SHAP) Recupero) │
│ │
│ 🔄 CLOSED LOOP │
│ (Feedback → Reentrenamiento → Mejora Continua) │
│ │
└─────────────────────────────────────────────────────────────────────────────┘

### Inspiración del Nombre: Orion

**Orion** (la constelación del cazador) simboliza:

| Elemento | Significado para el Proyecto |
|---|---|
| 🏹 El cazador | El equipo que detecta el hurto |
| ⭐ Tres estrellas del cinturón | Detección → Priorización → Recuperación |
| 👁️ Visión privilegiada | Datos que iluminan anomalías |
| 🛡️ El escudo | Prevención y closed loop |

---

## 🏗️ Arquitectura del Sistema

### Diagrama de Alto Nivel
┌─────────────────────────────────────────────────────────────────────────────┐
│ ARQUITECTURA ORION v2.0 │
├─────────────────────────────────────────────────────────────────────────────┤
│ │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │ 1. CAPA DE DATOS │ │
│ │ ▶ Ingesta incremental ▶ Validación ▶ Normalización ▶ Limpieza │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
│ ↓ │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │ 2. PIPELINE DE DATOS │ │
│ │ ▶ Feature Engineering causal ▶ Almacenamiento en Parquet │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
│ ↓ │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │ 3. MODELO DE DETECCIÓN │ │
│ │ ▶ Random Forest / XGBoost ▶ SHAP Explainability ▶ Umbral Dinámico│ │
│ └─────────────────────────────────────────────────────────────────────┘ │
│ ↓ │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │ 4. PRIORIZACIÓN │ │
│ │ ▶ Score Simple ▶ Active Learning ▶ Análisis de Reincidencia │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
│ ↓ │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │ 5. CAPA DE PRESENTACIÓN │ │
│ │ ▶ API FastAPI ▶ Dashboard Streamlit ▶ Google Sheets │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
│ ↓ │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │ 6. CLOSED LOOP │ │
│ │ ▶ Feedback ▶ Backtesting ▶ Reentrenamiento ▶ Alertas │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘

### Stack Tecnológico

| Capa | Tecnología | Versión | Propósito |
|---|---|---|---|
| Lenguaje | Python | 3.10+ | Desarrollo principal |
| Data | pandas, numpy | 2.0+, 1.24+ | Análisis de datos |
| ML | scikit-learn, xgboost, lightgbm | 1.3+, 2.0+, 4.0+ | Modelos de detección |
| Explicabilidad | SHAP | 0.42+ | Explicación de predicciones |
| API | FastAPI, uvicorn | 0.100+, 0.23+ | Servicio REST |
| Dashboard | Streamlit, Plotly | 1.25+, 5.17+ | Visualización |
| Inspección | gspread | 5.12+ | Google Sheets |
| Utilidades | loguru, pyyaml, dotenv | - | Logs, config |

---

## 📂 Estructura del Proyecto

---

## 🚀 Instalación

### Requisitos Previos

| Requisito | Versión Mínima |
|---|---|
| Python | 3.10+ |
| Git | 2.30+ |
| Sistema Operativo | Windows, Linux, Mac |

### Paso 1: Clonar el repositorio

```bash
git clone https://github.com/Angel816/Orion-deteccion-hurto-de-energia.git
cd Orion-deteccion-hurto-de-energia

###
### Paso 2: Crear entorno virtual

Windows:

powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
Linux/Mac:


python -m venv .venv
source .venv/bin/activate
## Paso 3: Instalar dependencias

pip install --upgrade pip
pip install -r requirements.txt
Paso 4: Verificar instalación

python -c "import pandas, numpy, sklearn, fastapi, streamlit; print('✅ Todo OK')"