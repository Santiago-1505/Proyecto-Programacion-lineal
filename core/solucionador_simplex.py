"""
Solucionador simplex con método Gran M.

Este módulo gestiona el progreso del algoritmo simplex iteración por iteración,
incluyendo la Fase 1 (eliminación de variables artificiales) y Fase 2 (optimización).
"""

from core.modelo import Iteracion, Variable, TipoVariable
from core import simplex_utils


class SolucionadorSimplex:
    """
    Gestiona la resolución de un problema de PL usando el método simplex.
    
    Soporta:
    - Fase 1 del Gran M: elimina variables artificiales
    - Fase 2: optimización del problema original
    - Detección de infactibilidad, ilimitado
    """
    
    def __init__(self, iteracion_inicial: Iteracion, es_minimizacion: bool):
        """
        Inicializa el solucionador con la primera iteración.
        
        Args:
            iteracion_inicial: Objeto Iteracion con el tableau inicial
            es_minimizacion: True si es problema de minimización, False si es maximización
        """
        self.iteraciones = [iteracion_inicial]
        self.iteracion_actual = 0
        self.resuelto = False
        self.es_minimizacion = es_minimizacion
        self.es_ilimitado = False
        self.es_infactible = False
        
        # Información de pivotaje de la iteración actual
        self.columna_pivote_actual = None
        self.fila_pivote_actual = None
        self.razones_minimo_cociente = None
        
        # Estado de la Fase 1
        self.en_fase_1 = self._tiene_variables_artificiales(iteracion_inicial)
        
        # Multiplicador para corregir el valor Z al reportar:
        # Minimización se resuelve como MAX -c·x, por lo que el Z del tableau
        # es el negativo del valor real. Se multiplica por -1 al reportar.
        self._z_multiplier = -1.0 if es_minimizacion else 1.0
    
    def _tiene_variables_artificiales(self, iteracion: Iteracion) -> bool:
        """Verifica si hay variables artificiales en la base inicial."""
        for var in iteracion.variables_basicas:
            if var.tipo == TipoVariable.ARTIFICIAL:
                return True
        return False
    
    def obtener_iteracion_actual(self) -> Iteracion:
        """Retorna la iteración actual."""
        return self.iteraciones[self.iteracion_actual]
    
    def obtener_valor_objetivo(self) -> float:
        """
        Retorna el valor Z corregido según el tipo de optimización.
        
        Para minimización, el tableau almacena el valor de MAX -c·x,
        por lo que se multiplica por -1 para obtener el mínimo real.
        """
        return self._z_multiplier * self.obtener_iteracion_actual().terminos_independientes[0]
    
    def puede_avanzar(self) -> bool:
        """
        Determina si se puede avanzar a la siguiente iteración.
        
        Retorna False si:
        - Se alcanzó la solución óptima
        - El problema es ilimitado o infactible
        """
        if self.resuelto or self.es_ilimitado or self.es_infactible:
            return False
        
        iteracion_actual = self.obtener_iteracion_actual()
        
        # Si estamos en Fase 1, buscar si podemos eliminar artificiales
        if self.en_fase_1:
            col_entrante = self._seleccionar_variable_entrante(iteracion_actual)
            if col_entrante is not None:
                return True
            # En Fase 1, si no hay variable entrante, verificar si A1 fue eliminada
            for var in iteracion_actual.variables_basicas:
                if var.tipo == TipoVariable.ARTIFICIAL:
                    return True  # Aún hay artificial en base
            # Fase 1 completada, pasar a Fase 2
            self.en_fase_1 = False
        
        # Fase 2: búsqueda normal de optimidad
        col_entrante = self._seleccionar_variable_entrante(iteracion_actual)
        return col_entrante is not None
    
    def siguiente_iteracion(self):
        """
        Avanza a la siguiente iteración del algoritmo.
        
        Realiza los pasos:
        1. Seleccionar variable entrante
        2. Seleccionar variable saliente (mínimo cociente)
        3. Realizar operaciones de pivoteo
        4. Crear nueva iteración
        5. Verificar optimalidad
        
        Raises:
            RuntimeError: Si el problema es ilimitado, infactible o ya está resuelto
        """
        if self.resuelto:
            raise RuntimeError("El problema ya ha sido resuelto")
        
        if self.es_ilimitado:
            raise RuntimeError("El problema es ilimitado")
        
        if self.es_infactible:
            raise RuntimeError("El problema es infactible")
        
        iteracion_actual = self.obtener_iteracion_actual()
        
        # Seleccionar variable entrante
        col_entrante = self._seleccionar_variable_entrante(iteracion_actual)
        
        if col_entrante is None:
            # Verificar si estamos en Fase 1
            if self.en_fase_1:
                # Verificar si hay artificiales no eliminadas
                hay_artificial = any(
                    var.tipo == TipoVariable.ARTIFICIAL 
                    for var in iteracion_actual.variables_basicas
                )
                if hay_artificial:
                    # Problema infactible
                    self.es_infactible = True
                    raise RuntimeError("El problema es infactible (variable artificial no se eliminó)")
                # Transicionar a Fase 2
                self.en_fase_1 = False
                # Reintentar
                return self.siguiente_iteracion()
            else:
                # Se alcanzó óptimo en Fase 2
                self.resuelto = True
                return
        
        # Seleccionar variable saliente (calcula razones alineadas)
        razones = simplex_utils.calcular_razones_alineadas(
            iteracion_actual.tableau,
            iteracion_actual.terminos_independientes,
            col_entrante,
        )
        fila_saliente = simplex_utils.elegir_fila_pivote_desde_razones(razones)
        
        if fila_saliente is None:
            # El problema es ilimitado
            self.es_ilimitado = True
            raise RuntimeError(
                f"El problema es ilimitado. "
                f"Variable {iteracion_actual.nombres_variables_todas[col_entrante]} "
                f"puede crecer sin límite."
            )
        
        # Guardar información de pivotaje
        self.columna_pivote_actual = col_entrante
        self.fila_pivote_actual = fila_saliente
        self.razones_minimo_cociente = razones
        
        # Realizar pivoteo produciendo nuevas estructuras (no mutar iteración anterior)
        nuevo_tableau, nuevos_terminos = simplex_utils.pivot_pure(
            iteracion_actual.tableau,
            iteracion_actual.terminos_independientes,
            fila_saliente,
            col_entrante,
        )

        # Actualizar variables básicas (crear copia y reemplazar)
        nuevas_vars_basicas = iteracion_actual.variables_basicas[:]
        nueva_var_basica = iteracion_actual.nombres_variables_todas[col_entrante]
        nuevas_vars_basicas[fila_saliente - 1] = nueva_var_basica

        # Crear nueva iteración usando las copias resultantes
        nueva_iteracion = Iteracion(
            numero_iteracion=iteracion_actual.numero_iteracion + 1,
            tableau=[fila[:] for fila in nuevo_tableau],
            variables_basicas=nuevas_vars_basicas,
            terminos_independientes=nuevos_terminos[:],
            nombres_variables_todas=iteracion_actual.nombres_variables_todas[:],
            columna_pivote=col_entrante,
            fila_pivote=fila_saliente,
            razones_minimo_cociente=razones,
            variable_entrante=iteracion_actual.nombres_variables_todas[col_entrante],
            variable_saliente=iteracion_actual.variables_basicas[fila_saliente - 1]
        )

        # Agregar al historial
        self.iteraciones.append(nueva_iteracion)
        self.iteracion_actual += 1

        # Verificar optimalidad
        if self._es_optimo(nueva_iteracion):
            if self.en_fase_1:
                # En Fase 1, verificar si artificiales se eliminaron
                hay_artificial = any(
                    var.tipo == TipoVariable.ARTIFICIAL 
                    for var in nueva_iteracion.variables_basicas
                )
                if hay_artificial:
                    self.es_infactible = True
                    raise RuntimeError("El problema es infactible")
                self.en_fase_1 = False
            else:
                self.resuelto = True
            return
        # Guardar información de pivotaje en estado público para UI
        self.columna_pivote_actual = col_entrante
        self.fila_pivote_actual = fila_saliente
        self.razones_minimo_cociente = razones
    
    def _seleccionar_variable_entrante(self, iteracion: Iteracion) -> int | None:
        """
        Selecciona la variable que entra a la base.
        
        Busca el coeficiente más NEGATIVO de la fila Z.
        Si no hay negativos, se alcanzó el óptimo.
        
        Esto funciona tanto para minimización como maximización porque:
        - En minimización: el tableau se construye con signos invertidos
          (equivalente a MAX -c·x), por lo que la regla es la misma.
        - En maximización: se usa la convención estándar.
        
        Args:
            iteracion: Iteración actual
        
        Returns:
            Índice de columna (0 a n-1) o None si se alcanzó óptimo
        """
        fila_z = iteracion.tableau[0]

        best_idx = None
        best_val = None

        # Buscar coeficiente más negativo (menor que -1e-12)
        for j, val in enumerate(fila_z):
            if best_val is None or val < best_val:
                if val < -1e-12:
                    best_val = val
                    best_idx = j

        return best_idx
    
    def _seleccionar_variable_saliente(
        self,
        iteracion: Iteracion,
        columna_entrante: int
    ) -> tuple[int | None, list[float]]:
        """
        Selecciona la variable que sale de la base usando regla del mínimo cociente.
        
        Para cada restricción i:
            Si a[i][j] > 0:  razón[i] = b[i] / a[i][j]
            Si a[i][j] ≤ 0:  razón[i] = ∞
        
        Fila pivote = argmin(razón[i])
        
        Args:
            iteracion: Iteración actual
            columna_entrante: Índice de la columna que entra
        
        Returns:
            (índice_fila_pivote, vector_razones) o (None, []) si es ilimitado
        """
        # Delegar cálculo de razones al utilitario (devuelve lista alineada)
        razones = simplex_utils.calcular_razones_alineadas(
            iteracion.tableau,
            iteracion.terminos_independientes,
            columna_entrante,
        )

        fila_pivote = simplex_utils.elegir_fila_pivote_desde_razones(razones)
        if fila_pivote is None:
            return None, razones
        return fila_pivote, razones
    
    def _realizar_pivoteo(
        self,
        iteracion: Iteracion,
        fila_pivote: int,
        columna_pivote: int
    ):
        """
        Realiza las operaciones de fila para el pivoteo en lugar.
        
        Pasos:
        1. Normalizar fila pivote: dividir entre el pivote
        2. Eliminar en otras filas: usar operaciones de fila elementales
        
        Modifica directamente iteracion.tableau y iteracion.terminos_independientes
        
        Args:
            iteracion: Iteración a pivotear
            fila_pivote: Índice de fila pivote (1-indexed en el tableau)
            columna_pivote: Índice de columna pivote (0-indexed)
        """
        # Ahora delegamos la lógica al utilitario puro para evitar mutaciones.
        # Este método queda como wrapper por compatibilidad interna y no muta
        # la iteración pasada; se mantiene para llamadas antiguas pero su uso
        # no es recomendado.
        tabla, terminos = simplex_utils.pivot_pure(
            iteracion.tableau,
            iteracion.terminos_independientes,
            fila_pivote,
            columna_pivote,
        )
        # No se asigna de vuelta a `iteracion` para evitar mutar historiales.
        return tabla, terminos
    
    def _es_optimo(self, iteracion: Iteracion) -> bool:
        """
        Verifica si se alcanzó la solución óptima.
        
        Óptimo se alcanza cuando TODOS los coeficientes de la fila Z son ≥ 0
        (dentro de tolerancia). Esto funciona para ambos tipos de optimización
        porque la minimización se transforma a MAX -c·x en la construcción.
        
        Args:
            iteracion: Iteración a verificar
        
        Returns:
            True si es óptimo, False en caso contrario
        """
        fila_z = iteracion.tableau[0]
        tolerancia = 1e-9

        # Todos los coeficientes deben ser >= 0
        return all(coef >= -tolerancia for coef in fila_z)
    
    def _crear_siguiente_iteracion(
        self,
        iteracion_anterior: Iteracion,
        columna_pivote: int,
        fila_pivote: int,
        razones: list[float]
    ) -> Iteracion:
        """
        Crea la siguiente iteración a partir de la actual.
        
        Copia el tableau pivoteado, las variables básicas actualizadas,
        y guarda metadatos de pivotaje para visualización.
        
        Args:
            iteracion_anterior: Iteración anterior (ya pivoteada)
            columna_pivote: Índice de columna que entra
            fila_pivote: Índice de fila que sale
            razones: Vector de razones del mínimo cociente
        
        Returns:
            Nueva Iteracion con número incrementado
        """
        nueva_iteracion = Iteracion(
            numero_iteracion=iteracion_anterior.numero_iteracion + 1,
            tableau=[fila[:] for fila in iteracion_anterior.tableau],  # Copia profunda
            variables_basicas=iteracion_anterior.variables_basicas[:],  # Copia
            terminos_independientes=iteracion_anterior.terminos_independientes[:],  # Copia
            nombres_variables_todas=iteracion_anterior.nombres_variables_todas[:],
            columna_pivote=columna_pivote,
            fila_pivote=fila_pivote,
            razones_minimo_cociente=razones,
            variable_entrante=iteracion_anterior.nombres_variables_todas[columna_pivote],
            variable_saliente=iteracion_anterior.variables_basicas[fila_pivote - 1]
        )
        
        return nueva_iteracion
