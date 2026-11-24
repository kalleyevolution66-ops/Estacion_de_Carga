"""
simulador.py
------------
Motor de simulación y lógica energética para la estación de carga.
Implementado exclusivamente con las estructuras básicas de Python:
if, elif, for, while, and, or, listas, matrices, def, f-strings y json.
"""

import json

# ==============================================================================
# PARÁMETROS GLOBALES AJUSTABLES EN SUSTENTACIÓN
# ==============================================================================
UMBRAL_ALERTA_ESPERA_HORAS = 1.0  # Alerta si espera >= este umbral (horas)


# ==============================================================================
# FUNCIONES DE VALIDACIÓN DE DATOS
# ==============================================================================
def validar_datos_json(datos_json):
    """
    Valida que un objeto cargado desde JSON tenga la estructura y valores válidos:
    - Campos obligatorios: estacion, potencia, precio, vehiculos
    - potencia > 0 y precio > 0
    - Cada vehículo con placa, llegada entre 0 y 23, y kwh > 0
    Retorna una lista de mensajes de error (vacía si todo es válido).
    """
    errores = []

    if "estacion" not in datos_json or "potencia" not in datos_json or "precio" not in datos_json or "vehiculos" not in datos_json:
        errores.append("Faltan campos obligatorios en el JSON (estacion, potencia, precio, vehiculos).")
        return errores

    if str(datos_json["estacion"]).strip() == "":
        errores.append("El nombre de la estación no puede estar vacío.")

    potencia = float(datos_json["potencia"])
    precio = float(datos_json["precio"])

    if potencia <= 0:
        errores.append(f"La potencia ({potencia} kW) debe ser mayor a 0.")
    if precio <= 0:
        errores.append(f"El precio ({precio}) debe ser mayor a 0.")

    vehiculos_raw = datos_json["vehiculos"]
    for i in range(len(vehiculos_raw)):
        v = vehiculos_raw[i]
        if "placa" not in v or "llegada" not in v or "kwh" not in v:
            errores.append(f"Al vehículo #{i + 1} le faltan campos obligatorios (placa, llegada, kwh).")
        elif "placa" in v and "llegada" in v and "kwh" in v:
            placa = str(v["placa"]).strip()
            llegada = float(v["llegada"])
            kwh = float(v["kwh"])
            if placa == "":
                errores.append(f"El vehículo #{i + 1} tiene una placa vacía.")
            if llegada < 0 or llegada > 23:
                errores.append(f"El vehículo '{placa}' tiene llegada {llegada} h fuera del rango 0 a 23 h.")
            if kwh <= 0:
                errores.append(f"El vehículo '{placa}' tiene energía {kwh} kWh no positiva (debe ser > 0).")

    return errores


def validar_vehiculo(placa, llegada, kwh):
    """
    Valida los datos de un vehículo antes de agregarlo a la fila.
    Retorna una lista de mensajes de error (vacía si todo es válido).
    """
    errores = []
    if str(placa).strip() == "":
        errores.append("La placa del vehículo es obligatoria.")
    if float(llegada) < 0 or float(llegada) > 23:
        errores.append(f"La hora de llegada ({llegada} h) debe estar entre 0 y 23 h.")
    if float(kwh) <= 0:
        errores.append(f"La energía requerida ({kwh} kWh) debe ser mayor a 0.")
    return errores


def validar_estacion(nombre, potencia, precio):
    """
    Valida los parámetros de una estación antes de crearla.
    Retorna una lista de mensajes de error.
    """
    errores = []
    if str(nombre).strip() == "":
        errores.append("El nombre de la estación no puede estar vacío.")
    if float(potencia) <= 0:
        errores.append(f"La potencia ({potencia} kW) debe ser mayor a 0.")
    if float(precio) <= 0:
        errores.append(f"La tarifa ({precio}) debe ser mayor a 0.")
    return errores


def validar_cargadores(num_cargadores):
    """
    Valida que el número de cargadores sea al menos 1.
    Retorna un mensaje de error o cadena vacía si es válido.
    """
    if num_cargadores <= 0:
        return "El número de cargadores está en cero o negativo. Se requiere al menos 1 cargador para simular."
    return ""


# ==============================================================================
# GESTIÓN DE DATOS EN LISTAS, MATRICES Y JSON
# ==============================================================================
def ordenar_vehiculos(matriz_vehiculos):
    """
    Ordena una matriz de vehículos [placa, nombre, llegada, kwh] por
    hora de llegada ascendente y, en caso de empate, por placa ascendente (FIFO).
    """
    copia = []
    for i in range(len(matriz_vehiculos)):
        fila = matriz_vehiculos[i]
        copia.append([fila[0], fila[1], float(fila[2]), float(fila[3])])

    n = len(copia)
    for i in range(n):
        for j in range(0, n - i - 1):
            v1 = copia[j]
            v2 = copia[j + 1]
            if v1[2] > v2[2] or (v1[2] == v2[2] and v1[0] > v2[0]):
                copia[j] = v2
                copia[j + 1] = v1

    return copia


def convertir_json_a_estacion(datos_json):
    """
    Convierte un objeto JSON de entrada en la estructura de lista de estación:
    [nombre_estacion, potencia, precio, matriz_vehiculos]
    donde cada fila de matriz_vehiculos es [placa, nombre, llegada, kwh].
    """
    nombre_est = str(datos_json["estacion"]).strip()
    potencia = float(datos_json["potencia"])
    precio = float(datos_json["precio"])
    vehiculos_raw = datos_json["vehiculos"]

    matriz_vehiculos = []
    for i in range(len(vehiculos_raw)):
        v = vehiculos_raw[i]
        placa = str(v["placa"]).strip().upper()
        if "nombre" in v and str(v["nombre"]).strip() != "":
            nombre_v = str(v["nombre"]).strip()
        elif "nombre" not in v or str(v["nombre"]).strip() == "":
            nombre_v = f"Vehículo {placa}"
        llegada = float(v["llegada"])
        kwh = float(v["kwh"])
        matriz_vehiculos.append([placa, nombre_v, llegada, kwh])

    matriz_ordenada = ordenar_vehiculos(matriz_vehiculos)
    return [nombre_est, potencia, precio, matriz_ordenada]


def convertir_estacion_a_json(estacion):
    """
    Convierte una lista de estación [nombre, potencia, precio, matriz_vehiculos]
    a una estructura compatible con json.dumps / json.dump.
    """
    lista_vehiculos_json = []
    matriz_vehiculos = estacion[3]
    for i in range(len(matriz_vehiculos)):
        v = matriz_vehiculos[i]
        lista_vehiculos_json.append({
            "placa": v[0],
            "nombre": v[1],
            "llegada": v[2],
            "kwh": v[3]
        })

    return {
        "estacion": estacion[0],
        "potencia": estacion[1],
        "precio": estacion[2],
        "vehiculos": lista_vehiculos_json
    }


def cargar_datos(ruta_archivo):
    """
    Lee un archivo JSON desde disco y retorna la estación en formato lista/matriz.
    """
    with open(ruta_archivo, "r", encoding="utf-8") as archivo:
        datos_json = json.load(archivo)
    return convertir_json_a_estacion(datos_json)


def guardar_datos(ruta_archivo, estacion):
    """
    Guarda una estación (y su matriz de vehículos) en un archivo JSON.
    """
    datos_json = convertir_estacion_a_json(estacion)
    with open(ruta_archivo, "w", encoding="utf-8") as archivo:
        json.dump(datos_json, archivo, indent=2, ensure_ascii=False)


def exportar_json_texto(estacion):
    """
    Retorna el texto JSON formateado de una estación para descarga o inspección.
    """
    datos_json = convertir_estacion_a_json(estacion)
    return json.dumps(datos_json, indent=2, ensure_ascii=False)


def crear_estacion(nombre, potencia=10.0, precio=1500.0, matriz_vehiculos=None):
    """
    Crea la estructura estandarizada para una nueva estación de carga:
    [nombre, potencia, precio, matriz_vehiculos]
    """
    if str(nombre).strip() != "":
        nom_final = str(nombre).strip()
    elif str(nombre).strip() == "":
        nom_final = "Nueva Estación"

    if matriz_vehiculos is None:
        vehiculos_final = []
    elif matriz_vehiculos is not None:
        vehiculos_final = ordenar_vehiculos(matriz_vehiculos)

    return [nom_final, float(potencia), float(precio), vehiculos_final]


# ==============================================================================
# MOTOR DE SIMULACIÓN ENERGÉTICA
# ==============================================================================
def simular_estacion(estacion, num_cargadores=2):
    """
    Ejecuta el despacho de vehículos hacia los cargadores disponibles.

    Parámetros:
    - estacion: [nombre, potencia, precio, matriz_vehiculos]
    - num_cargadores: cantidad de cargadores activos (int)

    Retorna una lista con los resultados de la simulación:
    [0] nombre_estacion (str)
    [1] potencia (float)
    [2] precio (float)
    [3] num_cargadores (int)
    [4] matriz_asignaciones: cada fila es
        [placa, nombre, llegada, kwh, cargador_id, hora_inicio, hora_fin, duracion, espera]
    [5] espera_total (float)
    [6] energia_total (float)
    [7] ingresos_totales (float)
    [8] matriz_alertas: filas de asignaciones con espera >= UMBRAL_ALERTA_ESPERA_HORAS
    [9] umbral_espera (float)
    """
    nombre_estacion = estacion[0]
    potencia = float(estacion[1])
    precio = float(estacion[2])
    matriz_vehiculos = ordenar_vehiculos(estacion[3])

    if num_cargadores <= 0 or potencia <= 0:
        return [
            nombre_estacion,
            potencia,
            precio,
            num_cargadores,
            [],
            0.0,
            0.0,
            0.0,
            [],
            UMBRAL_ALERTA_ESPERA_HORAS
        ]

    # Lista con la hora en que queda libre cada cargador (índice 0 = Cargador 1)
    cargadores_disp = []
    for i in range(num_cargadores):
        cargadores_disp.append(0.0)

    matriz_asignaciones = []
    espera_total = 0.0
    energia_total = 0.0

    for i in range(len(matriz_vehiculos)):
        vehiculo = matriz_vehiculos[i]
        placa = str(vehiculo[0])
        nombre = str(vehiculo[1])
        llegada = float(vehiculo[2])
        kwh = float(vehiculo[3])

        # Tiempo de carga: Δt = kWh / Potencia [horas]
        duracion = kwh / potencia

        # Buscar el cargador que inicia más temprano (en empate gana el menor índice)
        mejor_c = 0
        if llegada > cargadores_disp[0]:
            mejor_inicio = llegada
        elif llegada <= cargadores_disp[0]:
            mejor_inicio = cargadores_disp[0]

        for c in range(1, num_cargadores):
            if llegada > cargadores_disp[c]:
                inicio_c = llegada
            elif llegada <= cargadores_disp[c]:
                inicio_c = cargadores_disp[c]

            if inicio_c < mejor_inicio:
                mejor_inicio = inicio_c
                mejor_c = c

        cargador_id = mejor_c + 1
        hora_inicio = mejor_inicio
        espera = hora_inicio - llegada
        hora_fin = hora_inicio + duracion

        # Actualizar disponibilidad del cargador asignado
        cargadores_disp[mejor_c] = hora_fin

        fila_asignacion = [
            placa,
            nombre,
            llegada,
            kwh,
            cargador_id,
            hora_inicio,
            hora_fin,
            duracion,
            espera
        ]
        matriz_asignaciones.append(fila_asignacion)

        espera_total = espera_total + espera
        energia_total = energia_total + kwh

    ingresos_totales = energia_total * precio

    # Detectar vehículos con espera mayor o igual al umbral
    matriz_alertas = []
    for i in range(len(matriz_asignaciones)):
        fila = matriz_asignaciones[i]
        if fila[8] >= UMBRAL_ALERTA_ESPERA_HORAS:
            matriz_alertas.append(fila)

    return [
        nombre_estacion,
        potencia,
        precio,
        num_cargadores,
        matriz_asignaciones,
        espera_total,
        energia_total,
        ingresos_totales,
        matriz_alertas,
        UMBRAL_ALERTA_ESPERA_HORAS
    ]


def calcular_hora_pico(resultado_simulacion, paso=0.25):
    """
    Reto Funcional: Determina el intervalo de máxima ocupación horaria.
    Evalúa paso a paso (ej. cada 15 min = 0.25 h) cuántos cargadores están activos.

    Retorna una lista:
    [0] max_vehiculos_simultaneos (int)
    [1] porcentaje_ocupacion_pico (float)
    [2] hora_inicio_pico (float)
    [3] hora_fin_pico (float)
    [4] intervalo_pico (str)
    [5] matriz_ocupacion: filas [tiempo, activos, lista_placas]
    """
    matriz_asignaciones = resultado_simulacion[4]
    num_cargadores = resultado_simulacion[3]

    if len(matriz_asignaciones) == 0 or num_cargadores <= 0:
        return [0, 0.0, 0.0, 0.0, "Sin actividad", []]

    # Hallar hora mínima de llegada y hora máxima de fin
    h_min = matriz_asignaciones[0][2]
    h_max = matriz_asignaciones[0][6]
    for i in range(1, len(matriz_asignaciones)):
        fila = matriz_asignaciones[i]
        if fila[2] < h_min:
            h_min = fila[2]
        if fila[6] > h_max:
            h_max = fila[6]

    # Discretización temporal
    tiempos = []
    t = h_min
    while t <= h_max:
        tiempos.append(round(t, 2))
        t = t + paso

    matriz_ocupacion = []
    max_activos = 0

    for i in range(len(tiempos)):
        t_actual = tiempos[i]
        placas_activas = []
        for j in range(len(matriz_asignaciones)):
            v = matriz_asignaciones[j]
            if v[5] <= t_actual and t_actual < v[6]:
                placas_activas.append(v[0])
        activos = len(placas_activas)
        if activos > max_activos:
            max_activos = activos
        matriz_ocupacion.append([t_actual, activos, placas_activas])

    # Hallar el intervalo de mayor ocupación
    puntos_pico = []
    for i in range(len(matriz_ocupacion)):
        item = matriz_ocupacion[i]
        if item[1] == max_activos:
            puntos_pico.append(item)

    t_inicio_pico = puntos_pico[0][0]
    t_fin_pico = round(puntos_pico[len(puntos_pico) - 1][0] + paso, 2)

    if num_cargadores > 0:
        pct_pico = round((max_activos / num_cargadores) * 100.0, 1)
    elif num_cargadores <= 0:
        pct_pico = 0.0

    intervalo_texto = f"{t_inicio_pico:.2f} h a {t_fin_pico:.2f} h"

    return [
        max_activos,
        pct_pico,
        t_inicio_pico,
        t_fin_pico,
        intervalo_texto,
        matriz_ocupacion
    ]


def obtener_estado_en_instante(resultado_simulacion, t_consulta):
    """
    Devuelve una matriz con el estado de cada cargador (1..N) en t_consulta.
    Cada fila es:
    [0] cargador_id (int)
    [1] estado ("Ocupado" o "Libre")
    [2] placa (str)
    [3] nombre (str)
    [4] progreso_pct (float)
    [5] kwh_entregados (float)
    [6] kwh_totales (float)
    [7] hora_fin (float)
    """
    matriz_asignaciones = resultado_simulacion[4]
    num_cargadores = resultado_simulacion[3]
    potencia = resultado_simulacion[1]

    matriz_estados = []

    if num_cargadores <= 0:
        return matriz_estados

    for c_id in range(1, num_cargadores + 1):
        vehiculo_en_carga = None
        idx_v = 0
        while idx_v < len(matriz_asignaciones) and vehiculo_en_carga is None:
            v = matriz_asignaciones[idx_v]
            if v[4] == c_id and v[5] <= t_consulta and t_consulta < v[6]:
                vehiculo_en_carga = v
            idx_v = idx_v + 1

        if vehiculo_en_carga is not None:
            tiempo_transcurrido = t_consulta - vehiculo_en_carga[5]
            progreso = (tiempo_transcurrido / vehiculo_en_carga[7]) * 100.0
            if progreso > 100.0:
                progreso = 100.0
            elif progreso < 0.0:
                progreso = 0.0

            kwh_entregados = tiempo_transcurrido * potencia
            if kwh_entregados > vehiculo_en_carga[3]:
                kwh_entregados = vehiculo_en_carga[3]
            elif kwh_entregados < 0.0:
                kwh_entregados = 0.0

            matriz_estados.append([
                c_id,
                "Ocupado",
                vehiculo_en_carga[0],
                vehiculo_en_carga[1],
                round(progreso, 1),
                round(kwh_entregados, 2),
                vehiculo_en_carga[3],
                vehiculo_en_carga[6]
            ])
        elif vehiculo_en_carga is None:
            matriz_estados.append([
                c_id,
                "Libre",
                "",
                "",
                0.0,
                0.0,
                0.0,
                0.0
            ])

    return matriz_estados
