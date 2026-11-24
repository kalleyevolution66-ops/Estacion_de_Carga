# Bitácora de Proyecto: Estación de Carga de Vehículos Eléctricos
**Curso:** Fundamentos de Programación - Ingeniería Energética  
**Rol:** Operador y Desarrollador de la Estación de Carga  
**Fecha de Inicio:** 21 de noviembre de 2026  

---

## 📋 Guía y Reglas de Trabajo del Proyecto

> **Reglas Obligatorias de Desarrollo:**
>
> 1. **Registro en BITACORA.md (sin contaminar el código de la app):** Todo prompt importante, decisión de diseño o cambio relevante debe quedar asentado en `BITACORA.md` (con fecha, contexto y resumen), manteniendo el código de la aplicación limpio y libre de notas o bitácoras incrustadas.
> 2. **Explicación antes de aplicar código:** No asumir la aceptación de código no comprendido. Cuando se proponga lógica nueva o cambios relevantes, explicar de forma clara y breve (qué hace, por qué se usa y cómo encaja) antes de darlo por cerrado.
> 3. **Preparación para cambios en vivo (sustentación):** Estructurar el código de forma modular y con parámetros claros (umbrales, colores, datos). En cada modificación, indicar dónde está el cambio (archivo, función o variable) y por qué afecta el comportamiento, para poder responder o ajustar en vivo durante la sustentación.
> 4. **Interfaz visual con Streamlit (o Tkinter):** Usar Streamlit como opción visual recomendada, o Tkinter si se busca evitar instalaciones externas. Guiar paso a paso con ejemplos claros y explicaciones de cómo funcionan sus elementos principales.

---

## 🎯 Definición del Problema y Objetivos de Ingeniería Energética

Una estación de carga rápida/semirrápida cuenta con un conjunto de cargadores ($N$ cargadores, configurable de 1 a 6). Los vehículos eléctricos (VE) arriban a lo largo del día con distintas demandas energéticas expresadas en kilovatios-hora ($\text{kWh}$).

### Variables Físicas y Matemáticas:
- **Potencia del cargador ($P$):** En $\text{kW}$. La tasa de transferencia de energía.
- **Tiempo de carga ($\Delta t$):** Relación energética fundamental:
  $$\Delta t = \frac{E_{\text{solicitada}}}{P} = \frac{\text{kWh}}{\text{kW}} \quad [\text{horas}]$$
- **Regla de Asignación (Despacho FIFO por disponibilidad):**
  1. Orden de llegada de los vehículos.
  2. Asignación al cargador que se desocupa primero.
  3. En caso de empate en tiempo de liberación, desempate por el de menor identificador numérico (Cargador 1 antes que Cargador 2).
- **Cálculo de Tiempos:**
  - $\text{Hora Inicio} = \max(\text{Hora Llegada}, \text{Hora Liberación Cargador})$
  - $\text{Tiempo de Espera} = \text{Hora Inicio} - \text{Hora Llegada}$
  - $\text{Hora Fin} = \text{Hora Inicio} + \Delta t$
- **Indicadores Económicos y Energéticos:**
  - $\text{Energía Total Vendida} = \sum \text{kWh}_i$
  - $\text{Ingresos Totales} = \text{Energía Total} \times \text{Precio por kWh}$
  - $\text{Espera Total} = \sum \text{Espera}_i$
- **Reto Funcional (Pico de Demanda / Máxima Ocupación):**
  - Determinar el intervalo horario de máxima concurrencia de cargadores ocupados simultáneamente y el porcentaje de ocupación pico.

---

## 🧪 Caso de Verificación Oficial (Benchmark)

- **Parámetros:** 2 cargadores de $10\text{ kW}$, Precio: $\$1\,500/\text{kWh}$.
- **Flota de prueba:**
  - Vehículo A: Llega $8\text{ h}$, $20\text{ kWh}$ ($\Delta t = 2\text{ h}$).
  - Vehículo B: Llega $8\text{ h}$, $10\text{ kWh}$ ($\Delta t = 1\text{ h}$).
  - Vehículo C: Llega $9\text{ h}$, $30\text{ kWh}$ ($\Delta t = 3\text{ h}$).
  - Vehículo D: Llega $9\text{ h}$, $10\text{ kWh}$ ($\Delta t = 1\text{ h}$).

### Resultado Esperado:
- **Vehículo A:** Cargador 1, de $8:00$ a $10:00\text{ h}$ (Espera: $0\text{ h}$).
- **Vehículo B:** Cargador 2, de $8:00$ a $9:00\text{ h}$ (Espera: $0\text{ h}$).
- **Vehículo C:** Cargador 2, de $9:00$ a $12:00\text{ h}$ (Espera: $0\text{ h}$).
- **Vehículo D:** Cargador 1, de $10:00$ a $11:00\text{ h}$ (Espera: $1\text{ h}$).
- **Totales:**
  - Espera total: $1.0\text{ hora}$.
  - Energía total vendida: $70\text{ kWh}$.
  - Ingresos: $\$105\,000$.
  - Hora de mayor ocupación: de $8:00$ a $11:00\text{ h}$ (2 cargadores activos simultáneamente = $100\%$ de ocupación).

---

## 🛠️ Estructura Modular del Proyecto

1. **`datos/entrada.json`**: Datos de entrada en formato estándar JSON.
2. **`simulador.py`**: Motor de simulación puro basado en listas, matrices, funciones `def`, ciclos `for`/`while`, condicionales `if`/`elif`, `f-strings` y `json`.
3. **`test_simulador.py`**: Suite de validación automática que verifica el caso benchmark, la hora pico, las tarjetas y las validaciones.
4. **`app.py`**: Interfaz web interactiva en Streamlit.
5. **`app_tkinter.py`**: Interfaz de escritorio equivalente en Tkinter (sin clases).
6. **`LEEME.txt`**: Instrucciones rápidas de ejecución y resumen del reto funcional.

---

## 📝 Registro de Prompts y Decisiones de Diseño

### Registro #1 al #10
- Configuración inicial, motor de despacho FIFO, pruebas unitarias, rediseño SCADA con aguja temporal en Gantt, registro interactivo de vehículos, eliminación de parpadeo en Tkinter, soporte multi-estación y fix de `ValueError` con `int(h_tick)` en `app.py`.

### Registro #11 — Refactorización a Herramientas Básicas de Python y Validación Completa (Rúbrica PDF)
- **Fecha:** 24-11-2026
- **Contexto:** Solicitud del usuario para mantener toda la lógica de la página usando exclusivamente las herramientas vistas en clase (`if`, `elif`, `for`, `while`, `and`, `or`, `matrices`, `listas`, `def`, `f"..."` string y `JSON`) teniendo en cuenta todos los criterios del PDF.
- **Decisión y Cambios Aplicados:**
  1. **Uso estricto de listas y matrices en `simulador.py`:** Se eliminaron `class`, `lambda`, comprensiones de listas/diccionarios, `sorted(..., key=...)`, `min(..., key=...)` y anotaciones de tipos avanzadas. Toda la información de estaciones, vehículos, asignaciones, estados por bahía y curva de ocupación se almacena en **listas** y **matrices** (listas de listas).
  2. **Ordenamiento FIFO manual (`ordenar_vehiculos`):** Se implementó ordenamiento con ciclos `for` anidados e `if`/`or`/`and` por hora de llegada y placa.
  3. **Validaciones robustas (Criterio D de la Rúbrica):** Se agregaron `validar_datos_json()`, `validar_vehiculo()`, `validar_estacion()` y `validar_cargadores()` para detectar sin romper el programa: `kWh <= 0`, `potencia <= 0`, `cargadores <= 0`, o `llegada < 0 or llegada > 23`.
  4. **Guardado y descarga de JSON:** Se agregaron `guardar_datos()` (`datos/salida.json`) y `exportar_json_texto()` en `simulador.py`, conectados a botones de guardado y descarga en `app.py` y `app_tkinter.py`.
  5. **Interfaz `app.py` y `app_tkinter.py` y pruebas `test_simulador.py`:** Se refactorizaron sin `class`, sin `lambda` y sin comprensiones, manteniendo exactamente el diseño SCADA, la aguja temporal del Gantt, el soporte multi-estación y el caso benchmark oficial.

### Prompt 15
- **Fecha y Hora:** 2026-11-24 14:19:32
- **Texto original:**
```text
Bien. Necesito que mantengas la logica del codigo pero que solo uses
-  if
-  elif
-  for
-  while
-  and
-  or
-  matrices
-  listas
-  def
-  f" string
-  JSON
```

### Prompt 16
- **Fecha y Hora:** 2026-11-24 14:24:24
- **Texto original:**
```text
Bien. Necesito que mantengas la logica del codigo pero que solo uses
-   if
-   elif
-   for
-   while
-   and
-   or
-   matrices
-   listas
-   def
-   f" string
-   JSON
```

### Prompt 17
- **Fecha y Hora:** 2026-11-24 14:25:27
- **Texto original:**
```text
Bien. Necesito que mantengas la logica del codigo pero que solo uses
-    if
-    elif
- else
-    for
-    while
-    and
-    or
-    matrices
-    listas
-    def
-    f" string
-    JSON
```

### Prompt 18
- **Fecha y Hora:** 2026-11-24 14:29:18
- **Texto original:**
```text
en que lugar del computador lo estad guardando por que no lo encuentro
```
