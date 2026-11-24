"""
test_simulador.py
-----------------
Pruebas para validar los requerimientos obligatorios, la validación de datos
y el caso de verificación oficial del proyecto de Ingeniería Energética.
Implementado exclusivamente con: def, if, elif, for, and, or, listas, matrices, f-strings y json.
"""

import os
from simulador import (
    cargar_datos,
    guardar_datos,
    crear_estacion,
    simular_estacion,
    calcular_hora_pico,
    obtener_estado_en_instante,
    validar_datos_json,
    validar_vehiculo,
    validar_cargadores
)


def verificar_igual(actual, esperado, mensaje):
    if actual != esperado:
        print(f"FALLO: {mensaje}. Esperado: {esperado}, Obtenido: {actual}")
        return False
    return True


def verificar_casi_igual(actual, esperado, mensaje):
    diferencia = actual - esperado
    if diferencia < 0:
        diferencia = -diferencia
    if diferencia > 0.01:
        print(f"FALLO: {mensaje}. Esperado: {esperado}, Obtenido: {actual}")
        return False
    return True


def buscar_fila_por_placa(matriz_asignaciones, placa):
    for i in range(len(matriz_asignaciones)):
        if matriz_asignaciones[i][0] == placa:
            return matriz_asignaciones[i]
    return None


def test_caso_verificacion_oficial():
    estacion = crear_estacion("Norte", 10, 1500, [
        ["A", "Vehículo A", 8, 20],
        ["B", "Vehículo B", 8, 10],
        ["C", "Vehículo C", 9, 30],
        ["D", "Vehículo D", 9, 10]
    ])
    resultado = simular_estacion(estacion, num_cargadores=2)
    matriz = resultado[4]

    ok = True
    fila_a = buscar_fila_por_placa(matriz, "A")
    fila_b = buscar_fila_por_placa(matriz, "B")
    fila_c = buscar_fila_por_placa(matriz, "C")
    fila_d = buscar_fila_por_placa(matriz, "D")

    ok = ok and verificar_igual(fila_a[4], 1, "A cargador")
    ok = ok and verificar_igual(fila_a[5], 8.0, "A inicio")
    ok = ok and verificar_igual(fila_a[6], 10.0, "A fin")
    ok = ok and verificar_igual(fila_a[8], 0.0, "A espera")

    ok = ok and verificar_igual(fila_b[4], 2, "B cargador")
    ok = ok and verificar_igual(fila_b[5], 8.0, "B inicio")
    ok = ok and verificar_igual(fila_b[6], 9.0, "B fin")
    ok = ok and verificar_igual(fila_b[8], 0.0, "B espera")

    ok = ok and verificar_igual(fila_c[4], 2, "C cargador")
    ok = ok and verificar_igual(fila_c[5], 9.0, "C inicio")
    ok = ok and verificar_igual(fila_c[6], 12.0, "C fin")
    ok = ok and verificar_igual(fila_c[8], 0.0, "C espera")

    ok = ok and verificar_igual(fila_d[4], 1, "D cargador")
    ok = ok and verificar_igual(fila_d[5], 10.0, "D inicio")
    ok = ok and verificar_igual(fila_d[6], 11.0, "D fin")
    ok = ok and verificar_igual(fila_d[8], 1.0, "D espera")

    ok = ok and verificar_igual(resultado[5], 1.0, "Espera total")
    ok = ok and verificar_igual(resultado[6], 70.0, "Energía total")
    ok = ok and verificar_igual(resultado[7], 105000.0, "Ingresos totales")
    ok = ok and verificar_igual(len(resultado[8]), 1, "Cantidad de alertas")
    ok = ok and verificar_igual(resultado[8][0][0], "D", "Placa en alerta")
    return ok


def test_reto_funcional_hora_pico():
    estacion = crear_estacion("Norte", 10, 1500, [
        ["A", "Vehículo A", 8, 20],
        ["B", "Vehículo B", 8, 10],
        ["C", "Vehículo C", 9, 30],
        ["D", "Vehículo D", 9, 10]
    ])
    resultado = simular_estacion(estacion, num_cargadores=2)
    pico = calcular_hora_pico(resultado)

    ok = True
    ok = ok and verificar_igual(pico[0], 2, "Máximo vehículos simultáneos")
    ok = ok and verificar_igual(pico[1], 100.0, "Porcentaje ocupación pico")
    ok = ok and verificar_igual(pico[4], "8.00 h a 11.00 h", "Intervalo pico")
    return ok


def test_estados_dinamicos_tarjetas():
    estacion = crear_estacion("Norte", 10, 1500, [
        ["A", "Vehículo A", 8, 20],
        ["B", "Vehículo B", 8, 10],
        ["C", "Vehículo C", 9, 30],
        ["D", "Vehículo D", 9, 10]
    ])
    resultado = simular_estacion(estacion, num_cargadores=2)

    estados_8_5 = obtener_estado_en_instante(resultado, 8.5)
    ok = True
    ok = ok and verificar_igual(estados_8_5[0][1], "Ocupado", "Cargador 1 a las 8.5")
    ok = ok and verificar_igual(estados_8_5[0][2], "A", "Placa cargador 1 a las 8.5")
    ok = ok and verificar_casi_igual(estados_8_5[0][4], 25.0, "Progreso A a las 8.5")

    ok = ok and verificar_igual(estados_8_5[1][1], "Ocupado", "Cargador 2 a las 8.5")
    ok = ok and verificar_igual(estados_8_5[1][2], "B", "Placa cargador 2 a las 8.5")
    ok = ok and verificar_casi_igual(estados_8_5[1][4], 50.0, "Progreso B a las 8.5")

    estados_11_5 = obtener_estado_en_instante(resultado, 11.5)
    ok = ok and verificar_igual(estados_11_5[0][1], "Libre", "Cargador 1 a las 11.5")
    ok = ok and verificar_igual(estados_11_5[1][1], "Ocupado", "Cargador 2 a las 11.5")
    ok = ok and verificar_igual(estados_11_5[1][2], "C", "Placa cargador 2 a las 11.5")
    return ok


def test_vehiculos_con_nombre_y_multi_estacion():
    est_sur = crear_estacion("Sur - Terminal", 20.0, 1800.0, [
        ["BUS-01", "Bus Articulado", 10.0, 40.0],
        ["TAXI-05", "Taxi Urbano", 10.0, 20.0]
    ])
    res = simular_estacion(est_sur, num_cargadores=2)
    matriz = res[4]
    fila_bus = buscar_fila_por_placa(matriz, "BUS-01")
    fila_taxi = buscar_fila_por_placa(matriz, "TAXI-05")

    ok = True
    ok = ok and verificar_igual(est_sur[0], "Sur - Terminal", "Nombre estación")
    ok = ok and verificar_igual(fila_bus[1], "Bus Articulado", "Nombre Bus")
    ok = ok and verificar_igual(fila_bus[7], 2.0, "Duración Bus")
    ok = ok and verificar_igual(fila_taxi[1], "Taxi Urbano", "Nombre Taxi")
    ok = ok and verificar_igual(fila_taxi[7], 1.0, "Duración Taxi")
    return ok


def test_json_y_validaciones():
    ruta_entrada = os.path.join(os.path.dirname(__file__), "datos", "entrada.json")
    ruta_salida = os.path.join(os.path.dirname(__file__), "datos", "salida_test.json")

    est = cargar_datos(ruta_entrada)
    guardar_datos(ruta_salida, est)
    est_recargada = cargar_datos(ruta_salida)

    ok = True
    ok = ok and verificar_igual(est_recargada[0], "Norte", "JSON guardado y recargado")
    ok = ok and verificar_igual(len(est_recargada[3]), 4, "Vehículos en JSON")

    # Validar errores de entrada
    err_v1 = validar_vehiculo("X", 25, 10)
    err_v2 = validar_vehiculo("X", 10, 0)
    err_c = validar_cargadores(0)
    err_j = validar_datos_json({
        "estacion": "Prueba",
        "potencia": -5,
        "precio": 1000,
        "vehiculos": [{"placa": "Z", "llegada": -1, "kwh": 0}]
    })

    ok = ok and verificar_igual(len(err_v1) > 0, True, "Detecta llegada > 23")
    ok = ok and verificar_igual(len(err_v2) > 0, True, "Detecta kWh <= 0")
    ok = ok and verificar_igual(err_c != "", True, "Detecta cargadores en cero")
    ok = ok and verificar_igual(len(err_j) >= 3, True, "Detecta múltiples errores en JSON")

    if os.path.exists(ruta_salida):
        os.remove(ruta_salida)
    return ok


def ejecutar_todas_las_pruebas():
    pruebas = [
        ["Caso de verificación oficial", test_caso_verificacion_oficial],
        ["Reto funcional hora pico", test_reto_funcional_hora_pico],
        ["Estados dinámicos tarjetas", test_estados_dinamicos_tarjetas],
        ["Multi-estación y nombres", test_vehiculos_con_nombre_y_multi_estacion],
        ["JSON y validaciones", test_json_y_validaciones]
    ]

    todas_ok = True
    for i in range(len(pruebas)):
        nombre_p = pruebas[i][0]
        funcion_p = pruebas[i][1]
        resultado = funcion_p()
        if resultado:
            print(f"[OK] {nombre_p}")
        else:
            print(f"[ERROR] {nombre_p}")
            todas_ok = False

    if todas_ok:
        print("TODAS LAS PRUEBAS PASARON CORRECTAMENTE.")
    else:
        print("HUBO PRUEBAS CON ERROR.")


if __name__ == "__main__":
    ejecutar_todas_las_pruebas()
