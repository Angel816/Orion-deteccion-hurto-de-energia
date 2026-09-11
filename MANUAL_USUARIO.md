# 📘 Manual de Usuario - Proyecto Orion

## Sistema de Detección de Hurto de Energía

**Versión:** 2.0.0
**Última actualización:** Septiembre 2026
**Audiencia:** Analistas, Coordinadores, Gerentes

---

## 📋 ÍNDICE

1. [Introducción](#introducción)
2. [¿Qué es Orion?](#qué-es-orion)
3. [Cómo Acceder al Dashboard](#cómo-acceder-al-dashboard)
4. [Interpretación de Métricas](#interpretación-de-métricas)
5. [Uso del Buscador de Clientes](#uso-del-buscador-de-clientes)
6. [Lista de Inspección](#lista-de-inspección)
7. [Histórico Acumulado](#histórico-acumulado)
8. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## 🎯 Introducción

Bienvenido al **Manual de Usuario del Proyecto Orion**. Este documento te guiará paso a paso en el uso del sistema de detección y priorización de hurto de energía.

**Objetivo:** Ayudarte a interpretar las métricas, usar el dashboard y tomar decisiones basadas en datos.

---

## 🌌 ¿Qué es Orion?

Orion es un sistema que:

1. **Analiza** datos de consumo, alarmas y facturación
2. **Detecta** suministros con alta probabilidad de hurto
3. **Prioriza** las inspecciones por impacto económico
4. **Aprende** continuamente de los resultados de campo

### Beneficios

| Beneficio | Descripción |
|---|---|
| 🎯 Enfoque | Concentra esfuerzos en casos de mayor impacto |
| ⏱️ Rapidez | Identifica casos sospechosos en minutos |
| 💰 Rentabilidad | Maximiza el ROI de las inspecciones |
| 📊 Transparencia | Explica por qué cada caso fue priorizado |

---

## 🚀 Cómo Acceder al Dashboard

### Paso 1: Iniciar el sistema

**Opción A: Script automático (Windows)**
1. Doble clic en `ejecutar_todo.bat`
2. Seleccionar opción **7** (Ver dashboard)

**Opción B: Manual**
```powershell
# 1. Configurar encoding
$env:PYTHONIOENCODING="utf-8"

# 2. Activar entorno
.\.venv\Scripts\Activate.ps1

# 3. Iniciar dashboard
streamlit run scripts\tablero_orion.py

Paso 2: Abrir en el navegador
El dashboard se abrirá automáticamente en:

text
http://localhost:8501
Paso 3: Navegar por el dashboard
El dashboard tiene estas secciones:

Sección	Descripción
📊 Resumen Acumulado	KPIs globales del sistema
📈 Distribución	Gráfico de prioridades
🧠 Métricas del Modelo	Accuracy, Precision, Recall, F1
💰 Métricas de Negocio	Recuperación, Costo, ROI
🔍 Buscador de Clientes	Buscar historial de un cliente
📋 Lista de Inspección	Top 20 casos priorizados
📚 Histórico	Todas las ejecuciones
📊 Interpretación de Métricas
Métricas del Modelo
Métrica	¿Qué significa?	Valor Ideal
Accuracy	Precisión general del modelo	> 85%
Precision	De los marcados como hurto, ¿cuántos lo son?	> 80%
Recall	De los hurtos reales, ¿cuántos detectamos?	> 75%
F1-Score	Media armónica de Precision y Recall	> 80%
ROC-AUC	Capacidad de discriminación	> 0.85
Métricas de Negocio
Métrica	¿Qué significa?	Valor Ideal
Tasa de Éxito	Inspecciones que confirman hurto	> 20%
Recuperación	Monto recuperado (S/)	Máximo posible
Costo Total	Costo de inspecciones (S/)	Mínimo posible
ROI	Retorno de inversión	> 50%
Rentabilidad	Recuperación - Costo (S/)	> 0
Ejemplo de Interpretación
text
📊 Métricas del Modelo
🎯 Accuracy:  87.5%  → El modelo acierta en 87.5% de los casos
📊 Precision: 82.3%  → De los marcados como hurto, 82.3% lo son
📈 Recall:    78.9%  → De los hurtos reales, 78.9% son detectados
⚡ F1-Score:  80.5%  → Balance entre Precision y Recall

💰 Métricas de Negocio
✅ Tasa de Éxito: 25.3%  → 1 de cada 4 inspecciones confirma hurto
💰 Recuperación:  S/ 45,230.50
💸 Costo Total:   S/ 3,420.00
📈 ROI:           1,222.5%  → Por cada S/ 1 invertido, se recuperan S/ 12.22
🔍 Uso del Buscador de Clientes
¿Para qué sirve?
Para ver el historial completo de un cliente específico.

Cómo usarlo
En el dashboard, busca la sección 🔍 Buscar Historial de Cliente

Escribe el ID del cliente (ej: CL-00001)

Haz clic en 🔍 Buscar

¿Qué muestra?
Métrica	Descripción
Total Registros	Cuántas veces apareció en el histórico
Alertas Altas	Cuántas veces fue prioridad ALTA
Puntaje Máximo	Su puntaje más alto de priorización
Última Actualización	Cuándo fue la última vez que apareció
Gráfico de Evolución
Muestra cómo ha evolucionado el puntaje de prioridad del cliente a lo largo del tiempo.

Interpretación:

Patrón	Significado
📈 Puntaje subiendo	El cliente se está volviendo más sospechoso
📉 Puntaje bajando	El cliente se ha regularizado
➡️ Puntaje estable	Comportamiento consistente
🔄 Puntaje oscilante	Comportamiento irregular
📋 Lista de Inspección
¿Qué es?
Una lista priorizada de los suministros que deben ser inspeccionados.

¿Cómo se genera?
El modelo calcula la probabilidad de hurto de cada cliente

Se combina con el impacto económico y el historial

Se ordena por puntaje de prioridad

Columnas de la lista
Columna	Descripción
id_cliente	ID del cliente
probabilidad	Probabilidad de hurto (0-1)
puntaje_prioridad	Score final (0-1)
prioridad	ALTA, MEDIA o BAJA
Cómo usar la lista
Prioridad ALTA → Inspeccionar primero

Prioridad MEDIA → Inspeccionar después

Prioridad BAJA → Monitorear

Exportar la lista
Haz clic en 📥 Exportar Lista Completa

Se descargará un archivo CSV

Compártelo con el equipo de inspección

📚 Histórico Acumulado
¿Qué es?
Un registro de todas las ejecuciones del sistema.

¿Qué muestra?
Métrica	Descripción
Total Registros	Total de registros acumulados
Clientes Únicos	Cuántos clientes distintos aparecen
Ejecuciones	Cuántas veces se ejecutó el pipeline
Alta Prioridad	Total de casos de alta prioridad
¿Para qué sirve?
Análisis de tendencias: Ver cómo evoluciona el sistema

Auditoría: Verificar decisiones pasadas

Reincidencia: Identificar clientes problemáticos

Mejora continua: Validar el modelo

❓ Preguntas Frecuentes
¿Cada cuánto se actualiza el dashboard?
Respuesta: Cada vez que se ejecuta el pipeline diario (6:00 AM por defecto).

¿Puedo cambiar los umbrales de prioridad?
Respuesta: Sí, se pueden ajustar en configuracion/desarrollo.yaml.

¿Qué hago si veo un cliente sospechoso?
Respuesta:

Buscar su historial en el dashboard

Revisar las métricas (probabilidad, impacto, historial)

Incluirlo en la lista de inspección

¿Cómo sé si el modelo está funcionando bien?
Respuesta: Revisa las métricas del modelo:

Accuracy > 85%

F1-Score > 80%

Tasa de Éxito > 20%

¿Qué hago si el ROI es bajo?
Respuesta: Puede significar:

Muchos falsos positivos → Ajustar umbral

Costos altos → Revisar proceso de inspección

Recuperación baja → Mejorar estimación de CNR

¿Dónde reporto un problema?
Respuesta: En el repositorio de GitHub:

text
https://github.com/Angel816/Orion-deteccion-hurto-de-energia/issues
📞 Contacto y Soporte
Canal	Descripción
Repositorio	GitHub
Issues	Reportar problemas
Documentación	LEEME.md
📄 Glosario
Término	Definición
CNR	Consumo No Registrado
ROI	Retorno de Inversión
Accuracy	Precisión general del modelo
Precision	De los marcados como hurto, ¿cuántos lo son?
Recall	De los hurtos reales, ¿cuántos detectamos?
F1-Score	Media armónica de Precision y Recall
Puntaje de Prioridad	Score final para ordenar inspecciones
🌌 Orion: De los Datos a la Acción 🌌

