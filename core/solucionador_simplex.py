"""
Solucionador simplex con método Gran M.

Este módulo gestiona el progreso del algoritmo simplex iteración por iteración.
"""

from core.modelo import Iteracion, Variable


class SolucionadorSimplex:
    """
    Gestiona la resolución de un problema de PL usando el método simplex.
    
    Mantiene control del historial de iteraciones y permite avanzar paso a paso.
    """
    
    def __init__(self, iteracion_inicial: Iteracion):
        """
        Inicializa el solucionador con la primera iteración.
        
        Args:
            iteracion_inicial: Objeto Iteracion con el tableau inicial
        """
        self.iteraciones = [iteracion_inicial]
        self.iteracion_actual = 0
        self.resuelto = False
    
    def obtener_iteracion_actual(self) -> Iteracion:
        """Retorna la iteración actual."""
        return self.iteraciones[self.iteracion_actual]
    
    def puede_avanzar(self) -> bool:
        """
        Determina si se puede avanzar a la siguiente iteración.
        
        Por ahora, retorna False (solo mostramos la primera iteración).
        """
        return False  # TODO: Implementar lógica de pivoteo
    
    def siguiente_iteracion(self):
        """
        Avanza a la siguiente iteración del algoritmo.
        
        TODO: Implementar algoritmo de pivoteo
        """
        if not self.puede_avanzar():
            raise RuntimeError("No se puede avanzar más iteraciones")
        
        # TODO: Calcular siguiente iteración
        self.iteracion_actual += 1
