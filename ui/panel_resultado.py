"""
Panel visual para mostrar el tableau simplex iteración por iteración.
"""

import tkinter as tk
from tkinter import ttk
from core.modelo import Iteracion
from ui.tabla_simplex import TablaSimplex
from ui.formateador_tableau import FormateadorTableau


# Colores
BG_PANEL = "#0f1923"
BG_HEADER = "#1e2a3a"
FG_TEXTO = "#e8edf2"
FG_HEADER = "#7fb3d3"
COLOR_BORDE = "#2d4a6e"
COLOR_BASICA = "#1a6b3c"

# Colores para información de pivotaje
COLOR_PIVOTE_COLUMNA = "#2a7d3e"
COLOR_PIVOTE_FILA = "#8b7d2e"
COLOR_RAZON_MINIMA = "#a81e3d"
BG_INFO_PIVOTE = "#1a2a3a"


class PanelResultado(tk.Frame):
    """
    Panel derecho que muestra el tableau simplex.

    Muestra:
    - Información de la iteración actual
    - Tabla con encabezados y scrollbars
    - Variables básicas
    - Información de pivotaje
    """

    def __init__(self, parent, **kwargs):
        kwargs.setdefault("bg", BG_PANEL)
        super().__init__(parent, **kwargs)

        self._iteracion_actual = None
        self._construir_layout()

    def _construir_layout(self):
        """Construye la estructura interna del panel.

        Layout (de arriba hacia abajo, todos con pack):
          1. header         — fill="x"
          2. separador      — fill="x"
          3. frame_bottom   — side="bottom", fill="x"  ← anclado PRIMERO
          4. frame_pivote   — side="bottom", fill="x"  ← anclado SEGUNDO
          5. container      — fill="both", expand=True  ← tabla, crece al centro

        El mismo principio que en VentanaPrincipal: declarar los frames
        "bottom" antes que el frame con expand=True para que X11 les
        garantice espacio y no los expulse fuera de la ventana.
        """

        # ── Encabezado ────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=BG_HEADER, pady=12)
        header.pack(fill="x")

        self._lbl_titulo = tk.Label(
            header,
            text="Tabla Simplex - Método de la Gran M",
            font=("Georgia", 16, "bold"),
            bg=BG_HEADER,
            fg=FG_TEXTO,
        )
        self._lbl_titulo.pack()

        self._lbl_iteracion = tk.Label(
            header,
            text="Esperando resolver problema...",
            font=("Segoe UI", 12),
            bg=BG_HEADER,
            fg=FG_HEADER,
        )
        self._lbl_iteracion.pack()

        # Separador
        tk.Frame(self, height=2, bg=COLOR_BORDE).pack(fill="x")

        # ── FIX X11: frames inferiores declarados ANTES del container ─────────
        # Frame de información de pivotaje (el más bajo)
        self._frame_info_pivote = tk.Frame(
            self, bg=BG_INFO_PIVOTE, relief="sunken", borderwidth=1
        )
        self._frame_info_pivote.pack(side="bottom", fill="x", padx=10, pady=5)

        # Frame de variables básicas (encima del pivote)
        self._frame_info_basicas = tk.Frame(self, bg=BG_PANEL)
        self._frame_info_basicas.pack(side="bottom", fill="x", padx=10, pady=5)
        # ── fin FIX ────────────────────────────────────────────────────────────

        # ── Contenedor de la tabla (ocupa el espacio restante) ────────────────
        container = tk.Frame(self, bg=BG_PANEL)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        scrollbar_v = ttk.Scrollbar(container, orient="vertical")
        scrollbar_h = ttk.Scrollbar(container, orient="horizontal")

        self._tabla = TablaSimplex(
            container,
            yscrollcommand=scrollbar_v.set,
            xscrollcommand=scrollbar_h.set,
        )

        scrollbar_v.config(command=self._tabla.yview)
        scrollbar_h.config(command=self._tabla.xview)

        self._tabla.grid(row=0, column=0, sticky="nsew")
        scrollbar_v.grid(row=0, column=1, sticky="ns")
        scrollbar_h.grid(row=1, column=0, sticky="ew")

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

    # ── API pública ────────────────────────────────────────────────────────────

    def mostrar_iteracion(self, iteracion: Iteracion):
        """Muestra una iteración del simplex en el panel."""
        self._iteracion_actual = iteracion

        self._lbl_iteracion.config(
            text=(
                f"Iteración {iteracion.numero_iteracion} | "
                f"{iteracion.obtener_num_restricciones()} restricciones, "
                f"{iteracion.obtener_num_variables()} variables"
            )
        )

        datos = FormateadorTableau.obtener_datos_tabla(iteracion)
        self._tabla.cargar_iteracion(iteracion)

        if (
            iteracion.numero_iteracion > 1
            and iteracion.columna_pivote >= 0
            and iteracion.fila_pivote >= 0
        ):
            self._tabla.resaltar_pivote(iteracion.fila_pivote, iteracion.columna_pivote)
            self._mostrar_info_pivote(iteracion)
        else:
            self._limpiar_info_pivote()

        self._construir_info_basicas(datos)

    def mostrar_sensibilidad(self, sensibilidad: dict):
        """Muestra una tabla de análisis de sensibilidad."""
        if hasattr(self, '_frame_sensibilidad'):
            self._frame_sensibilidad.destroy()

        # Se inserta entre variables básicas y el borde inferior;
        # usa pack con side="bottom" para respetar el orden fijo.
        self._frame_sensibilidad = tk.Frame(self, bg=BG_PANEL)
        self._frame_sensibilidad.pack(side="bottom", fill="x", padx=10, pady=(2, 8))

        tk.Label(
            self._frame_sensibilidad,
            text="Análisis de Sensibilidad:",
            font=("Segoe UI", 11, "bold"),
            bg=BG_PANEL,
            fg=FG_HEADER,
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=(2, 0), pady=(2, 6))

        hdr_font = ("Consolas", 10, "bold")
        cell_font = ("Consolas", 10)

        self._frame_sensibilidad.grid_columnconfigure(0, weight=1, uniform='c')
        self._frame_sensibilidad.grid_columnconfigure(1, weight=0)
        self._frame_sensibilidad.grid_columnconfigure(2, weight=2, uniform='c')

        tk.Label(self._frame_sensibilidad, text="Parámetro",     font=hdr_font, bg=BG_PANEL, fg=FG_TEXTO).grid(row=1, column=0, sticky="w", padx=4)
        tk.Label(self._frame_sensibilidad, text="Valor Inicial", font=hdr_font, bg=BG_PANEL, fg=FG_TEXTO).grid(row=1, column=1, sticky="e", padx=4)
        tk.Label(self._frame_sensibilidad, text="Rango Permitido", font=hdr_font, bg=BG_PANEL, fg=FG_TEXTO).grid(row=1, column=2, sticky="w", padx=4)

        def fmt(val):
            return FormateadorTableau.formatear_coeficiente(val) if val is not None else None

        row_idx = 2
        for section in ('coef_objetivo', 'rhs'):
            for row in sensibilidad.get(section, []):
                param = row['parametro']
                val   = fmt(row['valor_inicial'])
                lo, hi = row['rango']
                lo_s = "-∞" if lo is None else fmt(lo)
                hi_s = "+∞" if hi is None else fmt(hi)
                rango_s = f"{lo_s} <= {param} <= {hi_s}"

                tk.Label(self._frame_sensibilidad, text=param,   font=cell_font, bg=BG_PANEL, fg=FG_TEXTO).grid(row=row_idx, column=0, sticky="w", padx=4, pady=1)
                tk.Label(self._frame_sensibilidad, text=val,     font=cell_font, bg=BG_PANEL, fg=FG_TEXTO).grid(row=row_idx, column=1, sticky="e", padx=4)
                tk.Label(self._frame_sensibilidad, text=rango_s, font=cell_font, bg=BG_PANEL, fg=FG_TEXTO).grid(row=row_idx, column=2, sticky="w", padx=4)
                row_idx += 1

    def ocultar_sensibilidad(self):
        """Elimina la vista de sensibilidad si existe."""
        if hasattr(self, '_frame_sensibilidad'):
            try:
                self._frame_sensibilidad.destroy()
            except Exception:
                pass
            delattr(self, '_frame_sensibilidad')

    def limpiar(self):
        """Limpia el panel."""
        for item in self._tabla.get_children():
            self._tabla.delete(item)
        for widget in self._frame_info_basicas.winfo_children():
            widget.destroy()
        self._limpiar_info_pivote()
        self._lbl_iteracion.config(text="Esperando resolver problema...")
        self._iteracion_actual = None

    # ── Internos ───────────────────────────────────────────────────────────────

    def _construir_info_basicas(self, datos: dict):
        """Rellena el frame de variables básicas."""
        for widget in self._frame_info_basicas.winfo_children():
            widget.destroy()

        tk.Label(
            self._frame_info_basicas,
            text="Variables Básicas:",
            font=("Segoe UI", 11, "bold"),
            bg=BG_PANEL,
            fg=FG_HEADER,
        ).pack(anchor="w")

        for i, (restriccion, var_basica) in enumerate(
            zip(datos['filas'][1:], datos['variables_basicas'])
        ):
            info_text = f"  {restriccion}: {var_basica} = {datos['terminos_independientes'][i + 1]}"
            tk.Label(
                self._frame_info_basicas,
                text=info_text,
                font=("Consolas", 11),
                bg=BG_PANEL,
                fg=FG_TEXTO,
            ).pack(anchor="w")

        # Limpiar sensibilidad previa al mostrar nueva iteración
        if hasattr(self, '_frame_sensibilidad'):
            self._frame_sensibilidad.destroy()
            delattr(self, '_frame_sensibilidad')

    def _mostrar_info_pivote(self, iteracion: Iteracion):
        """Muestra información sobre el pivotaje realizado."""
        for widget in self._frame_info_pivote.winfo_children():
            widget.destroy()

        tk.Label(
            self._frame_info_pivote,
            text="📊 Información de Pivotaje",
            font=("Segoe UI", 10, "bold"),
            bg=BG_INFO_PIVOTE,
            fg=FG_HEADER,
        ).pack(anchor="w", padx=8, pady=(6, 3))

        frame_vars = tk.Frame(self._frame_info_pivote, bg=BG_INFO_PIVOTE)
        frame_vars.pack(anchor="w", padx=12, pady=2)

        var_entra = str(iteracion.variable_entrante) if iteracion.variable_entrante else "—"
        var_sale  = str(iteracion.variable_saliente) if iteracion.variable_saliente else "—"

        for texto, valor, color in [
            ("Entra: ", var_entra, COLOR_PIVOTE_COLUMNA),
            ("| Sale: ", var_sale, COLOR_PIVOTE_FILA),
        ]:
            tk.Label(frame_vars, text=texto, font=("Consolas", 10),
                     bg=BG_INFO_PIVOTE, fg=FG_HEADER).pack(side="left")
            tk.Label(frame_vars, text=valor, font=("Consolas", 10, "bold"),
                     bg=color, fg="white", padx=4,
                     relief="solid", borderwidth=1).pack(side="left", padx=4)

        if iteracion.razones_minimo_cociente:
            frame_razon = tk.Frame(self._frame_info_pivote, bg=BG_INFO_PIVOTE)
            frame_razon.pack(anchor="w", padx=12, pady=2)

            razones_validas = [
                r for r in iteracion.razones_minimo_cociente
                if r != float('inf') and r is not None
            ]
            razon_min = min(razones_validas) if razones_validas else None

            tk.Label(frame_razon, text="Razón mínima: ",
                     font=("Consolas", 10), bg=BG_INFO_PIVOTE,
                     fg=FG_HEADER).pack(side="left")

            if razon_min is not None:
                tk.Label(frame_razon, text=f"{razon_min:.6g}",
                         font=("Consolas", 10, "bold"),
                         bg=COLOR_RAZON_MINIMA, fg="white",
                         padx=4, relief="solid", borderwidth=1).pack(side="left", padx=4)

        frame_op = tk.Frame(self._frame_info_pivote, bg=BG_INFO_PIVOTE)
        frame_op.pack(anchor="w", padx=12, pady=3)
        tk.Label(
            frame_op,
            text="Operación: F_pivote ÷ pivote; F_i ← F_i − a[i,j] × F_pivote",
            font=("Consolas", 9),
            bg=BG_INFO_PIVOTE,
            fg=FG_TEXTO,
            wraplength=350,
            justify="left",
        ).pack(anchor="w")

    def _limpiar_info_pivote(self):
        """Limpia el panel de información de pivotaje."""
        self._tabla.limpiar_resaltado()
        for widget in self._frame_info_pivote.winfo_children():
            widget.destroy()