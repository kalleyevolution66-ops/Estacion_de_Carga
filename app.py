"""
app.py
------
Aplicación interactiva de supervisión y despacho energético para la
Estación de Carga de Vehículos Eléctricos en Streamlit.
Implementada manteniendo la lógica y diseño SCADA usando únicamente:
if, elif, else, for, while, and, or, listas, matrices, def, f-strings y json.
"""

import streamlit as st
import json
import os
from simulador import (
    cargar_datos,
    guardar_datos,
    exportar_json_texto,
    convertir_json_a_estacion,
    crear_estacion,
    simular_estacion,
    calcular_hora_pico,
    obtener_estado_en_instante,
    validar_datos_json,
    validar_vehiculo,
    validar_estacion,
    validar_cargadores,
    UMBRAL_ALERTA_ESPERA_HORAS
)

# ==============================================================================
# 1. CONFIGURACIÓN VISUAL Y PALETA DE COLORES (MODULAR PARA SUSTENTACIÓN)
# ==============================================================================
st.set_page_config(
    page_title="Centro de Control EV | Estación de Carga",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paleta armónica moderna con alto contraste (UI inspirada en sistemas SCADA modernos)
COLORES_VEHICULOS = [
    "#3B82F6",  # Azul royal (Vehículo 1)
    "#10B981",  # Verde esmeralda (Vehículo 2)
    "#8B5CF6",  # Púrpura moderno (Vehículo 3)
    "#F59E0B",  # Ámbar dorado (Vehículo 4)
    "#EC4899",  # Rosa moderno (Vehículo 5)
    "#06B6D4"   # Cian eléctrico (Vehículo 6)
]

COLOR_ESPERA = "#94A3B8"        # Gris pizarra para tramos de espera
COLOR_LIBRE = "#10B981"         # Verde estado disponible
COLOR_OCUPADO = "#2563EB"       # Azul estado cargando
COLOR_CURSOR_TIEMPO = "#DC2626" # Rojo carmín para la aguja de tiempo sincrónica

# Inyección de estilos CSS limpios y adaptables a tema claro/oscuro
st.markdown("""
<style>
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2rem;
        max-width: 1250px;
    }
    .station-header {
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        color: white;
        padding: 20px 24px;
        border-radius: 14px;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.15);
    }
    .station-title {
        font-size: 1.8rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .station-subtitle {
        font-size: 0.95rem;
        opacity: 0.9;
        margin-top: 4px;
    }
    .kpi-card {
        background: var(--secondary-background-color);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 12px;
        padding: 16px;
        text-align: left;
        position: relative;
        overflow: hidden;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
    }
    .kpi-header {
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        color: var(--text-color);
        opacity: 0.7;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 4px;
    }
    .kpi-footer {
        font-size: 0.8rem;
        color: var(--text-color);
        opacity: 0.75;
    }
    .bay-card {
        background: var(--secondary-background-color);
        border: 1.5px solid rgba(148, 163, 184, 0.25);
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
        min-height: 205px;
    }
    .bay-card.bay-active {
        border-color: #3B82F6;
    }
    .bay-card.bay-idle {
        border-color: #10B981;
    }
    .bay-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    .bay-title {
        font-size: 1.1rem;
        font-weight: 700;
        margin: 0;
    }
    .bay-badge-idle {
        background: #DCFCE7;
        color: #15803D;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 20px;
        text-transform: uppercase;
    }
    .bay-badge-busy {
        background: #DBEAFE;
        color: #1D4ED8;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 20px;
        text-transform: uppercase;
    }
    .bay-meta {
        font-size: 0.88rem;
        margin: 4px 0;
        display: flex;
        justify-content: space-between;
    }
    .bay-meta-label {
        color: var(--text-color);
        opacity: 0.7;
    }
    .bay-meta-val {
        font-weight: 600;
    }
    .gantt-panel {
        background: var(--secondary-background-color);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 14px;
        padding: 20px;
        margin-top: 10px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }
    .tabla-despacho {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9rem;
    }
    .tabla-despacho th, .tabla-despacho td {
        padding: 10px 12px;
        border-bottom: 1px solid rgba(148, 163, 184, 0.25);
        text-align: left;
    }
    .tabla-despacho th {
        font-weight: 700;
        text-transform: uppercase;
        font-size: 0.78rem;
        opacity: 0.8;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# FUNCIONES AUXILIARES DE INTERFAZ (SOLO LISTAS, MATRICES Y CICLOS)
# ==============================================================================
def buscar_indice_estacion(lista_estaciones, nombre_buscar):
    for i in range(len(lista_estaciones)):
        if lista_estaciones[i][0] == nombre_buscar:
            return i
    return 0


def obtener_nombres_estaciones(lista_estaciones):
    nombres = []
    for i in range(len(lista_estaciones)):
        nombres.append(lista_estaciones[i][0])
    return nombres


def eliminar_estacion_por_indice(lista_estaciones, indice_eliminar):
    nueva_lista = []
    for i in range(len(lista_estaciones)):
        if i != indice_eliminar:
            nueva_lista.append(lista_estaciones[i])
    return nueva_lista


def obtener_color_placa(placa, placas_vistas):
    for i in range(len(placas_vistas)):
        if placas_vistas[i] == placa:
            return COLORES_VEHICULOS[i % len(COLORES_VEHICULOS)]
    placas_vistas.append(placa)
    idx = len(placas_vistas) - 1
    return COLORES_VEHICULOS[idx % len(COLORES_VEHICULOS)]


def calcular_posicion_x(h, h_min, duracion_total, margen_izq, ancho_util):
    return margen_izq + ((h - h_min) / duracion_total) * ancho_util


def generar_gantt_svg_moderno(matriz_asignaciones, num_cargadores, h_min, h_max, t_cursor):
    """
    Genera un diagrama de Gantt vectorial SVG con aguja de tiempo roja sincronizada,
    tramos de espera rayados y bloques de carga redondeados.
    """
    if num_cargadores <= 0:
        return "<p>No hay cargadores disponibles para graficar.</p>"

    margen_izq = 130
    margen_der = 50
    margen_sup = 35
    margen_inf = 50
    alto_fila = 58
    ancho_total = 960
    alto_total = margen_sup + (num_cargadores * alto_fila) + margen_inf

    duracion_total = h_max - h_min
    if duracion_total < 1.0:
        duracion_total = 1.0
    ancho_util = ancho_total - margen_izq - margen_der

    svg = [
        f'<svg width="100%" height="{alto_total}" viewBox="0 0 {ancho_total} {alto_total}" '
        f'xmlns="http://www.w3.org/2000/svg" style="font-family: system-ui, -apple-system, sans-serif;">',
        '<defs>'
        '<pattern id="wait-hatch" width="8" height="8" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">'
        '<line x1="0" y1="0" x2="0" y2="8" stroke="#94A3B8" stroke-width="2.5" />'
        '<rect x="0" y="0" width="8" height="8" fill="#F1F5F9" opacity="0.6"/>'
        '</pattern>'
        '<filter id="shadow" x="-5%" y="-10%" width="110%" height="130%">'
        '<feDropShadow dx="0" dy="2" stdDeviation="2" flood-opacity="0.12"/>'
        '</filter>'
        '</defs>'
    ]

    # Guías verticales de horas
    if duracion_total <= 8:
        paso_hora = 1.0
    else:
        paso_hora = 2.0

    h_tick = int(h_min)
    while h_tick <= int(h_max) + 1:
        if h_min <= h_tick and h_tick <= h_max:
            xt = calcular_posicion_x(h_tick, h_min, duracion_total, margen_izq, ancho_util)
            svg.append(
                f'<line x1="{xt}" y1="{margen_sup}" x2="{xt}" y2="{alto_total - margen_inf}" '
                f'stroke="#E2E8F0" stroke-width="1.2" stroke-dasharray="3 3"/>'
            )
            svg.append(
                f'<text x="{xt}" y="{alto_total - margen_inf + 22}" text-anchor="middle" '
                f'fill="#64748B" font-size="12px" font-weight="600">{int(h_tick):02d}:00</text>'
            )
        h_tick = h_tick + paso_hora

    # Filas de cargadores
    for c in range(1, num_cargadores + 1):
        yc = margen_sup + (c - 1) * alto_fila
        svg.append(
            f'<rect x="{margen_izq}" y="{yc + 6}" width="{ancho_util}" height="{alto_fila - 12}" '
            f'fill="#F8FAFC" rx="8" stroke="#E2E8F0" stroke-width="1"/>'
        )
        svg.append(
            f'<text x="20" y="{yc + (alto_fila / 2) + 4}" fill="#64748B" '
            f'font-size="13px" font-weight="700">Cargador {c}</text>'
        )

    # Asignar colores únicos por placa con una lista simple
    placas_vistas = []
    for i in range(len(matriz_asignaciones)):
        v = matriz_asignaciones[i]
        placa_v = v[0]
        nombre_v = v[1]
        llegada_v = v[2]
        kwh_v = v[3]
        c = v[4]
        hora_inicio_v = v[5]
        hora_fin_v = v[6]
        espera_v = v[8]

        yc = margen_sup + (c - 1) * alto_fila
        y_b = yc + 9
        h_b = alto_fila - 18

        # 1. Tramo de espera si existe
        if espera_v > 0:
            x_arr = calcular_posicion_x(llegada_v, h_min, duracion_total, margen_izq, ancho_util)
            w_esp = calcular_posicion_x(hora_inicio_v, h_min, duracion_total, margen_izq, ancho_util) - x_arr
            svg.append(
                f'<rect x="{x_arr}" y="{y_b}" width="{w_esp}" height="{h_b}" '
                f'fill="url(#wait-hatch)" stroke="#94A3B8" stroke-width="1.5" rx="6"/>'
            )
            if w_esp > 35:
                svg.append(
                    f'<text x="{x_arr + w_esp / 2}" y="{y_b + h_b / 2 + 4}" text-anchor="middle" '
                    f'fill="#334155" font-size="11px" font-weight="700">Espera {placa_v}</text>'
                )

        # 2. Bloque de carga activa
        x_ini = calcular_posicion_x(hora_inicio_v, h_min, duracion_total, margen_izq, ancho_util)
        w_car = calcular_posicion_x(hora_fin_v, h_min, duracion_total, margen_izq, ancho_util) - x_ini
        if w_car < 16:
            w_car = 16
        col_v = obtener_color_placa(placa_v, placas_vistas)

        svg.append(
            f'<rect x="{x_ini}" y="{y_b}" width="{w_car}" height="{h_b}" '
            f'fill="{col_v}" rx="6" filter="url(#shadow)"/>'
        )
        if nombre_v != placa_v and w_car > 110:
            txt_label = f'🚗 {placa_v} - {nombre_v} ({kwh_v:.0f}k)'
        else:
            txt_label = f'🚗 {placa_v} ({kwh_v:.0f} kWh)'

        svg.append(
            f'<text x="{x_ini + w_car / 2}" y="{y_b + h_b / 2 + 4}" text-anchor="middle" '
            f'fill="#FFFFFF" font-size="12px" font-weight="700">{txt_label}</text>'
        )

    # 3. AGUJA DE TIEMPO SINCRONIZADA
    if h_min <= t_cursor and t_cursor <= h_max:
        x_cur = calcular_posicion_x(t_cursor, h_min, duracion_total, margen_izq, ancho_util)
        svg.append(
            f'<line x1="{x_cur}" y1="{margen_sup - 10}" x2="{x_cur}" y2="{alto_total - margen_inf}" '
            f'stroke="{COLOR_CURSOR_TIEMPO}" stroke-width="2.5" stroke-dasharray="4 2"/>'
        )
        h_c_int = int(t_cursor)
        m_c_int = int((t_cursor - h_c_int) * 60)
        svg.append(
            f'<rect x="{x_cur - 32}" y="{margen_sup - 24}" width="64" height="20" rx="4" fill="{COLOR_CURSOR_TIEMPO}"/>'
        )
        svg.append(
            f'<text x="{x_cur}" y="{margen_sup - 10}" text-anchor="middle" fill="#FFFFFF" '
            f'font-size="11px" font-weight="800">{h_c_int:02d}:{m_c_int:02d}</text>'
        )

    svg.append('</svg>')
    return "".join(svg)


# ==============================================================================
# 2. CARGA Y GESTIÓN DE DATOS (POR DEFECTO O PERSONALIZADO)
# ==============================================================================
RUTA_BASE = os.path.dirname(__file__)
RUTA_DEFAULT = os.path.join(RUTA_BASE, "datos", "entrada.json")
RUTA_SALIDA = os.path.join(RUTA_BASE, "datos", "salida.json")

if "estaciones" not in st.session_state:
    if os.path.exists(RUTA_DEFAULT):
        estacion_base = cargar_datos(RUTA_DEFAULT)
    else:
        estacion_base = crear_estacion("Norte", 10.0, 1500.0, [
            ["A", "Vehículo A", 8.0, 20.0],
            ["B", "Vehículo B", 8.0, 10.0],
            ["C", "Vehículo C", 9.0, 30.0],
            ["D", "Vehículo D", 9.0, 10.0]
        ])
    st.session_state["estaciones"] = [estacion_base]

if "estacion_activa" not in st.session_state:
    st.session_state["estacion_activa"] = st.session_state["estaciones"][0][0]

# ==============================================================================
# BARRA LATERAL DE CONFIGURACIÓN
# ==============================================================================
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1593941707882-a5bba14938c7?w=500&auto=format&fit=crop&q=60", width="stretch")
    st.title("⚙️ Red de Carga Eléctrica")

    st.subheader("1. Gestión de Estaciones")
    nombres_estaciones = obtener_nombres_estaciones(st.session_state["estaciones"])

    if len(nombres_estaciones) > 0:
        idx_activa = buscar_indice_estacion(st.session_state["estaciones"], st.session_state["estacion_activa"])

        estacion_seleccionada = st.selectbox(
            "Estación de Carga Activa:",
            options=nombres_estaciones,
            index=idx_activa,
            help="Selecciona qué estación de la red deseas supervisar y simular."
        )
        st.session_state["estacion_activa"] = estacion_seleccionada
        idx_activa = buscar_indice_estacion(st.session_state["estaciones"], estacion_seleccionada)

        if st.button("🗑️ Eliminar Estación Activa", help="Elimina la estación seleccionada de la red"):
            nombre_eliminada = st.session_state["estaciones"][idx_activa][0]
            st.session_state["estaciones"] = eliminar_estacion_por_indice(
                st.session_state["estaciones"],
                idx_activa
            )
            if len(st.session_state["estaciones"]) > 0:
                st.session_state["estacion_activa"] = st.session_state["estaciones"][0][0]
            else:
                st.session_state["estacion_activa"] = ""
            st.toast(f"Estación '{nombre_eliminada}' eliminada.")
            st.rerun()
    else:
        idx_activa = -1
        st.info("No hay estaciones activas. Agrega una nueva estación o importa un archivo JSON.")

    with st.expander("🏢 Agregar Nueva Estación"):
        with st.form("form_nueva_estacion", clear_on_submit=True):
            nueva_est_nom = st.text_input("Nombre de la Estación:", value="Sur").strip()
            nueva_est_pot = st.number_input("Potencia (kW/cargador):", min_value=-10.0, max_value=350.0, value=20.0, step=5.0)
            nueva_est_prec = st.number_input("Tarifa ($/kWh):", min_value=-100.0, max_value=10000.0, value=1600.0, step=100.0)
            btn_crear_est = st.form_submit_button("Crear Estación")

            if btn_crear_est:
                errores_est = validar_estacion(nueva_est_nom, nueva_est_pot, nueva_est_prec)
                if len(errores_est) > 0:
                    for err in errores_est:
                        st.warning(err)
                else:
                    nueva_obj = crear_estacion(nueva_est_nom, nueva_est_pot, nueva_est_prec)
                    st.session_state["estaciones"].append(nueva_obj)
                    st.session_state["estacion_activa"] = nueva_obj[0]
                    st.success(f"Estación '{nueva_obj[0]}' incorporada a la red.")
                    st.rerun()

    st.subheader("2. Capacidad de Carga")
    num_cargadores = st.slider(
        "Cargadores disponibles en la estación:",
        min_value=0,
        max_value=6,
        value=2,
        help="Ajusta el número de cargadores activos (1 a 6, o 0 para probar validación)."
    )

    st.subheader("3. Flota de Vehículos")
    if len(st.session_state["estaciones"]) > 0:
        with st.expander("➕ Registrar Nuevo Vehículo"):
            with st.form("form_nuevo_vehiculo", clear_on_submit=True):
                n_nombre = st.text_input("Nombre / Modelo:", value="Tesla Model 3").strip()
                n_placa = st.text_input("Placa del vehículo:", value="E").strip().upper()
                n_llegada = st.number_input("Hora de llegada (0 a 23 h):", min_value=-5.0, max_value=30.0, value=10.0, step=0.5)
                n_kwh = st.number_input("Energía requerida (kWh):", min_value=-20.0, max_value=150.0, value=15.0, step=5.0)
                btn_registrar = st.form_submit_button("Ingresar a la Fila")

                if btn_registrar:
                    errores_v = validar_vehiculo(n_placa, n_llegada, n_kwh)
                    if len(errores_v) > 0:
                        for err in errores_v:
                            st.warning(err)
                    else:
                        if n_nombre != "":
                            nom_final = n_nombre
                        else:
                            nom_final = f"Vehículo {n_placa}"
                        st.session_state["estaciones"][idx_activa][3].append([
                            n_placa,
                            nom_final,
                            float(n_llegada),
                            float(n_kwh)
                        ])
                        st.success(f"{nom_final} ({n_placa}) registrado en fila.")
                        st.rerun()

        if st.button("🔄 Restablecer Flota Oficial", help="Vuelve a los vehículos base de la estación"):
            if st.session_state["estacion_activa"] == "Norte" and os.path.exists(RUTA_DEFAULT):
                st.session_state["estaciones"][idx_activa] = cargar_datos(RUTA_DEFAULT)
            else:
                st.session_state["estaciones"][idx_activa][3] = []
            st.rerun()
    else:
        st.caption("Crea o importa una estación para registrar vehículos.")

    st.subheader("4. Fuente Externa y Respaldo (.JSON)")
    archivo_subido = st.file_uploader(
        "Importar archivo JSON:",
        type=["json"],
        help="Carga una estación externa con sus vehículos."
    )
    if archivo_subido is not None:
        texto_subido = archivo_subido.getvalue().decode("utf-8")
        if texto_subido.strip() == "":
            st.error("El archivo JSON está vacío.")
        else:
            contenido_json = json.loads(texto_subido)
            errores_json = validar_datos_json(contenido_json)
            if len(errores_json) > 0:
                for err in errores_json:
                    st.error(err)
            else:
                cargada = convertir_json_a_estacion(contenido_json)
                ya_existe = False
                for i in range(len(st.session_state["estaciones"])):
                    if st.session_state["estaciones"][i][0] == cargada[0]:
                        st.session_state["estaciones"][i] = cargada
                        ya_existe = True
                if not ya_existe:
                    st.session_state["estaciones"].append(cargada)
                st.session_state["estacion_activa"] = cargada[0]
                st.success(f"Estación '{cargada[0]}' importada con éxito.")

    if len(st.session_state["estaciones"]) > 0:
        idx_activa = buscar_indice_estacion(st.session_state["estaciones"], st.session_state["estacion_activa"])
        estacion_actual = st.session_state["estaciones"][idx_activa]

        if st.button("💾 Guardar JSON en datos/salida.json"):
            guardar_datos(RUTA_SALIDA, estacion_actual)
            st.success("Archivo guardado en datos/salida.json.")

        json_descarga = exportar_json_texto(estacion_actual)
        st.download_button(
            label="⬇️ Descargar JSON de Estación",
            data=json_descarga,
            file_name=f"{estacion_actual[0].lower()}_estacion.json",
            mime="application/json"
        )

        st.markdown("---")
        st.markdown("### 📋 Ficha Técnica")
        st.caption(f"**Sede Activa:** {estacion_actual[0]}")
        st.caption(f"**Potencia Nominal:** {estacion_actual[1]} kW por cargador")
        st.caption(f"**Tarifa Regulada:** ${estacion_actual[2]:,.0f} COP / kWh")
        st.caption(f"**Flota Programada:** {len(estacion_actual[3])} vehículos")
    else:
        estacion_actual = None


# ==============================================================================
# 3. MOTOR DE SIMULACIÓN, VISUALIZACIONES Y TABLA DE DESPACHO
# ==============================================================================
if estacion_actual is not None:
    error_cargadores = validar_cargadores(num_cargadores)
    resultado = simular_estacion(estacion_actual, num_cargadores=num_cargadores)
    pico = calcular_hora_pico(resultado)
    asignaciones = resultado[4]

    if len(asignaciones) > 0:
        h_min = asignaciones[0][2]
        h_max = asignaciones[0][6]
        for i in range(1, len(asignaciones)):
            if asignaciones[i][2] < h_min:
                h_min = asignaciones[i][2]
            if asignaciones[i][6] > h_max:
                h_max = asignaciones[i][6]
    else:
        h_min = 8.0
        h_max = 12.0

    # ==========================================================================
    # 4. ENCABEZADO PRINCIPAL (BANNER ESTILO SCADA)
    # ==========================================================================
    st.markdown(f"""
    <div class="station-header">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <h1 class="station-title">⚡ Estación de Carga "{resultado[0]}"</h1>
                <div class="station-subtitle">
                    Sistema Inteligente de Despacho y Monitoreo de Recarga para Vehículos Eléctricos
                </div>
            </div>
            <div style="text-align: right; background: rgba(255,255,255,0.15); padding: 8px 16px; border-radius: 10px;">
                <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;">Infraestructura</div>
                <div style="font-size: 1.3rem; font-weight: 800;">{num_cargadores} Cargadores ({resultado[1]} kW c/u)</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if error_cargadores != "":
        st.error(f"⚠️ {error_cargadores}", icon="🚨")

    # ==========================================================================
    # 5. VISUALIZACIÓN 3: TARJETAS KPI EJECUTIVAS Y ALERTA INTUITIVA
    # ==========================================================================
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

    with col_kpi1:
        if resultado[5] > 0:
            color_espera = "#EF4444"
        else:
            color_espera = "#10B981"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-header">⏱️ Espera Total Acumulada</div>
            <div class="kpi-value" style="color: {color_espera};">{resultado[5]:.1f} <span style="font-size: 1.1rem;">h</span></div>
            <div class="kpi-footer">{resultado[5] * 60:.0f} minutos totales en cola</div>
        </div>
        """, unsafe_allow_html=True)

    with col_kpi2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-header">⚡ Energía Entregada</div>
            <div class="kpi-value" style="color: #2563EB;">{resultado[6]:.1f} <span style="font-size: 1.1rem;">kWh</span></div>
            <div class="kpi-footer">Demanda suministrada al 100%</div>
        </div>
        """, unsafe_allow_html=True)

    with col_kpi3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-header">💰 Facturación Total</div>
            <div class="kpi-value" style="color: #059669;">${resultado[7]:,.0f}</div>
            <div class="kpi-footer">Tarifa: ${resultado[2]:,.0f} / kWh</div>
        </div>
        """, unsafe_allow_html=True)

    with col_kpi4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-header">🔥 Reto: Hora de Mayor Ocupación</div>
            <div class="kpi-value" style="color: #D97706; font-size: 1.6rem;">{pico[4]}</div>
            <div class="kpi-footer">{pico[0]} de {num_cargadores} cargadores ({pico[1]}%)</div>
        </div>
        """, unsafe_allow_html=True)

    # Alerta de servicio clara y accionable
    alertas = resultado[8]
    if len(alertas) > 0:
        partes_placas = []
        for i in range(len(alertas)):
            v_alerta = alertas[i]
            partes_placas.append(f"**{v_alerta[0]}** ({v_alerta[8]:.1f} h)")
        placas_texto = ", ".join(partes_placas)
        sugerido = num_cargadores + 1
        if sugerido > 6:
            sugerido = 6
        st.error(
            f"⚠️ **Alerta de Nivel de Servicio:** Vehículo(s) {placas_texto} superan el umbral máximo de espera de "
            f"{UMBRAL_ALERTA_ESPERA_HORAS:.1f} h.  \n"
            f"💡 **Recomendación Energética:** Aumente el número de cargadores a **{sugerido}** "
            f"en la barra lateral para optimizar la rotación y eliminar las esperas.",
            icon="🚨"
        )
    elif error_cargadores == "":
        st.success("✅ **Excelente Desempeño:** Todos los vehículos ingresaron a carga sin superar el umbral de espera.", icon="✅")

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================================================
    # 6. SECCIÓN CENTRAL: MONITOREO DINÁMICO EN TIEMPO REAL
    # ==========================================================================
    st.markdown("### 🔌 Bahías de Carga y Monitoreo en Tiempo Real")
    st.caption(
        "Mueva el control horario para ver cómo avanza el llenado de baterías y el estado de cada bahía. "
        "La aguja roja vertical en el diagrama inferior se moverá en simultáneo con esta hora."
    )

    col_ctrl1, col_ctrl2 = st.columns([3, 1])

    with col_ctrl1:
        if h_max <= h_min:
            h_max_slider = h_min + 1.0
        else:
            h_max_slider = h_max
        t_inspeccion = st.slider(
            "🕒 Selecciona la Hora del Día para Inspección:",
            min_value=float(h_min),
            max_value=float(h_max_slider),
            value=float(h_min),
            step=0.25,
            format="%.2f h"
        )

    with col_ctrl2:
        h_int = int(t_inspeccion)
        m_int = int((t_inspeccion - h_int) * 60)
        st.markdown(f"""
        <div style="text-align: center; background: var(--secondary-background-color); border: 1px solid rgba(148,163,184,0.3); border-radius: 12px; padding: 12px;">
            <div style="font-size: 0.75rem; text-transform: uppercase; font-weight: 700; opacity: 0.7;">Hora Seleccionada</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #2563EB;">{h_int:02d}:{m_int:02d}</div>
        </div>
        """, unsafe_allow_html=True)

    estados_cargadores = obtener_estado_en_instante(resultado, t_inspeccion)

    if len(estados_cargadores) > 0:
        if num_cargadores < 3:
            num_cols = num_cargadores
        else:
            num_cols = 3
        cols_bays = st.columns(num_cols)

        for idx in range(len(estados_cargadores)):
            est = estados_cargadores[idx]
            c_idx = idx % num_cols

            with cols_bays[c_idx]:
                if est[1] == "Ocupado":
                    st.markdown(f"""
                    <div class="bay-card bay-active">
                        <div class="bay-header">
                            <h4 class="bay-title">⚡ Bahía {est[0]}</h4>
                            <span class="bay-badge-busy">Cargando ({est[2]})</span>
                        </div>
                        <div class="bay-meta">
                            <span class="bay-meta-label">Vehículo en Carga:</span>
                            <span class="bay-meta-val" style="color: #2563EB;">{est[3]} (Placa {est[2]})</span>
                        </div>
                        <div class="bay-meta">
                            <span class="bay-meta-label">Energía Transferida:</span>
                            <span class="bay-meta-val">{est[5]:.1f} / {est[6]:.1f} kWh</span>
                        </div>
                        <div class="bay-meta">
                            <span class="bay-meta-label">Hora Estimada Fin:</span>
                            <span class="bay-meta-val">{est[7]:.2f} h</span>
                        </div>
                        <div style="margin-top: 10px; margin-bottom: 4px; display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 700;">
                            <span>Progreso Batería</span>
                            <span style="color: #2563EB;">{est[4]:.1f}%</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.progress(float(est[4]) / 100.0)
                else:
                    st.markdown(f"""
                    <div class="bay-card bay-idle">
                        <div class="bay-header">
                            <h4 class="bay-title">⚡ Bahía {est[0]}</h4>
                            <span class="bay-badge-idle">Disponible</span>
                        </div>
                        <div class="bay-meta">
                            <span class="bay-meta-label">Estado Operativo:</span>
                            <span class="bay-meta-val" style="color: #10B981;">Libre para conectar</span>
                        </div>
                        <div class="bay-meta">
                            <span class="bay-meta-label">Potencia en Espera:</span>
                            <span class="bay-meta-val">{resultado[1]} kW</span>
                        </div>
                        <div class="bay-meta">
                            <span class="bay-meta-label">Flujo Activo:</span>
                            <span class="bay-meta-val">0.0 kW</span>
                        </div>
                        <div style="margin-top: 10px; margin-bottom: 4px; display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 700; color: #64748B;">
                            <span>Bahía Desocupada</span>
                            <span>0.0%</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.progress(0.0)

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================================================
    # 7. VISUALIZACIÓN 1: GANTT INTERACTIVO CON AGUJA TEMPORAL SINCRONIZADA
    # ==========================================================================
    st.markdown("### 📅 Programación y Despacho Temporal (Diagrama de Gantt)")
    st.caption(
        "Visualiza la asignación secuencial de cada vehículo en su respectivo cargador. "
        "La **línea roja vertical** marca el instante que estás observando en las bahías de arriba."
    )

    gantt_svg = generar_gantt_svg_moderno(asignaciones, num_cargadores, h_min, h_max, t_inspeccion)
    st.markdown(f'<div class="gantt-panel">{gantt_svg}</div>', unsafe_allow_html=True)

    col_l1, col_l2, col_l3 = st.columns([1, 1, 1.5])
    with col_l1:
        st.markdown("🟦 **Bloques Sólidos:** Vehículo en proceso de carga activa.")
    with col_l2:
        st.markdown("🏁 **Tramo Rayado:** Tiempo en fila de espera hasta disponibilidad.")
    with col_l3:
        st.markdown("📍 **Línea Roja Punteada:** Hora actual inspeccionada en las bahías.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================================================
    # 8. DETALLE OPERATIVO Y MATRIZ DE DESPACHO
    # ==========================================================================
    with st.expander("📊 Consultar Registro Detallado de Despacho (Flota Completa)"):
        filas_html = []
        for i in range(len(asignaciones)):
            v = asignaciones[i]
            facturacion_v = v[3] * resultado[2]
            filas_html.append(
                f"<tr>"
                f"<td><b>{v[0]}</b></td>"
                f"<td>{v[1]}</td>"
                f"<td>{v[2]:05.2f} h</td>"
                f"<td>Cargador {v[4]}</td>"
                f"<td>{v[5]:05.2f} h</td>"
                f"<td>{v[6]:05.2f} h</td>"
                f"<td>{v[7]:.2f} h</td>"
                f"<td>{v[8]:.2f} h</td>"
                f"<td>{v[3]:.1f} kWh</td>"
                f"<td>${facturacion_v:,.0f}</td>"
                f"</tr>"
            )

        cuerpo_tabla = "".join(filas_html)
        tabla_html = f"""
        <table class="tabla-despacho">
            <thead>
                <tr>
                    <th>Placa</th>
                    <th>Nombre / Modelo</th>
                    <th>Llegada</th>
                    <th>Bahía</th>
                    <th>Inicio</th>
                    <th>Fin</th>
                    <th>Carga</th>
                    <th>Espera</th>
                    <th>Energía</th>
                    <th>Facturación</th>
                </tr>
            </thead>
            <tbody>
                {cuerpo_tabla}
            </tbody>
        </table>
        """
        st.markdown(tabla_html, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="station-header">
        <div>
            <h1 class="station-title">⚡ Red de Carga EV</h1>
            <div class="station-subtitle">
                No hay estaciones de carga activas en este momento
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.info("ℹ️ Todas las estaciones fueron eliminadas. Usa **🏢 Agregar Nueva Estación** o **Importar archivo JSON** en la barra lateral para continuar.")
