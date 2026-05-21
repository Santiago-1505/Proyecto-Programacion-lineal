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
    
    def limpiar(self):
        """Limpia el panel."""
        # Limpiar tabla
        for item in self._tabla.get_children():
            self._tabla.delete(item)
        
        # Limpiar información
        for widget in self._frame_info_basicas.winfo_children():
            widget.destroy()
        
        self._lbl_iteracion.config(text="Esperando resolver problema...")
        self._iteracion_actual = None
