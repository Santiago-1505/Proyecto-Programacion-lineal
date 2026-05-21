"""
Panel visual para mostrar el tableau simplex iteración por iteración.
"""

import tkinter as tk
from tkinter import ttk
from core.modelo import Iteracion
from ui.formateador_tableau import FormateadorTableau


# Colores
BG_PANEL = "#0f1923"
BG_TABLA = "#141e2b"
BG_HEADER = "#1e2a3a"
FG_TEXTO = "#e8edf2"
FG_HEADER = "#7fb3d3"
COLOR_BORDE = "#2d4a6e"
COLOR_RESALTADO = "#3d8bcd"
COLOR_BASICA = "#1a6b3c"
COLOR_M = "#d4a574"  # Color dorado para M


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
            text="Tableau Simplex - Método de la Gran M",
            font=("Georgia", 14, "bold"),
            bg=BG_HEADER,
            fg=FG_TEXTO
        )
        self._lbl_titulo.pack()
        
        self._lbl_iteracion = tk.Label(
            header,
            text="Esperando resolver problema...",
            font=("Segoe UI", 10),
            bg=BG_HEADER,
            fg=FG_HEADER
        )
        self._lbl_iteracion.pack()
        
        # Separador
        tk.Frame(self, height=2, bg=COLOR_BORDE).pack(fill="x")
        
        # Frame para scroll
        container = tk.Frame(self, bg=BG_PANEL)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Canvas con scroll
        self._canvas = tk.Canvas(
            container,
            bg=BG_TABLA,
            highlightthickness=0,
            scrollregion=(0, 0, 1000, 800)
        )
        
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)
        
        self._canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Frame dentro del canvas para el contenido
        self._frame_contenido = tk.Frame(self._canvas, bg=BG_TABLA)
        self._canvas.create_window((0, 0), window=self._frame_contenido, anchor="nw")
        
        # Bind para actualizar scroll region cuando cambia el tamaño
        self._frame_contenido.bind("<Configure>", 
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
    
    def mostrar_iteracion(self, iteracion: Iteracion):
        """
        Muestra una iteración del simplex en el panel.
        
        Args:
            iteracion: Objeto Iteracion con los datos a mostrar
        """
        self._iteracion_actual = iteracion
        
        # Limpiar contenido anterior
        for widget in self._frame_contenido.winfo_children():
            widget.destroy()
        
        # Actualizar etiqueta de iteración
        self._lbl_iteracion.config(
            text=f"Iteración {iteracion.numero_iteracion} | "
                 f"{iteracion.obtener_num_restricciones()} restricciones, "
                 f"{iteracion.obtener_num_variables()} variables"
        )
        
        # Obtener datos formateados
        datos = FormateadorTableau.obtener_datos_tabla(iteracion)
        
        # Construir tabla
        self._construir_tabla(datos)
        
        # Información de variables básicas
        self._construir_info_basicas(datos)
    
    def _construir_tabla(self, datos: dict):
        """Construye la tabla visual del tableau."""
        
        frame_tabla = tk.Frame(self._frame_contenido, bg=BG_TABLA)
        frame_tabla.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Encabezado con nombres de variables
        frame_header = tk.Frame(frame_tabla, bg=BG_HEADER)
        frame_header.pack(fill="x")
        
        # Columna de etiquetas (vacía en header)
        tk.Label(
            frame_header,
            text="",
            width=6,
            bg=BG_HEADER,
            fg=FG_HEADER,
            font=("Segoe UI", 9, "bold"),
            relief="solid",
            borderwidth=1
        ).pack(side="left", padx=1, pady=1)
        
        # Nombres de variables
        for nombre in datos['encabezados']:
            tk.Label(
                frame_header,
                text=nombre,
                width=8,
                bg=BG_HEADER,
                fg=FG_HEADER,
                font=("Segoe UI", 8, "bold"),
                relief="solid",
                borderwidth=1
            ).pack(side="left", padx=1, pady=1)
        
        # Columna b (términos independientes)
        tk.Label(
            frame_header,
            text="b",
            width=8,
            bg=BG_HEADER,
            fg=FG_HEADER,
            font=("Segoe UI", 8, "bold"),
            relief="solid",
            borderwidth=1
        ).pack(side="left", padx=1, pady=1)
        
        # Filas de datos
        for i, (etiqueta, fila_datos, termino_ind) in enumerate(
            zip(datos['filas'], datos['datos'], datos['terminos_independientes'])
        ):
            frame_fila = tk.Frame(frame_tabla, bg=BG_TABLA)
            frame_fila.pack(fill="x")
            
            # Etiqueta de fila (Z o R1, R2, ...)
            color_fila = BG_HEADER if i == 0 else BG_TABLA
            tk.Label(
                frame_fila,
                text=etiqueta,
                width=6,
                bg=color_fila,
                fg=FG_HEADER,
                font=("Consolas", 9, "bold"),
                relief="solid",
                borderwidth=1
            ).pack(side="left", padx=1, pady=1)
            
            # Valores de la fila
            for valor in fila_datos:
                # Determinar color según valor
                if valor == "M":
                    color_valor = COLOR_M
                    color_texto = "black"
                else:
                    color_valor = BG_TABLA
                    color_texto = FG_TEXTO
                
                tk.Label(
                    frame_fila,
                    text=valor,
                    width=8,
                    bg=color_valor,
                    fg=color_texto,
                    font=("Consolas", 8),
                    relief="solid",
                    borderwidth=1
                ).pack(side="left", padx=1, pady=1)
            
            # Término independiente
            tk.Label(
                frame_fila,
                text=termino_ind,
                width=8,
                bg=COLOR_BASICA if i > 0 else BG_TABLA,
                fg=FG_TEXTO,
                font=("Consolas", 8, "bold"),
                relief="solid",
                borderwidth=1
            ).pack(side="left", padx=1, pady=1)
    
    def _construir_info_basicas(self, datos: dict):
        """Muestra la información de variables básicas."""
        
        frame_info = tk.Frame(self._frame_contenido, bg=BG_TABLA)
        frame_info.pack(fill="x", padx=5, pady=(10, 5))
        
        tk.Label(
            frame_info,
            text="Variables Básicas:",
            font=("Segoe UI", 9, "bold"),
            bg=BG_TABLA,
            fg=FG_HEADER
        ).pack(anchor="w")
        
        for i, (restriccion, var_basica) in enumerate(
            zip(datos['filas'][1:], datos['variables_basicas'])
        ):
            info_text = f"  {restriccion}: {var_basica} = {datos['terminos_independientes'][i + 1]}"
            tk.Label(
                frame_info,
                text=info_text,
                font=("Consolas", 8),
                bg=BG_TABLA,
                fg=FG_TEXTO
            ).pack(anchor="w")
    
    def limpiar(self):
        """Limpia el panel."""
        for widget in self._frame_contenido.winfo_children():
            widget.destroy()
        
        self._lbl_iteracion.config(text="Esperando resolver problema...")
        self._iteracion_actual = None
