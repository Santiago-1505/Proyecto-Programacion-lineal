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
    - Tabla con encabezados
    - Variables básicas
    - Términos independientes
    """
    
    def __init__(self, parent, **kwargs):
        kwargs.setdefault("bg", BG_PANEL)
        super().__init__(parent, **kwargs)
        
        self._iteracion_actual = None
        self._construir_layout()
    
    def _construir_layout(self):
        """Construye la estructura del panel."""
        
        # Encabezado
        header = tk.Frame(self, bg=BG_HEADER, pady=12)
        header.pack(fill="x")
        
        self._lbl_titulo = tk.Label(
            header,
            text="Tabla Simplex - Método de la Gran M",
            font=("Georgia", 16, "bold"),
            bg=BG_HEADER,
            fg=FG_TEXTO
        )
        self._lbl_titulo.pack()
        
        self._lbl_iteracion = tk.Label(
            header,
            text="Esperando resolver problema...",
            font=("Segoe UI", 12),
            bg=BG_HEADER,
            fg=FG_HEADER
        )
        self._lbl_iteracion.pack()
        
        # Separador
        tk.Frame(self, height=2, bg=COLOR_BORDE).pack(fill="x")
        
        # Frame para scroll
        container = tk.Frame(self, bg=BG_PANEL)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Frame con scroll para la tabla
        scrollbar_v = ttk.Scrollbar(container, orient="vertical")
        scrollbar_h = ttk.Scrollbar(container, orient="horizontal")
        
        self._tabla = TablaSimplex(
            container,
            yscrollcommand=scrollbar_v.set,
            xscrollcommand=scrollbar_h.set
        )
        
        scrollbar_v.config(command=self._tabla.yview)
        scrollbar_h.config(command=self._tabla.xview)
        
        # Grid layout para tabla con scrollbars
        self._tabla.grid(row=0, column=0, sticky="nsew")
        scrollbar_v.grid(row=0, column=1, sticky="ns")
        scrollbar_h.grid(row=1, column=0, sticky="ew")
        
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        # Frame para información de variables básicas
        self._frame_info_basicas = tk.Frame(self, bg=BG_PANEL)
        self._frame_info_basicas.pack(fill="x", padx=10, pady=5)
        
        # Frame para información de pivotaje (nueva)
        self._frame_info_pivote = tk.Frame(self, bg=BG_INFO_PIVOTE, relief="sunken", borderwidth=1)
        self._frame_info_pivote.pack(fill="x", padx=10, pady=5)
    
    def mostrar_iteracion(self, iteracion: Iteracion):
        """
        Muestra una iteración del simplex en el panel.
        
        Args:
            iteracion: Objeto Iteracion con los datos a mostrar
        """
        self._iteracion_actual = iteracion
        
        # Actualizar etiqueta de iteración
        self._lbl_iteracion.config(
            text=f"Iteración {iteracion.numero_iteracion} | "
                 f"{iteracion.obtener_num_restricciones()} restricciones, "
                 f"{iteracion.obtener_num_variables()} variables"
        )
        
        # Obtener datos formateados
        datos = FormateadorTableau.obtener_datos_tabla(iteracion)
        
        # Cargar tabla simplex
        self._tabla.cargar_iteracion(iteracion)
        
        # Resaltar pivote si corresponde (iteración > 1)
        if iteracion.numero_iteracion > 1 and iteracion.columna_pivote >= 0 and iteracion.fila_pivote >= 0:
            self._tabla.resaltar_pivote(iteracion.fila_pivote, iteracion.columna_pivote)
            self._mostrar_info_pivote(iteracion)
        else:
            self._limpiar_info_pivote()
        
        # Información de variables básicas
        self._construir_info_basicas(datos)
    
    def _construir_info_basicas(self, datos: dict):
        """Muestra la información de variables básicas."""
        
        # Limpiar información anterior
        for widget in self._frame_info_basicas.winfo_children():
            widget.destroy()
        
        tk.Label(
            self._frame_info_basicas,
            text="Variables Básicas:",
            font=("Segoe UI", 11, "bold"),
            bg=BG_PANEL,
            fg=FG_HEADER
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
                fg=FG_TEXTO
            ).pack(anchor="w")

        # Remover panel de sensibilidad previo si existía
        if hasattr(self, '_frame_sensibilidad'):
            self._frame_sensibilidad.destroy()

    def mostrar_sensibilidad(self, sensibilidad: dict):
        """Muestra una tabla simple de análisis de sensibilidad con 3 columnas.

        sensibilidad: dict retornado por core.analisis_sensibilidad.calcular_sensibilidad
        """
        # Limpiar panel previo
        if hasattr(self, '_frame_sensibilidad'):
            self._frame_sensibilidad.destroy()

        self._frame_sensibilidad = tk.Frame(self, bg=BG_PANEL)
        self._frame_sensibilidad.pack(fill="x", padx=10, pady=(2, 8))

        tk.Label(
            self._frame_sensibilidad,
            text="Análisis de Sensibilidad:",
            font=("Segoe UI", 11, "bold"),
            bg=BG_PANEL,
            fg=FG_HEADER
        ).pack(anchor="w")

        # Crear encabezados
        header = tk.Frame(self._frame_sensibilidad, bg=BG_PANEL)
        header.pack(fill="x", pady=(4, 2))
        tk.Label(header, text="Parámetro", font=("Consolas", 10, "bold"), bg=BG_PANEL, fg=FG_TEXTO, width=20, anchor="w").grid(row=0, column=0)
        tk.Label(header, text="Valor Inicial", font=("Consolas", 10, "bold"), bg=BG_PANEL, fg=FG_TEXTO, width=16, anchor="e").grid(row=0, column=1)
        tk.Label(header, text="Rango Permitido", font=("Consolas", 10, "bold"), bg=BG_PANEL, fg=FG_TEXTO, width=40, anchor="w").grid(row=0, column=2)

        def fmt_limit(val):
            if val is None:
                return "-∞" if isinstance(val, float) or val is None else str(val)
            return FormateadorTableau.formatear_coeficiente(val)

        # Mostrar coeficientes objetivo
        for row in sensibilidad.get('coef_objetivo', []):
            param = row['parametro']
            val = FormateadorTableau.formatear_coeficiente(row['valor_inicial'])
            lo, hi = row['rango']
            lo_s = "-∞" if lo is None else FormateadorTableau.formatear_coeficiente(lo)
            hi_s = "+∞" if hi is None else FormateadorTableau.formatear_coeficiente(hi)
            rango_s = f"{lo_s} <= {param} <= {hi_s}"

            frame_row = tk.Frame(self._frame_sensibilidad, bg=BG_PANEL)
            frame_row.pack(fill="x")
            tk.Label(frame_row, text=param, font=("Consolas", 10), bg=BG_PANEL, fg=FG_TEXTO, width=20, anchor="w").grid(row=0, column=0)
            tk.Label(frame_row, text=val, font=("Consolas", 10), bg=BG_PANEL, fg=FG_TEXTO, width=16, anchor="e").grid(row=0, column=1)
            tk.Label(frame_row, text=rango_s, font=("Consolas", 10), bg=BG_PANEL, fg=FG_TEXTO, width=40, anchor="w").grid(row=0, column=2)

        # Mostrar RHS
        for row in sensibilidad.get('rhs', []):
            param = row['parametro']
            val = FormateadorTableau.formatear_coeficiente(row['valor_inicial'])
            lo, hi = row['rango']
            lo_s = "-∞" if lo is None else FormateadorTableau.formatear_coeficiente(lo)
            hi_s = "+∞" if hi is None else FormateadorTableau.formatear_coeficiente(hi)
            rango_s = f"{lo_s} <= {param} <= {hi_s}"

            frame_row = tk.Frame(self._frame_sensibilidad, bg=BG_PANEL)
            frame_row.pack(fill="x")
            tk.Label(frame_row, text=param, font=("Consolas", 10), bg=BG_PANEL, fg=FG_TEXTO, width=20, anchor="w").grid(row=0, column=0)
            tk.Label(frame_row, text=val, font=("Consolas", 10), bg=BG_PANEL, fg=FG_TEXTO, width=16, anchor="e").grid(row=0, column=1)
            tk.Label(frame_row, text=rango_s, font=("Consolas", 10), bg=BG_PANEL, fg=FG_TEXTO, width=40, anchor="w").grid(row=0, column=2)

    def ocultar_sensibilidad(self):
        """Oculta/elimina la vista de sensibilidad si existe."""
        if hasattr(self, '_frame_sensibilidad'):
            try:
                self._frame_sensibilidad.destroy()
            except Exception:
                pass
            delattr(self, '_frame_sensibilidad')

    
    def limpiar(self):
        """Limpia el panel."""
        # Limpiar tabla
        for item in self._tabla.get_children():
            self._tabla.delete(item)
        
        # Limpiar información
        for widget in self._frame_info_basicas.winfo_children():
            widget.destroy()
        
        self._limpiar_info_pivote()
        
        self._lbl_iteracion.config(text="Esperando resolver problema...")
        self._iteracion_actual = None
    
    def _mostrar_info_pivote(self, iteracion: Iteracion):
        """
        Muestra información sobre el pivotaje realizado.
        
        Args:
            iteracion: Iteración con datos de pivotaje
        """
        # Limpiar información anterior
        for widget in self._frame_info_pivote.winfo_children():
            widget.destroy()
        
        # Título
        tk.Label(
            self._frame_info_pivote,
            text="📊 Información de Pivotaje",
            font=("Segoe UI", 10, "bold"),
            bg=BG_INFO_PIVOTE,
            fg=FG_HEADER
        ).pack(anchor="w", padx=8, pady=(6, 3))
        
        # Variables que entran y salen
        frame_vars = tk.Frame(self._frame_info_pivote, bg=BG_INFO_PIVOTE)
        frame_vars.pack(anchor="w", padx=12, pady=2)
        
        var_entra = str(iteracion.variable_entrante) if iteracion.variable_entrante else "—"
        var_sale = str(iteracion.variable_saliente) if iteracion.variable_saliente else "—"
        
        tk.Label(
            frame_vars,
            text=f"Entra: ",
            font=("Consolas", 10),
            bg=BG_INFO_PIVOTE,
            fg=FG_HEADER
        ).pack(side="left")
        
        tk.Label(
            frame_vars,
            text=f"{var_entra}",
            font=("Consolas", 10, "bold"),
            bg=COLOR_PIVOTE_COLUMNA,
            fg="white",
            padx=4,
            relief="solid",
            borderwidth=1
        ).pack(side="left", padx=4)
        
        tk.Label(
            frame_vars,
            text=f"| Sale: ",
            font=("Consolas", 10),
            bg=BG_INFO_PIVOTE,
            fg=FG_HEADER
        ).pack(side="left")
        
        tk.Label(
            frame_vars,
            text=f"{var_sale}",
            font=("Consolas", 10, "bold"),
            bg=COLOR_PIVOTE_FILA,
            fg="white",
            padx=4,
            relief="solid",
            borderwidth=1
        ).pack(side="left", padx=4)
        
        # Razón mínima
        frame_razon = tk.Frame(self._frame_info_pivote, bg=BG_INFO_PIVOTE)
        frame_razon.pack(anchor="w", padx=12, pady=2)
        
        if iteracion.razones_minimo_cociente:
            # Encontrar la razón mínima
            razones_validas = [r for r in iteracion.razones_minimo_cociente if r != float('inf') and r is not None]
            razon_min = min(razones_validas) if razones_validas else None
            
            tk.Label(
                frame_razon,
                text=f"Razón mínima: ",
                font=("Consolas", 10),
                bg=BG_INFO_PIVOTE,
                fg=FG_HEADER
            ).pack(side="left")
            
            if razon_min is not None:
                tk.Label(
                    frame_razon,
                    text=f"{razon_min:.6g}",
                    font=("Consolas", 10, "bold"),
                    bg=COLOR_RAZON_MINIMA,
                    fg="white",
                    padx=4,
                    relief="solid",
                    borderwidth=1
                ).pack(side="left", padx=4)
        
        # Operación de fila (pequeño resumen)
        frame_op = tk.Frame(self._frame_info_pivote, bg=BG_INFO_PIVOTE)
        frame_op.pack(anchor="w", padx=12, pady=3)
        
        tk.Label(
            frame_op,
            text="Operación: F_pivote ÷ pivote; F_i ← F_i − a[i,j] × F_pivote",
            font=("Consolas", 9),
            bg=BG_INFO_PIVOTE,
            fg=FG_TEXTO,
            wraplength=350,
            justify="left"
        ).pack(anchor="w")
    
    def _limpiar_info_pivote(self):
        """Limpia el panel de información de pivotaje."""
        self._tabla.limpiar_resaltado()
        for widget in self._frame_info_pivote.winfo_children():
            widget.destroy()
