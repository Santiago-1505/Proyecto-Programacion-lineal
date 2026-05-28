"""
Solucionador simplex con método Gran M.

Este módulo gestiona el progreso del algoritmo simplex iteración por iteración,
incluyendo la Fase 1 (eliminación de variables artificiales) y Fase 2 (optimización).
"""

from core.modelo import Iteracion, Variable, TipoVariable


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
    
    def _tiene_variables_artificiales(self, iteracion: Iteracion) -> bool:
        """Verifica si hay variables artificiales en la base inicial."""
        for var in iteracion.variables_basicas:
            if var.tipo == TipoVariable.ARTIFICIAL:
                return True
        return False
    
    def obtener_iteracion_actual(self) -> Iteracion:
        """Retorna la iteración actual."""
        return self.iteraciones[self.iteracion_actual]
    
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
        
        # Seleccionar variable saliente
        fila_saliente, razones = self._seleccionar_variable_saliente(
            iteracion_actual,
            col_entrante
        )
        
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
        
        # Realizar pivoteo
        self._realizar_pivoteo(iteracion_actual, fila_saliente, col_entrante)
        
        # Actualizar variables básicas
        nueva_var_basica = iteracion_actual.nombres_variables_todas[col_entrante]
        iteracion_actual.variables_basicas[fila_saliente - 1] = nueva_var_basica
        
        # Crear nueva iteración
        nueva_iteracion = self._crear_siguiente_iteracion(
            iteracion_actual,
            col_entrante,
            fila_saliente,
            razones
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
        
        # Paso 2: Seleccionar variable saliente
        fila_saliente, razones = self._seleccionar_variable_saliente(
            iteracion_actual,
            col_entrante
        )
        
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
        
        # Paso 3: Realizar pivoteo
        self._realizar_pivoteo(iteracion_actual, fila_saliente, col_entrante)
        
        # Paso 4: Actualizar variables básicas
        nueva_var_basica = iteracion_actual.nombres_variables_todas[col_entrante]
        iteracion_actual.variables_basicas[fila_saliente - 1] = nueva_var_basica
        
        # Paso 5: Crear nueva iteración
        nueva_iteracion = self._crear_siguiente_iteracion(
            iteracion_actual,
            col_entrante,
            fila_saliente,
            razones
        )
        
        # Agregar al historial
        self.iteraciones.append(nueva_iteracion)
        self.iteracion_actual += 1
        
        # Verificar optimalidad
        if self._es_optimo(nueva_iteracion):
            self.resuelto = True
    
    def _seleccionar_variable_entrante(self, iteracion: Iteracion) -> int | None:
        """
        Selecciona la variable que entra a la base.
        
        En el tableau simplex estándar, usamos SIEMPRE la misma regla:
        - Buscar el coeficiente más NEGATIVO de la fila Z
        - Si no hay negativos, hemos alcanzado óptimo
        
        Esto funciona tanto para minimización como maximización porque:
        - En minimización: los coeficientes se mantienen con su signo original
        - En maximización: los coeficientes se niegan al inicio
        
        Args:
            iteracion: Iteración actual
        
        Returns:
            Índice de columna (0 a n-1) o None si se alcanzó óptimo
        """
        fila_z = iteracion.tableau[0]
        
        # Buscar coeficiente más NEGATIVO
        min_idx = None
        min_val = 0.0
        
        for j in range(len(fila_z)):
            if fila_z[j] < min_val:
                min_val = fila_z[j]
                min_idx = j
        
        return min_idx
    
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
        razones = []
        fila_pivote = None
        razon_minima = float('inf')
        
        # Recorrer filas de restricciones (índices 1 a m)
        num_restricciones = iteracion.obtener_num_restricciones()
        
        for i in range(1, num_restricciones + 1):
            a_ij = iteracion.tableau[i][columna_entrante]
            b_i = iteracion.terminos_independientes[i]
            
            if a_ij > 0:  # SOLO valores positivos
                razon = b_i / a_ij
                razones.append(razon)
                
                # Actualizar mínimo
                if razon < razon_minima:
                    razon_minima = razon
                    fila_pivote = i
            else:
                # Valor no positivo: razón indefinida
                razones.append(float('inf'))
        
        if fila_pivote is None:
            # No hay divisor positivo: problema ilimitado
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
        # Paso 1: Normalizar fila pivote
        pivote = iteracion.tableau[fila_pivote][columna_pivote]
        
        if abs(pivote) < 1e-12:
            raise RuntimeError(f"Pivote demasiado pequeño: {pivote}")
        
        # Dividir fila pivote entre el pivote
        for j in range(len(iteracion.tableau[fila_pivote])):
            iteracion.tableau[fila_pivote][j] /= pivote
        iteracion.terminos_independientes[fila_pivote] /= pivote
        
        # Paso 2: Eliminar en otras filas
        for i in range(len(iteracion.tableau)):
            if i != fila_pivote:
                factor = -iteracion.tableau[i][columna_pivote]
                
                for j in range(len(iteracion.tableau[i])):
                    iteracion.tableau[i][j] += factor * iteracion.tableau[fila_pivote][j]
                
                iteracion.terminos_independientes[i] += factor * iteracion.terminos_independientes[fila_pivote]
    
    def _es_optimo(self, iteracion: Iteracion) -> bool:
        """
        Verifica si se alcanzó la solución óptima.
        
        En el tableau simplex estándar:
        - Óptimo se alcanza cuando TODOS los coeficientes de la fila Z son ≥ 0
        - Esto es válido tanto para minimización como para maximización
          porque los coeficientes se tratan de forma simétrica
        
        Args:
            iteracion: Iteración a verificar
        
        Returns:
            True si es óptimo, False en caso contrario
        """
        fila_z = iteracion.tableau[0]
        tolerancia = 1e-9
        
        # Todos los coeficientes deben ser >= 0 (dentro de tolerancia)
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
