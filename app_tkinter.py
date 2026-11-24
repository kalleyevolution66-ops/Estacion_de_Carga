"""
app_tkinter.py
--------------
Aplicación de escritorio interactiva en Tkinter (Librería Estándar de Python).
Refactorizada sin clases ni comprehensions, usando únicamente:
if, elif, else, for, while, and, or, listas, matrices, def, f-strings y json.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
from simulador import (
    cargar_datos,
    guardar_datos,
    convertir_json_a_estacion,
    crear_estacion,
    simular_estacion,
    calcular_hora_pico,
    obtener_estado_en_instante,
    validar_datos_json,
    validar_vehiculo,
    validar_estacion,
    validar_cargadores
)

# ==============================================================================
# CONFIGURACIÓN Y PALETA DE COLORES (MODULAR PARA SUSTENTACIÓN)
# ==============================================================================
COLORES_VEHICULOS = [
    "#2563EB",
    "#10B981",
    "#8B5CF6",
    "#F59E0B",
    "#EC4899",
    "#06B6D4"
]

COLOR_BG = "#F8FAFC"
COLOR_CARD = "#FFFFFF"
COLOR_TEXT = "#0F172A"
COLOR_TEXT_MUTED = "#64748B"
COLOR_ESPERA = "#94A3B8"
COLOR_AGUJA = "#DC2626"


def iniciar_aplicacion():
    root = tk.Tk()
    root.title("⚡ Centro de Control EV - Estación de Carga")
    root.geometry("1120x860")
    root.minsize(980, 750)
    root.configure(bg=COLOR_BG)

    ruta_archivo = os.path.join(os.path.dirname(__file__), "datos", "entrada.json")
    if os.path.exists(ruta_archivo):
        estacion_base = cargar_datos(ruta_archivo)
    else:
        estacion_base = crear_estacion("Norte", 10.0, 1500.0)

    # Estado guardado en listas/matrices en lugar de atributos de clase
    estado_app = [
        [estacion_base],   # [0] lista de estaciones
        0,                 # [1] índice estación activa
        None,              # [2] resultado última simulación
        None,              # [3] resultado hora pico
        [],                # [4] matriz de widgets de tarjetas de bahías
        []                 # [5] parámetros del Gantt [h_min, h_max, dur, m_izq, ancho_util, m_sup, h_tot]
    ]

    var_estacion_activa = tk.StringVar(value=estacion_base[0])
    var_num_cargadores = tk.IntVar(value=2)
    var_tiempo_slider = tk.DoubleVar(value=8.0)

    # Funciones auxiliares locales
    def obtener_nombres_est():
        lista_est = estado_app[0]
        nombres = []
        for i in range(len(lista_est)):
            nombres.append(lista_est[i][0])
        return nombres

    def buscar_idx_est(nombre):
        lista_est = estado_app[0]
        for i in range(len(lista_est)):
            if lista_est[i][0] == nombre:
                return i
        return 0

    def obtener_color_placa(placa, placas_vistas):
        for i in range(len(placas_vistas)):
            if placas_vistas[i] == placa:
                return COLORES_VEHICULOS[i % len(COLORES_VEHICULOS)]
        placas_vistas.append(placa)
        return COLORES_VEHICULOS[(len(placas_vistas) - 1) % len(COLORES_VEHICULOS)]

    # --------------------------------------------------------------------------
    # INTERFAZ PRINCIPAL
    # --------------------------------------------------------------------------
    frame_header = tk.Frame(root, bg="#1E3A8A", padx=20, pady=14)
    frame_header.pack(fill=tk.X, side=tk.TOP)

    lbl_tit = tk.Label(
        frame_header,
        text=f"⚡ Red EV | Estación {estacion_base[0]}",
        font=("Helvetica", 15, "bold"),
        bg="#1E3A8A",
        fg="#FFFFFF"
    )
    lbl_tit.pack(side=tk.LEFT)

    frame_controles_top = tk.Frame(frame_header, bg="#1E3A8A")
    frame_controles_top.pack(side=tk.RIGHT)

    lbl_sel_est = tk.Label(frame_controles_top, text="Estación:", font=("Helvetica", 9, "bold"), bg="#1E3A8A", fg="#E2E8F0")
    lbl_sel_est.pack(side=tk.LEFT, padx=(2, 2))

    combo_estaciones = ttk.Combobox(
        frame_controles_top,
        textvariable=var_estacion_activa,
        values=obtener_nombres_est(),
        state="readonly",
        width=9,
        font=("Helvetica", 9, "bold")
    )
    combo_estaciones.pack(side=tk.LEFT, padx=3)

    # Contenedor principal con scroll
    canvas_scroll = tk.Canvas(root, bg=COLOR_BG, highlightthickness=0)
    scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=canvas_scroll.yview)
    frame_contenido = tk.Frame(canvas_scroll, bg=COLOR_BG, padx=20, pady=14)

    def al_configurar(event=None):
        canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))

    frame_contenido.bind("<Configure>", al_configurar)
    canvas_scroll.create_window((0, 0), window=frame_contenido, anchor="nw", width=1070)
    canvas_scroll.configure(yscrollcommand=scrollbar.set)

    canvas_scroll.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Alerta
    frame_alerta = tk.Frame(frame_contenido, bg="#FEF2F2", bd=1, relief=tk.SOLID, padx=14, pady=8)
    lbl_alerta = tk.Label(
        frame_alerta,
        text="",
        font=("Helvetica", 10, "bold"),
        bg="#FEF2F2",
        fg="#991B1B",
        justify=tk.LEFT
    )
    lbl_alerta.pack(anchor="w")

    # Tarjetas KPI
    frame_kpis = tk.Frame(frame_contenido, bg=COLOR_BG)
    frame_kpis.pack(fill=tk.X, pady=(6, 12))

    def crear_card_metrica(parent, titulo, valor, color_val, subtitulo):
        f = tk.Frame(parent, bg=COLOR_CARD, relief=tk.FLAT, bd=1, padx=14, pady=10)
        f.configure(highlightbackground="#E2E8F0", highlightthickness=1)
        lbl_t = tk.Label(f, text=titulo, font=("Helvetica", 8, "bold"), fg=COLOR_TEXT_MUTED, bg=COLOR_CARD)
        lbl_t.pack(anchor="w")
        lbl_v = tk.Label(f, text=valor, font=("Helvetica", 17, "bold"), fg=color_val, bg=COLOR_CARD)
        lbl_v.pack(anchor="w", pady=2)
        lbl_sub = tk.Label(f, text=subtitulo, font=("Helvetica", 8), fg=COLOR_TEXT_MUTED, bg=COLOR_CARD)
        lbl_sub.pack(anchor="w")
        return [f, lbl_v, lbl_sub]

    card_espera = crear_card_metrica(frame_kpis, "⏱️ ESPERA TOTAL", "0.0 h", "#EF4444", "Tiempo en cola")
    card_espera[0].pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

    card_energia = crear_card_metrica(frame_kpis, "⚡ ENERGÍA VENDIDA", "0.0 kWh", "#2563EB", "Demanda total")
    card_energia[0].pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

    card_ingresos = crear_card_metrica(frame_kpis, "💰 INGRESOS TOTALES", "$0", "#059669", "Facturación")
    card_ingresos[0].pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

    card_pico = crear_card_metrica(frame_kpis, "🔥 HORA PICO (RETO)", "--", "#D97706", "Máxima ocupación")
    card_pico[0].pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

    # Monitoreo en tiempo real
    lbl_sec_vivo = tk.Label(
        frame_contenido,
        text="🔌 Monitoreo de Bahías en Tiempo Real (Deslizador Horario)",
        font=("Helvetica", 12, "bold"),
        bg=COLOR_BG,
        fg=COLOR_TEXT
    )
    lbl_sec_vivo.pack(anchor="w", pady=(8, 4))

    frame_ctrl_tiempo = tk.Frame(frame_contenido, bg=COLOR_CARD, padx=16, pady=10)
    frame_ctrl_tiempo.configure(highlightbackground="#E2E8F0", highlightthickness=1)
    frame_ctrl_tiempo.pack(fill=tk.X, pady=4)

    lbl_reloj = tk.Label(
        frame_ctrl_tiempo,
        text="🕒 Hora de Inspección: 08:00 h",
        font=("Helvetica", 11, "bold"),
        bg=COLOR_CARD,
        fg="#2563EB"
    )
    lbl_reloj.pack(side=tk.LEFT, padx=(0, 16))

    slider_tiempo = ttk.Scale(
        frame_ctrl_tiempo,
        from_=8.0,
        to=12.0,
        orient=tk.HORIZONTAL,
        variable=var_tiempo_slider
    )
    slider_tiempo.pack(side=tk.LEFT, fill=tk.X, expand=True)

    frame_cards_bays = tk.Frame(frame_contenido, bg=COLOR_BG)
    frame_cards_bays.pack(fill=tk.X, pady=8)

    # Gantt
    lbl_sec_gantt = tk.Label(
        frame_contenido,
        text="📅 Programación y Despacho Temporal (Diagrama de Gantt)",
        font=("Helvetica", 12, "bold"),
        bg=COLOR_BG,
        fg=COLOR_TEXT
    )
    lbl_sec_gantt.pack(anchor="w", pady=(10, 4))

    frame_gantt = tk.Frame(frame_contenido, bg=COLOR_CARD, padx=12, pady=12)
    frame_gantt.configure(highlightbackground="#E2E8F0", highlightthickness=1)
    frame_gantt.pack(fill=tk.X, pady=4)

    canvas_gantt = tk.Canvas(frame_gantt, height=210, bg="#FAFAFA", highlightthickness=0)
    canvas_gantt.pack(fill=tk.BOTH, expand=True)

    lbl_leyenda = tk.Label(
        frame_gantt,
        text="Leyenda:  [🟦 Bloque de Color = Vehículo Cargando]   [🏁 Tramo Gris = Espera en Cola]   [📍 Línea Roja = Hora Seleccionada]",
        font=("Helvetica", 9),
        bg=COLOR_CARD,
        fg=COLOR_TEXT_MUTED
    )
    lbl_leyenda.pack(anchor="w", pady=(8, 0))

    # --------------------------------------------------------------------------
    # LÓGICA DE RENDERIZADO Y ACTUALIZACIÓN
    # --------------------------------------------------------------------------
    def dibujar_gantt_estatico(h_min, h_max):
        canvas_gantt.delete("all")
        resultado = estado_app[2]
        asigs = resultado[4]
        n_carg = resultado[3]

        if n_carg <= 0:
            estado_app[5] = []
            return

        w_canvas = 990
        alto_fila = 42
        margen_izq = 110
        margen_der = 50
        margen_sup = 28
        h_total = margen_sup + (n_carg * alto_fila) + 38

        canvas_gantt.config(height=h_total)
        duracion_total = h_max - h_min
        if duracion_total < 1.0:
            duracion_total = 1.0
        ancho_util = w_canvas - margen_izq - margen_der

        estado_app[5] = [h_min, h_max, duracion_total, margen_izq, ancho_util, margen_sup, h_total]

        def x_pos(h):
            return margen_izq + ((h - h_min) / duracion_total) * ancho_util

        h_tick = int(h_min)
        while h_tick <= int(h_max) + 1:
            if h_min <= h_tick and h_tick <= h_max:
                xt = x_pos(h_tick)
                canvas_gantt.create_line(xt, margen_sup, xt, h_total - 25, fill="#E2E8F0", dash=(2, 2))
                canvas_gantt.create_text(xt, h_total - 12, text=f"{int(h_tick):02d}:00", font=("Helvetica", 9, "bold"), fill=COLOR_TEXT_MUTED)
            h_tick = h_tick + 1

        for c in range(1, n_carg + 1):
            yc = margen_sup + (c - 1) * alto_fila
            canvas_gantt.create_rectangle(margen_izq, yc + 4, margen_izq + ancho_util, yc + alto_fila - 4, fill="#F8FAFC", outline="#E2E8F0")
            canvas_gantt.create_text(18, yc + (alto_fila / 2), anchor="w", text=f"Cargador {c}", font=("Helvetica", 10, "bold"), fill=COLOR_TEXT)

        placas_vistas = []
        for i in range(len(asigs)):
            v = asigs[i]
            c = v[4]
            yc = margen_sup + (c - 1) * alto_fila
            y1 = yc + 6
            y2 = yc + alto_fila - 6

            if v[8] > 0:
                x_arr = x_pos(v[2])
                x_ini = x_pos(v[5])
                canvas_gantt.create_rectangle(x_arr, y1, x_ini, y2, fill=COLOR_ESPERA, outline="#64748B", stipple="gray50")
                if (x_ini - x_arr) > 28:
                    canvas_gantt.create_text((x_arr + x_ini) / 2, (y1 + y2) / 2, text=f"Esp. {v[0]}", font=("Helvetica", 8, "bold"), fill="#0F172A")

            x_ini = x_pos(v[5])
            x_fin = x_pos(v[6])
            col_v = obtener_color_placa(v[0], placas_vistas)
            canvas_gantt.create_rectangle(x_ini, y1, x_fin, y2, fill=col_v, outline="#1E40AF", width=1)

            w_box = x_fin - x_ini
            nom_v = v[1]
            if nom_v != v[0] and w_box > 100:
                txt_v = f"🚗 {v[0]} - {nom_v} ({v[3]:.0f}k)"
            elif w_box > 50:
                txt_v = f"🚗 {v[0]} ({v[3]:.0f} kWh)"
            else:
                txt_v = f"🚗 {v[0]}"
            canvas_gantt.create_text((x_ini + x_fin) / 2, (y1 + y2) / 2, text=txt_v, font=("Helvetica", 8, "bold"), fill="#FFFFFF")

    def actualizar_aguja_gantt(t_cursor):
        canvas_gantt.delete("aguja")
        params = estado_app[5]
        if len(params) == 0:
            return

        h_min = params[0]
        h_max = params[1]
        duracion_total = params[2]
        margen_izq = params[3]
        ancho_util = params[4]
        margen_sup = params[5]
        h_total = params[6]

        if h_min <= t_cursor and t_cursor <= h_max:
            x_cur = margen_izq + ((t_cursor - h_min) / duracion_total) * ancho_util
            canvas_gantt.create_line(x_cur, margen_sup - 8, x_cur, h_total - 25, fill=COLOR_AGUJA, width=2, dash=(4, 2), tags="aguja")
            h_c = int(t_cursor)
            m_c = int((t_cursor - h_c) * 60)
            canvas_gantt.create_rectangle(x_cur - 26, margen_sup - 22, x_cur + 26, margen_sup - 4, fill=COLOR_AGUJA, outline="", tags="aguja")
            canvas_gantt.create_text(x_cur, margen_sup - 13, text=f"{h_c:02d}:{m_c:02d}", font=("Helvetica", 8, "bold"), fill="#FFFFFF", tags="aguja")

    def crear_cards_bahias():
        hijos = frame_cards_bays.winfo_children()
        for i in range(len(hijos)):
            hijos[i].destroy()
        estado_app[4] = []

        resultado = estado_app[2]
        num_carg = resultado[3]
        if num_carg <= 0:
            return

        for c_id in range(1, num_carg + 1):
            f_card = tk.Frame(frame_cards_bays, bg=COLOR_CARD, padx=14, pady=12)
            f_card.configure(highlightbackground="#E2E8F0", highlightthickness=1.5)
            f_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

            f_head = tk.Frame(f_card, bg=COLOR_CARD)
            f_head.pack(fill=tk.X, pady=(0, 6))

            lbl_titulo = tk.Label(f_head, text=f"⚡ Bahía {c_id}", font=("Helvetica", 11, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT)
            lbl_titulo.pack(side=tk.LEFT)

            lbl_badge = tk.Label(f_head, text="DISPONIBLE", font=("Helvetica", 8, "bold"), bg="#DCFCE7", fg="#15803D", padx=8, pady=2)
            lbl_badge.pack(side=tk.RIGHT)

            lbl_estado_veh = tk.Label(f_card, text="Estado: Libre para conectar", font=("Helvetica", 9, "bold"), bg=COLOR_CARD, fg="#10B981")
            lbl_estado_veh.pack(anchor="w")

            lbl_energia = tk.Label(f_card, text=f"Potencia disponible: {resultado[1]} kW", font=("Helvetica", 8), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED)
            lbl_energia.pack(anchor="w")

            lbl_fin = tk.Label(f_card, text="Flujo: 0.0 kW", font=("Helvetica", 8), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED)
            lbl_fin.pack(anchor="w")

            lbl_bateria = tk.Label(f_card, text="Batería: 0.0%", font=("Helvetica", 9, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT)
            lbl_bateria.pack(anchor="w", pady=(6, 2))

            pb = ttk.Progressbar(f_card, value=0.0, maximum=100)
            pb.pack(fill=tk.X, expand=True)

            estado_app[4].append([f_card, lbl_badge, lbl_estado_veh, lbl_energia, lbl_fin, lbl_bateria, pb])

    def actualizar_valores_bahias(t):
        h_ent = int(t)
        mins = int((t - h_ent) * 60)
        lbl_reloj.config(text=f"🕒 Hora Seleccionada: {h_ent:02d}:{mins:02d} ({t:.2f} h)")

        resultado = estado_app[2]
        estados = obtener_estado_en_instante(resultado, t)
        cards = estado_app[4]

        for i in range(len(estados)):
            if i >= len(cards):
                break
            est = estados[i]
            card = cards[i]
            if est[1] == "Ocupado":
                card[0].configure(highlightbackground="#93C5FD")
                card[1].config(text=f"CARGANDO ({est[2]})", bg="#DBEAFE", fg="#1D4ED8")
                card[2].config(text=f"{est[3]} ({est[2]})", fg="#2563EB")
                card[3].config(text=f"Energía: {est[5]:.1f} / {est[6]:.1f} kWh")
                card[4].config(text=f"Fin Estimado: {est[7]:.2f} h")
                card[5].config(text=f"Batería: {est[4]:.1f}%")
                card[6]["value"] = est[4]
            else:
                card[0].configure(highlightbackground="#86EFAC")
                card[1].config(text="DISPONIBLE", bg="#DCFCE7", fg="#15803D")
                card[2].config(text="Estado: Libre para conectar", fg="#10B981")
                card[3].config(text=f"Potencia disponible: {resultado[1]} kW")
                card[4].config(text="Flujo: 0.0 kW")
                card[5].config(text="Batería: 0.0%")
                card[6]["value"] = 0.0

    def al_mover_slider(val=None):
        t = float(var_tiempo_slider.get())
        actualizar_aguja_gantt(t)
        actualizar_valores_bahias(t)

    slider_tiempo.config(command=al_mover_slider)

    def ejecutar_simulacion():
        n_cargadores = int(var_num_cargadores.get())
        err_carg = validar_cargadores(n_cargadores)
        estacion_actual = estado_app[0][estado_app[1]]

        resultado = simular_estacion(estacion_actual, num_cargadores=n_cargadores)
        pico = calcular_hora_pico(resultado)
        estado_app[2] = resultado
        estado_app[3] = pico

        if resultado[5] > 0:
            col_esp = "#EF4444"
        else:
            col_esp = "#10B981"

        card_espera[1].config(text=f"{resultado[5]:.1f} h", fg=col_esp)
        card_espera[2].config(text=f"{resultado[5] * 60:.0f} min acumulados")
        card_energia[1].config(text=f"{resultado[6]:.1f} kWh")
        card_ingresos[1].config(text=f"${resultado[7]:,.0f}")
        card_pico[1].config(text=f"{pico[4]}")
        card_pico[2].config(text=f"{pico[0]} cargadores ({pico[1]}%)")

        if err_carg != "":
            lbl_alerta.config(text=f"🚨 {err_carg}")
            frame_alerta.pack(fill=tk.X, pady=(2, 8), before=frame_kpis)
        elif len(resultado[8]) > 0:
            partes = []
            for i in range(len(resultado[8])):
                v_a = resultado[8][i]
                partes.append(f"{v_a[0]} ({v_a[8]:.1f} h)")
            placas_txt = ", ".join(partes)
            sugerido = n_cargadores + 1
            if sugerido > 6:
                sugerido = 6
            lbl_alerta.config(
                text=f"🚨 ALERTA DE SERVICIO: Vehículo(s) {placas_txt} superan el umbral de 1 hora de espera.\n"
                     f"💡 Sugerencia: Aumente los cargadores a {sugerido} para eliminar demoras."
            )
            frame_alerta.pack(fill=tk.X, pady=(2, 8), before=frame_kpis)
        else:
            frame_alerta.pack_forget()

        asigs = resultado[4]
        if len(asigs) > 0:
            h_min = asigs[0][2]
            h_max = asigs[0][6]
            for i in range(1, len(asigs)):
                if asigs[i][2] < h_min:
                    h_min = asigs[i][2]
                if asigs[i][6] > h_max:
                    h_max = asigs[i][6]
        else:
            h_min = 8.0
            h_max = 12.0

        slider_tiempo.config(from_=h_min, to=h_max)
        if var_tiempo_slider.get() < h_min or var_tiempo_slider.get() > h_max:
            var_tiempo_slider.set(h_min)

        dibujar_gantt_estatico(h_min, h_max)
        crear_cards_bahias()
        t_inicial = float(var_tiempo_slider.get())
        actualizar_aguja_gantt(t_inicial)
        actualizar_valores_bahias(t_inicial)

    # --------------------------------------------------------------------------
    # EVENTOS Y DIÁLOGOS
    # --------------------------------------------------------------------------
    def al_cambiar_estacion(event=None):
        nom = var_estacion_activa.get()
        estado_app[1] = buscar_idx_est(nom)
        lbl_tit.config(text=f"⚡ Red EV | Estación {nom}")
        ejecutar_simulacion()

    combo_estaciones.bind("<<ComboboxSelected>>", al_cambiar_estacion)

    def abrir_dialogo_nueva_estacion():
        dialogo = tk.Toplevel(root)
        dialogo.title("🏢 Nueva Estación de Carga")
        dialogo.geometry("340x260")
        dialogo.resizable(False, False)
        dialogo.configure(bg="#FFFFFF")
        dialogo.transient(root)
        dialogo.grab_set()

        tk.Label(dialogo, text="Registrar Nueva Estación", font=("Helvetica", 11, "bold"), bg="#FFFFFF", fg="#1E3A8A").pack(pady=(12, 8))
        f_form = tk.Frame(dialogo, bg="#FFFFFF", padx=16)
        f_form.pack(fill=tk.BOTH, expand=True)

        tk.Label(f_form, text="Nombre:", font=("Helvetica", 9, "bold"), bg="#FFFFFF", fg=COLOR_TEXT).grid(row=0, column=0, sticky="w", pady=4)
        entry_nom = tk.Entry(f_form, font=("Helvetica", 10))
        entry_nom.insert(0, "Sur")
        entry_nom.grid(row=0, column=1, sticky="ew", pady=4, padx=(8, 0))

        tk.Label(f_form, text="Potencia (kW):", font=("Helvetica", 9, "bold"), bg="#FFFFFF", fg=COLOR_TEXT).grid(row=1, column=0, sticky="w", pady=4)
        entry_pot = tk.Entry(f_form, font=("Helvetica", 10))
        entry_pot.insert(0, "20.0")
        entry_pot.grid(row=1, column=1, sticky="ew", pady=4, padx=(8, 0))

        tk.Label(f_form, text="Precio ($/kWh):", font=("Helvetica", 9, "bold"), bg="#FFFFFF", fg=COLOR_TEXT).grid(row=2, column=0, sticky="w", pady=4)
        entry_prec = tk.Entry(f_form, font=("Helvetica", 10))
        entry_prec.insert(0, "1600.0")
        entry_prec.grid(row=2, column=1, sticky="ew", pady=4, padx=(8, 0))

        def confirmar_estacion():
            nom = entry_nom.get().strip()
            pot_txt = entry_pot.get().strip()
            prec_txt = entry_prec.get().strip()
            if pot_txt == "" or prec_txt == "":
                messagebox.showwarning("Dato requerido", "Potencia y precio no pueden estar vacíos.", parent=dialogo)
                return
            pot = float(pot_txt)
            prec = float(prec_txt)
            errores = validar_estacion(nom, pot, prec)
            if len(errores) > 0:
                messagebox.showwarning("Datos inválidos", "\n".join(errores), parent=dialogo)
                return

            nueva = crear_estacion(nom, pot, prec)
            estado_app[0].append(nueva)
            estado_app[1] = len(estado_app[0]) - 1
            combo_estaciones["values"] = obtener_nombres_est()
            var_estacion_activa.set(nueva[0])
            lbl_tit.config(text=f"⚡ Red EV | Estación {nueva[0]}")
            dialogo.destroy()
            ejecutar_simulacion()

        btn_crear = tk.Button(dialogo, text="Crear Estación", command=confirmar_estacion, bg="#0284C7", fg="#FFFFFF", font=("Helvetica", 10, "bold"), relief=tk.FLAT, pady=4)
        btn_crear.pack(fill=tk.X, padx=16, pady=(0, 14))

    def cargar_archivo_dialogo():
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo JSON",
            filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")]
        )
        if ruta != "":
            with open(ruta, "r", encoding="utf-8") as archivo:
                datos_json = json.load(archivo)
            errores = validar_datos_json(datos_json)
            if len(errores) > 0:
                messagebox.showerror("JSON inválido", "\n".join(errores))
                return
            cargada = convertir_json_a_estacion(datos_json)
            estado_app[0].append(cargada)
            estado_app[1] = len(estado_app[0]) - 1
            combo_estaciones["values"] = obtener_nombres_est()
            var_estacion_activa.set(cargada[0])
            lbl_tit.config(text=f"⚡ Red EV | Estación {cargada[0]}")
            ejecutar_simulacion()

    def guardar_archivo_dialogo():
        ruta = filedialog.asksaveasfilename(
            title="Guardar estación en JSON",
            defaultextension=".json",
            filetypes=[("Archivos JSON", "*.json")]
        )
        if ruta != "":
            estacion_actual = estado_app[0][estado_app[1]]
            guardar_datos(ruta, estacion_actual)
            messagebox.showinfo("Guardado", f"Estación '{estacion_actual[0]}' guardada correctamente.")

    def abrir_dialogo_registro():
        dialogo = tk.Toplevel(root)
        dialogo.title("➕ Registrar Vehículo")
        dialogo.geometry("340x280")
        dialogo.resizable(False, False)
        dialogo.configure(bg="#FFFFFF")
        dialogo.transient(root)
        dialogo.grab_set()

        estacion_actual = estado_app[0][estado_app[1]]
        tk.Label(dialogo, text=f"Registrar Vehículo en {estacion_actual[0]}", font=("Helvetica", 11, "bold"), bg="#FFFFFF", fg="#1E3A8A").pack(pady=(10, 6))

        f_form = tk.Frame(dialogo, bg="#FFFFFF", padx=16)
        f_form.pack(fill=tk.BOTH, expand=True)

        tk.Label(f_form, text="Nombre/Modelo:", font=("Helvetica", 9, "bold"), bg="#FFFFFF", fg=COLOR_TEXT).grid(row=0, column=0, sticky="w", pady=3)
        entry_nombre = tk.Entry(f_form, font=("Helvetica", 10))
        entry_nombre.insert(0, "Tesla Model 3")
        entry_nombre.grid(row=0, column=1, sticky="ew", pady=3, padx=(8, 0))

        tk.Label(f_form, text="Placa:", font=("Helvetica", 9, "bold"), bg="#FFFFFF", fg=COLOR_TEXT).grid(row=1, column=0, sticky="w", pady=3)
        entry_placa = tk.Entry(f_form, font=("Helvetica", 10))
        entry_placa.insert(0, "E")
        entry_placa.grid(row=1, column=1, sticky="ew", pady=3, padx=(8, 0))

        tk.Label(f_form, text="Hora Llegada (0-23 h):", font=("Helvetica", 9, "bold"), bg="#FFFFFF", fg=COLOR_TEXT).grid(row=2, column=0, sticky="w", pady=3)
        entry_llegada = tk.Entry(f_form, font=("Helvetica", 10))
        entry_llegada.insert(0, "10.0")
        entry_llegada.grid(row=2, column=1, sticky="ew", pady=3, padx=(8, 0))

        tk.Label(f_form, text="Energía (kWh):", font=("Helvetica", 9, "bold"), bg="#FFFFFF", fg=COLOR_TEXT).grid(row=3, column=0, sticky="w", pady=3)
        entry_kwh = tk.Entry(f_form, font=("Helvetica", 10))
        entry_kwh.insert(0, "15.0")
        entry_kwh.grid(row=3, column=1, sticky="ew", pady=3, padx=(8, 0))

        def confirmar():
            nombre = entry_nombre.get().strip()
            placa = entry_placa.get().strip().upper()
            llegada = float(entry_llegada.get().strip())
            kwh = float(entry_kwh.get().strip())
            errores = validar_vehiculo(placa, llegada, kwh)
            if len(errores) > 0:
                messagebox.showwarning("Datos inválidos", "\n".join(errores), parent=dialogo)
                return
            if nombre == "":
                nombre = f"Vehículo {placa}"
            estacion_actual[3].append([placa, nombre, llegada, kwh])
            dialogo.destroy()
            ejecutar_simulacion()

        btn_guardar = tk.Button(dialogo, text="Guardar en Fila", command=confirmar, bg="#10B981", fg="#FFFFFF", font=("Helvetica", 10, "bold"), relief=tk.FLAT, pady=4)
        btn_guardar.pack(fill=tk.X, padx=16, pady=(0, 12))

    def restablecer_datos():
        nom_activa = var_estacion_activa.get()
        if nom_activa == "Norte" and os.path.exists(ruta_archivo):
            estado_app[0][estado_app[1]] = cargar_datos(ruta_archivo)
            messagebox.showinfo("Restablecido", "Estación 'Norte' restablecida a la flota oficial (A, B, C, D).")
        else:
            estado_app[0][estado_app[1]][3] = []
            messagebox.showinfo("Restablecido", f"Flota de estación '{nom_activa}' limpiada.")
        ejecutar_simulacion()

    # Botones barra superior
    btn_nueva_est = tk.Button(frame_controles_top, text="🏢 + Estación", command=abrir_dialogo_nueva_estacion, font=("Helvetica", 9, "bold"), bg="#0284C7", fg="#FFFFFF", relief=tk.FLAT, padx=8, pady=3, cursor="hand2")
    btn_nueva_est.pack(side=tk.LEFT, padx=3)

    btn_cargar = tk.Button(frame_controles_top, text="📂 Cargar JSON", command=cargar_archivo_dialogo, font=("Helvetica", 9, "bold"), bg="#3B82F6", fg="#FFFFFF", relief=tk.FLAT, padx=8, pady=3, cursor="hand2")
    btn_cargar.pack(side=tk.LEFT, padx=3)

    btn_guardar = tk.Button(frame_controles_top, text="💾 Guardar JSON", command=guardar_archivo_dialogo, font=("Helvetica", 9, "bold"), bg="#6366F1", fg="#FFFFFF", relief=tk.FLAT, padx=8, pady=3, cursor="hand2")
    btn_guardar.pack(side=tk.LEFT, padx=3)

    btn_registrar = tk.Button(frame_controles_top, text="➕ Vehículo", command=abrir_dialogo_registro, font=("Helvetica", 9, "bold"), bg="#10B981", fg="#FFFFFF", relief=tk.FLAT, padx=8, pady=3, cursor="hand2")
    btn_registrar.pack(side=tk.LEFT, padx=3)

    btn_reset = tk.Button(frame_controles_top, text="🔄 Reset", command=restablecer_datos, font=("Helvetica", 9, "bold"), bg="#475569", fg="#FFFFFF", relief=tk.FLAT, padx=8, pady=3, cursor="hand2")
    btn_reset.pack(side=tk.LEFT, padx=3)

    lbl_carg = tk.Label(frame_controles_top, text="Cargadores:", font=("Helvetica", 9, "bold"), bg="#1E3A8A", fg="#E2E8F0")
    lbl_carg.pack(side=tk.LEFT, padx=(6, 2))

    spin_carg = ttk.Spinbox(
        frame_controles_top,
        from_=0,
        to=6,
        width=3,
        textvariable=var_num_cargadores,
        command=ejecutar_simulacion,
        font=("Helvetica", 10, "bold")
    )
    spin_carg.pack(side=tk.LEFT, padx=2)

    ejecutar_simulacion()
    root.mainloop()


if __name__ == "__main__":
    iniciar_aplicacion()
