"""
Utilidades para formatear y mostrar el tableau en la UI.
"""

from core.modelo import Iteracion, Variable


class FormateadorTableau:
    """Clase para formatear datos del tableau para visualización."""
    
    PRECISION = 2  # Dos decimales como especificó el usuario
    
    @staticmethod
    def formatear_coeficiente(valor) -> str:
        """
        Formatea un coeficiente para mostrar.
        
        - Si es un string (ej: "M"), retorna tal cual
        - Si es float, redondea a 2 decimales
        
        Args:
            valor: float o str (representación de M)
        
        Returns:
            String formateado
        """
        if isinstance(valor, str):
            return valor
        
        if isinstance(valor, (int, float)):
            return f"{float(valor):.{FormateadorTableau.PRECISION}f}"
        
        return str(valor)
    
    @staticmethod
    def formatear_fila(fila: list) -> list[str]:
        """Formatea una fila completa del tableau."""
        return [FormateadorTableau.formatear_coeficiente(v) for v in fila]
    
    @staticmethod
    def obtener_nombres_columnas(iteracion: Iteracion) -> list[str]:
        """
        Obtiene los nombres de las columnas del tableau.
        
        Returns:
            Lista con nombres de variables formateados
        """
        nombres = []
        for var in iteracion.nombres_variables_todas:
            nombres.append(str(var))
        return nombres
    
    @staticmethod
    def obtener_datos_tabla(iteracion: Iteracion) -> dict:
        """
        Prepara datos completos para mostrar el tableau.
        
        Returns:
            Dict con:
            - 'encabezados': List[str] - nombres de variables
            - 'filas': List[str] - etiquetas de filas (Z, R1, R2, ...)
            - 'datos': List[List[str]] - tabla formateada
            - 'terminos_independientes': List[str] - vector b formateado
            - 'variables_basicas': List[str] - variables básicas de cada restricción
        """
        encabezados = FormateadorTableau.obtener_nombres_columnas(iteracion)
        
        # Etiquetas de filas
        filas = ["Z"]
        for i in range(iteracion.obtener_num_restricciones()):
            filas.append(f"R{i + 1}")
        
        # Datos del tableau formateados
        datos = [FormateadorTableau.formatear_fila(fila) for fila in iteracion.tableau]
        
        # Vector b formateado
        terminos_ind = FormateadorTableau.formatear_fila(iteracion.terminos_independientes)
        
        # Variables básicas
        variables_basicas = [str(var) for var in iteracion.variables_basicas]
        
        return {
            'encabezados': encabezados,
            'filas': filas,
            'datos': datos,
            'terminos_independientes': terminos_ind,
            'variables_basicas': variables_basicas,
        }


def construir_info_iteracion(iteracion: Iteracion) -> str:
    """
    Construye una descripción legible de la iteración para mostrar al usuario.
    
    Returns:
        String con información de la iteración
    """
    info = f"ITERACIÓN {iteracion.numero_iteracion}\n"
    info += f"=" * 40 + "\n"
    info += f"Variables básicas: {', '.join(str(v) for v in iteracion.variables_basicas)}\n"
    info += f"Número de restricciones: {iteracion.obtener_num_restricciones()}\n"
    info += f"Número de variables: {iteracion.obtener_num_variables()}\n"
    
    return info
