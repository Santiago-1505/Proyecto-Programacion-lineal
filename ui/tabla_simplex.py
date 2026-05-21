"""
Componente visual para mostrar el tableau simplex usando ttk.Treeview.

Proporciona:
- Alineación perfecta de columnas
- Anchos dinámicos basados en contenido
- Fuentes grandes y legibles (12pt+)
- Scroll integrado
- Estilos personalizados oscuros
"""

import tkinter as tk
from tkinter import ttk
from core.modelo import Iteracion
from ui.formateador_tableau import FormateadorTableau


# Colores del tema
BG_PANEL = "#0f1923"
BG_TABLA = "#141e2b"
BG_HEADER = "#1e2a3a"
BG_ALT_ROW = "#0a1622"
FG_TEXTO = "#e8edf2"
FG_HEADER = "#7fb3d3"
COLOR_BORDE = "#2d4a6e"
COLOR_M = "#d4a574"
COLOR_BASICA = "#1a6b3c"


class TablaSimplex(ttk.Treeview):
    """
    Tabla especializada para visualizar el tableau simplex.
    
    Características:
    - Alineación automática perfecta
    - Anchos de columna dinámicos
    - Fuentes grandes (12pt para headers, 11pt para datos)
    - Scroll integrado
    - Estilos personalizados
    """
    
    def __init__(self, parent, **kwargs):
        """
        Inicializa la tabla simplex.
        
        Args:
            parent: Widget padre
            **kwargs: Argumentos adicionales para ttk.Treeview
        """
        super().__init__(parent, **kwargs)
        
        self._iteracion_actual = None
        self._configurar_estilos()
        self._configurar_propiedades()
    
    def _configurar_estilos(self):
        """Configura estilos personalizados para la tabla."""
        style = ttk.Style()
        
        # Estilo para encabezados
        style.configure(
            "Treeview.Heading",
            font=("Consolas", 12, "bold"),
            background=BG_HEADER,
            foreground=FG_HEADER,
            relief="solid",
            borderwidth=1
        )
        
        # Estilo para filas normales
        style.configure(
            "Treeview",
            font=("Consolas", 11),
            background=BG_TABLA,
            foreground=FG_TEXTO,
            fieldbackground=BG_TABLA,
            relief="solid",
            borderwidth=1,
            rowheight=30  # Altura de filas más grande
        )
        
        # Estilo para filas alternadas
        style.map(
            "Treeview",
            background=[("alternate", BG_ALT_ROW)],
            foreground=[("alternate", FG_TEXTO)]
        )
    
    def _configurar_propiedades(self):
        """Configura propiedades de la tabla."""
        # Activar filas alternadas
        self["selectmode"] = "none"  # No permitir selección
        self.tag_configure("oddrow", background=BG_ALT_ROW)
        self.tag_configure("evenrow", background=BG_TABLA)
        
        # Tag especial para valores de M
        self.tag_configure("valor_m", background=COLOR_M, foreground="black", font=("Consolas", 11, "bold"))
        
        # Tag especial para término independiente
        self.tag_configure("termino_ind", background=COLOR_BASICA, foreground=FG_TEXTO, font=("Consolas", 11, "bold"))
    
    def cargar_iteracion(self, iteracion: Iteracion):
        """
        Carga una iteración del tableau en la tabla.
        
        Args:
            iteracion: Objeto Iteracion con los datos
        """
        self._iteracion_actual = iteracion
        
        # Limpiar tabla anterior
        for item in self.get_children():
            self.delete(item)
        
        # Obtener datos formateados
        datos = FormateadorTableau.obtener_datos_tabla(iteracion)
        
        # Configurar columnas: Fila | Variables | b
        columnas = ["Fila"] + datos["encabezados"] + ["b"]
        self["columns"] = columnas
        
        # Configurar columna índice (primera, sin header visible)
        self.column("#0", width=0, stretch=False)
        self.heading("#0", text="", command=lambda: None)
        
        # Configurar columnas de datos con anchos dinámicos
        self._configurar_anchos_columnas(columnas, datos)
        
        # Cargar datos en la tabla
        self._insertar_datos(datos)
    
    def _configurar_anchos_columnas(self, columnas, datos):
        """
        Configura anchos de columnas de forma dinámica basados en contenido.
        
        Args:
            columnas: Lista de nombres de columnas
            datos: Diccionario con datos formateados
        """
        # Ancho mínimo por columna (en píxeles)
        ANCHO_MIN = 60
        ANCHO_PADRON_HEADER = 12  # caracteres * font size
        ANCHO_CHAR = 7  # píxeles por carácter en Consolas 11pt
        
        # Calcular anchos para cada columna
        for i, col in enumerate(columnas):
            if col == "Fila":
                ancho = max(ANCHO_MIN, 40)
            elif col == "b":
                # Columna de términos independientes
                max_len = max(len(str(v)) for v in datos["terminos_independientes"])
                ancho = max(ANCHO_MIN, int(max_len * ANCHO_CHAR) + 20)
            else:
                # Columnas de variables - calcular basado en nombre y valores
                max_len_header = len(col)
                max_len_valores = max(
                    len(str(datos["datos"][j][i - 1]))
                    for j in range(len(datos["datos"]))
                )
                max_len = max(max_len_header, max_len_valores)
                ancho = max(ANCHO_MIN, int(max_len * ANCHO_CHAR) + 20)
            
            self.column(col, width=ancho, anchor="center")
            self.heading(col, text=col, command=lambda: None)
    
    def _insertar_datos(self, datos):
        """
        Inserta datos en la tabla.
        
        Args:
            datos: Diccionario con datos formateados
        """
        # Insertar fila Z (función objetivo)
        valores_z = [datos["filas"][0]] + datos["datos"][0] + [datos["terminos_independientes"][0]]
        
        # Construir lista con tags para valores especiales
        tags_z = []
        for i, valor in enumerate(valores_z):
            if valor == "M":
                tags_z.append("valor_m")
            else:
                tags_z.append("evenrow")
        
        self.insert("", "end", values=valores_z, tags=tags_z)
        
        # Insertar restricciones (R1, R2, ...)
        for idx, (fila_label, fila_datos, termino_ind) in enumerate(
            zip(datos["filas"][1:], datos["datos"][1:], datos["terminos_independientes"][1:])
        ):
            valores_fila = [fila_label] + fila_datos + [termino_ind]
            
            # Asignar tags: alternancia de filas + tags especiales
            tags_fila = []
            for valor in valores_fila:
                if valor == "M":
                    tags_fila.append("valor_m")
                elif valor == termino_ind:
                    tags_fila.append("termino_ind")
                else:
                    tags_fila.append("oddrow" if idx % 2 == 0 else "evenrow")
            
            self.insert("", "end", values=valores_fila, tags=tags_fila)
    
    def obtener_iteracion_actual(self):
        """Retorna la iteración actualmente mostrada."""
        return self._iteracion_actual
