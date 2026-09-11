# 🔍 Manual del Inspector de Campo - Proyecto Orion

## Guía para Inspecciones de Hurto de Energía

**Versión:** 2.0.0
**Audiencia:** Inspectores de campo, Técnicos

---

## 📋 ÍNDICE

1. [Introducción](#introducción)
2. [¿Qué es Orion?](#qué-es-orion)
3. [Cómo Recibir tu Lista de Inspección](#cómo-recibir-tu-lista-de-inspección)
4. [Cómo Interpretar la Lista](#cómo-interpretar-la-lista)
5. [Cómo Registrar Resultados](#cómo-registrar-resultados)
6. [Tipos de Irregularidad](#tipos-de-irregularidad)
7. [Protocolo de Inspección](#protocolo-de-inspección)
8. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## 🎯 Introducción

Bienvenido al **Manual del Inspector de Campo del Proyecto Orion**. Este documento te guiará en el uso del sistema para tus inspecciones diarias.

**Objetivo:** Ayudarte a:
- Recibir tu lista de inspección priorizada
- Entender por qué cada caso fue priorizado
- Registrar resultados de manera eficiente
- Contribuir al aprendizaje del sistema

---

## 🌌 ¿Qué es Orion?

Orion es un sistema que **te ayuda a priorizar tus inspecciones**. En lugar de inspeccionar al azar, te dice:

- 🎯 **Qué clientes** inspeccionar primero
- 📊 **Por qué** son sospechosos
- 💰 **Cuánto** podrías recuperar

### ¿Cómo te ayuda?

| Antes | Con Orion |
|---|---|
| Inspecciones al azar | Inspecciones priorizadas |
| Baja tasa de éxito | Mayor tasa de éxito |
| No sabes por qué inspeccionar | Sabes por qué cada caso es sospechoso |
| Tiempo desperdiciado | Tiempo optimizado |

---

## 📥 Cómo Recibir tu Lista de Inspección

### Opción A: Google Sheets (Recomendado)

1. Recibirás un **correo** con el enlace a Google Sheets
2. Abre el enlace en tu tablet o celular
3. Verás dos pestañas:
   - **Lista de Inspección**: Los casos a inspeccionar
   - **Resultados**: Donde registrarás tus hallazgos

### Opción B: Archivo Excel

1. Recibirás un **archivo Excel** por correo
2. Descárgalo en tu dispositivo
3. Ábrelo con Excel o Google Sheets

### Opción C: Impresión en papel

1. Si no tienes acceso digital, puedes **imprimir la lista**
2. Llévala contigo en tu ruta
3. Registra los resultados al volver a la oficina

---

## 📋 Cómo Interpretar la Lista

### Columnas de la lista

| Columna | ¿Qué significa? | Ejemplo |
|---|---|---|
| **ID Cliente** | Código único del cliente | CL-00042 |
| **Dirección** | Ubicación del suministro | Av. Principal 123 |
| **Sector** | Zona geográfica | Alto Trujillo |
| **Prioridad** | Urgencia de inspección | ALTA |
| **Probabilidad** | Probabilidad de hurto | 92% |
| **Motivo** | Por qué es sospechoso | Bypass detectado + Caída de consumo |
| **CNR Estimado** | Consumo No Registrado estimado | 2,500 kWh |

### Cómo priorizar

| Prioridad | Acción |
|---|---|
| 🔴 **ALTA** | Inspeccionar **hoy** (máxima urgencia) |
| 🟡 **MEDIA** | Inspeccionar **esta semana** |
| 🟢 **BAJA** | Inspeccionar **si hay tiempo** |

### Motivos comunes

| Motivo | ¿Qué significa? |
|---|---|
| Bypass detectado | El medidor detectó un puente |
| Caída brusca | El consumo cayó repentinamente |
| Precinto roto | El precinto del medidor está manipulado |
| Reincidente | El cliente ya hurtó antes |
| Consumo anómalo | Consume mucho menos que sus pares |

---

## 📝 Cómo Registrar Resultados

### En Google Sheets

1. Abre la pestaña **Resultados**
2. Busca el **ID del cliente** que inspeccionaste
3. Completa las columnas:

| Columna | ¿Qué registrar? | Ejemplo |
|---|---|---|
| **Fecha Inspección** | Fecha de la visita | 10/09/2026 |
| **Resultado** | Hallazgo | Hurto Confirmado |
| **Tipo Irregularidad** | Tipo de hurto | Bypass |
| **Descripción** | Detalles del hallazgo | Puente en base socket |
| **CNR Estimado** | kWh no registrados | 2,500 |
| **Monto Recuperar** | S/ a recuperar | 2,125.00 |
| **Inspector** | Tu nombre | Juan Pérez |
| **Observaciones** | Notas adicionales | Cliente cooperó |

### Valores permitidos

**Resultado:**
- ✅ **Hurto Confirmado** → Encontraste hurto
- ⚠️ **Anomalía** → Algo raro pero no hurto claro
- ❌ **Normal** → Todo en orden
- 🔍 **Falso Positivo** → El sistema se equivocó

**Tipo Irregularidad:**
- **Bypass** → Puente en el medidor
- **Cable Rajado** → Derivación antes del medidor
- **Manipulación Medidor** → Medidor alterado
- **Conexión Clandestina** → Conexión directa a red
- **Auto-reconexión** → Reconexión tras corte
- **N/A** → No aplica

### En Excel

1. Abre el archivo Excel
2. Ve a la hoja **Resultados**
3. Completa las mismas columnas
4. Envía el archivo por correo al coordinador

### En papel

1. Completa el formato impreso
2. Entrega al coordinador al volver a la oficina
3. El coordinador lo digitalizará

---

## 🔧 Tipos de Irregularidad

### 1. Bypass (Puente)

| Aspecto | Descripción |
|---|---|
| **¿Qué es?** | Puente en la base del medidor que evita la medición |
| **¿Cómo detectarlo?** | Cables adicionales, marcas de manipulación |
| **CNR típico** | 2,000 - 4,000 kWh/mes |
| **Riesgo** | Alto (puede causar incendios) |

### 2. Cable Rajado

| Aspecto | Descripción |
|---|---|
| **¿Qué es?** | Derivación antes del medidor |
| **¿Cómo detectarlo?** | Cables pelados, conexiones precarias |
| **CNR típico** | 800 - 1,500 kWh/mes |
| **Riesgo** | Medio-alto |

### 3. Manipulación del Medidor

| Aspecto | Descripción |
|---|---|
| **¿Qué es?** | Alteración de la medición |
| **¿Cómo detectarlo?** | Precinto roto, medidor abierto, marcas |
| **CNR típico** | 1,000 - 2,500 kWh/mes |
| **Riesgo** | Medio |

### 4. Conexión Clandestina

| Aspecto | Descripción |
|---|---|
| **¿Qué es?** | Conexión directa a la red sin medidor |
| **¿Cómo detectarlo?** | Cables directos, sin medidor |
| **CNR típico** | 3,000 - 8,000 kWh/mes |
| **Riesgo** | Muy alto |

### 5. Auto-reconexión

| Aspecto | Descripción |
|---|---|
| **¿Qué es?** | Cliente cortado que se reconectó ilegalmente |
| **¿Cómo detectarlo?** | Servicio cortado pero con consumo |
| **CNR típico** | 500 - 1,500 kWh/mes |
| **Riesgo** | Medio |

---

## 🛠️ Protocolo de Inspección

### Antes de la inspección

1. **Revisa la lista** de inspección del día
2. **Planifica la ruta** por zona (optimiza tiempo)
3. **Lleva el equipo**: multímetro, herramientas, cámara
4. **Verifica la seguridad**: casco, guantes, chaleco

### Durante la inspección

1. **Identifícate** con el cliente
2. **Explica el motivo** de la inspección
3. **Revisa el medidor**:
   - ¿Está el precinto intacto?
   - ¿Hay cables adicionales?
   - ¿El medidor está alterado?
4. **Toma fotos** del hallazgo
5. **Registra los datos** en el sistema

### Después de la inspección

1. **Completa el registro** en Google Sheets o Excel
2. **Reporta irregularidades** al coordinador
3. **Toma medidas** si hay riesgo (corte, denuncia)

### Medidas de seguridad

| Situación | Acción |
|---|---|
| Bypass detectado | **NO tocar**, llamar a soporte técnico |
| Cables pelados | **NO tocar**, alejarse |
| Cliente agresivo | Retirarse, reportar a seguridad |
| Riesgo de incendio | Llamar a bomberos |

---

## ❓ Preguntas Frecuentes

### ¿Qué hago si el cliente no está?

**Respuesta:** Registra como **"No se encontró"** y continúa con el siguiente.

### ¿Qué hago si el cliente se niega a la inspección?

**Respuesta:**
1. Explica que es un procedimiento rutinario
2. Si insiste, registra como **"Rechazó inspección"**
3. Reporta al coordinador

### ¿Cómo calculo el CNR?

**Respuesta:** El CNR se calcula así:
CNR = (Consumo esperado - Consumo registrado) × Días


**Ejemplo:**
- Consumo esperado: 300 kWh/mes
- Consumo registrado: 100 kWh/mes
- CNR = (300 - 100) = 200 kWh/mes

### ¿Qué hago si encuentro un hurto?

**Respuesta:**
1. **NO tocar** la instalación
2. **Tomar fotos** del hallazgo
3. **Registrar** en el sistema como "Hurto Confirmado"
4. **Reportar** al coordinador
5. **Aplicar** el protocolo de corte

### ¿Puedo inspeccionar sin la lista de Orion?

**Respuesta:** Sí, pero perderás la priorización. Orion te ayuda a **optimizar tu tiempo** y aumentar tu **tasa de éxito**.

### ¿Cómo sé que el sistema no me está mintiendo?

**Respuesta:** Orion **no te miente**, solo te **prioriza**. El sistema explica por qué cada caso es sospechoso:

- **Bypass detectado** → Hay evidencia física
- **Caída brusca** → El consumo cayó
- **Reincidente** → Ya hurtó antes

### ¿Qué pasa si registro un falso positivo?

**Respuesta:** Es **muy importante** que lo registres. Así el sistema aprende y mejora.

### ¿Cuántas inspecciones hago al día?

**Respuesta:** Depende de la zona y la complejidad, pero se recomienda:
- Zona urbana: 8-10 inspecciones
- Zona rural: 4-6 inspecciones

### ¿Qué hago si me equivoco al registrar?

**Respuesta:** Corrige el registro en Google Sheets. El sistema actualizará automáticamente.

---

## 📞 Contacto y Soporte

| Problema | Contacto |
|---|---|
| Problemas técnicos | Soporte técnico |
| Problemas de ruta | Coordinador |
| Problemas de seguridad | Seguridad |
| Dudas del sistema | Analista de datos |

---

## 📄 Formato de Registro (Papel)

Si trabajas con papel, usa este formato:
┌─────────────────────────────────────────────────────────────────┐
│ REGISTRO DE INSPECCIÓN - ORION │
├─────────────────────────────────────────────────────────────────┤
│ │
│ Fecha: ___________ Inspector: _________________________ │
│ │
│ ┌────────────┬────────────┬────────────┬────────────────────┐ │
│ │ ID Cliente │ Resultado │ Tipo │ CNR Estimado │ │
│ ├────────────┼────────────┼────────────┼────────────────────┤ │
│ │ │ │ │ │ │
│ │ │ │ │ │ │
│ │ │ │ │ │ │
│ │ │ │ │ │ │
│ └────────────┴────────────┴────────────┴────────────────────┘ │
│ │
│ Observaciones: │
│ ________________________________________________________ │
│ ________________________________________________________ │
│ │
│ Firma: _______________________ │
│ │
└─────────────────────────────────────────────────────────────────┘


---

## 🎯 Resumen

### Flujo de trabajo diario

Recibir lista de inspección (Google Sheets / Excel / Papel)

Planificar ruta por zonas

Inspeccionar casos (prioridad ALTA primero)

Registrar resultados en el sistema

Reportar irregularidades

Repetir al día siguiente



### Claves del éxito

| Clave | Descripción |
|---|---|
| 🎯 **Prioriza** | Empieza por los casos de ALTA prioridad |
| 📝 **Registra** | Completa todos los campos |
| 📸 **Documenta** | Toma fotos de los hallazgos |
| 🔒 **Seguridad** | No toques instalaciones peligrosas |
| 🤝 **Reporta** | Informa irregularidades al coordinador |

---

🌌 **Orion: De los Datos a la Acción** 🌌

**¡Gracias por tu trabajo! Tu esfuerzo ayuda a recuperar energía y proteger a la empresa.**